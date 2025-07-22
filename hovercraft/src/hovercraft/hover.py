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


class CSVHoverProvider:
    """Manages CSV files and provides hover information."""

    # Pattern to extract extension from filename
    # Example: hovercraft.py.csv → .py
    FILENAME_PATTERN = re.compile(r"^hovercraft\.(.+)\.csv$")

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.vscode_path = workspace_path / ".vscode"
        # Store entries per file extension
        self.entries_by_extension: dict[str, dict[str, HoverEntry]] = {}
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
        """Load all CSV files in the .vscode directory."""
        if not self.vscode_path.exists():
            logger.info(f".vscode directory not found at {self.vscode_path}")
            return

        csv_files = list(self.vscode_path.glob("hovercraft.*.csv"))
        logger.info(f"Found {len(csv_files)} hover CSV files in .vscode directory")

        for csv_file in csv_files:
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

            # Initialize extension dictionary if needed
            if extension not in self.entries_by_extension:
                self.entries_by_extension[extension] = {}

            # Process each row
            for _, row in df.iterrows():
                keyword = row["keyword"].strip()
                if not keyword:
                    continue

                entry = HoverEntry(
                    keyword=keyword,
                    description=row["description"],
                    category=row.get("category"),
                    source_file=str(file_path),
                    additional_info={
                        col: row[col]
                        for col in df.columns
                        if col
                        not in ["keyword", "description", "category", "source_file"]
                        and row[col]
                    },
                )

                self.entries_by_extension[extension][keyword.lower()] = entry

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
        entries_to_remove = [
            keyword
            for keyword, entry in self.entries_by_extension[extension].items()
            if entry.source_file == file_path
        ]

        for keyword in entries_to_remove:
            del self.entries_by_extension[extension][keyword]

        # Clean up empty extension dictionary
        if not self.entries_by_extension[extension]:
            del self.entries_by_extension[extension]

        # Remove from csv_files dict
        if file_path in self.csv_files:
            del self.csv_files[file_path]

        logger.info(f"Removed {len(entries_to_remove)} entries from {file_path}")

    def get_hover_info(self, word: str, file_extension: str) -> str | None:
        """Get hover information for a word in a specific file type."""

        logger.debug(
            f"get_hover_info called: word='{word}', extension='{file_extension}'"
        )

        # Normalize the extension
        if not file_extension.startswith("."):
            file_extension = f".{file_extension}"

        logger.debug(f"Normalized extension: '{file_extension}'")
        logger.debug(f"Available extensions: {list(self.entries_by_extension.keys())}")

        # Look up entries for this file extension
        extension_entries = self.entries_by_extension.get(file_extension, {})
        logger.debug(f"Found {len(extension_entries)} entries for {file_extension}")

        if extension_entries and word:
            logger.debug(
                f"Looking for '{word.lower()}' in: {list(extension_entries.keys())[:5]}..."
            )  # Show first 5

        entry = extension_entries.get(word.lower())

        if entry:
            logger.debug(f"Found hover entry for '{word}'")
        else:
            logger.debug(f"No hover entry found for '{word}'")

        if not entry:
            return None

        # Build markdown content
        lines = [f"## {entry.keyword}"]

        if entry.category:
            lines.append(f"*Category: {entry.category}*")

        lines.append("")  # Empty line
        lines.append(entry.description)

        # Add additional info if available
        if entry.additional_info:
            lines.append("")
            lines.append("### Additional Information")
            for key, value in entry.additional_info.items():
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")

        # Add source file in debug mode
        if logger.isEnabledFor(logging.DEBUG):
            lines.append("")
            if entry.source_file is not None:
                lines.append(f"*Source: {Path(entry.source_file).name}*")

        return "\n".join(lines)

    def get_supported_extensions(self) -> Set[str]:
        """Get all file extensions that have hover data."""
        return set(self.entries_by_extension.keys())
