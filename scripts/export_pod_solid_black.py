#!/usr/bin/env python3
"""Turn a white-background PNG into solid black ink on transparent (POD-safe)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageFilter


def export_pod_solid_black(
    src: Path, dest: Path | None = None, *, white_threshold: int = 250
) -> Path:
    """Keep artwork as #000000; only near-white pixels become transparent."""
    dest = Path(dest) if dest is not None else src
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    opx = out.load()
    rgb = im.convert("RGB").load()

    for y in range(h):
        for x in range(w):
            r, g, b = rgb[x, y]
            if r >= white_threshold and g >= white_threshold and b >= white_threshold:
                continue
            if r > 175 and g > 175 and b > 175:
                continue
            opx[x, y] = (0, 0, 0, 255)

    alpha = out.split()[3].filter(ImageFilter.MaxFilter(3))
    final = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    final.putalpha(alpha)
    final.save(dest)
    return dest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("src", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()
    out = export_pod_solid_black(args.src, args.output)
    print(f"Exported: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
