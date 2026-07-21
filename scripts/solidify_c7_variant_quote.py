#!/usr/bin/env python3
"""Add local quote text to C7 variant B — draw only, no erase pass.

Use after regenerating `c7_variant_B_collection.png` with no small AI text.
Do not use `overlay_collection_quote.py` on this black-car master.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"

LINES = [
    "Razor-sharp design",
    "and track-ready power.",
    "Bold, brutal, and built to turn every",
    "highway into a runway.",
]

FONT_SIZE = 32


def solidify_quote(input_path: Path, output_path: Path | None = None) -> Path:
    img = Image.open(input_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, size=FONT_SIZE)

    w, h = img.size
    right_edge = int(w * 0.91)
    y_positions = [int(h * 0.705), int(h * 0.755), int(h * 0.805), int(h * 0.855)]

    for y, line in zip(y_positions, LINES):
        tw = font.getbbox(line)[2] - font.getbbox(line)[0]
        draw.text((right_edge - tw, y), line, fill=(0, 0, 0, 255), font=font)

    out = output_path or input_path
    img.save(out, format="PNG")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?", default=Path("designs/corvette/c7_variant_B_collection.png"))
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()
    out = solidify_quote(args.input, args.output)
    print(f"OK  {out}")


if __name__ == "__main__":
    main()
