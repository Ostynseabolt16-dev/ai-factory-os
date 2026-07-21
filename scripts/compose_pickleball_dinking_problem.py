#!/usr/bin/env python3
"""Compose Pickleball 'Dinking Problem' tee master (type-first, no OpenAI).

Layout locked in designs/listings/PICKLEBALL_WAVE2.md Design B:
  I MIGHT HAVE A   (white)
  DINKING          (lime/yellow, largest)
  PROBLEM          (white)
  + ball below (not letter substitution)
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CANVAS = (4500, 5400)
WHITE = (255, 255, 255, 255)
# Match IT WAS IN / ball yellow-green (~avg 218,239,31 on live art)
LIME = (218, 239, 31, 255)
FONT_PATH = ROOT / "designs/fonts/Anton-Regular.ttf"
BALL_PATH = ROOT / "designs/pickleball/pickleball_ball_transparent_holes.png"
MASTER_OUT = ROOT / "designs/pickleball/pickleball_dinking_problem_master.png"
PREVIEW_OUT = ROOT / "designs/pickleball/pickleball_dinking_problem_preview_black.jpg"
PRINTIFY_OUT = ROOT / "designs/pickleball/pickleball_dinking_problem_UPLOAD_TO_PRINTIFY.png"


def load_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def paste_centered(base: Image.Image, overlay: Image.Image, cx: int, cy: int) -> None:
    x = int(cx - overlay.width / 2)
    y = int(cy - overlay.height / 2)
    base.alpha_composite(overlay, (x, y))


def compose() -> Path:
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"Missing font: {FONT_PATH}")
    if not BALL_PATH.exists():
        raise FileNotFoundError(f"Missing ball: {BALL_PATH}")

    W, H = CANVAS
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Type hierarchy: DINKING ~1.7x the flanking lines
    font_small = load_font(220)
    font_hero = load_font(380)

    line1 = "I MIGHT HAVE A"
    line2 = "DINKING"
    line3 = "PROBLEM"

    w1, h1 = text_size(draw, line1, font_small)
    w2, h2 = text_size(draw, line2, font_hero)
    w3, h3 = text_size(draw, line3, font_small)

    gap_small = 40
    gap_after_hero = 50
    text_block_h = h1 + gap_small + h2 + gap_after_hero + h3

    # Ball ~18% of canvas height — BELOW text, never inside a letter
    ball = Image.open(BALL_PATH).convert("RGBA")
    ball_target_h = int(H * 0.18)
    scale = ball_target_h / ball.height
    ball = ball.resize((max(1, int(ball.width * scale)), ball_target_h), Image.Resampling.LANCZOS)
    gap_ball = 120
    total_h = text_block_h + gap_ball + ball.height

    # Vertically center the stack slightly high (chest placement)
    top = int(H * 0.28 - total_h / 2)
    top = max(int(H * 0.12), top)
    cx = W // 2

    y = top
    draw.text((cx - w1 // 2, y), line1, font=font_small, fill=WHITE)
    y += h1 + gap_small
    draw.text((cx - w2 // 2, y), line2, font=font_hero, fill=LIME)
    y += h2 + gap_after_hero
    draw.text((cx - w3 // 2, y), line3, font=font_small, fill=WHITE)
    y += h3 + gap_ball

    paste_centered(canvas, ball, cx, y + ball.height // 2)

    MASTER_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(MASTER_OUT, format="PNG", optimize=True)
    return MASTER_OUT


def make_black_preview(master_path: Path) -> Path:
    master = Image.open(master_path).convert("RGBA")
    bg = Image.new("RGB", master.size, (12, 12, 12))
    bg.paste(master, mask=master.split()[3])
    bbox = master.getbbox()
    if bbox:
        pad = 200
        l, t, r, b = bbox
        l = max(0, l - pad)
        t = max(0, t - pad)
        r = min(master.width, r + pad)
        b = min(master.height, b + pad)
        crop = bg.crop((l, t, r, b))
    else:
        crop = bg
    crop.save(PREVIEW_OUT, format="JPEG", quality=92, optimize=True)
    return PREVIEW_OUT


def main() -> None:
    master = compose()
    preview = make_black_preview(master)
    import subprocess
    import sys

    # --no-knock-out-counters: lime DINKING reads as "dark" and deletes white lines.
    subprocess.check_call(
        [
            sys.executable,
            str(ROOT / "scripts/prepare_printify_exports.py"),
            str(master),
            "--threshold",
            "235",
            "--no-knock-out-counters",
        ],
        cwd=str(ROOT),
    )
    generated = master.with_name(f"{master.stem}_UPLOAD_TO_PRINTIFY.png")
    if generated.exists():
        generated.replace(PRINTIFY_OUT)

    with Image.open(master) as im:
        print(f"OK  {master.name}  {im.size}  bbox={im.getbbox()}")
    print(f"OK  {preview.name}")
    print(f"OK  {PRINTIFY_OUT.name}  exists={PRINTIFY_OUT.exists()}")


if __name__ == "__main__":
    main()
