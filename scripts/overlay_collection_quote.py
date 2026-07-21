#!/usr/bin/env python3
"""Overlay 4-line staggered quote on C5/C6/C7 collection masters.

Layout matches c7_laguna_blue_collection.png (proven Etsy mockup):
  - Georgia Italic 30px
  - Per-line right edges step inward top → bottom
  - Selective quote-zone erase before draw (avoids AI typography drift)

Usage:
  .venv/bin/python scripts/overlay_collection_quote.py designs/foo.png
  .venv/bin/python scripts/overlay_collection_quote.py designs/foo.png --gen c6
  .venv/bin/python scripts/overlay_collection_quote.py designs/foo.png --lines "Line1" "Line2" "Line3" "Line4"
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REF_SIZE = (1536, 1024)
FONT_PATH = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"

DEFAULT_LINES = [
    "Razor-sharp design",
    "and track-ready power.",
    "Bold, brutal, and built to turn every",
    "highway into a runway.",
]

VELOCITY_YELLOW_LINES = [
    "End of the classic formula.",
    "No mid-engine compromise.",
    "Built when the engine still",
    "lived ahead of the driver.",
]


@dataclass(frozen=True)
class QuoteProfile:
    y_positions: list[int]
    right_edges: list[int]
    font_size: int
    erase_x0_pct: float
    erase_y0_pct: float
    gray_erase_x_pct: float


# C7 — measured from designs/corvette/c7_laguna_blue_collection.png
C7_PROFILE = QuoteProfile(
    y_positions=[798, 848, 897, 944],
    right_edges=[1355, 1326, 1255, 1187],
    font_size=30,
    erase_x0_pct=0.36,
    erase_y0_pct=0.775,
    gray_erase_x_pct=0.50,
)

# C6 — same quote layout as C7 (Laguna Blue mockup)
C6_PROFILE = QuoteProfile(
    y_positions=[798, 848, 897, 944],
    right_edges=[1355, 1326, 1255, 1187],
    font_size=30,
    erase_x0_pct=0.52,
    erase_y0_pct=0.82,
    gray_erase_x_pct=0.55,
)

PROFILES = {"c7": C7_PROFILE, "c6": C6_PROFILE, "c5": C7_PROFILE}


def _is_car_paint(r: int, g: int, b: int) -> bool:
    if r > 140 and g > 60 and b < 140 and r > g:
        return True
    if b > 100 and r < 180 and g < 180 and b >= r:
        return True
    if r > 120 and g > 120 and b > 120 and abs(r - g) < 40 and abs(g - b) < 40:
        return True
    # Gloss black / dark grey body (C7 variant B, C5 black) — must not treat as eraseable text
    mx, mn = max(r, g, b), min(r, g, b)
    if mx < 110 and mn < 55 and (mx - mn) <= 45 and (r + g + b) > 20:
        return True
    return False


def _erase_quote_zone(arr: np.ndarray, profile: QuoteProfile) -> None:
    h, w = arr.shape[:2]
    rgb = arr[:, :, :3]
    lum = rgb.mean(axis=2)
    a = arr[:, :, 3]
    x0 = int(w * profile.erase_x0_pct)
    y0 = int(h * profile.erase_y0_pct)
    gray_x = int(w * profile.gray_erase_x_pct)
    for y in range(y0, h - 8):
        for x in range(x0, w - 8):
            if a[y, x] < 128:
                continue
            r, g, b = int(rgb[y, x, 0]), int(rgb[y, x, 1]), int(rgb[y, x, 2])
            if _is_car_paint(r, g, b):
                continue
            if lum[y, x] < 50 or (x > gray_x and lum[y, x] < 120):
                arr[y, x] = (255, 255, 255, 255)

    # Bottom-right quote corner: wipe AI ghost text (incl. faded grey duplicates)
    corner_x0 = int(w * 0.52)
    corner_y0 = int(h * 0.755)
    for y in range(corner_y0, h - 4):
        for x in range(corner_x0, w - 4):
            if a[y, x] < 128:
                continue
            r, g, b = int(rgb[y, x, 0]), int(rgb[y, x, 1]), int(rgb[y, x, 2])
            if _is_car_paint(r, g, b):
                continue
            if lum[y, x] < 245:
                arr[y, x] = (255, 255, 255, 255)


def _scale_profile(profile: QuoteProfile, width: int, height: int) -> QuoteProfile:
    rw, rh = REF_SIZE
    sx, sy = width / rw, height / rh
    return QuoteProfile(
        y_positions=[int(round(y * sy)) for y in profile.y_positions],
        right_edges=[int(round(x * sx)) for x in profile.right_edges],
        font_size=max(18, int(round(profile.font_size * sy))),
        erase_x0_pct=profile.erase_x0_pct,
        erase_y0_pct=profile.erase_y0_pct,
        gray_erase_x_pct=profile.gray_erase_x_pct,
    )


def overlay_collection_quote(
    input_path: Path,
    output_path: Path | None = None,
    lines: list[str] | None = None,
    *,
    gen: str = "c7",
) -> Path:
    if lines is None:
        lines = DEFAULT_LINES
    if len(lines) != 4:
        raise ValueError("Exactly 4 quote lines required")

    profile_key = gen.lower()
    if profile_key not in PROFILES:
        raise ValueError(f"Unknown gen profile: {gen}")

    src = Image.open(input_path).convert("RGBA")
    arr = np.array(src.copy())
    h, w = arr.shape[:2]

    base = PROFILES[profile_key]
    profile = _scale_profile(base, w, h)
    _erase_quote_zone(arr, profile)

    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, size=profile.font_size)

    for y, right_x, line in zip(profile.y_positions, profile.right_edges, lines):
        tw = font.getbbox(line)[2] - font.getbbox(line)[0]
        draw.text((right_x - tw, y), line, fill=(0, 0, 0, 255), font=font)

    out = output_path or input_path
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=None)
    parser.add_argument("--gen", choices=tuple(PROFILES), default="c7", help="Quote layout profile")
    parser.add_argument(
        "--preset",
        choices=("default", "velocity-yellow"),
        default="default",
        help="Built-in quote line presets",
    )
    parser.add_argument("--lines", nargs=4, metavar="LINE", help="Four quote lines (overrides --preset)")
    args = parser.parse_args()

    if args.lines:
        lines = list(args.lines)
    elif args.preset == "velocity-yellow":
        lines = VELOCITY_YELLOW_LINES
    else:
        lines = DEFAULT_LINES

    out = overlay_collection_quote(args.input, args.output, lines, gen=args.gen)
    print(f"OK  {out}")


if __name__ == "__main__":
    main()
