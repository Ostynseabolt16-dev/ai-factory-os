#!/usr/bin/env python3
"""Controlled C4 pop-up headlights design: car-only gen, local type, safe export."""

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

Generate ONLY the car and a very faint natural tire contact shadow. Absolutely no letters,
no numbers, no text, no logos, no emblems, no badges, no license plate, no watermark.

Subject: 1984-1996 C4-style American sports coupe, front three-quarter view facing slightly left.
- Sharp 1980s/1990s wedge profile
- Pop-up headlights raised and clearly visible
- Glossy black paint with crisp realistic reflections and readable body edges
- Bright silver/chrome five-spoke wheels for contrast (not black wheels)
- Smooth debadged nose, no crossed flags, no bowtie, no wordmarks
- No front plate, no plate bracket, no plate pocket text

Quality constraints:
- Photorealistic render quality, not cartoon, not vector illustration
- Crisp car edges, no motion blur, no smear artifacts
- Uniform dark smoke window tint
- Keep empty space above and below for local typography
- Centered composition with car occupying the lower-middle area
""".strip()

PRINTIFY_CANVAS = (3951, 4919)
GOTHIC_FONT = ROOT / "designs/fonts/UnifrakturMaguntia-Regular.ttf"
HEADLINE_FONT = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"
SERIF_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"


def _is_bg(r: int, g: int, b: int, a: int, threshold: int) -> bool:
    return a == 0 or (r >= threshold and g >= threshold and b >= threshold)


def _flood_remove_white(image: Image.Image, threshold: int = 250) -> Image.Image:
    """Fallback for non-transparent generations; remove edge-connected white only."""
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


def _suppress_alpha_noise(image: Image.Image, *, alpha_cutoff: int = 42, min_component: int = 900) -> Image.Image:
    """Remove faint haze and tiny disconnected alpha artifacts before scaling."""
    img = image.convert("RGBA")
    px = img.load()
    w, h = img.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < alpha_cutoff:
                px[x, y] = (r, g, b, 0)

    seen: set[tuple[int, int]] = set()
    for y in range(h):
        for x in range(w):
            if (x, y) in seen or px[x, y][3] <= alpha_cutoff:
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
                    if px[nx, ny][3] <= alpha_cutoff:
                        continue
                    seen.add((nx, ny))
                    q.append((nx, ny))

            xs = [p[0] for p in comp]
            ys = [p[1] for p in comp]
            comp_w = max(xs) - min(xs) + 1
            comp_h = max(ys) - min(ys) + 1
            if len(comp) < min_component or (comp_w <= 6 and comp_h > 120):
                for xx, yy in comp:
                    r, g, b, _ = px[xx, yy]
                    px[xx, yy] = (r, g, b, 0)
    return img


def _soften_shadow(image: Image.Image) -> Image.Image:
    """Keep only a subtle tire contact shadow; remove broad haze."""
    img = image.convert("RGBA")
    px = img.load()
    w, h = img.size
    y0 = int(h * 0.63)
    for y in range(y0, h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            mx, mn = max(r, g, b), min(r, g, b)
            sat = mx - mn
            lum = (r + g + b) / 3
            # Only touch translucent grey shadows; preserve opaque black tires/underbody.
            if a < 185 and sat < 42 and 18 < lum < 205:
                px[x, y] = (r, g, b, min(30, int(a * 0.14)))
    return img


def _prep_subject(car_path: Path) -> Image.Image:
    src = Image.open(car_path).convert("RGBA")
    alpha = src.getchannel("A").getextrema()
    subject = src if alpha[0] < 255 else _flood_remove_white(src)
    subject = _suppress_alpha_noise(subject)
    subject = _soften_shadow(subject)
    return subject


def _draw_master(car_path: Path, master_out: Path) -> Path:
    subject = _prep_subject(car_path)
    w, h = subject.size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    c4_font = ImageFont.truetype(str(GOTHIC_FONT), size=210)
    c4 = "C4"
    c4_bbox = draw.textbbox((0, 0), c4, font=c4_font)
    draw.text((95, 78), c4, font=c4_font, fill=(22, 22, 22, 255))

    headline_font = ImageFont.truetype(HEADLINE_FONT, size=150)
    headline = "POP-UP ERA"
    hb = draw.textbbox((0, 0), headline, font=headline_font)
    draw.text(((w - (hb[2] - hb[0])) // 2 + 70, 70), headline, font=headline_font, fill=(22, 22, 22, 255))

    canvas.alpha_composite(subject)

    sub_font = ImageFont.truetype(SERIF_BOLD, size=70)
    sub = "FOURTH GEN V8"
    sb = draw.textbbox((0, 0), sub, font=sub_font)
    draw.text(((w - (sb[2] - sb[0])) // 2, h - 138), sub, font=sub_font, fill=(24, 24, 24, 255))

    year_font = ImageFont.truetype(HEADLINE_FONT, size=54)
    years = "1984-1996"
    yb = draw.textbbox((0, 0), years, font=year_font)
    draw.text((w - (yb[2] - yb[0]) - 100, h - 235), years, font=year_font, fill=(58, 58, 58, 255))

    master_out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(master_out, format="PNG")
    return master_out


def _export(master_path: Path, upload_out: Path, *, target_width: int) -> Path:
    src = Image.open(master_path).convert("RGBA")
    bbox = src.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("Master has no visible content.")

    l, t, r, b = bbox
    pad = 8
    crop = src.crop((max(0, l - pad), max(0, t - pad), min(src.width, r + pad), min(src.height, b + pad)))
    scale = target_width / crop.width
    resized = crop.resize(
        (max(1, round(crop.width * scale)), max(1, round(crop.height * scale))),
        Image.Resampling.LANCZOS,
    )
    out = Image.new("RGBA", PRINTIFY_CANVAS, (0, 0, 0, 0))
    x = (PRINTIFY_CANVAS[0] - resized.width) // 2
    y = (PRINTIFY_CANVAS[1] - resized.height) // 2
    out.alpha_composite(resized, (x, y))
    upload_out.parent.mkdir(parents=True, exist_ok=True)
    out.save(upload_out, format="PNG", optimize=True)
    return upload_out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--car-out", type=Path, default=Path("designs/_c4_popup_car_only.png"))
    parser.add_argument("--master-out", type=Path, default=Path("designs/corvette/c4_popup_gothic_collection.png"))
    parser.add_argument(
        "--upload-out",
        type=Path,
        default=Path("designs/corvette/c4_popup_gothic_collection_UPLOAD_TO_PRINTIFY.png"),
    )
    parser.add_argument("--skip-generate", action="store_true")
    parser.add_argument("--target-width", type=int, default=3200)
    args = parser.parse_args()

    if args.skip_generate:
        if not args.car_out.exists():
            raise FileNotFoundError(args.car_out)
        print(f"OK  reuse car-only {args.car_out.resolve()}")
    else:
        generated = generate_simple_image_to_file(
            CAR_ONLY_PROMPT,
            args.car_out,
            model="gpt-image-1",
            size="1536x1024",
            background="transparent",
        )
        print(f"OK  car-only {generated}")

    master = _draw_master(args.car_out, args.master_out)
    print(f"OK  master {master.resolve()}")
    upload = _export(args.master_out, args.upload_out, target_width=args.target_width)
    print(f"OK  upload {upload.resolve()}")


if __name__ == "__main__":
    main()
