#!/usr/bin/env python3
"""Compose Pickleball 'My Six Pack' tee master (no OpenAI).

Body-joke parallel to Eyes Up Here: six pickleballs as abs.
Wave 2 Design C — original label MY SIX PACK (not CHECK OUT MY SIX PACK clone).

v2 layout (Printify AI failed abs grid — keep local compose):
  MY SIX PACK     (lime Anton, above — DINKING pop)
  2×3 ball grid   (tight torso/abs read — same ball as Eyes Up Here)
  no bottom label (cleaner thumb, like Eyes Up Here)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CANVAS = (4500, 5400)
WHITE = (255, 255, 255, 255)
# Match DINKING / IT WAS IN lime
LIME = (218, 239, 31, 255)
FONT_PATH = ROOT / "designs/fonts/Anton-Regular.ttf"
BALL_PATH = ROOT / "designs/pickleball/pickleball_ball_transparent_holes.png"
MASTER_OUT = ROOT / "designs/pickleball/pickleball_six_pack_master.png"
PREVIEW_OUT = ROOT / "designs/pickleball/pickleball_six_pack_preview_black.jpg"
PRINTIFY_OUT = ROOT / "designs/pickleball/pickleball_six_pack_UPLOAD_TO_PRINTIFY.png"

# Abs silhouette: 2 columns × 3 rows (reads as six-pack on chest)
COLS, ROWS = 2, 3


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

    font_hero = load_font(380)
    line1 = "MY SIX PACK"
    w1, h1 = text_size(draw, line1, font_hero)

    # Slightly larger balls, much tighter gaps → abs block not sticker sheet
    ball_src = Image.open(BALL_PATH).convert("RGBA")
    ball_h = int(H * 0.155)
    scale = ball_h / ball_src.height
    ball = ball_src.resize(
        (max(1, int(ball_src.width * scale)), ball_h), Image.Resampling.LANCZOS
    )
    gap_x = int(ball.width * 0.04)
    gap_y = int(ball.height * 0.04)
    grid_w = COLS * ball.width + (COLS - 1) * gap_x
    grid_h = ROWS * ball.height + (ROWS - 1) * gap_y

    gap_after_title = 70
    total_h = h1 + gap_after_title + grid_h

    # Chest-centered stack (same idea as Eyes Up Here)
    top = int(H * 0.32 - total_h / 2)
    top = max(int(H * 0.12), top)
    cx = W // 2

    y = top
    draw.text((cx - w1 // 2, y), line1, font=font_hero, fill=LIME)
    y += h1 + gap_after_title

    grid_left = cx - grid_w // 2
    grid_top = y
    for row in range(ROWS):
        for col in range(COLS):
            bx = grid_left + col * (ball.width + gap_x) + ball.width // 2
            by = grid_top + row * (ball.height + gap_y) + ball.height // 2
            paste_centered(canvas, ball, bx, by)

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
        crop = bg.crop(
            (
                max(0, l - pad),
                max(0, t - pad),
                min(master.width, r + pad),
                min(master.height, b + pad),
            )
        )
    else:
        crop = bg
    crop.save(PREVIEW_OUT, format="JPEG", quality=92, optimize=True)
    return PREVIEW_OUT


def main() -> None:
    master = compose()
    preview = make_black_preview(master)

    # White type + transparent ball holes — don't knock out counters
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
