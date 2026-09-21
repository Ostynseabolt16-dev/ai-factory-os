#!/usr/bin/env python3
"""Compose type-first joke tee masters (no OpenAI — Pillow + Anton only).

Same layout family as the pickleball IT WAS IN / Dinking Problem tees, which are
the only non-Corvette designs that have converted: small white setup line, big
accent-colored punchline, small white tag line. White + accent type means these
print on DARK shirts only.

Usage:
  python3 scripts/compose_type_first_tee.py                # build every SKU
  python3 scripts/compose_type_first_tee.py third_pedal     # build one
  python3 scripts/compose_type_first_tee.py --list
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT_PATH = ROOT / "designs/fonts/Anton-Regular.ttf"
CANVAS = (4500, 5400)
WHITE = (255, 255, 255, 255)

# Accents picked bright enough to hold up on Black / Navy / Charcoal DTG.
AMBER = (255, 176, 32, 255)
CONE_ORANGE = (255, 106, 19, 255)
LIME = (218, 239, 31, 255)

MAX_LINE_WIDTH = int(CANVAS[0] * 0.88)
HERO_MAX_SIZE = 460
SMALL_MAX_SIZE = 230

SKUS: dict[str, dict] = {
    "third_pedal": {
        "niche": "car_culture",
        "stem": "manual_third_pedal",
        "lines": ["MY ANTI-THEFT DEVICE", "THIRD PEDAL", "GOOD LUCK"],
        "hero": 1,
        "accent": AMBER,
    },
    "five_minute_job": {
        "niche": "car_culture",
        "stem": "garage_five_minute_job",
        "lines": ["IT WAS SUPPOSED TO BE A", "5 MINUTE JOB", "THAT WAS SATURDAY"],
        "hero": 1,
        "accent": AMBER,
    },
    "cone_hit_me": {
        "niche": "car_culture",
        "stem": "autocross_cone_hit_me",
        "lines": ["I DIDN'T HIT THE CONE", "THE CONE", "HIT ME"],
        "hero": 1,
        "accent": CONE_ORANGE,
    },
}


def load_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


def ink_box(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int, int, int]:
    """Ink bbox as (left, top, width, height). left/top are the offsets between the
    draw origin and the first painted pixel — Anton's are large, so ignoring them
    stacks the lines on top of each other."""
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return left, top, right - left, bottom - top


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    _, _, width, height = ink_box(draw, text, font)
    return width, height


def fit_font(
    draw: ImageDraw.ImageDraw, text: str, max_size: int, max_width: int = MAX_LINE_WIDTH
) -> ImageFont.FreeTypeFont:
    """Largest Anton size (<= max_size) that keeps the line inside the print width."""
    size = max_size
    font = load_font(size)
    while size > 40 and text_size(draw, text, font)[0] > max_width:
        size -= 10
        font = load_font(size)
    return font


def compose(spec: dict) -> Path:
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    hero_index = spec["hero"]

    rendered = []
    for i, text in enumerate(spec["lines"]):
        is_hero = i == hero_index
        font = fit_font(draw, text, HERO_MAX_SIZE if is_hero else SMALL_MAX_SIZE)
        left, top, w, h = ink_box(draw, text, font)
        rendered.append(
            {
                "text": text,
                "font": font,
                "left": left,
                "top": top,
                "w": w,
                "h": h,
                "fill": spec["accent"] if is_hero else WHITE,
            }
        )

    gap = 55
    total_h = sum(item["h"] for item in rendered) + gap * (len(rendered) - 1)

    cx = CANVAS[0] // 2
    y = int(CANVAS[1] * 0.32 - total_h / 2)
    for item in rendered:
        draw.text(
            (cx - item["w"] // 2 - item["left"], y - item["top"]),
            item["text"],
            font=item["font"],
            fill=item["fill"],
        )
        y += item["h"] + gap

    out = ROOT / f"designs/{spec['niche']}/{spec['stem']}_master.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, format="PNG", optimize=True)
    return out


def make_dark_preview(master_path: Path) -> Path:
    master = Image.open(master_path).convert("RGBA")
    bg = Image.new("RGB", master.size, (18, 18, 20))
    bg.paste(master, mask=master.split()[3])
    bbox = master.getbbox()
    if bbox:
        pad = 200
        left, top, right, bottom = bbox
        crop = bg.crop(
            (
                max(0, left - pad),
                max(0, top - pad),
                min(master.width, right + pad),
                min(master.height, bottom + pad),
            )
        )
    else:
        crop = bg
    out = master_path.with_name(master_path.stem.replace("_master", "") + "_preview_black.jpg")
    crop.save(out, format="JPEG", quality=92, optimize=True)
    return out


def export_for_printify(master_path: Path) -> Path:
    # --no-knock-out-counters: the accent line reads as "dark" ink, so counter
    # knock-out would delete the white lines around it.
    subprocess.check_call(
        [
            sys.executable,
            str(ROOT / "scripts/prepare_printify_exports.py"),
            str(master_path),
            "--threshold",
            "235",
            "--no-knock-out-counters",
        ],
        cwd=str(ROOT),
    )
    generated = master_path.with_name(f"{master_path.stem}_UPLOAD_TO_PRINTIFY.png")
    final = master_path.with_name(master_path.stem.replace("_master", "") + "_UPLOAD_TO_PRINTIFY.png")
    if generated != final:
        generated.replace(final)
    return final


def build(key: str) -> None:
    spec = SKUS[key]
    master = compose(spec)
    preview = make_dark_preview(master)
    export = export_for_printify(master)
    with Image.open(export) as im:
        print(f"OK  {key}: {export.relative_to(ROOT)}  {im.size}")
    print(f"    preview {preview.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skus", nargs="*", choices=sorted(SKUS) or None, help="SKU keys (default: all)")
    parser.add_argument("--list", action="store_true", help="List SKU keys and their copy")
    args = parser.parse_args()

    if args.list:
        for key, spec in SKUS.items():
            print(f"{key}: {' / '.join(spec['lines'])}  ({spec['niche']})")
        return

    if not FONT_PATH.exists():
        raise FileNotFoundError(f"Missing font: {FONT_PATH}")

    for key in args.skus or list(SKUS):
        build(key)


if __name__ == "__main__":
    main()
