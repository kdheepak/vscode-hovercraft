# VSCode-Hovercraft - CSV-Powered Hover Provider for VSCode

Hovercraft is a VSCode extension that provides customizable hover information for any programming
language using simple CSV files. Define your own hover tooltips for keywords, functions, APIs, or
any text pattern in your codebase.

## Features

- 🎯 Language Agnostic - Works with any file type or programming language
- 📝 Simple CSV Format - Define hovers using familiar spreadsheet-friendly CSV files
- 🔄 Hot Reload - Changes to CSV files are picked up automatically
- 🏢 Workspace Specific - Each project can have its own hover definitions
- 🚀 Fast & Lightweight - Powered by Python Language Server Protocol
- 🔧 Zero Configuration - Just drop CSV files in `.vscode` and they work

## Installation

### From VSCode Marketplace

- Open VSCode
- Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
- Search for "Hovercraft"
- Click Install

## Getting Started

- Create a `.vscode` folder in your workspace (if it doesn't exist)
- Add a CSV file named `.vscode/hovercraft.<extension>.csv` with columns:

  - `keyword`: The text to match in your code
  - `description`: The hover text to display
  - `category`: (optional) A category for grouping hovers
  - `url`: (optional) A URL to link to for more information

- Define your hover information
- Open a file with that extension and hover over keywords!

The file extension in the filename determines which files the hover applies to. The convention is:

```plaintext
.vscode/hovercraft.<file-extension>.csv
```

Examples:

- `hovercraft.py.csv` → Python files (.py)
- `hovercraft.md.csv` → Markdown files (.md)
- `hovercraft.custom.csv` → Custom files (.custom)

## Requirements

- VSCode 1.75.0 or higher
- Python environment is automatically managed by the extension using `uv`
- No manual Python installation required!

## Troubleshooting

### No hovers appearing

- Check CSV file location: Must be in `.vscode` folder
- Check CSV filename: Must match pattern `hovercraft.<ext>.csv`
- Check CSV format: Must have `keyword` and `description` columns
- Check Output panel: View → Output → "Hovercraft Language Server"

### Extension not activating

- Check if `uv` is being installed: View → Output → "Hovercraft Language Server Setup"
- Reload window: Ctrl+R / Cmd+R
- Check extension is enabled: Extensions → Hovercraft → Enable

## Contributing

Contributions are welcome! Please:

- Fork the repository
- Create a feature branch (`git checkout -b feature/amazing-feature`)
- Commit your changes (`git commit -m 'Add amazing feature'`)
- Push to the branch (`git push origin feature/amazing-feature`)
- Open a Pull Request

## License

MIT License - see [./LICENSE] file for details

---

Made with ❤️ for developers who love documentation
