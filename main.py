"""cutest-picture-01 v4: ship the bundled entry.png to the output dir.

The picture (baby penguin astronaut + kitten astronaut on the moon) is
stored next to this file. This script only copies it, after checking the
competition gates itself: at most 1 MiB, at most 1024x1024, and a whole
image (PNG IEND or JPEG EOI present). Stdlib only, no network.
"""

import hashlib
import os
import struct
import sys

MAX_BYTES = 1_048_576
MAX_SIDE = 1024

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.png")


def read_dimensions(blob):
    """Return (width, height) for a PNG or JPEG byte string."""
    if blob[:8] == b"\x89PNG\r\n\x1a\n":
        width, height = struct.unpack(">II", blob[16:24])
        return width, height
    if blob[:2] == b"\xff\xd8":
        pos = 2
        while pos + 9 < len(blob):
            if blob[pos] != 0xFF:
                pos += 1
                continue
            marker = blob[pos + 1]
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                pos += 2
                continue
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                          0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                height, width = struct.unpack(">HH", blob[pos + 5:pos + 9])
                return width, height
            length = struct.unpack(">H", blob[pos + 2:pos + 4])[0]
            pos += 2 + length
    raise ValueError("not a PNG or JPEG image")


def is_whole_image(blob):
    """True when the file ends with its format's end marker."""
    if blob[:8] == b"\x89PNG\r\n\x1a\n":
        return blob.rstrip(b"\x00").endswith(b"IEND" + b"\xaeB`\x82")
    if blob[:2] == b"\xff\xd8":
        return blob.rstrip(b"\x00").endswith(b"\xff\xd9")
    return False


def main():
    with open(SOURCE, "rb") as handle:
        blob = handle.read()
    if not (blob[:8] == b"\x89PNG\r\n\x1a\n" or blob[:2] == b"\xff\xd8"):
        sys.exit("entry.png is neither PNG nor JPEG bytes")
    if len(blob) > MAX_BYTES:
        sys.exit(f"entry.png is {len(blob)} bytes, over the 1 MiB cap")
    width, height = read_dimensions(blob)
    if width > MAX_SIDE or height > MAX_SIDE:
        sys.exit(f"entry.png is {width}x{height}, over the 1024x1024 cap")
    if not is_whole_image(blob):
        sys.exit("entry.png looks truncated (no end marker)")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    with open(target, "wb") as handle:
        handle.write(blob)
    with open(target, "rb") as handle:
        written = handle.read()
    if hashlib.sha256(written).hexdigest() != hashlib.sha256(blob).hexdigest():
        sys.exit("written entry.png differs from the bundled one")
    print(f"wrote {target}: {width}x{height}, {len(blob)} bytes")


if __name__ == "__main__":
    main()
