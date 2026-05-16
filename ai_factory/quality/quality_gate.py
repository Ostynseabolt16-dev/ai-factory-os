"""Deterministic local quality gates."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from ai_factory.config import PROJECT_ROOT
from ai_factory.quality.duplicate_detector import detect_similar_products


def _quality_score(product: dict[str, str]) -> int:
    try:
        return int(float(product.get("quality_score") or 0))
    except ValueError:
        return 0


def _score_result(score: int, warnings: list[str]) -> dict[str, object]:
    return {"passed": score >= 70, "score": max(0, min(100, score)), "warnings": warnings}


def validate_design_quality(product: dict[str, str]) -> dict[str, object]:
    """Check local PNG existence/transparency/dimensions."""
    warnings: list[str] = []
    score = 0
    filename = product.get("filename") or product.get("image_path") or ""
    path = Path(filename)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        warnings.append("Design file is missing.")
        return _score_result(score, warnings)

    score += 30
    try:
        with Image.open(path) as image:
            width, height = image.size
            if width >= 1000 and height >= 1000:
                score += 30
            else:
                warnings.append("Image dimensions are smaller than expected.")
            if image.mode in {"RGBA", "LA"}:
                score += 20
            else:
                warnings.append("Image may not have transparency.")
    except Exception as exc:
        warnings.append(f"Could not inspect image: {exc}")
    score += min(20, _quality_score(product) * 5)
    return _score_result(score, warnings)


def validate_listing_quality(product: dict[str, str]) -> dict[str, object]:
    """Check title/tags/description readiness."""
    warnings: list[str] = []
    score = 0
    title = product.get("title") or ""
    tags = [tag for tag in (product.get("tags") or "").split("|") if tag.strip()]
    description = product.get("description") or ""

    if 40 <= len(title) <= 140:
        score += 35
    else:
        warnings.append("Title is missing or not Etsy-friendly length.")
    if len(tags) >= 10:
        score += 35
    else:
        warnings.append("Not enough tags.")
    if len(description) >= 120:
        score += 30
    else:
        warnings.append("Description is too short or missing.")
    return _score_result(score, warnings)


def validate_mockup_quality(product: dict[str, str]) -> dict[str, object]:
    """Check mockup count and local file existence."""
    warnings: list[str] = []
    paths = [path for path in (product.get("mockup_paths") or "").split("|") if path.strip()]
    existing = 0
    for raw in paths:
        path = Path(raw)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if path.exists():
            existing += 1
    if existing >= 2:
        return _score_result(100, warnings)
    warnings.append("At least two valid mockups are recommended.")
    return _score_result(existing * 35, warnings)


def calculate_overall_quality(product: dict[str, str]) -> dict[str, object]:
    """Combine design/listing/mockup quality and duplicate signals."""
    design = validate_design_quality(product)
    listing = validate_listing_quality(product)
    mockups = validate_mockup_quality(product)
    duplicates = detect_similar_products()
    duplicate_hit = any(item.get("product_id") == product.get("id") for item in duplicates)

    score = round((int(design["score"]) + int(listing["score"]) + int(mockups["score"])) / 3)
    warnings = list(design["warnings"]) + list(listing["warnings"]) + list(mockups["warnings"])  # type: ignore[arg-type]
    if duplicate_hit:
        score -= 15
        warnings.append("Possible duplicate or near-duplicate product.")
    if not product.get("niche"):
        score -= 5
        warnings.append("Missing niche reduces prioritization.")
    return _score_result(score, warnings)
