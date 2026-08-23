#!/usr/bin/env python3
"""Compose funny bar / meme type-first tees (no OpenAI).

SKUs locked by owner (Aug 23, 2026):
  1. Liquor? Ya if she lets me
  2. I was 2 girls away from having a threesome
  3. I bark for bad bitches
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CANVAS = (4500, 5400)
WHITE = (255, 255, 255, 255)
FONT_PATH = ROOT / "designs/fonts/Anton-Regular.ttf"
OUT_DIR = ROOT / "designs/bar"


@dataclass(frozen=True)
class BarTee:
    slug: str
    lines: tuple[str, ...]
    # Relative font sizes per line (hero lines get larger)
    weights: tuple[float, ...]
    gap: int = 50


TEES: dict[str, BarTee] = {
    "liquor": BarTee(
        slug="bar_liquor_if_she_lets_me",
        lines=("LIQUOR?", "YA IF SHE", "LETS ME"),
        weights=(1.35, 1.0, 1.0),
        gap=55,
    ),
    "threesome": BarTee(
        slug="bar_two_girls_away_threesome",
        lines=("I WAS 2 GIRLS", "AWAY FROM HAVING", "A THREESOME"),
        weights=(1.15, 1.0, 1.25),
        gap=45,
    ),
    "bark": BarTee(
        slug="bar_i_bark_for_bad_bitches",
        lines=("I BARK FOR", "BAD BITCHES"),
        weights=(1.0, 1.35),
        gap=60,
    ),
}


def load_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def fit_font(draw: ImageDraw.ImageDraw, text: str, target_w: int, base_size: int) -> ImageFont.FreeTypeFont:
    """Shrink until line fits target width."""
    size = base_size
    while size > 80:
        font = load_font(size)
        w, _ = text_size(draw, text, font)
        if w <= target_w:
            return font
        size -= 8
    return load_font(max(80, size))


def compose_one(tee: BarTee) -> Path:
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"Missing font: {FONT_PATH}")

    W, H = CANVAS
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    max_text_w = int(W * 0.82)
    # Base size ~320; scaled by weight
    base = 320
    fonts: list[ImageFont.FreeTypeFont] = []
    sizes: list[tuple[int, int]] = []

    for line, weight in zip(tee.lines, tee.weights, strict=True):
        font = fit_font(draw, line, max_text_w, int(base * weight))
        fonts.append(font)
        sizes.append(text_size(draw, line, font))

    block_h = sum(h for _, h in sizes) + tee.gap * (len(tee.lines) - 1)
    # Chest placement — slightly high
    top = int(H * 0.30 - block_h / 2)
    top = max(int(H * 0.14), top)
    cx = W // 2

    y = top
    for i, line in enumerate(tee.lines):
        w, h = sizes[i]
        draw.text((cx - w // 2, y), line, font=fonts[i], fill=WHITE)
        y += h + tee.gap

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    master = OUT_DIR / f"{tee.slug}_master.png"
    canvas.save(master, format="PNG", optimize=True)
    return master


def make_black_preview(master_path: Path, preview_path: Path) -> Path:
    master = Image.open(master_path).convert("RGBA")
    bg = Image.new("RGB", master.size, (12, 12, 12))
    bg.paste(master, mask=master.split()[3])
    bbox = master.getbbox()
    if bbox:
        pad = 220
        l, t, r, b = bbox
        l = max(0, l - pad)
        t = max(0, t - pad)
        r = min(master.width, r + pad)
        b = min(master.height, b + pad)
        crop = bg.crop((l, t, r, b))
    else:
        crop = bg
    crop.save(preview_path, format="JPEG", quality=92, optimize=True)
    return preview_path


def export_printify(master: Path, printify_out: Path) -> Path:
    # White type on transparent — must skip white knock-out or ink disappears.
    subprocess.check_call(
        [
            sys.executable,
            str(ROOT / "scripts/prepare_printify_exports.py"),
            str(master),
            "--threshold",
            "235",
            "--skip-background-removal",
            "--no-knock-out-counters",
        ],
        cwd=str(ROOT),
    )
    generated = master.with_name(f"{master.stem}_UPLOAD_TO_PRINTIFY.png")
    if generated.exists():
        generated.replace(printify_out)
    return printify_out


def build(slug_key: str) -> None:
    tee = TEES[slug_key]
    master = compose_one(tee)
    preview = make_black_preview(master, OUT_DIR / f"{tee.slug}_preview_black.jpg")
    printify = export_printify(master, OUT_DIR / f"{tee.slug}_UPLOAD_TO_PRINTIFY.png")
    with Image.open(master) as im:
        print(f"OK  {master.name}  {im.size}  bbox={im.getbbox()}")
    print(f"OK  {preview.name}")
    print(f"OK  {printify.name}  exists={printify.exists()}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "which",
        nargs="?",
        default="all",
        choices=[*TEES.keys(), "all"],
        help="Which tee to build (default: all)",
    )
    args = parser.parse_args()
    keys = list(TEES.keys()) if args.which == "all" else [args.which]
    for key in keys:
        build(key)


if __name__ == "__main__":
    main()
