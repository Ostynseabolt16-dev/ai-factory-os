#!/usr/bin/env python3
"""Build Etsy shop profile + banner for CozyOrbitPrints."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

PROFILE_SIZE = (500, 500)
BANNER_SIZE = (3360, 840)

ROOT = Path(__file__).resolve().parents[1]
GOTHIC_FONT = ROOT / "designs/fonts/UnifrakturMaguntia-Regular.ttf"
BANNER_CARS_DIR = ROOT / "designs" / "banner"
PROFILE_HERO_FILE = "etsy_profile_c5_hero.png"

BG = (6, 6, 8, 255)
SILVER = (200, 206, 218, 255)
WHITE = (248, 248, 250, 255)
TAGLINE = "Automotive Apparel For Enthusiasts"

CAR_GAP = 64
TAGLINE_BLOCK = 108
SIDE_MARGIN = 88
SCALE_INSET = 0.94  # shrink row slightly so C5/C7 noses aren't clipped at edges

# (filename, flip horizontal, scale multiplier, height multiplier)
BANNER_LINEUP: tuple[tuple[str, bool, float, float], ...] = (
    ("etsy_banner_c5_yellow.png", False, 1.20, 1.08),
    ("etsy_banner_c6_white.png", False, 1.0, 1.0),
    ("etsy_banner_c7_black.png", True, 1.0, 1.0),
)


def _font(
    size: int,
    *,
    gothic: bool = False,
    bold: bool = False,
    italic: bool = False,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if gothic and GOTHIC_FONT.exists():
        try:
            return ImageFont.truetype(str(GOTHIC_FONT), size)
        except OSError:
            pass

    candidates: list[str] = []
    if bold and italic:
        candidates.append("/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf")
    elif bold:
        candidates.append("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf")
    elif italic:
        candidates.append("/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf")
    else:
        candidates.append("/System/Library/Fonts/Supplemental/Times New Roman.ttf")

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _is_edge_background(red: int, green: int, blue: int, alpha: int, threshold: int) -> bool:
    if alpha == 0:
        return True
    return red >= threshold and green >= threshold and blue >= threshold


def _is_edge_dark(red: int, green: int, blue: int, alpha: int, threshold: int) -> bool:
    if alpha == 0:
        return True
    return max(red, green, blue) < threshold


def _knock_out_edge_dark(image: Image.Image, threshold: int = 52) -> Image.Image:
    """Remove baked-in floor/shadow slabs connected to image edges."""
    img = image.convert("RGBA")
    width, height = img.size
    pixels = img.load()
    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or x < 0 or y < 0 or x >= width or y >= height:
            continue
        red, green, blue, alpha = pixels[x, y]
        if not _is_edge_dark(red, green, blue, alpha, threshold):
            continue
        visited.add((x, y))
        pixels[x, y] = (red, green, blue, 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    return img


def _knock_out_edge_white(image: Image.Image, threshold: int = 240) -> Image.Image:
    """Remove white/grey fringe connected to image edges (keeps car highlights)."""
    img = image.convert("RGBA")
    width, height = img.size
    pixels = img.load()
    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or x < 0 or y < 0 or x >= width or y >= height:
            continue
        red, green, blue, alpha = pixels[x, y]
        if not _is_edge_background(red, green, blue, alpha, threshold):
            continue
        visited.add((x, y))
        pixels[x, y] = (red, green, blue, 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    return img


def _trim_transparent(image: Image.Image, padding: int = 4) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return image
    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(image.width, right + padding)
    bottom = min(image.height, bottom + padding)
    return image.crop((left, top, right, bottom))


def _clean_alpha_fringe(image: Image.Image, *, cutoff: int = 96) -> Image.Image:
    """Hard cutout + remove light semi-transparent halos from API export."""
    img = image.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            red, green, blue, alpha = px[x, y]
            if alpha < cutoff:
                px[x, y] = (0, 0, 0, 0)
                continue
            lum = 0.299 * red + 0.587 * green + 0.114 * blue
            if alpha < 245 and lum > 180:
                px[x, y] = (0, 0, 0, 0)
                continue
            px[x, y] = (red, green, blue, 255)
    return img


def _is_yellow_body(red: int, green: int, blue: int) -> bool:
    return red > 95 and green > 72 and blue < 130 and red > green


def _strip_top_grey_line(image: Image.Image, *, top_rows: int = 12) -> Image.Image:
    """Remove baked-in grey horizon lines from API exports (common on C5)."""
    out = image.copy()
    px = out.load()
    w, h = out.size
    for y in range(min(top_rows, h)):
        opaque = 0
        greyish = 0
        for x in range(w):
            red, green, blue, alpha = px[x, y]
            if alpha < 16:
                continue
            if _is_yellow_body(red, green, blue):
                continue
            opaque += 1
            lum = 0.299 * red + 0.587 * green + 0.114 * blue
            if 80 <= lum < 230:
                greyish += 1
                px[x, y] = (0, 0, 0, 0)
        # full-width grey horizon (few yellow pixels on row)
        if opaque > w // 4 and greyish == opaque:
            for x in range(w):
                px[x, y] = (0, 0, 0, 0)
    return out


def _wheel_span(image: Image.Image) -> int:
    """Horizontal span of opaque pixels at tire height — used to normalize visual scale."""
    alpha = image.getchannel("A")
    w, h = image.size
    px = alpha.load()
    y0, y1 = int(h * 0.70), int(h * 0.94)
    xs: list[int] = []
    for y in range(y0, min(h, y1)):
        for x in range(w):
            if px[x, y] > 128:
                xs.append(x)
    if xs:
        return max(xs) - min(xs) + 1
    bbox = alpha.getbbox()
    if bbox:
        return bbox[2] - bbox[0]
    return w


def _prepare_banner_car(path: Path, *, flip: bool = False) -> Image.Image:
    car = _knock_out_edge_white(Image.open(path).convert("RGBA"))
    car = _knock_out_edge_dark(car)
    car = _clean_alpha_fringe(car)
    if "c5" in path.name or "profile" in path.name:
        car = _strip_top_grey_line(car)
    if flip:
        car = ImageOps.mirror(car)
    return _trim_transparent(car)


def _fit_height(image: Image.Image, height: int) -> Image.Image:
    scale = height / image.height
    width = max(1, int(image.width * scale))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def _layout_car_lineup(
    cars_dir: Path,
    lineup: tuple[tuple[str, bool, float, float], ...],
    *,
    canvas_w: int,
    max_car_h: int,
    side_margin: int,
    car_gap: int,
    scale_inset: float,
) -> list[Image.Image]:
    """Prepare and scale cars for a horizontal row (banner + profile)."""
    cars_raw: list[Image.Image] = []
    scale_boosts: list[float] = []
    height_mults: list[float] = []
    for name, flip, boost, height_mult in lineup:
        path = cars_dir / name
        if not path.exists():
            raise FileNotFoundError(
                f"Missing banner car asset: {path}\n"
                f"Run: .venv/bin/python scripts/generate_banner_cars.py"
            )
        cars_raw.append(_prepare_banner_car(path, flip=flip))
        scale_boosts.append(boost)
        height_mults.append(height_mult)

    spans = [_wheel_span(c) for c in cars_raw]
    target_span = sorted(spans)[len(spans) // 2]
    size_factors = [(target_span / max(1, s)) * boost for s, boost in zip(spans, scale_boosts)]

    zoomed: list[Image.Image] = []
    for car, sf in zip(cars_raw, size_factors):
        nw = max(1, int(car.width * sf))
        nh = max(1, int(car.height * sf))
        zoomed.append(_trim_transparent(car.resize((nw, nh), Image.Resampling.LANCZOS)))

    gap_total = car_gap * (len(zoomed) - 1)
    max_row_w = canvas_w - side_margin * 2
    width_coeff = sum(c.width / c.height for c in zoomed)
    h_from_width = (max_row_w - gap_total) / max(1.0, width_coeff)
    target_h = max(1, int(min(float(max_car_h), h_from_width) * scale_inset))
    return [_fit_height(c, max(1, int(target_h * hm))) for c, hm in zip(zoomed, height_mults)]


def _composite_car_row(
    canvas: Image.Image,
    cars: list[Image.Image],
    *,
    car_gap: int,
    car_bottom: int,
) -> None:
    total_w = sum(c.width for c in cars) + car_gap * (len(cars) - 1)
    x = (canvas.width - total_w) // 2
    for car in cars:
        y = car_bottom - car.height
        canvas.alpha_composite(car, (x, y))
        x += car.width + car_gap


def _profile_background(size: tuple[int, int]) -> Image.Image:
    """Charcoal studio gradient + vignette — lighter center stage, darker edges."""
    w, h = size
    img = Image.new("RGBA", size)
    px = img.load()
    cx, cy = w / 2, h * 0.46
    for y in range(h):
        for x in range(w):
            t = y / max(1, h - 1)
            base = 20 - t * 10
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            vig = 1.0 - 0.28 * min(1.0, dist / (w * 0.50))
            v = max(4, int(base * vig))
            px[x, y] = (v, v, min(255, v + 2), 255)
    return img


def _profile_spotlight(
    size: tuple[int, int],
    center: tuple[int, int],
    *,
    radius: int,
    peak_alpha: int = 32,
) -> Image.Image:
    """Warm radial glow behind the car."""
    w, h = size
    cx, cy = center
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    px = layer.load()
    for y in range(h):
        for x in range(w):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist >= radius:
                continue
            t = 1.0 - dist / radius
            alpha = int(peak_alpha * t * t)
            px[x, y] = (255, 210, 70, alpha)
    return layer


def _profile_floor_shadow(
    size: tuple[int, int],
    center: tuple[int, int],
    *,
    width: int,
    height: int,
    opacity: int = 88,
) -> Image.Image:
    """Soft elliptical contact shadow under the tires."""
    cx, cy = center
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse(
        (cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2),
        fill=(0, 0, 0, opacity),
    )
    blur = max(4, height // 3)
    return layer.filter(ImageFilter.GaussianBlur(radius=blur))


def _profile_reflection(car: Image.Image, *, peak_alpha: int = 38) -> Image.Image:
    """Faded mirror reflection for studio floor."""
    reflected = ImageOps.flip(car)
    w, h = reflected.size
    grad = Image.new("L", (w, h), 0)
    gpx = grad.load()
    for y in range(h):
        fade = int(peak_alpha * (1.0 - y / max(1, h - 1)) ** 1.6)
        for x in range(w):
            gpx[x, y] = fade
    out = reflected.copy()
    alpha = out.getchannel("A")
    out.putalpha(Image.composite(alpha, Image.new("L", (w, h), 0), grad))
    return out


def build_profile(cars_dir: Path, output_path: Path) -> Path:
    """500×500 shop icon — solo yellow C5 hero, studio polish, no text."""
    hero_path = cars_dir / PROFILE_HERO_FILE
    if not hero_path.exists():
        hero_path = cars_dir / "etsy_banner_c5_yellow.png"
    if not hero_path.exists():
        raise FileNotFoundError(
            f"Missing profile hero: {cars_dir / PROFILE_HERO_FILE}\n"
            f"Run: .venv/bin/python scripts/generate_banner_cars.py --profile"
        )

    car = _prepare_banner_car(hero_path)
    w, h = PROFILE_SIZE
    max_dim = 400
    scale = min(max_dim / car.width, max_dim / car.height)
    car = car.resize(
        (max(1, int(car.width * scale)), max(1, int(car.height * scale))),
        Image.Resampling.LANCZOS,
    )

    img = _profile_background(PROFILE_SIZE)
    x = (w - car.width) // 2
    y = (h - car.height) // 2 + 6
    car_cx = x + car.width // 2
    car_cy = y + int(car.height * 0.44)

    img.alpha_composite(_profile_spotlight(PROFILE_SIZE, (car_cx, car_cy), radius=int(w * 0.42)))

    tire_y = y + int(car.height * 0.93)
    reflection = _profile_reflection(car)
    gap = max(2, int(car.height * 0.012))
    img.alpha_composite(reflection, (x, tire_y + gap))

    shadow = _profile_floor_shadow(
        PROFILE_SIZE,
        (car_cx, tire_y),
        width=int(car.width * 0.78),
        height=max(8, int(car.height * 0.045)),
    )
    img.alpha_composite(shadow)

    img.alpha_composite(car, (x, y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(output_path, quality=95)
    return output_path


def build_banner(
    cars_dir: Path,
    output_path: Path,
    *,
    tagline: str = TAGLINE,
    lineup: tuple[tuple[str, bool, float, float], ...] = BANNER_LINEUP,
) -> Path:
    banner = Image.new("RGBA", BANNER_SIZE, BG)
    draw = ImageDraw.Draw(banner)
    w, h = BANNER_SIZE

    max_car_h = h - TAGLINE_BLOCK - 32

    cars = _layout_car_lineup(
        cars_dir,
        lineup,
        canvas_w=w,
        max_car_h=max_car_h,
        side_margin=SIDE_MARGIN,
        car_gap=CAR_GAP,
        scale_inset=SCALE_INSET,
    )

    _composite_car_row(banner, cars, car_gap=CAR_GAP, car_bottom=h - TAGLINE_BLOCK - 6)

    tag_font = _font(44, italic=True)
    tag_w = draw.textlength(tagline, font=tag_font)
    tag_x = (w - int(tag_w)) // 2
    tag_y = h - 82

    rule_w = int(tag_w * 0.55)
    rule_x = tag_x + (int(tag_w) - rule_w) // 2
    draw.line([(rule_x, tag_y - 20), (rule_x + rule_w, tag_y - 20)], fill=(130, 138, 152, 200), width=2)
    draw.text((tag_x + 1, tag_y + 1), tagline, fill=(0, 0, 0, 160), font=tag_font)
    draw.text((tag_x, tag_y), tagline, fill=WHITE, font=tag_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    banner.convert("RGB").save(output_path, quality=95)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CozyOrbitPrints Etsy profile + banner.")
    parser.add_argument("--profile-only", action="store_true")
    parser.add_argument("--banner-only", action="store_true")
    parser.add_argument(
        "--cars-dir",
        type=Path,
        default=BANNER_CARS_DIR,
        help="Directory with etsy_banner_c5/c6/c7 PNGs",
    )
    args = parser.parse_args()

    profile_out = ROOT / "designs" / "cozy_orbit_etsy_profile_500.png"
    banner_out = ROOT / "designs" / "cozy_orbit_etsy_banner_3360x840.png"

    if not GOTHIC_FONT.exists():
        print(f"Warning: gothic font missing at {GOTHIC_FONT}")

    if not args.banner_only:
        build_profile(args.cars_dir, profile_out)
        print(f"Saved {profile_out}")

    if not args.profile_only:
        build_banner(args.cars_dir, banner_out)
        print(f"Saved {banner_out}")


if __name__ == "__main__":
    main()
