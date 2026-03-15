"""
Beyond Divinity - Extra File Tools
Extract and repack supplementary text files:
  - equipment.txt  (weapon/armor/accessory names)
  - hints.txt      (loading screen tips)
  - strings.txt    (UI strings, stat descriptions, system messages)
  - books.txt      (in-game book entries)
"""
import json
import os
import re
import csv
import io


# ═══════════════════════════════════════════════════════════════════════════════
# equipment.txt
# Format: translation "key","value"
# ═══════════════════════════════════════════════════════════════════════════════

def extract_equipment(filepath, output_json_path, encoding='cp1254'):
    """Extract equipment.txt to JSON.

    Args:
        filepath: Path to the source equipment.txt.
        output_json_path: Path to write the output JSON.
        encoding: Character encoding of the source file.
    """
    data = []

    with open(filepath, 'r', encoding=encoding, errors='replace') as f:
        for i, line in enumerate(f):
            line = line.rstrip('\r\n')
            if not line.strip():
                data.append({"line_index": i, "type": "empty", "raw": line})
                continue

            # Parse: translation "key","value"
            match = re.match(r'^translation\s+"([^"]*?)"\s*,\s*"([^"]*?)"$', line)
            if match:
                data.append({
                    "line_index": i,
                    "type": "translation",
                    "key": match.group(1),
                    "value": match.group(2)
                })
            else:
                # Unrecognized format lines
                data.append({"line_index": i, "type": "raw", "raw": line})

    with open(output_json_path, 'w', encoding='utf-8') as out:
        json.dump(data, out, indent=2, ensure_ascii=False)

    print(f"Extracted equipment: {len([d for d in data if d['type'] == 'translation'])} entries -> {output_json_path}")


