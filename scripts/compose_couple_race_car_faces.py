#!/usr/bin/env python3
"""Compose original matching couple race-car face tee masters (no OpenAI).

Two complementary chest graphics:
  - Race Red (his): bold windshield eyes + bumper smile
  - Sky Blue (hers): softer eyes with lashes + thin smile

IP rules (hard):
  - No Disney / Pixar / Cars character names, numbers, logos, or wordmarks
  - Original vector proportions — inspired by viral couple demand, not a clone
  - Listing copy must stay generic (race car face / matching couple / theme park)
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "designs/couple_faces"
ARTIFACTS = Path("/opt/cursor/artifacts/screenshots")

CANVAS = (4500, 5400)
PRINTIFY_CANVAS = (3951, 4919)
TARGET_CONTENT_WIDTH = 2400

WHITE = (255, 255, 255, 255)
BLACK = (12, 12, 12, 255)
IRIS = (125, 190, 225, 255)
IRIS_RING = (85, 150, 195, 255)

RED_SHIRT = (205, 32, 42)
SKY_SHIRT = (160, 205, 232)


def _ellipse(draw: ImageDraw.ImageDraw, cx: float, cy: float, rx: float, ry: float, fill) -> None:
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill)


def _paste_layer(base: Image.Image, layer: Image.Image, cx: float, cy: float) -> None:
    x = int(cx - layer.width / 2)
    y = int(cy - layer.height / 2)
    base.alpha_composite(layer, (x, y))


def _windshield_eye(
    base: Image.Image,
    cx: float,
    cy: float,
    w: float,
    h: float,
    *,
    tilt_deg: float,
    look_x: float,
) -> None:
    """Original rounded windshield eye with iris + pupil."""
    pad = int(max(w, h) * 0.4)
    layer = Image.new("RGBA", (int(w) + pad * 2, int(h) + pad * 2), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ox, oy = layer.width / 2, layer.height / 2

    # Soft black rim so white holds on light shirts too
    ld.rounded_rectangle(
        [ox - w / 2 - 10, oy - h / 2 - 10, ox + w / 2 + 10, oy + h / 2 + 10],
        radius=h * 0.48,
        fill=BLACK,
    )
    ld.rounded_rectangle(
        [ox - w / 2, oy - h / 2, ox + w / 2, oy + h / 2],
        radius=h * 0.45,
        fill=WHITE,
    )

    iris_r = min(w, h) * 0.28
    ix, iy = ox + look_x, oy + h * 0.04
    _ellipse(ld, ix, iy, iris_r, iris_r * 0.96, IRIS_RING)
    _ellipse(ld, ix, iy, iris_r * 0.88, iris_r * 0.84, IRIS)
    _ellipse(ld, ix, iy, iris_r * 0.42, iris_r * 0.42, BLACK)
    # Specular highlight
    _ellipse(ld, ix - iris_r * 0.28, iy - iris_r * 0.3, iris_r * 0.18, iris_r * 0.14, WHITE)

    if abs(tilt_deg) > 0.01:
        layer = layer.rotate(tilt_deg, resample=Image.Resampling.BICUBIC, expand=False)
    _paste_layer(base, layer, cx, cy)


def _stroke_arc(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    start: float,
    end: float,
    *,
    width: int,
    fill,
) -> None:
    """Smooth thick arc via overlapping disks (avoids frayed line joins)."""
    steps = max(60, int(abs(end - start) * 1.5))
    r = width / 2
    for i in range(steps + 1):
        t = start + (end - start) * (i / steps)
        rad = math.radians(t)
        x = cx + rx * math.cos(rad)
        y = cy + ry * math.sin(rad)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def _lash_cluster(
    draw: ImageDraw.ImageDraw,
    base_x: float,
    base_y: float,
    *,
    side: str,
) -> None:
    """Three outward lashes — original cluster, not a character trace."""
    if side == "right":
        specs = [(22, 155), (48, 195), (72, 150)]
    else:
        specs = [(158, 155), (132, 195), (108, 150)]
    for ang, length in specs:
        rad = math.radians(ang)
        steps = 18
        for i in range(steps + 1):
            t = i / steps
            x = base_x + length * t * math.cos(rad)
            y = base_y - length * t * math.sin(rad)
            # Taper toward tip
            r = 14 * (1.0 - t * 0.65)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=BLACK)


def _bumper_smile(base: Image.Image, cx: float, cy: float, rx: float, ry: float) -> None:
    """Thick white bumper crescent with black outline (prints on red blanks)."""
    # Build as: black outer crescent, then white inner crescent (fatter smile)
    def crescent(scale_out: float, scale_in: float, y_lift: float, fill) -> Image.Image:
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        outer, inner = [], []
        for deg in range(18, 163):
            rad = math.radians(deg)
            outer.append(
                (cx + rx * scale_out * math.cos(rad), cy + ry * scale_out * math.sin(rad))
            )
        for deg in range(162, 17, -1):
            rad = math.radians(deg)
            inner.append(
                (
                    cx + rx * scale_in * math.cos(rad),
                    cy + ry * scale_in * 0.55 * math.sin(rad) + y_lift,
                )
            )
        d.polygon(outer + inner, fill=fill)
        return layer

    # Black outline shell — thicker bumper band
    base.alpha_composite(crescent(1.0, 0.62, ry * 0.28, BLACK))
    # White bumper body (inset)
    base.alpha_composite(crescent(0.95, 0.70, ry * 0.34, WHITE))

    # Inner bumper crease — disk stroke so it stays smooth
    draw = ImageDraw.Draw(base)
    for deg in range(42, 139):
        rad = math.radians(deg)
        x = cx + rx * 0.86 * math.cos(rad)
        y = cy + ry * 0.78 * math.sin(rad) + 4
        r = 12
        draw.ellipse([x - r, y - r, x + r, y + r], fill=BLACK)


def compose_race_red() -> Image.Image:
    """Bold 'his' race-car face — determined brows, bumper smile."""
    W, H = CANVAS
    img = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = W / 2, H * 0.40
    eye_w, eye_h = 1050, 560
    gap = 140
    left_cx = cx - eye_w / 2 - gap / 2
    right_cx = cx + eye_w / 2 + gap / 2
    eye_cy = cy

    _windshield_eye(img, left_cx, eye_cy, eye_w, eye_h, tilt_deg=7, look_x=22)
    _windshield_eye(img, right_cx, eye_cy, eye_w, eye_h, tilt_deg=-7, look_x=-22)

    # Thick determined brows
    brow_y = eye_cy - eye_h / 2 - 70
    _stroke_arc(draw, left_cx + 30, brow_y, eye_w * 0.38, 55, 205, 335, width=78, fill=BLACK)
    _stroke_arc(draw, right_cx - 30, brow_y, eye_w * 0.38, 55, 205, 335, width=78, fill=BLACK)

    _bumper_smile(img, cx, cy + 500, rx=860, ry=380)
    return img


def compose_sky_blue() -> Image.Image:
    """Soft 'hers' race-car face — lashes, arched brows, thin smile."""
    W, H = CANVAS
    img = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = W / 2, H * 0.40
    eye_w, eye_h = 980, 520
    gap = 160
    left_cx = cx - eye_w / 2 - gap / 2
    right_cx = cx + eye_w / 2 + gap / 2
    eye_cy = cy

    _windshield_eye(img, left_cx, eye_cy, eye_w, eye_h, tilt_deg=2, look_x=14)
    _windshield_eye(img, right_cx, eye_cy, eye_w, eye_h, tilt_deg=-2, look_x=-14)

    # Soft arched brows (clearer than hairline thin)
    brow_y = eye_cy - eye_h / 2 - 95
    _stroke_arc(draw, left_cx + 10, brow_y + 10, eye_w * 0.36, 75, 215, 330, width=48, fill=BLACK)
    _stroke_arc(draw, right_cx - 10, brow_y + 10, eye_w * 0.36, 75, 215, 330, width=48, fill=BLACK)

    _lash_cluster(draw, left_cx - eye_w * 0.42, eye_cy - eye_h * 0.05, side="left")
    _lash_cluster(draw, right_cx + eye_w * 0.42, eye_cy - eye_h * 0.05, side="right")

    # Thin elegant smile (disk stroke = smooth)
    smile_cy = cy + 430
    for deg in range(28, 153):
        rad = math.radians(deg)
        x = cx + 500 * math.cos(rad)
        y = smile_cy + 160 * math.sin(rad)
        r = 17
        draw.ellipse([x - r, y - r, x + r, y + r], fill=BLACK)
    return img


def trim_and_fit(image: Image.Image, target_width: int = TARGET_CONTENT_WIDTH) -> Image.Image:
    """Fit transparent art to Printify canvas WITHOUT knocking out white ink."""
    bbox = image.getbbox()
    if not bbox:
        raise ValueError("Empty design")
    pad = 48
    l, t, r, b = bbox
    cropped = image.crop(
        (max(0, l - pad), max(0, t - pad), min(image.width, r + pad), min(image.height, b + pad))
    )
    scale = target_width / cropped.width
    new_size = (
        max(1, int(round(cropped.width * scale))),
        max(1, int(round(cropped.height * scale))),
    )
    resized = cropped.resize(new_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", PRINTIFY_CANVAS, (0, 0, 0, 0))
    x = (PRINTIFY_CANVAS[0] - resized.width) // 2
    # Chest-centered placement on Printify DTG canvas
    y = (PRINTIFY_CANVAS[1] - resized.height) // 2 - 120
    y = max(180, min(y, PRINTIFY_CANVAS[1] - resized.height - 180))
    canvas.alpha_composite(resized, (x, y))
    return canvas


def shirt_preview(master: Image.Image, shirt_rgb: tuple[int, int, int], out: Path) -> Path:
    bbox = master.getbbox()
    assert bbox
    pad = 260
    l, t, r, b = bbox
    crop = master.crop(
        (max(0, l - pad), max(0, t - pad), min(master.width, r + pad), min(master.height, b + pad))
    )
    bg = Image.new("RGB", crop.size, shirt_rgb)
    bg.paste(crop, mask=crop.split()[3])
    preview = bg.resize(
        (min(1200, bg.width), int(bg.height * min(1200, bg.width) / bg.width)),
        Image.Resampling.LANCZOS,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    preview.save(out, format="JPEG", quality=92, optimize=True)
    return out


def couple_preview(red_master: Image.Image, blue_master: Image.Image, out: Path) -> Path:
    left = Image.new("RGB", (900, 1100), RED_SHIRT)
    right = Image.new("RGB", (900, 1100), SKY_SHIRT)

    def place(dest: Image.Image, art: Image.Image) -> None:
        bbox = art.getbbox()
        assert bbox
        crop = art.crop(bbox)
        target_w = 640
        scale = target_w / crop.width
        resized = crop.resize(
            (target_w, max(1, int(crop.height * scale))), Image.Resampling.LANCZOS
        )
        x = (dest.width - resized.width) // 2
        y = int(dest.height * 0.30)
        dest.paste(resized, (x, y), resized)

    place(left, red_master)
    place(right, blue_master)
    combo = Image.new(
        "RGB",
        (left.width + right.width + 40, max(left.height, right.height)),
        (245, 245, 245),
    )
    combo.paste(left, (0, 0))
    combo.paste(right, (left.width + 40, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    combo.save(out, format="JPEG", quality=92, optimize=True)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    red = compose_race_red()
    blue = compose_sky_blue()

    red_master = OUT_DIR / "couple_race_red_face_master.png"
    blue_master = OUT_DIR / "couple_sky_blue_face_master.png"
    red.save(red_master, format="PNG", optimize=True)
    blue.save(blue_master, format="PNG", optimize=True)

    red_print = trim_and_fit(red)
    blue_print = trim_and_fit(blue)
    red_upload = OUT_DIR / "couple_race_red_face_UPLOAD_TO_PRINTIFY.png"
    blue_upload = OUT_DIR / "couple_sky_blue_face_UPLOAD_TO_PRINTIFY.png"
    red_print.save(red_upload, format="PNG", optimize=True)
    blue_print.save(blue_upload, format="PNG", optimize=True)

    red_prev = shirt_preview(red, RED_SHIRT, OUT_DIR / "couple_race_red_face_preview.jpg")
    blue_prev = shirt_preview(blue, SKY_SHIRT, OUT_DIR / "couple_sky_blue_face_preview.jpg")
    duo = couple_preview(red, blue, OUT_DIR / "couple_race_faces_side_by_side_preview.jpg")

    for src in (red_prev, blue_prev, duo):
        Image.open(src).save(ARTIFACTS / src.name, format="JPEG", quality=92)

    for path in (red_master, blue_master, red_upload, blue_upload):
        with Image.open(path) as im:
            print(f"OK  {path.name}  {im.size}  bbox={im.getbbox()}")
    print(f"OK  {red_prev.name}")
    print(f"OK  {blue_prev.name}")
    print(f"OK  {duo.name}")


if __name__ == "__main__":
    main()
