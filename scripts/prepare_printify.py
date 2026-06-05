#!/usr/bin/env python3
"""
Build a Printify-ready PNG: 3951×4919 px transparent canvas with artwork centered.

Matches your sold C5 scale by default (~72% of print width).

Examples:
  .venv/bin/python scripts/prepare_printify.py designs/corvette_c8_streetwear_design.png
  .venv/bin/python scripts/prepare_printify.py designs/corvette_c8_streetwear_design.png \\
      -o designs/corvette_c8_streetwear_design_printify.png \\
      --width-percent 0.72
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

PRINTIFY_WIDTH = 3951
PRINTIFY_HEIGHT = 4919
DEFAULT_WIDTH_PERCENT = 0.72


def _to_solid_black_rgba(design: Image.Image, *, white_threshold: int = 250) -> Image.Image:
    """White/checkerboard -> transparent; artwork -> solid black."""
    design = design.convert("RGBA")
    w, h = design.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    opx = out.load()
    rgb = design.convert("RGB").load()
    for y in range(h):
        for x in range(w):
            r, g, b = rgb[x, y]
            if r >= white_threshold and g >= white_threshold and b >= white_threshold:
                continue
            if r > 175 and g > 175 and b > 175:
                continue
            opx[x, y] = (0, 0, 0, 255)
    return out


def prepare_printify(
    design_path: Path,
    output_path: Path,
    *,
    width_percent: float = DEFAULT_WIDTH_PERCENT,
    canvas_width: int = PRINTIFY_WIDTH,
    canvas_height: int = PRINTIFY_HEIGHT,
    vertical_offset: float = 0.0,
) -> Path:
    """
    Place RGBA design on transparent Printify canvas.

    vertical_offset: fraction of leftover height to push down (0 = centered, 0.08 = slightly higher on shirt).
    Negative values push art up.
    """
    design = Image.open(design_path).convert("RGBA")
    target_w = max(1, int(canvas_width * width_percent))
    scale = target_w / design.width
    target_h = max(1, int(design.height * scale))
    resized = design.resize((target_w, target_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    x = (canvas_width - target_w) // 2
    leftover = canvas_height - target_h
    y = int(leftover * (0.5 + vertical_offset))
    y = max(0, min(y, canvas_height - target_h))
    canvas.alpha_composite(resized, (x, y))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, "PNG", optimize=True)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare PNG for Printify print area.")
    parser.add_argument("design", type=Path, help="Source design PNG (transparent)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path (default: <stem>_printify.png next to input)",
    )
    parser.add_argument(
        "--width-percent",
        type=float,
        default=DEFAULT_WIDTH_PERCENT,
        help=f"Art width as fraction of canvas (default {DEFAULT_WIDTH_PERCENT})",
    )
    parser.add_argument(
        "--vertical-offset",
        type=float,
        default=0.0,
        help="Shift art vertically: negative=up, positive=down (fraction of extra space)",
    )
    parser.add_argument(
        "--ink-black",
        action="store_true",
        help="Convert white background to transparent + solid black ink (for raw AI PNGs)",
    )
    args = parser.parse_args()

    if not args.design.exists():
        print(f"Not found: {args.design}", file=sys.stderr)
        return 1

    out = args.output or args.design.with_name(f"{args.design.stem}_printify.png")

    design = Image.open(args.design).convert("RGBA")
    if args.ink_black:
        design = _to_solid_black_rgba(design)
        tmp = args.design.with_name(f"{args.design.stem}_ink.png")
        design.save(tmp)

    path = prepare_printify(
        tmp if args.ink_black else args.design,
        out,
        width_percent=args.width_percent,
        vertical_offset=args.vertical_offset,
    )
    im = Image.open(path)
    mb = path.stat().st_size / 1_048_576
    print(f"Saved: {path}")
    print(f"  Canvas: {im.size[0]}×{im.size[1]} px ({mb:.2f} MB)")
    print(f"  Art width: {int(im.size[0] * args.width_percent)} px ({args.width_percent:.0%} of canvas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
