#!/usr/bin/env python3
"""Build Facebook Page covers for Pure Speed Apparel."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

COVER_SIZE = (1640, 624)
BG = (8, 8, 10, 255)
YELLOW = (255, 214, 0, 255)
TAGLINE = "Gothic streetwear for car people."

DESIGNS = [
    "c5_variant_B_blackwheels_plate_UPLOAD_TO_PRINTIFY.png",
    "c6_variant_B_collection_UPLOAD_TO_PRINTIFY.png",
    "c7_variant_B_collection_UPLOAD_TO_PRINTIFY.png",
]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_speed_lines(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    for i, y in enumerate(range(60, height - 60, 36)):
        opacity = 14 + (i % 4) * 6
        draw.line([(40, y), (width - 40, y)], fill=(255, 255, 255, opacity), width=1)


def _draw_vignette(cover: Image.Image) -> None:
    """Soft edge fade so the center brand area pops."""
    w, h = cover.size
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    for i in range(6):
        inset = i * 18
        alpha = 8 + i * 5
        draw.rectangle((inset, inset, w - inset, h - inset), outline=(0, 0, 0, alpha), width=24)
    cover.alpha_composite(vignette)


def build_basic_cover(
    logo_path: Path,
    output_path: Path,
    *,
    tagline: str = TAGLINE,
) -> Path:
    """Brand-only cover: logo + tagline, no product images."""
    cover = Image.new("RGBA", COVER_SIZE, BG)
    draw = ImageDraw.Draw(cover)
    _draw_speed_lines(draw, *COVER_SIZE)

    logo = Image.open(logo_path).convert("RGBA")
    logo_max_w = 520
    scale = logo_max_w / logo.width
    logo = logo.resize((logo_max_w, int(logo.height * scale)), Image.Resampling.LANCZOS)

    # Slightly left of center — survives mobile crop better than hard-right placement
    center_x = int(COVER_SIZE[0] * 0.46)
    lx = center_x - logo.width // 2
    ly = (COVER_SIZE[1] - logo.height) // 2 - 28
    cover.alpha_composite(logo, (lx, ly))

    tag_font = _font(24)
    tag_w = draw.textlength(tagline, font=tag_font)
    tag_x = center_x - int(tag_w) // 2
    tag_y = ly + logo.height + 22
    draw.text((tag_x, tag_y), tagline, fill=(210, 210, 210, 255), font=tag_font)

    # Yellow accent bar under tagline (matches profile pic accent)
    bar_w = int(tag_w * 0.55)
    bar_x = center_x - bar_w // 2
    bar_y = tag_y + 34
    draw.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + 3), fill=YELLOW)

    _draw_vignette(cover)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cover.convert("RGB").save(output_path, quality=95)
    return output_path


def _content_crop(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return image
    return image.crop(bbox)


def _shirt_mockup(design: Image.Image, size: tuple[int, int]) -> Image.Image:
    w, h = size
    shirt = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shirt)

    body = (18, 34, w - 18, h - 24)
    draw.rounded_rectangle(body, radius=22, fill=(248, 248, 246, 255), outline=(210, 210, 205, 255), width=2)
    draw.arc((w // 2 - 46, 18, w // 2 + 46, 92), start=0, end=180, fill=(210, 210, 205, 255), width=2)
    draw.polygon([(18, 58), (0, 98), (18, 118), (34, 78)], fill=(248, 248, 246, 255), outline=(210, 210, 205, 255))
    draw.polygon([(w - 18, 58), (w, 98), (w - 18, 118), (w - 34, 78)], fill=(248, 248, 246, 255), outline=(210, 210, 205, 255))

    art = _content_crop(design)
    max_art = (int(w * 0.72), int(h * 0.52))
    art.thumbnail(max_art, Image.Resampling.LANCZOS)
    ax = (w - art.width) // 2
    ay = int(h * 0.30)
    shirt.alpha_composite(art, (ax, ay))
    return shirt


def build_mockup_cover(
    designs_dir: Path,
    logo_path: Path,
    output_path: Path,
    *,
    tagline: str = TAGLINE,
) -> Path:
    """Cover with shirt mockups + logo (legacy mode)."""
    cover = Image.new("RGBA", COVER_SIZE, BG)
    draw = ImageDraw.Draw(cover)
    _draw_speed_lines(draw, *COVER_SIZE)

    shirt_w, shirt_h = 290, 360
    start_x = 72
    gap = 36
    y = (COVER_SIZE[1] - shirt_h) // 2 + 8

    for i, name in enumerate(DESIGNS):
        design_path = designs_dir / name
        design = Image.open(design_path).convert("RGBA")
        mockup = _shirt_mockup(design, (shirt_w, shirt_h))

        shadow = Image.new("RGBA", (shirt_w + 40, shirt_h + 40), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle((20, 24, shirt_w + 20, shirt_h + 20), radius=24, fill=(0, 0, 0, 70))
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))

        x = start_x + i * (shirt_w + gap)
        cover.alpha_composite(shadow, (x - 10, y - 6))
        cover.alpha_composite(mockup, (x, y))

    logo = Image.open(logo_path).convert("RGBA")
    logo_max_w = 420
    scale = logo_max_w / logo.width
    logo = logo.resize((logo_max_w, int(logo.height * scale)), Image.Resampling.LANCZOS)
    lx = COVER_SIZE[0] - logo.width - 88
    ly = (COVER_SIZE[1] - logo.height) // 2 - 24
    cover.alpha_composite(logo, (lx, ly))

    tag_font = _font(22)
    tx = lx + 8
    ty = ly + logo.height + 18
    draw.text((tx, ty), tagline, fill=(220, 220, 220, 255), font=tag_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cover.convert("RGB").save(output_path, quality=95)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Pure Speed Apparel Facebook cover photos.")
    parser.add_argument(
        "--mockups",
        action="store_true",
        help="Legacy cover with shirt mockups (default is brand-only).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path (default: designs/pure_speed_apparel_cover_1640x624.png)",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    logo = root / "designs/pure_speed_apparel_profile_1024.png"
    output = args.output or root / "designs/pure_speed_apparel_cover_1640x624.png"

    if args.mockups:
        out = build_mockup_cover(root / "designs", logo, output)
    else:
        out = build_basic_cover(logo, output)

    print(f"Saved {out}")


if __name__ == "__main__":
    main()
