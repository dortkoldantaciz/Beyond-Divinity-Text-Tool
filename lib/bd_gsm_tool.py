"""
Beyond Divinity - GSM Dialog Tool
Extract and repack .gsm dialog/quest files.

GSM files are CSV-formatted text files with the structure:
  int, int, int, int, int, "dialog text"

The first 5 columns are numeric IDs/flags, and the last column is the
translatable dialog text enclosed in quotes.
"""
import csv
import json
import os
import sys


def extract_gsm(gsm_path, output_json_path, encoding='cp1254'):
    """Extract a .gsm dialog file to JSON.

    Args:
        gsm_path: Path to the source .gsm file.
        output_json_path: Path to write the output JSON.
        encoding: Character encoding of the source file (default: cp1254).
    """
    rows = []
    try:
        with open(gsm_path, 'r', encoding=encoding) as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    rows.append(row)
    except Exception as e:
        print(f"Error reading {gsm_path}: {e}")
        return

    data = []
    for row in rows:
        if len(row) > 0:
            item = {
                "original_row": row,
                "text_index": len(row) - 1,  # last element is the dialog text
                "text": row[-1]
            }
            data.append(item)

    with open(output_json_path, 'w', encoding='utf-8') as out:
        json.dump(data, out, indent=2, ensure_ascii=False)

    print(f"Extracted to {output_json_path}")


def repack_gsm(json_path, output_gsm_path, encoding='cp1254'):
    """Repack a JSON file back into .gsm format.

    Args:
        json_path: Path to the source JSON (previously extracted).
        output_gsm_path: Path to write the output .gsm file.
        encoding: Character encoding of the output file (default: cp1254).
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open(output_gsm_path, 'w', encoding=encoding, errors='replace', newline='') as f:
        # QUOTE_NONNUMERIC quotes only non-numeric fields (the dialog text).
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        for item in data:
            row = list(item['original_row'])
            text_idx = item['text_index']
            new_text = item['text']

            # Update the text column in the row
            if text_idx < len(row):
                row[text_idx] = new_text
            else:
                row.append(new_text)

            # Convert the first 5 columns to int to prevent quoting
            converted_row = []
            for i, val in enumerate(row):
                if i < 5:
                    try:
                        converted_row.append(int(val))
                    except (ValueError, TypeError):
                        converted_row.append(val)
                else:
                    converted_row.append(val)

            writer.writerow(converted_row)

    print(f"Repacked to {output_gsm_path}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python bd_gsm_tool.py <extract|repack> <input> <output> [encoding=cp1254]")
        sys.exit(1)

    action = sys.argv[1]
    input_file = sys.argv[2]
    output_file = sys.argv[3]
    enc = sys.argv[4] if len(sys.argv) > 4 else 'cp1254'

    if action == "extract":
        extract_gsm(input_file, output_file, encoding=enc)
    elif action == "repack":
        repack_gsm(input_file, output_file, encoding=enc)
    else:
        print(f"Invalid action: {action}. Use 'extract' or 'repack'.")
