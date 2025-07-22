"""CSV-based hover information provider."""

import logging
import re
from pathlib import Path
from typing import Set
from dataclasses import dataclass, field

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class HoverEntry:
    """Represents a single hover entry from CSV."""

    keyword: str
    description: str
    category: str | None = None
    source_file: str | None = None
    additional_info: dict[str, str] = field(default_factory=dict)
    is_regex: bool = False
    word: str = field(default="")


class CSVHoverProvider:
    """Manages CSV files and provides hover information."""

    # Pattern to extract extension from filename
    # Example: hovercraft.py.csv → .py
    FILENAME_PATTERN = re.compile(r"^hovercraft\.(.+)\.csv$")

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        # Store entries per file extension
        self.entries_by_extension: dict[str, list[HoverEntry]] = {}
        self.csv_files: dict[str, pd.DataFrame] = {}

    @property
    def entry_count(self) -> int:
        """Get the total number of hover entries."""
        total = 0
        for ext_entries in self.entries_by_extension.values():
            total += len(ext_entries)
        return total

    def parse_filename_extension(self, filename: str) -> str | None:
        """Parse filename to determine target file extension."""
        match = self.FILENAME_PATTERN.match(filename)
        if not match:
            logger.warning(
                f"Filename {filename} doesn't match expected pattern hovercraft.<ext>.csv"
            )
            return None

        extension = match.group(1)
        # Ensure it starts with a dot
        if not extension.startswith("."):
            extension = f".{extension}"

        return extension

    def load_all_csv_files(self):
        """Load all CSV files in the .vscode and .data directories."""
        csv_dirs = [self.workspace_path / ".vscode", self.workspace_path / ".data"]
        all_csv_files = []
        for csv_dir in csv_dirs:
            if csv_dir.exists():
                found = list(csv_dir.glob("hovercraft.*.csv"))
                logger.info(f"Found {len(found)} hover CSV files in {csv_dir}")
                all_csv_files.extend(found)
            else:
                logger.info(f"Directory not found: {csv_dir}")
        logger.info(f"Total hover CSV files found: {len(all_csv_files)}")
        for csv_file in all_csv_files:
            try:
                self.load_csv_file(csv_file)
            except Exception as e:
                logger.error(f"Failed to load {csv_file}: {e}")

    def load_csv_file(self, file_path: Path):
        """Load a single CSV file."""
        try:
            # Parse target extension from filename
            extension = self.parse_filename_extension(file_path.name)
            if not extension:
                return

            logger.info(f"Loading {file_path.name} for extension: {extension}")

            # Read CSV with pandas
            df = pd.read_csv(file_path, dtype=str)
            df = df.fillna("")

            # Store the dataframe
            self.csv_files[str(file_path)] = df

            # Expected columns
            required_columns = {"keyword", "description"}
            available_columns = set(df.columns)

            if not required_columns.issubset(available_columns):
                logger.warning(
                    f"CSV {file_path} missing required columns. "
                    f"Required: {required_columns}, Found: {available_columns}"
                )
                return

            # Initialize extension list if needed
            if extension not in self.entries_by_extension:
                self.entries_by_extension[extension] = []

            # Process each row
            for _, row in df.iterrows():
                keyword = row["keyword"].strip()
                if not keyword:
                    continue
                is_regex = False
                if "is_regex" in df.columns:
                    val = row["is_regex"].strip().lower()
                    is_regex = val in ("1", "true", "yes", "y")
                entry = HoverEntry(
                    keyword=keyword,
                    description=row["description"],
                    category=row.get("category"),
                    source_file=str(file_path),
                    additional_info={
                        col: row[col]
                        for col in df.columns
                        if col
                        not in [
                            "keyword",
                            "description",
                            "category",
                            "source_file",
                            "is_regex",
                        ]
                        and row[col]
                    },
                    is_regex=is_regex,
                )

                self.entries_by_extension[extension].append(entry)

            logger.info(
                f"Loaded {len(df)} entries from {file_path.name} "
                f"for extension: {extension}"
            )

        except Exception as e:
            logger.error(f"Error loading CSV {file_path}: {e}")

    def reload_csv_file(self, file_path: str):
        """Reload a specific CSV file."""
        # Remove old entries from this file
        self.remove_csv_file(file_path)

        # Load the file again
        path = Path(file_path)
        if self.FILENAME_PATTERN.match(path.name):
            self.load_csv_file(path)

    def remove_csv_file(self, file_path: str):
        """Remove entries from a specific CSV file."""
        # Find which extension this file was for
        path = Path(file_path)
        extension = self.parse_filename_extension(path.name)

        if not extension or extension not in self.entries_by_extension:
            return

        # Remove entries that came from this file
        before_count = len(self.entries_by_extension[extension])
        self.entries_by_extension[extension] = [
            entry
            for entry in self.entries_by_extension[extension]
            if entry.source_file != file_path
        ]
        removed_count = before_count - len(self.entries_by_extension[extension])

        # Clean up empty extension dictionary
        if not self.entries_by_extension[extension]:
            del self.entries_by_extension[extension]

        # Remove from csv_files dict
        if file_path in self.csv_files:
            del self.csv_files[file_path]

        logger.info(f"Removed {removed_count} entries from {file_path}")

    def get_hover_info(self, word: str, file_extension: str) -> str | None:
        """Get hover information for a word in a specific file type. Show all matching entries, including regex."""

        logger.debug(
            f"get_hover_info called: word='{word}', extension='{file_extension}'"
        )

        # Normalize the extension
        if not file_extension.startswith("."):
            file_extension = f".{file_extension}"

        logger.debug(f"Normalized extension: '{file_extension}'")
        logger.debug(f"Available extensions: {list(self.entries_by_extension.keys())}")

        # Look up entries for this file extension
        extension_entries = self.entries_by_extension.get(file_extension, [])
        logger.debug(f"Found {len(extension_entries)} entries for {file_extension}")

        # Find all entries for this word (case-insensitive or regex)
        matches = []
        for entry in extension_entries:
            if entry.is_regex:
                try:
                    if re.fullmatch(entry.keyword, word):
                        entry.word = word
                        matches.append(entry)
                except re.error:
                    logger.warning(f"Invalid regex pattern: {entry.keyword}")
            else:
                if entry.keyword.lower() == word.lower():
                    entry.word = word
                    matches.append(entry)

        if not matches:
            logger.debug(f"No hover entry found for '{word}'")
            return None

        logger.debug(f"Found {len(matches)} hover entries for '{word}'")

        # Build markdown content for all matches
        output = []
        for idx, entry in enumerate(matches, 1):
            lines = [f"## {idx}. {entry.word}"]
            if entry.is_regex:
                lines.append(f"*Regex match*: {entry.keyword}")
                lines.append("")
            if entry.category:
                lines.append(f"*Category: {entry.category}*")
                lines.append("")
            lines.append(entry.description)
            lines.append("")
            if entry.additional_info:
                lines.append("")
                lines.append("### Additional Information")
                for key, value in entry.additional_info.items():
                    lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
            if logger.isEnabledFor(logging.DEBUG):
                lines.append("")
                if entry.source_file is not None:
                    lines.append(f"*Source: {Path(entry.source_file).name}*")
            output.append("\n".join(lines))
        return "\n- - -\n".join(output)

    def get_supported_extensions(self) -> Set[str]:
        """Get all file extensions that have hover data."""
        return set(self.entries_by_extension.keys())
