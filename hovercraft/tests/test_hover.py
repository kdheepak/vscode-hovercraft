"""Tests for hover functionality."""

import json
import tempfile
from pathlib import Path


from hovercraft.hover import CSVHoverProvider, JSONHoverProvider, HoverEntry


class TestCSVHoverProvider:
    """Test CSV hover provider functionality."""

    def test_parse_filename_extension(self):
        """Test parsing extensions from CSV filenames."""
        provider = CSVHoverProvider(Path("/tmp"))

        assert provider.parse_filename_extension("hovercraft.py.csv") == ".py"
        assert provider.parse_filename_extension("hovercraft.js.csv") == ".js"
        assert provider.parse_filename_extension("hovercraft.md.csv") == ".md"
        assert provider.parse_filename_extension("invalid.csv") is None
        assert provider.parse_filename_extension("hovercraft.csv") is None

    def test_load_csv_file(self):
        """Test loading a CSV file with hover data."""
        provider = CSVHoverProvider(Path("/tmp"))

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_content = """keyword,description,category
print,Python print function,function
list,Python list type,type
dict,Python dictionary type,type"""
            f.write(csv_content)
            csv_path = Path(f.name)

        try:
            # Rename to match expected pattern
            new_path = csv_path.parent / "hovercraft.py.csv"
            csv_path.rename(new_path)

            provider.load_csv_file(new_path)

            assert ".py" in provider.entries
            assert len(provider.entries[".py"]) == 3

            # Check specific entries
            keywords = [entry.keyword for entry in provider.entries[".py"]]
            assert "print" in keywords
            assert "list" in keywords
            assert "dict" in keywords

        finally:
            new_path.unlink(missing_ok=True)

    def test_get_hover_info_exact_match(self):
        """Test getting hover info for exact keyword matches."""
        provider = CSVHoverProvider(Path("/tmp"))

        # Add test entries manually
        provider.entries[".py"] = [
            HoverEntry(
                keyword="print",
                description="Python print function",
                category="function",
            ),
            HoverEntry(keyword="List", description="Python list type", category="type"),
        ]

        # Test exact match (case insensitive)
        result = provider.get_hover_info("print", ".py")
        assert result is not None
        assert "print" in result
        assert "Python print function" in result

        # Test case insensitive match
        result = provider.get_hover_info("list", ".py")
        assert result is not None
        assert "list" in result
        assert "Python list type" in result

        # Test no match
        result = provider.get_hover_info("nonexistent", ".py")
        assert result is None

    def test_get_hover_info_regex_match(self):
        """Test getting hover info for regex pattern matches."""
        provider = CSVHoverProvider(Path("/tmp"))

        # Add test entries with regex
        provider.entries[".py"] = [
            HoverEntry(
                keyword=r"test_.*",
                description="Test function pattern",
                category="function",
                is_regex=True,
            ),
            HoverEntry(
                keyword=r".*Error",
                description="Error classes",
                category="exception",
                is_regex=True,
            ),
        ]

        # Test regex matches
        result = provider.get_hover_info("test_function", ".py")
        assert result is not None
        assert "test_function" in result
        assert "Test function pattern" in result
        assert "Regex match" in result

        result = provider.get_hover_info("ValueError", ".py")
        assert result is not None
        assert "ValueError" in result
        assert "Error classes" in result

        # Test no regex match
        result = provider.get_hover_info("regular_function", ".py")
        assert result is None

    def test_remove_csv_file(self):
        """Test removing entries from a specific CSV file."""
        provider = CSVHoverProvider(Path("/tmp"))

        # Add entries from different files with proper filenames
        provider.entries[".py"] = [
            HoverEntry(
                keyword="print",
                description="desc1",
                source_file="/tmp/hovercraft.py.csv",
            ),
            HoverEntry(
                keyword="list",
                description="desc2",
                source_file="/tmp/hovercraft2.py.csv",
            ),
            HoverEntry(
                keyword="dict",
                description="desc3",
                source_file="/tmp/hovercraft.py.csv",
            ),
        ]

        # Remove entries from hovercraft.py.csv
        provider.remove_csv_file("/tmp/hovercraft.py.csv")

        # Should only have entry from hovercraft2.py.csv
        assert len(provider.entries[".py"]) == 1
        assert provider.entries[".py"][0].keyword == "list"

    def test_get_supported_extensions(self):
        """Test getting supported file extensions."""
        provider = CSVHoverProvider(Path("/tmp"))

        provider.entries[".py"] = [HoverEntry(keyword="test", description="test")]
        provider.entries[".js"] = [HoverEntry(keyword="test", description="test")]

        extensions = provider.get_supported_extensions()
        assert extensions == {".py", ".js"}


