"""Local design weakness analysis and repair suggestions."""

from __future__ import annotations

from ai_factory.listings.etsy_readiness import evaluate_etsy_readiness
from ai_factory.products.listing_generator import score_listing_quality
from ai_factory.products.product_manager import read_products
from ai_factory.quality.duplicate_detector import generate_duplicate_report
from ai_factory.signals.product_signal_engine import calculate_product_signal


def _product(product_id: str | int) -> dict[str, str]:
    target = str(product_id)
    for product in read_products():
        if product.get("id") == target:
            return product
    raise ValueError(f"Product id not found: {product_id}")


def _duplicate_ids() -> set[str]:
    findings = generate_duplicate_report()
    return {item["product_id"] for item in findings} | {item["duplicate_id"] for item in findings}


def analyze_design_weaknesses(product_id: str | int) -> dict[str, object]:
    """Identify blockers preventing a product from becoming upload-ready."""
    product = _product(product_id)
    blockers: list[str] = []
    warnings: list[str] = []
    duplicate_risk = product.get("id") in _duplicate_ids()
    listing_quality = score_listing_quality(product)
    readiness = evaluate_etsy_readiness(product_id)
    signal = calculate_product_signal(product_id)

    if duplicate_risk:
        blockers.append("duplicate risk detected")
    if not product.get("mockup_paths"):
        blockers.append("missing mockups")
    if not product.get("title"):
        blockers.append("missing title")
    if not product.get("tags"):
        blockers.append("missing tags")
    if not product.get("description"):
        blockers.append("missing description")
    if float(product.get("quality_score") or 0) < 2:
        blockers.append("quality score below upload threshold")
    if product.get("status") not in {"reviewed", "mockup_ready", "upload_ready"}:
        warnings.append("product is not in a repair-friendly lifecycle state")
    if not listing_quality["passed"]:
        warnings.extend(str(item) for item in listing_quality["warnings"])
    if signal["signal_level"] == "weak":
        warnings.append("product has weak local signal score")

    return {
        "product_id": str(product_id),
        "upload_blockers": blockers,
        "warnings": warnings,
        "duplicate_risk": duplicate_risk,
        "listing_quality": listing_quality,
        "readiness": readiness,
        "signal": signal,
    }


def suggest_design_improvements(product_id: str | int) -> dict[str, object]:
    """Return practical manual repair steps for a weak product."""
    analysis = analyze_design_weaknesses(product_id)
    blockers = set(analysis["upload_blockers"])
    recommendations: list[str] = []

    if "missing title" in blockers or "missing tags" in blockers or "missing description" in blockers:
        recommendations.append("Regenerate local listing metadata and review title/tags manually.")
    if "missing mockups" in blockers:
        recommendations.append("Generate a fresh mockup set and keep the best 2-4 images.")
    if "duplicate risk detected" in blockers:
        recommendations.append("Differentiate the design angle, keywords, or archive the weaker duplicate.")
    if "quality score below upload threshold" in blockers:
        recommendations.append("Review the design before investing upload time.")
    if not recommendations:
        recommendations.append("Product is close to ready; run Etsy readiness check and export a listing package.")

    return {
        "product_id": str(product_id),
        "recommendations": recommendations,
        "upload_blockers": analysis["upload_blockers"],
        "readiness_recommendation": "repair before upload" if analysis["upload_blockers"] else "ready for final manual review",
    }
