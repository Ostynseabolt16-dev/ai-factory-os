"""Generate simple product mockups from transparent PNG designs.

This module uses Pillow only. It creates clean placeholder mockups now, and can
later be swapped to real template images without changing the batch pipeline.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from ai_factory.config import MOCKUPS_DIR, PROJECT_ROOT

CANVAS_SIZE = (1400, 1400)
PRODUCT_WHITE = (248, 248, 246, 255)
PRODUCT_GRAY = (232, 232, 228, 255)
BACKGROUND = (244, 238, 228, 255)


def _open_design(design_path: Path) -> Image.Image:
    """Open the transparent design PNG as RGBA."""
    if not design_path.exists():
        raise FileNotFoundError(f"Design image not found: {design_path}")
    return Image.open(design_path).convert("RGBA")


def _resize_to_fit(image: Image.Image, max_size: tuple[int, int]) -> Image.Image:
    """Resize while preserving aspect ratio."""
    copy = image.copy()
    copy.thumbnail(max_size, Image.Resampling.LANCZOS)
    return copy


def _paste_center(base: Image.Image, overlay: Image.Image, center: tuple[int, int]) -> None:
    """Alpha-composite an overlay centered at the given point."""
    x = center[0] - overlay.width // 2
    y = center[1] - overlay.height // 2
    base.alpha_composite(overlay, (x, y))


def _shadow(size: tuple[int, int], blur: int = 24) -> Image.Image:
    """Soft shadow behind product shapes."""
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    draw.ellipse((80, size[1] - 140, size[0] - 80, size[1] - 40), fill=(0, 0, 0, 55))
    return shadow.filter(ImageFilter.GaussianBlur(blur))


def _save(image: Image.Image, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(path, quality=95)
    return path


def _resolve_path(path: str | Path) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return resolved


def _shirt_base(background: tuple[int, int, int, int] = (255, 255, 255, 255)) -> Image.Image:
    image = Image.new("RGBA", CANVAS_SIZE, background)
    image.alpha_composite(_shadow(CANVAS_SIZE))
    draw = ImageDraw.Draw(image)

    # Simple front t-shirt silhouette.
    draw.polygon([(410, 260), (520, 180), (620, 240), (780, 240), (880, 180), (990, 260),
                  (900, 430), (830, 390), (830, 1060), (570, 1060), (570, 390),
                  (500, 430)], fill=PRODUCT_WHITE, outline=(210, 210, 205, 255), width=6)
    draw.arc((610, 180, 790, 330), start=0, end=180, fill=(210, 210, 205, 255), width=5)
    return image


def _hoodie_base() -> Image.Image:
    image = Image.new("RGBA", CANVAS_SIZE, (238, 242, 245, 255))
    image.alpha_composite(_shadow(CANVAS_SIZE))
    draw = ImageDraw.Draw(image)

    # Hoodie body, hood, sleeves, and pocket.
    draw.rounded_rectangle((470, 360, 930, 1120), radius=70, fill=PRODUCT_GRAY,
                           outline=(190, 190, 186, 255), width=6)
    draw.pieslice((520, 140, 880, 520), start=180, end=360, fill=PRODUCT_GRAY,
                  outline=(190, 190, 186, 255), width=6)
    draw.polygon([(470, 420), (320, 650), (430, 760), (520, 560)], fill=PRODUCT_GRAY,
                 outline=(190, 190, 186, 255))
    draw.polygon([(930, 420), (1080, 650), (970, 760), (880, 560)], fill=PRODUCT_GRAY,
                 outline=(190, 190, 186, 255))
    draw.rounded_rectangle((570, 830, 830, 1000), radius=45, fill=(220, 220, 216, 255))
    return image


def _mug_base() -> Image.Image:
    image = Image.new("RGBA", CANVAS_SIZE, (246, 245, 241, 255))
    image.alpha_composite(_shadow(CANVAS_SIZE))
    draw = ImageDraw.Draw(image)

    # Mug body and handle.
    draw.rounded_rectangle((430, 360, 850, 980), radius=80, fill=PRODUCT_WHITE,
                           outline=(205, 205, 200, 255), width=7)
    draw.ellipse((760, 500, 1060, 840), fill=(0, 0, 0, 0), outline=(205, 205, 200, 255), width=45)
    draw.ellipse((830, 570, 990, 770), fill=(246, 245, 241, 255))
    draw.ellipse((450, 325, 830, 410), fill=(235, 235, 230, 255), outline=(205, 205, 200, 255), width=5)
    return image


def create_front_shirt_mockup(design: Image.Image, output_path: Path) -> Path:
    image = _shirt_base()
    placed_design = _resize_to_fit(design, (440, 440))
    _paste_center(image, placed_design, (700, 650))
    return _save(image, output_path)


def create_hoodie_mockup(design: Image.Image, output_path: Path) -> Path:
    image = _hoodie_base()
    placed_design = _resize_to_fit(design, (390, 390))
    _paste_center(image, placed_design, (700, 660))
    return _save(image, output_path)


def create_mug_mockup(design: Image.Image, output_path: Path) -> Path:
    image = _mug_base()
    placed_design = _resize_to_fit(design, (310, 310))
    _paste_center(image, placed_design, (635, 650))
    return _save(image, output_path)


def create_lifestyle_mockup(design: Image.Image, output_path: Path) -> Path:
    image = Image.new("RGBA", CANVAS_SIZE, BACKGROUND)
    draw = ImageDraw.Draw(image)
    # Clean desk/lifestyle card: subtle frame, garment centered, no noisy labels.
    draw.rounded_rectangle((85, 85, 1315, 1315), radius=70, fill=(250, 247, 239, 255), outline=(224, 211, 193, 255), width=8)
    image.alpha_composite(_shirt_base((0, 0, 0, 0)))
    placed_design = _resize_to_fit(design, (420, 420))
    _paste_center(image, placed_design, (700, 650))
    return _save(image, output_path)


def validate_mockup_alignment(mockup_path: str | Path) -> dict[str, object]:
    """Check that mockup dimensions are square and large enough for Etsy previews."""
    path = _resolve_path(mockup_path)
    warnings: list[str] = []
    if not path.exists():
        return {"valid": False, "warnings": ["mockup file missing"], "width": 0, "height": 0}
    with Image.open(path) as image:
        width, height = image.size
    if width != height:
        warnings.append("mockup is not square")
    if width < 1000 or height < 1000:
        warnings.append("mockup is smaller than 1000px")
    return {"valid": not warnings, "warnings": warnings, "width": width, "height": height}


def score_mockup_quality(mockup_paths: list[str | Path]) -> dict[str, object]:
    """Score a product's mockup set from local image files."""
    if not mockup_paths:
        return {"score": 0, "passed": False, "warnings": ["no mockups found"]}
    score = 0
    warnings: list[str] = []
    valid_count = 0
    for path in mockup_paths:
        result = validate_mockup_alignment(path)
        if result["valid"]:
            valid_count += 1
            score += 25
        else:
            warnings.extend(str(w) for w in result["warnings"])
    if valid_count >= 2:
        score += 25
    else:
        warnings.append("at least two strong mockups recommended")
    if valid_count >= 4:
        score += 10
    return {"score": min(100, score), "passed": score >= 70, "warnings": warnings, "valid_count": valid_count}


def generate_product_mockups(product_id: int, design_path: Path | str) -> list[Path]:
    """Create all mockups for one product and return output paths."""
    design_file = Path(design_path)
    if not design_file.is_absolute():
        design_file = PROJECT_ROOT / design_file

    design = _open_design(design_file)
    output_dir = MOCKUPS_DIR / f"product_{product_id:04d}"

    outputs = [
        create_front_shirt_mockup(design, output_dir / "front_shirt_mockup.jpg"),
        create_lifestyle_mockup(design, output_dir / "lifestyle_mockup.jpg"),
        create_hoodie_mockup(design, output_dir / "hoodie_mockup.jpg"),
        create_mug_mockup(design, output_dir / "mug_mockup.jpg"),
    ]
    return outputs


def generate_mockup_set(product_id: int, design_path: Path | str) -> dict[str, object]:
    """Generate and score a small high-quality mockup set."""
    outputs = generate_product_mockups(product_id, design_path)
    score = score_mockup_quality(outputs)
    return {"product_id": product_id, "mockup_paths": outputs, "quality": score}