class TestJSONHoverProvider:
    """Test JSON hover provider functionality."""

    def test_parse_filename_extension(self):
        """Test parsing extensions from JSON filenames."""
        provider = JSONHoverProvider(Path("/tmp"))

        assert provider.parse_filename_extension("hovercraft.py.json") == ".py"
        assert provider.parse_filename_extension("hovercraft.js.json") == ".js"
        assert provider.parse_filename_extension("hovercraft.md.json") == ".md"
        assert provider.parse_filename_extension("invalid.json") is None
        assert provider.parse_filename_extension("hovercraft.json") is None

    def test_load_json_file(self):
        """Test loading a JSON file with hover data."""
        provider = JSONHoverProvider(Path("/tmp"))

        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json_content = [
                {
                    "keyword": "function",
                    "description": "JavaScript function",
                    "category": "keyword",
                },
                {
                    "keyword": "var.*",
                    "description": "Variable pattern",
                    "is_regex": True,
                },
            ]
            json.dump(json_content, f)
            json_path = Path(f.name)

        try:
            # Rename to match expected pattern
            new_path = json_path.parent / "hovercraft.js.json"
            json_path.rename(new_path)

            provider.load_json_file(new_path)

            assert ".js" in provider.entries
            assert len(provider.entries[".js"]) == 2

            # Check specific entries
            keywords = [entry.keyword for entry in provider.entries[".js"]]
            assert "function" in keywords
            assert "var.*" in keywords

            # Check regex flag
            regex_entry = next(
                e for e in provider.entries[".js"] if e.keyword == "var.*"
            )
            assert regex_entry.is_regex is True

        finally:
            new_path.unlink(missing_ok=True)

    def test_get_hover_info_json(self):
        """Test getting hover info from JSON entries."""
        provider = JSONHoverProvider(Path("/tmp"))

        # Add test entries manually
        provider.entries[".js"] = [
            HoverEntry(
                keyword="console",
                description="JavaScript console object",
                category="object",
                additional_info={"example": "console.log('hello')"},
            )
        ]

        result = provider.get_hover_info("console", ".js")
        assert result is not None
        assert "console" in result
        assert "JavaScript console object" in result
        assert "Additional Information" in result
        assert "Example" in result

    def test_remove_json_file(self):
        """Test removing entries from a specific JSON file."""
        provider = JSONHoverProvider(Path("/tmp"))

        # Add entries from different files with proper filenames
        provider.entries[".js"] = [
            HoverEntry(
                keyword="func1",
                description="desc1",
                source_file="/tmp/hovercraft.js.json",
            ),
            HoverEntry(
                keyword="func2",
                description="desc2",
                source_file="/tmp/hovercraft2.js.json",
            ),
        ]

        # Remove entries from hovercraft.js.json
        provider.remove_json_file("/tmp/hovercraft.js.json")

        # Should only have entry from hovercraft2.js.json
        assert len(provider.entries[".js"]) == 1
        assert provider.entries[".js"][0].keyword == "func2"


class TestHoverEntry:
    """Test HoverEntry dataclass."""

    def test_hover_entry_creation(self):
        """Test creating HoverEntry instances."""
        entry = HoverEntry(
            keyword="test",
            description="Test description",
            category="function",
            additional_info={"example": "test()"},
            is_regex=True,
        )

        assert entry.keyword == "test"
        assert entry.description == "Test description"
        assert entry.category == "function"
        assert entry.additional_info == {"example": "test()"}
        assert entry.is_regex is True
        assert entry.word == ""  # Default value

    def test_hover_entry_defaults(self):
        """Test HoverEntry with default values."""
        entry = HoverEntry(keyword="test", description="Test description")

        assert entry.category is None
        assert entry.source_file is None
        assert entry.additional_info == {}
        assert entry.is_regex is False
        assert entry.word == ""
