# `hovercraft` - File Based Hover Provider

`hovercraft` is a VSCode extension that provides customizable hover information for any programming
language using simple CSV or JSON files. You can define your own hover tooltips for keywords, functions,
APIs, or any text pattern in your codebase.

## Installation

### From VSCode Marketplace

- Open VSCode
- Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
- Search for "Hovercraft"
- Click Install

## Getting Started

- Create a `.data` folder in your workspace (if it doesn't exist)
- Add a CSV or JSON file named `.data/hovercraft.<extension>.csv` or
  `.data/hovercraft.<extension>.json`:

### CSV Format

- Columns:
  - `keyword`: The text to match in your code
  - `description`: The hover text to display
  - `source_file`: (optional) The source file where this hover is defined
  - `category`: (optional) A category for grouping hovers
  - `url`: (optional) A URL to link to for more information

### JSON Format

- Array of objects, each with:
  - `keyword`: The text to match in your code
  - `description`: The hover text to display
  - `source_file`: (optional) The source file where this hover is defined
  - `category`: (optional) A category for grouping hovers
  - `url`: (optional) A URL to link to for more information

The file extension in the filename determines which files the hover applies to. The convention is:

```plaintext
.data/hovercraft.<file-extension>.csv
.data/hovercraft.<file-extension>.json
```

Examples:

- `hovercraft.py.csv` → Python files (.py)
- `hovercraft.py.json` → Python files (.py)
- `hovercraft.md.csv` → Markdown files (.md)
- `hovercraft.md.json` → Markdown files (.md)
- `hovercraft.custom.csv` → Custom files (.custom)
- `hovercraft.custom.json` → Custom files (.custom)

## Requirements

- VSCode 1.75.0 or higher
- Python environment is automatically managed by the extension using `uv`

## Configuration

You can configure the location of your `uv` executable using VSCode settings:

- Open Command Palette (Cmd+Shift+P / Ctrl+Shift+P)
- Type `Preferences: Open Settings (UI)`
- Search for `Hovercraft: UV Path`
- Set the path to your `uv` executable (e.g. `/usr/local/bin/uv`)

Alternatively, add this to your `settings.json`:

```json
{
  "hovercraft.uvPath": "/path/to/your/uv"
}
```

If not set, the extension will use the default `uv` in your system PATH. If `uv` is not available,
it will be installed automatically by the extension.

## Development

### Running Tests

```bash
# All tests
./scripts/e2e.sh

# VSCode extension tests only
npm test

# Python language server tests only  
cd hovercraft && uv run python -m pytest tests/ -v
```

## Troubleshooting

### No hovers appearing

- Check CSV/JSON file location: Must be in `.data` folder or in the `.data` folder
- Check CSV/JSON filename: Must match pattern `hovercraft.<ext>.csv` or `hovercraft.<ext>.json`
- Check CSV format: Must have `keyword` and `description` columns
- Check JSON format: Must be an array of objects with `keyword` and `description` fields
- Check Output panel: View → Output → "Hovercraft Language Server"

### Extension not activating

- Check if `uv` is being installed: View → Output → "Hovercraft Language Server Setup"
- Reload window: Ctrl+R / Cmd+R
- Check extension is enabled: Extensions → Hovercraft → Enable
