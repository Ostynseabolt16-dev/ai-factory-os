#!/usr/bin/env python3
"""Controlled C8 black pipeline: car-only gen, local typography, safe Printify export."""

from __future__ import annotations

import argparse
import sys
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_factory.generation.openai_image import generate_simple_image_to_file

CAR_ONLY_PROMPT = """
Automotive streetwear t-shirt design source image, landscape 3:2, transparent background.

Generate ONLY the car and its natural ground shadow. Absolutely no letters, no numbers, no text,
no logos, no emblems, no badges, no quote, no watermark.

Subject must be a 2020+ C8 Stingray style mid-engine sports coupe:
- Correct mid-engine proportions: short hood, cabin-forward, long rear deck
- Front three-quarter angle facing slightly left
- Distinct side intake behind door, angular C8-style headlights
- Debadged nose and body (no crossed flags, no Corvette text, no bowtie)
- Front bumper with no plate pocket/bracket/filler panel

Paint and wheels:
- Glossy jet black paint with clean reflections
- Satin black forged wheels, split 5-spoke / Y-spoke style
- Wheel faces must stay readable with polished rim lip and bright edge highlights (avoid flat all-black blobs)
- Realistic brake calipers and tire sidewalls

Quality constraints:
- Crisp edges, no motion blur, no smear artifacts
- Uniform dark smoke window tint
- Keep generous empty space at top and bottom-left for local typography overlay
- Centered composition with car occupying the lower-middle area
""".strip()

GOTHIC_FONT = ROOT / "designs/fonts/UnifrakturMaguntia-Regular.ttf"
C8_FONT = ROOT / "designs/fonts/UnifrakturMaguntia-Regular.ttf"
V8_FONT = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
QUOTE_FONT = "/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf"
QUOTE_LINES = [
    "Blacked-out attitude,",
    "mid-engine Corvette balance.",
    "LT2 power, instant response.",
    "Built for street and circuit.",
]


def _is_bg(r: int, g: int, b: int, a: int, threshold: int) -> bool:
    if a == 0:
        return True
    return r >= threshold and g >= threshold and b >= threshold


