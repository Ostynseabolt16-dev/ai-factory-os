#!/usr/bin/env python3
"""Typeset a minimalist CORVETTE / -<code>- chest wordmark (real fonts, perfect text).

Renders crisp black (or white) text on a transparent PNG — no AI, so spelling and
letterforms are exact. Pairs with the detailed back graphic for a two-sided shirt.

Examples:
  .venv/bin/python scripts/make_minimal_front.py C4
  .venv/bin/python scripts/make_minimal_front.py C4 --color white
  .venv/bin/python scripts/make_minimal_front.py C4 --weight light --tracking 0.42
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESIGNS_DIR = PROJECT_ROOT / "designs"

HELVETICA_NEUE = "/System/Library/Fonts/HelveticaNeue.ttc"
WEIGHT_INDEX = {"thin": 12, "light": 7, "ultralight": 5, "regular": 0}

WORDMARK_PT = 240
SUB_RATIO = 0.55          # "-C4-" size relative to wordmark
DEFAULT_TRACKING = 0.34   # letter-spacing as fraction of point size
SUB_TRACKING = 0.26
LINE_GAP_RATIO = 0.40     # gap between wordmark and sub, fraction of wordmark size
PAD = 40                  # transparent padding around final art


def _render_tracked_line(
    text: str, font: ImageFont.FreeTypeFont, tracking_px: float, fill: tuple[int, int, int, int]
) -> Image.Image:
    """Render a single line with manual letter-spacing on a transparent strip."""
    ascent, descent = font.getmetrics()
    height = ascent + descent
    advances = [font.getlength(ch) for ch in text]
    total_w = sum(advances) + tracking_px * max(0, len(text) - 1)

    img = Image.new("RGBA", (max(1, int(total_w + 2)), height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    x = 0.0
    for ch, adv in zip(text, advances):
        draw.text((x, 0), ch, font=font, fill=fill, anchor="la")
        x += adv + tracking_px
    return img


def _trim(img: Image.Image, pad: int) -> Image.Image:
    bbox = img.getbbox()
    if bbox is None:
        return img
    cropped = img.crop(bbox)
    out = Image.new("RGBA", (cropped.width + 2 * pad, cropped.height + 2 * pad), (0, 0, 0, 0))
    out.alpha_composite(cropped, (pad, pad))
    return out


def make_minimal_front(
    code: str,
    *,
    color: str = "black",
    weight: str = "thin",
    sub_weight: str | None = None,
    sub_ratio: float = SUB_RATIO,
    tracking: float = DEFAULT_TRACKING,
    output: Path | None = None,
) -> Path:
    code = code.upper()
    index = WEIGHT_INDEX.get(weight.lower(), WEIGHT_INDEX["thin"])
    sub_index = WEIGHT_INDEX.get((sub_weight or weight).lower(), index)
    fill = (255, 255, 255, 255) if color.lower() == "white" else (0, 0, 0, 255)

    wordmark_font = ImageFont.truetype(HELVETICA_NEUE, WORDMARK_PT, index=index)
    sub_font = ImageFont.truetype(HELVETICA_NEUE, int(WORDMARK_PT * sub_ratio), index=sub_index)

    line1 = _render_tracked_line("CORVETTE", wordmark_font, WORDMARK_PT * tracking, fill)
    line2 = _render_tracked_line(f"-{code}-", sub_font, int(WORDMARK_PT * sub_ratio) * SUB_TRACKING, fill)

    gap = int(WORDMARK_PT * LINE_GAP_RATIO)
    width = max(line1.width, line2.width)
    height = line1.height + gap + line2.height
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    canvas.alpha_composite(line1, ((width - line1.width) // 2, 0))
    canvas.alpha_composite(line2, ((width - line2.width) // 2, line1.height + gap))

    final = _trim(canvas, PAD)
    out = output or DESIGNS_DIR / f"corvette_{code.lower()}_minimal_front.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    final.save(out, "PNG")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Typeset minimalist CORVETTE chest wordmark.")
    parser.add_argument("code", help="Generation code, e.g. C4")
    parser.add_argument("--color", choices=("black", "white"), default="black")
    parser.add_argument("--weight", choices=tuple(WEIGHT_INDEX), default="thin")
    parser.add_argument("--sub-weight", choices=tuple(WEIGHT_INDEX), default="light")
    parser.add_argument("--sub-ratio", type=float, default=SUB_RATIO)
    parser.add_argument("--tracking", type=float, default=DEFAULT_TRACKING)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()

    out = make_minimal_front(
        args.code,
        color=args.color,
        weight=args.weight,
        sub_weight=args.sub_weight,
        sub_ratio=args.sub_ratio,
        tracking=args.tracking,
        output=args.output,
    )
    im = Image.open(out)
    print(f"Saved: {out}")
    print(f"  Size: {im.size[0]}x{im.size[1]} px, color={args.color}, weight={args.weight}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
