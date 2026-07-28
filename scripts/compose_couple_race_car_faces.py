#!/usr/bin/env python3
"""Compose matching couple race-car face tees — shop-custom style (no OpenAI).

Target look: the popular custom-shop couple tees (shirt color = car body,
print = windshield eyes + bumper smile). Closer to that merch silhouette
than the thin v1 smirk.

IP rules (hard):
  - No Disney / Pixar / Cars character names, numbers, logos, or wordmarks
  - Listing copy stays generic (matching couple race-car face / theme park)
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
TARGET_CONTENT_WIDTH = 2600

WHITE = (255, 255, 255, 255)
BLACK = (8, 8, 8, 255)
IRIS = (70, 155, 210, 255)
IRIS_DARK = (40, 110, 165, 255)

RED_SHIRT = (196, 18, 28)
SKY_SHIRT = (145, 195, 225)


def _ellipse(draw: ImageDraw.ImageDraw, cx: float, cy: float, rx: float, ry: float, fill) -> None:
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill)


def _paste(base: Image.Image, layer: Image.Image, cx: float, cy: float) -> None:
    x = int(round(cx - layer.width / 2))
    y = int(round(cy - layer.height / 2))
    base.alpha_composite(layer, (x, y))


def _disk_stroke(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    *,
    width: float,
    fill,
) -> None:
    r = width / 2
    for x, y in points:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def _arc_points(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    start_deg: float,
    end_deg: float,
    steps: int | None = None,
) -> list[tuple[float, float]]:
    steps = steps or max(40, int(abs(end_deg - start_deg) * 2))
    pts = []
    for i in range(steps + 1):
        t = start_deg + (end_deg - start_deg) * (i / steps)
        rad = math.radians(t)
        pts.append((cx + rx * math.cos(rad), cy + ry * math.sin(rad)))
    return pts


def windshield_eye(
    *,
    w: float,
    h: float,
    look_x: float,
    iris_scale: float = 1.0,
) -> Image.Image:
    """Shop-style windshield eye: white stadium oval + blue iris + black pupil."""
    pad = int(max(w, h) * 0.35)
    layer = Image.new("RGBA", (int(w) + pad * 2, int(h) + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox, oy = layer.width / 2, layer.height / 2

    # Soft black rim so white ink holds on light shirts
    rim = 14
    d.rounded_rectangle(
        [ox - w / 2 - rim, oy - h / 2 - rim, ox + w / 2 + rim, oy + h / 2 + rim],
        radius=h * 0.52,
        fill=BLACK,
    )
    d.rounded_rectangle(
        [ox - w / 2, oy - h / 2, ox + w / 2, oy + h / 2],
        radius=h * 0.48,
        fill=WHITE,
    )

    iris_r = min(w, h) * 0.30 * iris_scale
    ix = ox + look_x
    iy = oy + h * 0.02
    _ellipse(d, ix, iy, iris_r, iris_r * 0.98, IRIS_DARK)
    _ellipse(d, ix, iy, iris_r * 0.88, iris_r * 0.86, IRIS)
    pupil = iris_r * 0.48
    _ellipse(d, ix, iy, pupil, pupil, BLACK)
    # Specular (upper-left — classic cartoon eye)
    _ellipse(d, ix - pupil * 0.35, iy - pupil * 0.38, pupil * 0.28, pupil * 0.22, WHITE)

    return layer


def thick_brow(
    draw: ImageDraw.ImageDraw,
    *,
    cx: float,
    cy: float,
    length: float,
    height: float,
    angle_deg: float,
    width: float,
) -> None:
    """Solid sausage brow rotated to angle (shop McQueen = inner-down / outer-up)."""
    pts = []
    # Capsule along local x, then rotate
    half = length / 2
    for i in range(50):
        t = -half + length * (i / 49)
        pts.append((t, 0.0))
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    world = []
    for x, y in pts:
        # slight arch
        y = -height * (1 - (x / half) ** 2) if half else 0
        rx = cx + x * cos_a - y * sin_a
        ry = cy + x * sin_a + y * cos_a
        world.append((rx, ry))
    _disk_stroke(draw, world, width=width, fill=BLACK)
    # Round caps already covered by disk stroke


def bumper_grin(base: Image.Image, cx: float, cy: float, rx: float, ry: float) -> None:
    """Big thick WHITE bumper smile with black outline — shop custom look."""
    # Build crescent via polygon: outer arc then inner arc reverse
    def crescent(scale_out: float, scale_in: float, inner_lift: float, fill) -> Image.Image:
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        outer = _arc_points(cx, cy, rx * scale_out, ry * scale_out, 12, 168, steps=120)
        inner = _arc_points(
            cx, cy + inner_lift, rx * scale_in, ry * scale_in * 0.42, 168, 12, steps=100
        )
        d.polygon(outer + inner, fill=fill)
        return layer

    # Black shell (outline) — thicker for shop-print punch
    base.alpha_composite(crescent(1.0, 0.52, ry * 0.18, BLACK))
    # White bumper body — fatter grin band
    base.alpha_composite(crescent(0.93, 0.62, ry * 0.26, WHITE))

    # Soft inner crease (one clean curve, not dotted teeth)
    draw = ImageDraw.Draw(base)
    crease = _arc_points(cx, cy + ry * 0.05, rx * 0.82, ry * 0.52, 38, 142, steps=90)
    _disk_stroke(draw, crease, width=22, fill=BLACK)


def lashes(
    draw: ImageDraw.ImageDraw,
    *,
    anchor_x: float,
    anchor_y: float,
    side: str,
) -> None:
    """Three long curved lashes on outer eye corner — shop Sally style."""
    if side == "right":
        specs = [(15, 160), (48, 195), (78, 155)]
    else:
        specs = [(165, 160), (132, 195), (102, 155)]
    for ang, length in specs:
        rad = math.radians(ang)
        pts = []
        for i in range(28):
            t = i / 27
            bend = 28 * math.sin(t * math.pi) * (1 if side == "right" else -1)
            x = anchor_x + length * t * math.cos(rad) + bend * (1 - t)
            y = anchor_y - length * t * math.sin(rad) * 0.9
            pts.append((x, y))
        for i, (x, y) in enumerate(pts):
            t = i / max(1, len(pts) - 1)
            r = 14 * (1.0 - t * 0.72)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=BLACK)


def compose_race_red() -> Image.Image:
    """His — bold determined brows + thick white bumper grin."""
    W, H = CANVAS
    img = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = W / 2
    eye_w, eye_h = 1180, 620
    gap = 90
    left_cx = cx - eye_w / 2 - gap / 2
    right_cx = cx + eye_w / 2 + gap / 2
    eye_cy = H * 0.36

    # Eyes tilt slightly toward center (shop look)
    left_eye = windshield_eye(w=eye_w, h=eye_h, look_x=55, iris_scale=1.05)
    right_eye = windshield_eye(w=eye_w, h=eye_h, look_x=-55, iris_scale=1.05)
    left_eye = left_eye.rotate(8, resample=Image.Resampling.BICUBIC, expand=True)
    right_eye = right_eye.rotate(-8, resample=Image.Resampling.BICUBIC, expand=True)
    _paste(img, left_eye, left_cx, eye_cy)
    _paste(img, right_eye, right_cx, eye_cy)

    # Determined brows: outer high, inner low (angry/confident)
    brow_y = eye_cy - eye_h * 0.55
    thick_brow(
        draw,
        cx=left_cx + 40,
        cy=brow_y,
        length=eye_w * 0.72,
        height=28,
        angle_deg=18,  # left: rises toward outer
        width=95,
    )
    thick_brow(
        draw,
        cx=right_cx - 40,
        cy=brow_y,
        length=eye_w * 0.72,
        height=28,
        angle_deg=-18,
        width=95,
    )

    bumper_grin(img, cx, eye_cy + 620, rx=980, ry=420)
    return img


def compose_sky_blue() -> Image.Image:
    """Hers — soft brows, outer lashes, thin elegant smile."""
    W, H = CANVAS
    img = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = W / 2
    eye_w, eye_h = 1100, 580
    gap = 110
    left_cx = cx - eye_w / 2 - gap / 2
    right_cx = cx + eye_w / 2 + gap / 2
    eye_cy = H * 0.36

    left_eye = windshield_eye(w=eye_w, h=eye_h, look_x=35, iris_scale=1.0)
    right_eye = windshield_eye(w=eye_w, h=eye_h, look_x=-35, iris_scale=1.0)
    left_eye = left_eye.rotate(3, resample=Image.Resampling.BICUBIC, expand=True)
    right_eye = right_eye.rotate(-3, resample=Image.Resampling.BICUBIC, expand=True)
    _paste(img, left_eye, left_cx, eye_cy)
    _paste(img, right_eye, right_cx, eye_cy)

    # Soft arched brows (gentler — not angry like red)
    brow_y = eye_cy - eye_h * 0.62
    thick_brow(
        draw,
        cx=left_cx + 10,
        cy=brow_y,
        length=eye_w * 0.70,
        height=70,
        angle_deg=4,
        width=44,
    )
    thick_brow(
        draw,
        cx=right_cx - 10,
        cy=brow_y,
        length=eye_w * 0.70,
        height=70,
        angle_deg=-4,
        width=44,
    )

    lashes(
        draw,
        anchor_x=left_cx - eye_w * 0.48,
        anchor_y=eye_cy - eye_h * 0.05,
        side="left",
    )
    lashes(
        draw,
        anchor_x=right_cx + eye_w * 0.48,
        anchor_y=eye_cy - eye_h * 0.05,
        side="right",
    )

    # Thin elegant smile — smooth disk stroke (still visible at chest size)
    smile_cy = eye_cy + 540
    smile = _arc_points(cx, smile_cy, 560, 190, 22, 158, steps=100)
    _disk_stroke(draw, smile, width=42, fill=BLACK)
    return img


def trim_and_fit(image: Image.Image, target_width: int = TARGET_CONTENT_WIDTH) -> Image.Image:
    """Fit transparent art to Printify canvas — keep white ink (no knock-out)."""
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
    y = (PRINTIFY_CANVAS[1] - resized.height) // 2 - 100
    y = max(160, min(y, PRINTIFY_CANVAS[1] - resized.height - 160))
    canvas.alpha_composite(resized, (x, y))
    return canvas


def shirt_preview(master: Image.Image, shirt_rgb: tuple[int, int, int], out: Path) -> Path:
    bbox = master.getbbox()
    assert bbox
    pad = 280
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
        target_w = 700
        scale = target_w / crop.width
        resized = crop.resize(
            (target_w, max(1, int(crop.height * scale))), Image.Resampling.LANCZOS
        )
        x = (dest.width - resized.width) // 2
        y = int(dest.height * 0.28)
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
