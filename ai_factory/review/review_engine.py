"""Local heuristic review engine for products.

No AI calls happen here. The review score is intentionally explainable and
based only on products.csv fields.
"""

from __future__ import annotations

from ai_factory.products.product_manager import read_products

PASSING_REVIEW_SCORE = 70


def _tag_count(product: dict[str, str]) -> int:
    raw = product.get("tags") or ""
    if not raw.strip():
        return 0
    return len([tag for tag in raw.split("|") if tag.strip()])


def _mockup_count(product: dict[str, str]) -> int:
    raw = product.get("mockup_paths") or ""
    if not raw.strip():
        return 0
    return len([path for path in raw.split("|") if path.strip()])


def _quality_score(product: dict[str, str]) -> int:
    try:
        return int(float(product.get("quality_score") or "0"))
    except ValueError:
        return 0


def _duplicate_count(product: dict[str, str]) -> int:
    filename = (product.get("filename") or "").strip().lower()
    niche = (product.get("niche") or "").strip().lower()
    count = 0
    for row in read_products():
        if row.get("id") == product.get("id"):
            continue
        if filename and filename == (row.get("filename") or "").strip().lower():
            count += 1
        elif niche and niche == (row.get("niche") or "").strip().lower():
            count += 1
    return count


def calculate_review_score(product: dict[str, str]) -> dict[str, object]:
    """Return score, warnings, and pass/fail recommendation for one product."""
    score = 0
    warnings: list[str] = []

    title_len = len((product.get("title") or "").strip())
    tags = _tag_count(product)
    mockups = _mockup_count(product)
    quality = _quality_score(product)
    niche = (product.get("niche") or "").strip()

    if 40 <= title_len <= 140:
        score += 20
    elif title_len:
        score += 10
        warnings.append("Title exists but length is not ideal.")
    else:
        warnings.append("Missing title.")

    if tags >= 10:
        score += 20
    elif tags:
        score += 10
        warnings.append("Add more tags before upload.")
    else:
        warnings.append("Missing tags.")

    if niche:
        score += 15
    else:
        warnings.append("Missing niche.")

    if mockups >= 2:
        score += 15
    elif mockups:
        score += 8
        warnings.append("Only one mockup found.")
    else:
        warnings.append("Missing mockups.")

    score += min(20, quality * 5)

    duplicates = _duplicate_count(product)
    if duplicates:
        score -= 15
        warnings.append(f"Possible duplicate detected ({duplicates} similar product(s)).")

    if not (product.get("filename") or "").strip():
        score -= 10
        warnings.append("Missing filename.")

    score = max(0, min(100, score))
    passed = score >= PASSING_REVIEW_SCORE
    return {
        "score": score,
        "warnings": warnings,
        "passed": passed,
        "recommendation": "pass" if passed else "needs_improvement",
    }


def suggest_improvements(product: dict[str, str]) -> list[str]:
    """Return human-readable improvements from review warnings."""
    review = calculate_review_score(product)
    suggestions = list(review["warnings"])  # type: ignore[arg-type]
    if _quality_score(product) < 2:
        suggestions.append("Improve or regenerate design; quality score is low.")
    if not suggestions:
        suggestions.append("Product looks ready for lifecycle review.")
    return suggestions


def review_product(product_id: str | int) -> dict[str, object]:
    """Review one product by id without changing its status."""
    target = str(product_id)
    for product in read_products():
        if product.get("id") == target:
            return calculate_review_score(product)
    raise ValueError(f"Product id not found: {product_id}")
