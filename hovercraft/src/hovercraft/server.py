#!/usr/bin/env python3
"""Hovercraft Language Server - CSV-powered hover provider."""

import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

from pygls.server import LanguageServer
from lsprotocol.types import (
    Hover,
    HoverParams,
    InitializeParams,
    MarkupContent,
    MarkupKind,
    Position,
    Range,
    DidChangeWatchedFilesParams,
    FileChangeType,
)

from .hover import CSVHoverProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("hovercraft")


class HovercraftServer(LanguageServer):
    """Language server that provides hover information from CSV files."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hover_provider: Optional[CSVHoverProvider] = None


server = HovercraftServer("hovercraft", "v0.1.0")


@server.feature("initialize")
def initialize(params: InitializeParams):
    """Initialize the language server."""
    logger.info("Hovercraft server initializing...")

    if params.workspace_folders:
        workspace_path = Path(params.workspace_folders[0].uri.replace("file://", ""))
        server.hover_provider = CSVHoverProvider(workspace_path)
        server.hover_provider.load_all_csv_files()

        supported_extensions = server.hover_provider.get_supported_extensions()
        logger.info(
            f"Initialized with workspace: {workspace_path}\n"
            f"Loaded {server.hover_provider.entry_count} entries\n"
            f"Supporting extensions: {', '.join(sorted(supported_extensions))}"
        )


@server.feature("workspace/didChangeWatchedFiles")
def did_change_watched_files(params: DidChangeWatchedFilesParams):
    """Handle file change notifications."""
    if not server.hover_provider:
        return

    for change in params.changes:
        file_path = change.uri.replace("file://", "")

        # Only process CSV files in .vscode directory with our pattern
        path = Path(file_path)
        if (
            path.parent.name == ".vscode"
            and server.hover_provider.FILENAME_PATTERN.match(path.name)
        ):
            logger.info(f"Hover CSV file changed: {file_path}")

            if change.type == FileChangeType.Deleted:
                server.hover_provider.remove_csv_file(file_path)
            else:
                server.hover_provider.reload_csv_file(file_path)


@server.feature("textDocument/hover")
def hover(params: HoverParams) -> Optional[Hover]:
    """Provide hover information."""
    if not server.hover_provider:
        return None

    document = server.workspace.get_document(params.text_document.uri)

    # Get file extension from document URI
    file_path = Path(params.text_document.uri.replace("file://", ""))
    file_extension = file_path.suffix

    # Get word at cursor position
    word = document.word_at_position(params.position)

    if not word:
        return None

    # Get hover info for this word and file type
    hover_info = server.hover_provider.get_hover_info(word, file_extension)

    if hover_info:
        # Calculate word range for hover
        start_char = params.position.character - len(word)
        if start_char < 0:
            start_char = 0

        return Hover(
            contents=MarkupContent(kind=MarkupKind.Markdown, value=hover_info),
            range=Range(
                start=Position(line=params.position.line, character=start_char),
                end=Position(
                    line=params.position.line, character=params.position.character
                ),
            ),
        )

    return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Hovercraft Language Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--log-file", type=str, help="Log to file instead of stderr")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.log_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(file_handler)

    logger.info("Starting Hovercraft Language Server...")
    server.start_io()


if __name__ == "__main__":
    sys.exit(main())
