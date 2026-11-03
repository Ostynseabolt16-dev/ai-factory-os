#!/usr/bin/env python3
"""Compose Pickleball 'Kitchen zone' tee master (type-first, no OpenAI).

Layout locked in designs/listings/PICKLEBALL_WAVE2.md Design A:
  THIS IS THE KITCHEN
  STAY OUT.
  NON-VOLLEY ZONE
Lime dashed rectangle = the kitchen box. One small ball, not a letter swap.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CANVAS = (4500, 5400)
WHITE = (255, 255, 255, 255)
LIME = (218, 239, 31, 255)
FONT_PATH = ROOT / "designs/fonts/Anton-Regular.ttf"
BALL_PATH = ROOT / "designs/pickleball/pickleball_ball_transparent_holes.png"
MASTER_OUT = ROOT / "designs/pickleball/pickleball_kitchen_master.png"
PREVIEW_OUT = ROOT / "designs/pickleball/pickleball_kitchen_preview_black.jpg"
PRINTIFY_OUT = ROOT / "designs/pickleball/pickleball_kitchen_UPLOAD_TO_PRINTIFY.png"


def load_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


def ink(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int, int, int]:
    """Return left, top, right, bottom relative to a draw at (0, 0). Top is often negative."""
    return draw.textbbox((0, 0), text, font=font)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = ink(draw, text, font)
    return right - left, bottom - top


def draw_ink(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font: ImageFont.ImageFont, fill) -> tuple[int, int, int, int]:
    """Draw so the ink top-left sits at (x, y). Returns the ink box in canvas coordinates."""
    left, top, right, bottom = ink(draw, text, font)
    draw.text((x - left, y - top), text, font=font, fill=fill)
    return x, y, x + (right - left), y + (bottom - top)


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start: int, floor: int) -> ImageFont.FreeTypeFont:
    size = start
    while size > floor:
        font = load_font(size)
        width, _ = text_size(draw, text, font)
        if width <= max_width:
            return font
        size -= 8
    return load_font(floor)


def dashed_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill, width: int, dash: int, gap: int) -> None:
    left, top, right, bottom = box
    step = dash + gap

    def segments(a: int, b: int):
        x = a
        while x < b:
            yield x, min(x + dash, b)
            x += step

    for x0, x1 in segments(left, right):
        draw.line([(x0, top), (x1, top)], fill=fill, width=width)
        draw.line([(x0, bottom), (x1, bottom)], fill=fill, width=width)
    for y0, y1 in segments(top, bottom):
        draw.line([(left, y0), (left, y1)], fill=fill, width=width)
        draw.line([(right, y0), (right, y1)], fill=fill, width=width)


def compose() -> Path:
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"Missing font: {FONT_PATH}")
    if not BALL_PATH.exists():
        raise FileNotFoundError(f"Missing ball: {BALL_PATH}")

    W, H = CANVAS
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    margin = 280
    max_w = W - margin * 2
    cx = W // 2

    kicker = "THIS IS THE KITCHEN"
    hero = "STAY OUT."
    sub = "NON-VOLLEY ZONE"

    font_kicker = fit_font(draw, kicker, max_w, 280, 160)
    font_hero = fit_font(draw, hero, int(max_w * 0.78), 520, 280)
    font_sub = fit_font(draw, sub, int(max_w * 0.7), 150, 90)

    kw, kh = text_size(draw, kicker, font_kicker)
    hw, hh = text_size(draw, hero, font_hero)
    sw, sh = text_size(draw, sub, font_sub)

    ball = Image.open(BALL_PATH).convert("RGBA")
    ball_h = int(hh * 0.72)
    scale = ball_h / ball.height
    ball = ball.resize((max(1, int(ball.width * scale)), ball_h), Image.Resampling.LANCZOS)

    # Padding is outside the ink, so the dashes cannot cut the letters.
    pad_x = 120
    pad_y = 70
    box_w = hw + pad_x * 2
    box_h = hh + pad_y * 2

    gap_kicker = 56
    gap_sub = 48
    total_h = kh + gap_kicker + box_h + gap_sub + sh
    top = int(H * 0.46 - total_h / 2)
    top = max(int(H * 0.16), top)

    y = top
    draw_ink(draw, cx - kw // 2, y, kicker, font_kicker, WHITE)
    y += kh + gap_kicker

    box_left = cx - box_w // 2
    box_top = y
    box_right = box_left + box_w
    box_bottom = box_top + box_h
    dashed_rect(draw, (box_left, box_top, box_right, box_bottom), LIME, width=16, dash=64, gap=34)
    draw_ink(draw, box_left + pad_x, box_top + pad_y, hero, font_hero, LIME)

    # Ball sits on the outside of the bottom-right corner, clear of the type.
    ball_x = box_right - ball.width // 2
    ball_y = box_bottom - int(ball.height * 0.55)
    if ball_x + ball.width > W - 80:
        ball_x = W - 80 - ball.width
    canvas.alpha_composite(ball, (int(ball_x), int(ball_y)))

    y = box_bottom + gap_sub
    draw_ink(draw, cx - sw // 2, y, sub, font_sub, WHITE)

    MASTER_OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(MASTER_OUT, format="PNG", optimize=True)
    return MASTER_OUT


def make_black_preview(master_path: Path) -> Path:
    master = Image.open(master_path).convert("RGBA")
    bg = Image.new("RGB", master.size, (12, 12, 12))
    bg.paste(master, mask=master.split()[3])
    bbox = master.getbbox()
    if bbox:
        pad = 180
        left, top, right, bottom = bbox
        left = max(0, left - pad)
        top = max(0, top - pad)
        right = min(master.width, right + pad)
        bottom = min(master.height, bottom + pad)
        crop = bg.crop((left, top, right, bottom))
    else:
        crop = bg
    crop.thumbnail((1200, 1400), Image.Resampling.LANCZOS)
    crop.save(PREVIEW_OUT, format="JPEG", quality=90, optimize=True)
    return PREVIEW_OUT


def main() -> None:
    master = compose()
    preview = make_black_preview(master)
    import subprocess
    import sys

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
