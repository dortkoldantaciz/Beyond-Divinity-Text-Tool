"""
Beyond Divinity - Text CMP Tool
Extract and repack text.cmp files used for UI strings, item names, etc.

Format:
  uint32  directory_count
  For each directory:
    uint32  dir_id
    int32   item_count  (positive = ANSI, negative = widechar)
    For each item:
      uint32  item_id
      dd_str  name      (length-prefixed, null-terminated string)
      dd_str  diz       (length-prefixed, null-terminated string)
"""
import struct
import os
import sys


def read_uint32(f):
    data = f.read(4)
    if len(data) < 4:
        return None
    return struct.unpack('<I', data)[0]


def read_int32(f):
    data = f.read(4)
    if len(data) < 4:
        return None
    return struct.unpack('<i', data)[0]


def read_uint16(f):
    data = f.read(2)
    if len(data) < 2:
        return None
    return struct.unpack('<H', data)[0]


def read_dd_str(f, widechar, encoding='cp1254'):
    """Read a length-prefixed, null-terminated string.

    Args:
        f: Binary file handle.
        widechar: If True, read 2 bytes per character (UTF-16-LE).
                  If False, read 1 byte per character (ANSI).
        encoding: ANSI codepage to use when widechar is False.
    """
    length = read_uint32(f)
    if length is None or length == 0:
        return ""

    if widechar:
        byte_count = length * 2
        data = f.read(byte_count)
        if len(data) < byte_count:
            return ""
        text = data.decode('utf-16-le', errors='replace')
        f.read(2)  # null terminator (2 bytes for widechar)
    else:
        data = f.read(length)
        if len(data) < length:
            return ""
        text = data.decode(encoding, errors='replace')
        f.read(1)  # null terminator (1 byte for ANSI)

    return text


def write_dd_str(f, s, widechar, encoding='cp1254'):
    """Write a length-prefixed, null-terminated string.

    Args:
        f: Binary file handle.
        s: String to write.
        widechar: If True, write 2 bytes per character (UTF-16-LE).
                  If False, write 1 byte per character (ANSI).
        encoding: ANSI codepage to use when widechar is False.
    """
    if widechar:
        encoded = s.encode('utf-16-le')
        char_count = len(s)
        f.write(struct.pack('<I', char_count))
        if char_count > 0:
            f.write(encoded)
            f.write(b'\x00\x00')  # null terminator
    else:
        encoded = s.encode(encoding, errors='replace')
        f.write(struct.pack('<I', len(encoded)))
        if len(encoded) > 0:
            f.write(encoded)
            f.write(b'\x00')  # null terminator


def extract_text_cmp(cmp_path, output_json_path, widechar=False, encoding='cp1254'):
    """Extract a text.cmp file to JSON.

    Args:
        cmp_path: Path to the source .cmp file.
        output_json_path: Path to write the output JSON.
        widechar: If True, strings are UTF-16-LE. If False, ANSI.
        encoding: ANSI codepage (used when widechar is False).
    """
    import json

    with open(cmp_path, 'rb') as f:
        dir_count = read_uint32(f)
        print(f"Directories: {dir_count}")

        data = []

        for j in range(dir_count if dir_count else 0):
            dir_id = read_uint32(f)
            raw_count = read_int32(f)

            if raw_count is None:
                break
            count = abs(raw_count)

            directory = {
                "id": dir_id,
                "items": []
            }

            for i in range(count):
                item_id = read_uint32(f)
                if item_id is None:
                    print(f"Failed to read ItemID at Dir {j} Item {i}")
                    break
                name = read_dd_str(f, widechar, encoding)
                diz = read_dd_str(f, widechar, encoding)

                directory["items"].append({
                    "id": item_id,
                    "name": name,
                    "diz": diz
                })

            data.append(directory)

    with open(output_json_path, 'w', encoding='utf-8') as out:
        json.dump(data, out, indent=2, ensure_ascii=False)

    print(f"Extracted to {output_json_path}")


def repack_text_cmp(json_path, output_cmp_path, widechar=False, mode=3, encoding='cp1254'):
    """Repack a JSON file back into text.cmp format.

    Args:
        json_path: Path to the source JSON file (previously extracted).
        output_cmp_path: Path to write the output .cmp file.
        widechar: If True, write UTF-16-LE strings. If False, write ANSI.
        mode: 3 = ANSI (positive count), 1 or 2 = widechar (negative count).
        encoding: ANSI codepage (used when widechar is False).
    """
    import json

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open(output_cmp_path, 'wb') as f:
        dir_count = len(data)
        f.write(struct.pack('<I', dir_count))

        for directory in data:
            f.write(struct.pack('<I', directory['id']))
            count = len(directory['items'])
            # Mode 3 = ANSI = positive count.
            # Mode 1/2 = Widechar = negative count.
            if mode == 3:
                f.write(struct.pack('<i', count))
            else:
                f.write(struct.pack('<i', -count))

            for item in directory['items']:
                f.write(struct.pack('<I', item['id']))
                write_dd_str(f, item['name'], widechar, encoding)
                write_dd_str(f, item['diz'], widechar, encoding)

    print(f"Repacked to {output_cmp_path}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python bd_text_tool.py <extract|repack> <input> <output> [widechar=0] [encoding=cp1254]")
        sys.exit(1)

    action = sys.argv[1]
    input_file = sys.argv[2]
    output_file = sys.argv[3]
    use_wide = False
    enc = 'cp1254'

    if len(sys.argv) > 4:
        use_wide = int(sys.argv[4]) == 1
    if len(sys.argv) > 5:
        enc = sys.argv[5]

    if action == "extract":
        extract_text_cmp(input_file, output_file, widechar=use_wide, encoding=enc)
    elif action == "repack":
        mode_val = 1 if use_wide else 3
        repack_text_cmp(input_file, output_file, widechar=use_wide, mode=mode_val, encoding=enc)
    else:
        print(f"Invalid action: {action}. Use 'extract' or 'repack'.")
