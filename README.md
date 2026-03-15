# Beyond Divinity Translation Tool

A Python-based toolset for extracting, translating, and repacking text files from **Beyond Divinity** (2004, Larian Studios).

## Features

- **GUI Application** (`BD_Tool.pyw`) — Batch extract/repack with a simple tkinter interface
- **CLI Tools** — Individual command-line scripts for each file type (inside `lib/`)
- **Byte-perfect roundtrip** — Extract → Repack produces identical files (verified)
- **Configurable encoding** — Supports CP1254 (Turkish), CP1250 (Czech/Polish), or any single-byte codepage

## Supported File Types

| File | Location | Content |
|------|----------|---------|
| `text.cmp` | `Localizations/`, `Acts/ActX/Localizations/` | UI strings, item descriptions (binary format) |
| `*.gsm` | `Acts/ActX/Dialogs/`, `Acts/ActX/Quests/` | Dialog and quest text (CSV format) |
| `equipment.txt` | `Localizations/` | Weapon, armor, and accessory names |
| `hints.txt` | `Localizations/` | Loading screen tips |
| `strings.txt` | `Common/` | UI labels, stat descriptions, system messages |
| `books.txt` | `Common/` | In-game book entries |

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Usage

### GUI Mode

Double-click `BD_Tool.pyw` or run:

```bash
python BD_Tool.pyw
```

1. Select the game executable (`div.exe`)
2. Select a project workspace folder
3. Choose **EXTRACT** mode and click **START**
4. Translate the generated JSON files
5. Choose **REPACK** mode and click **START**

### CLI Mode

Each tool inside `lib/` can be used independently from the command line:

```bash
# Extract text.cmp to JSON
python lib/bd_text_tool.py extract Localizations/text.cmp output.json

# Repack JSON back to text.cmp
python lib/bd_text_tool.py repack output.json Localizations/text.cmp

# Extract GSM dialog file
python lib/bd_gsm_tool.py extract "Acts/Act1/Dialogs/Guard.gsm" guard.json

# Repack GSM dialog file
python lib/bd_gsm_tool.py repack guard.json "Acts/Act1/Dialogs/Guard.gsm"
```

#### Optional encoding parameter:

```bash
# Use CP1250 for Czech translation
python lib/bd_text_tool.py extract text.cmp output.json 0 cp1250
python lib/bd_gsm_tool.py extract Guard.gsm guard.json cp1250
```

## Translation Workflow

1. **Back up** your game's `Acts/`, `Localizations/`, and `Common/` folders
2. **Extract** all text files to JSON using the GUI or CLI
3. **Translate** the JSON files (edit "text", "translation", "value", "name", "diz" fields)
4. **Repack** the JSON files back into game format
5. **Copy** the repacked files into the game directory

## text.cmp Format Details

The `text.cmp` binary format stores strings with a length prefix and null terminator:

- **ANSI mode** (mode=3): Single-byte encoding, positive item counts
- **Unicode mode** (mode=1/2): UTF-16-LE encoding, negative item counts

## Known Limitations

- **Starting quest text and initial skill descriptions** are hardcoded in the game's New Game save templates (`savegames/BD_ACT*_START/data.000`). These binary save files cannot be modified with this tool and require direct binary/hex editing.
- The tool processes loose text files only, not files packed inside `.dv` or other archive formats.

## File Structure

```
BD_Translation_Tool/
├── BD_Tool.pyw              # GUI application (double-click to run)
├── README.md                # This file
└── lib/                     # Library modules
    ├── __init__.py
    ├── bd_text_tool.py      # text.cmp extract/repack
    ├── bd_gsm_tool.py       # .gsm dialog extract/repack
    └── bd_extra_tools.py    # equipment, hints, strings, books
```

## Credits

- Format research based on [Divine Divinity Tools](https://www.artembutusov.com/sormy.nm.ru/dd-lk.htm) by Sormy
- Modified for Beyond Divinity with improvements by dortkoldantaciz