def repack_equipment(json_path, output_path, encoding='cp1254'):
    """Repack JSON back into equipment.txt format.

    Args:
        json_path: Path to the source JSON (previously extracted).
        output_path: Path to write the output equipment.txt.
        encoding: Character encoding of the output file.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    lines = []
    for item in data:
        if item['type'] == 'translation':
            lines.append(f'translation "{item["key"]}","{item["value"]}"')
        elif item['type'] == 'empty':
            lines.append(item.get('raw', ''))
        else:
            lines.append(item.get('raw', ''))

    with open(output_path, 'w', encoding=encoding, errors='replace', newline='') as f:
        f.write('\r\n'.join(lines))
        if lines:
            f.write('\r\n')

    print(f"Repacked equipment -> {output_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# hints.txt
# Format: One hint per line
# ═══════════════════════════════════════════════════════════════════════════════

def extract_hints(filepath, output_json_path, encoding='cp1254'):
    """Extract hints.txt to JSON.

    Args:
        filepath: Path to the source hints.txt.
        output_json_path: Path to write the output JSON.
        encoding: Character encoding of the source file.
    """
    data = []

    with open(filepath, 'r', encoding=encoding, errors='replace') as f:
        for i, line in enumerate(f):
            line = line.rstrip('\r\n')
            data.append({
                "line_index": i,
                "text": line
            })

    with open(output_json_path, 'w', encoding='utf-8') as out:
        json.dump(data, out, indent=2, ensure_ascii=False)

    print(f"Extracted hints: {len([d for d in data if d['text'].strip()])} non-empty lines -> {output_json_path}")


def repack_hints(json_path, output_path, encoding='cp1254'):
    """Repack JSON back into hints.txt format.

    Args:
        json_path: Path to the source JSON (previously extracted).
        output_path: Path to write the output hints.txt.
        encoding: Character encoding of the output file.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    lines = [item['text'] for item in data]

    with open(output_path, 'w', encoding=encoding, errors='replace', newline='') as f:
        f.write('\r\n'.join(lines))
        if lines:
            f.write('\r\n')

    print(f"Repacked hints -> {output_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# strings.txt
# Format: ID,"original","translation"  (CSV)
# ═══════════════════════════════════════════════════════════════════════════════

def extract_strings(filepath, output_json_path, encoding='cp1254'):
    """Extract strings.txt to JSON.

    Args:
        filepath: Path to the source strings.txt.
        output_json_path: Path to write the output JSON.
        encoding: Character encoding of the source file.
    """
    data = []

    with open(filepath, 'r', encoding=encoding, errors='replace') as f:
        content = f.read()

    # Parse with CSV reader
    reader = csv.reader(io.StringIO(content))
    for i, row in enumerate(reader):
        if not row:
            data.append({"line_index": i, "type": "empty", "raw": ""})
            continue

        if len(row) >= 3:
            data.append({
                "line_index": i,
                "type": "string",
                "id": row[0],
                "original": row[1],
                "translation": row[2]
            })
        elif len(row) == 2:
            data.append({
                "line_index": i,
                "type": "string",
                "id": row[0],
                "original": row[1],
                "translation": row[1],
                "col_count": 2
            })
        else:
            data.append({"line_index": i, "type": "raw", "raw": ','.join(row)})

    with open(output_json_path, 'w', encoding='utf-8') as out:
        json.dump(data, out, indent=2, ensure_ascii=False)

    print(f"Extracted strings: {len([d for d in data if d['type'] == 'string'])} entries -> {output_json_path}")


def repack_strings(json_path, output_path, encoding='cp1254'):
    """Repack JSON back into strings.txt format.

    Args:
        json_path: Path to the source JSON (previously extracted).
        output_path: Path to write the output strings.txt.
        encoding: Character encoding of the output file.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC, lineterminator='\r\n')

    for item in data:
        if item['type'] == 'string':
            # IDs may be numeric
            try:
                id_val = int(item['id'])
            except (ValueError, TypeError):
                id_val = item['id']
            if item.get('col_count') == 2 and item['original'] == item['translation']:
                # Preserve original 2-column format if text was not changed
                writer.writerow([id_val, item['original']])
            else:
                writer.writerow([id_val, item['original'], item['translation']])
        elif item['type'] == 'empty':
            output.write('\r\n')
        else:
            output.write(item.get('raw', '') + '\r\n')

    with open(output_path, 'w', encoding=encoding, errors='replace', newline='') as f:
        f.write(output.getvalue())

    print(f"Repacked strings -> {output_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# books.txt
# Format: [bookentry] ID PARAM1 PARAM2 \n Text content
# ═══════════════════════════════════════════════════════════════════════════════

def extract_books(filepath, output_json_path, encoding='cp1254'):
    """Extract books.txt to JSON.

    Args:
        filepath: Path to the source books.txt.
        output_json_path: Path to write the output JSON.
        encoding: Character encoding of the source file.
    """
    with open(filepath, 'rb') as f:
        raw = f.read()

    text = raw.decode(encoding, errors='replace')
    # Split while preserving line endings
    lines = text.split('\n')
    # Re-attach \n to each line (except possibly the last)
    rebuilt = []
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            rebuilt.append(line + '\n')
        else:
            if line:  # last line without trailing newline
                rebuilt.append(line)

    data = []
    i = 0
    while i < len(rebuilt):
        line = rebuilt[i]
        header_match = re.match(r'\[bookentry\]\s+([\d]+)\s+([-\d]+)\s+([\d]+)', line)
        if header_match:
            header_line = line
            # Collect all text lines until the next [bookentry] or end
            text_lines = []
            i += 1
            while i < len(rebuilt):
                if re.match(r'\[bookentry\]\s+[\d]+\s+[-\d]+\s+[\d]+', rebuilt[i]):
                    break
                text_lines.append(rebuilt[i])
                i += 1
            data.append({
                "type": "bookentry",
                "id": int(header_match.group(1)),
                "param1": int(header_match.group(2)),
                "param2": int(header_match.group(3)),
                "header_raw": header_line,
                "text_raw": ''.join(text_lines)
            })
        else:
            data.append({"type": "raw", "raw": line})
            i += 1

    with open(output_json_path, 'w', encoding='utf-8') as out:
        json.dump(data, out, indent=2, ensure_ascii=False)

    print(f"Extracted books: {len([d for d in data if d.get('type') == 'bookentry'])} entries -> {output_json_path}")


def repack_books(json_path, output_path, encoding='cp1254'):
    """Repack JSON back into books.txt format.

    Args:
        json_path: Path to the source JSON (previously extracted).
        output_path: Path to write the output books.txt.
        encoding: Character encoding of the output file.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    parts = []
    for item in data:
        if item.get('type') == 'bookentry':
            parts.append(item['header_raw'])
            parts.append(item['text_raw'])
        elif item.get('type') == 'raw':
            parts.append(item.get('raw', ''))

    with open(output_path, 'wb') as f:
        f.write(''.join(parts).encode(encoding, errors='replace'))

    print(f"Repacked books -> {output_path}")