def _flood_remove_white(image: Image.Image, threshold: int = 246) -> Image.Image:
    """Remove only edge-connected white so car highlights stay intact."""
    img = image.convert("RGBA")
    px = img.load()
    w, h = img.size
    q: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()

    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))

    while q:
        x, y = q.popleft()
        if (x, y) in seen or x < 0 or y < 0 or x >= w or y >= h:
            continue
        r, g, b, a = px[x, y]
        if not _is_bg(r, g, b, a, threshold):
            continue
        seen.add((x, y))
        px[x, y] = (r, g, b, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return img


def _remove_alpha_noise(image: Image.Image, *, alpha_min: int = 10, min_component: int = 1200) -> Image.Image:
    """Remove tiny disconnected alpha components (vertical specks/noise lines)."""
    img = image.convert("RGBA")
    px = img.load()
    w, h = img.size
    seen: set[tuple[int, int]] = set()

    for y in range(h):
        for x in range(w):
            if (x, y) in seen:
                continue
            if px[x, y][3] <= alpha_min:
                continue

            q: deque[tuple[int, int]] = deque([(x, y)])
            seen.add((x, y))
            comp: list[tuple[int, int]] = []

            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if nx < 0 or ny < 0 or nx >= w or ny >= h or (nx, ny) in seen:
                        continue
                    if px[nx, ny][3] <= alpha_min:
                        continue
                    seen.add((nx, ny))
                    q.append((nx, ny))

            xs = [c[0] for c in comp]
            ys = [c[1] for c in comp]
            comp_w = max(xs) - min(xs) + 1
            comp_h = max(ys) - min(ys) + 1
            is_vertical_noise = comp_w <= 6 and comp_h > 120

            if len(comp) < min_component or is_vertical_noise:
                for xx, yy in comp:
                    r, g, b, _ = px[xx, yy]
                    px[xx, yy] = (r, g, b, 0)

    return img


def _suppress_faint_alpha(image: Image.Image, *, alpha_cutoff: int = 48) -> Image.Image:
    """Drop very faint alpha haze that creates large noisy bbox regions."""
    img = image.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < alpha_cutoff:
                px[x, y] = (r, g, b, 0)
    return img


def _soften_ground_shadow(image: Image.Image, *, mode: str = "light") -> Image.Image:
    """Control ground shadow strength while preserving car body and wheels."""
    img = image.convert("RGBA")
    px = img.load()
    w, h = img.size
    y0 = int(h * 0.66)
    for y in range(y0, h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            mx, mn = max(r, g, b), min(r, g, b)
            sat = mx - mn
            lum = (r + g + b) / 3
            # Shadow pixels: semi-transparent, low saturation, mid/dark gray.
            shadow_candidate = sat < 42 and lum > 18 and lum < 200
            if shadow_candidate:
                if mode == "off":
                    px[x, y] = (r, g, b, 0)
                elif mode == "ultra-light":
                    # Keep only tiny tire contact, nearly invisible on light blanks.
                    px[x, y] = (r, g, b, min(24, int(a * 0.10)))
                else:
                    # Light contact shadow mode.
                    px[x, y] = (r, g, b, int(a * 0.22))
    return img


def _fill_text_counters(canvas: Image.Image, *, threshold: int = 245) -> None:
    """Fill enclosed white counters in C8/V8 text regions to solid black."""
    px = canvas.load()
    w, h = canvas.size
    seen: set[tuple[int, int]] = set()

    for y in range(h):
        for x in range(w):
            if (x, y) in seen:
                continue
            r, g, b, a = px[x, y]
            if a == 0 or not (r >= threshold and g >= threshold and b >= threshold):
                continue

            q: deque[tuple[int, int]] = deque([(x, y)])
            seen.add((x, y))
            comp: list[tuple[int, int]] = []
            touches_edge = False

            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                if cx == 0 or cy == 0 or cx == w - 1 or cy == h - 1:
                    touches_edge = True
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if nx < 0 or ny < 0 or nx >= w or ny >= h or (nx, ny) in seen:
                        continue
                    rr, gg, bb, aa = px[nx, ny]
                    if aa == 0 or not (rr >= threshold and gg >= threshold and bb >= threshold):
                        continue
                    seen.add((nx, ny))
                    q.append((nx, ny))

            if touches_edge or len(comp) < 60:
                continue

            center_x = sum(c[0] for c in comp) / len(comp)
            center_y = sum(c[1] for c in comp) / len(comp)

            in_top_c8_zone = center_y < 360 and center_x > (w * 0.42)
            in_bottom_v8_zone = center_y > (h - 300) and center_x < (w * 0.45)
            if not (in_top_c8_zone or in_bottom_v8_zone):
                continue

            for xx, yy in comp:
                px[xx, yy] = (10, 10, 10, 255)


def _draw_local_typography(car_only_path: Path, master_out: Path, *, with_quote: bool, shadow_mode: str) -> Path:
    src = Image.open(car_only_path).convert("RGBA")
    # If generator returned transparent art, keep it; otherwise clean white safely.
    alpha = src.getchannel("A").getextrema()
    subject = src if alpha[0] < 255 else _flood_remove_white(src, threshold=250)
    subject = _suppress_faint_alpha(subject, alpha_cutoff=48)
    subject = _remove_alpha_noise(subject)
    subject = _soften_ground_shadow(subject, mode=shadow_mode)
    w, h = src.size

    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    c8_font = ImageFont.truetype(str(C8_FONT), size=360)
    c8 = "C8"
    c8_bbox = draw.textbbox((0, 0), c8, font=c8_font)
    c8_w = c8_bbox[2] - c8_bbox[0]
    c8_x = (w - c8_w) // 2
    c8_y = 8
    draw.text((c8_x, c8_y), c8, fill=(170, 170, 170, 255), font=c8_font)

    v8_font = ImageFont.truetype(V8_FONT, size=165)
    draw.text((88, h - 232), "V8", fill=(150, 150, 150, 255), font=v8_font)

    canvas.alpha_composite(subject)

    if with_quote:
        quote_font = ImageFont.truetype(QUOTE_FONT, size=38)
        line = "Mid-engine balance. LT2 response."
        bbox = quote_font.getbbox(line)
        text_w = bbox[2] - bbox[0]
        draw.text((w - text_w - 85, h - 138), line, fill=(180, 180, 180, 255), font=quote_font)

    master_out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(master_out, format="PNG")
    return master_out


def _run_export(master_out: Path, upload_out: Path, *, target_width: int) -> None:
    """Transparent-safe export: trim, scale, and center on Printify canvas."""
    canvas_size = (3951, 4919)
    src = Image.open(master_out).convert("RGBA")
    bbox = src.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("Master has no visible alpha content.")

    left, top, right, bottom = bbox
    pad = 8
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(src.width, right + pad)
    bottom = min(src.height, bottom + pad)
    trimmed = src.crop((left, top, right, bottom))

    scale = target_width / trimmed.width
    new_size = (
        max(1, int(round(trimmed.width * scale))),
        max(1, int(round(trimmed.height * scale))),
    )
    resized = trimmed.resize(new_size, Image.Resampling.LANCZOS)

    out = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    x = (canvas_size[0] - resized.width) // 2
    y = (canvas_size[1] - resized.height) // 2
    out.alpha_composite(resized, (x, y))
    upload_out.parent.mkdir(parents=True, exist_ok=True)
    out.save(upload_out, format="PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--car-out", type=Path, default=Path("designs/_c8_black_car_only.png"))
    parser.add_argument("--master-out", type=Path, default=Path("designs/corvette/c8_black_gothic_collection.png"))
    parser.add_argument(
        "--upload-out",
        type=Path,
        default=Path("designs/corvette/c8_black_gothic_collection_UPLOAD_TO_PRINTIFY.png"),
    )
    parser.add_argument("--skip-generate", action="store_true", help="Reuse existing --car-out")
    parser.add_argument("--with-quote", action="store_true", help="Add small quote paragraph at bottom-right")
    parser.add_argument("--target-width", type=int, default=2850, help="Final artwork width on Printify canvas")
    parser.add_argument(
        "--shadow-mode",
        choices=("off", "ultra-light", "light"),
        default="light",
        help="Ground shadow intensity mode",
    )
    args = parser.parse_args()

    if not args.skip_generate:
        generated = generate_simple_image_to_file(
            CAR_ONLY_PROMPT,
            args.car_out,
            model="gpt-image-1",
            size="1536x1024",
            background="transparent",
        )
        print(f"OK  car-only {generated}")
    else:
        if not args.car_out.exists():
            raise FileNotFoundError(f"Missing --car-out file: {args.car_out}")
        print(f"OK  reuse car-only {args.car_out.resolve()}")

    master = _draw_local_typography(
        args.car_out,
        args.master_out,
        with_quote=args.with_quote,
        shadow_mode=args.shadow_mode,
    )
    print(f"OK  master {master.resolve()}")

    _run_export(args.master_out, args.upload_out, target_width=args.target_width)
    print(f"OK  upload {args.upload_out.resolve()}")


if __name__ == "__main__":
    main()
