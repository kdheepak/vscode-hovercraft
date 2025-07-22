#!/usr/bin/env python3
"""Hovercraft Language Server - CSV and JSON-powered hover provider."""

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

from .hover import CSVHoverProvider, JSONHoverProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("hovercraft")


class HovercraftServer(LanguageServer):
    """Language server that provides hover information from CSV and JSON files."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.csv_hover_provider: CSVHoverProvider | None = None
        self.json_hover_provider: JSONHoverProvider | None = None


server = HovercraftServer("hovercraft", "v0.1.0")


@server.feature("initialize")
def initialize(params: InitializeParams):
    """Initialize the language server."""
    logger.info("Hovercraft server initializing...")

    if params.workspace_folders:
        workspace_path = Path(params.workspace_folders[0].uri.replace("file://", ""))
        server.csv_hover_provider = CSVHoverProvider(workspace_path)
        server.csv_hover_provider.load_all_csv_files()
        server.json_hover_provider = JSONHoverProvider(workspace_path)
        server.json_hover_provider.load_all_json_files()

        supported_extensions = (
            server.csv_hover_provider.get_supported_extensions()
            | server.json_hover_provider.get_supported_extensions()
        )
        total_entries = (
            server.csv_hover_provider.entry_count
            + server.json_hover_provider.entry_count
        )
        logger.info(
            f"Initialized with workspace: {workspace_path}\n"
            f"Loaded {total_entries} entries\n"
            f"Supporting extensions: {', '.join(sorted(supported_extensions))}"
        )


@server.feature("workspace/didChangeWatchedFiles")
def did_change_watched_files(params: DidChangeWatchedFilesParams):
    """Handle file change notifications."""
    if not server.csv_hover_provider or not server.json_hover_provider:
        return

    for change in params.changes:
        file_path = change.uri.replace("file://", "")
        path = Path(file_path)

        # CSV
        if path.parent.name in [
            ".vscode",
            ".data",
        ] and server.csv_hover_provider.FILENAME_PATTERN.match(path.name):
            logger.info(f"Hover CSV file changed: {file_path}")

            if change.type == FileChangeType.Deleted:
                server.csv_hover_provider.remove_csv_file(file_path)
            else:
                server.csv_hover_provider.reload_csv_file(file_path)

        # JSON
        if path.parent.name in [
            ".vscode",
            ".data",
        ] and server.json_hover_provider.FILENAME_PATTERN.match(path.name):
            logger.info(f"Hover JSON file changed: {file_path}")

            if change.type == FileChangeType.Deleted:
                server.json_hover_provider.remove_json_file(file_path)
            else:
                server.json_hover_provider.reload_json_file(file_path)


@server.feature("textDocument/hover")
def hover(params: HoverParams) -> Hover | None:
    """Provide hover information from both providers."""
    if not server.csv_hover_provider or not server.json_hover_provider:
        return None

    document = server.workspace.get_document(params.text_document.uri)

    file_path = Path(params.text_document.uri.replace("file://", ""))
    file_extension = file_path.suffix

    word = document.word_at_position(params.position)

    if not word:
        return None

    hover_info_csv = server.csv_hover_provider.get_hover_info(word, file_extension)
    hover_info_json = server.json_hover_provider.get_hover_info(word, file_extension)

    hover_infos = [info for info in [hover_info_csv, hover_info_json] if info]

    if hover_infos:
        combined = "\n- - -\n".join(hover_infos)

        start_char = params.position.character - len(word)
        if start_char < 0:
            start_char = 0

        return Hover(
            contents=MarkupContent(kind=MarkupKind.Markdown, value=combined),
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
