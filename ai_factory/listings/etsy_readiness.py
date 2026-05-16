"""Read-only Etsy manual upload readiness checks."""

from __future__ import annotations

from ai_factory.products.product_manager import read_products
from ai_factory.quality.duplicate_detector import generate_duplicate_report


def _product(product_id: str | int) -> dict[str, str]:
    target = str(product_id)
    for product in read_products():
        if product.get("id") == target:
            return product
    raise ValueError(f"Product id not found: {product_id}")


def evaluate_etsy_readiness(product_id: str | int) -> dict[str, object]:
    """Evaluate if a product is ready for manual Etsy upload."""
    product = _product(product_id)
    duplicate_ids = {item["product_id"] for item in generate_duplicate_report()} | {item["duplicate_id"] for item in generate_duplicate_report()}
    checks = {
        "title_exists": bool(product.get("title")),
        "tags_exist": bool(product.get("tags")),
        "description_exists": bool(product.get("description")),
        "mockups_exist": bool(product.get("mockup_paths")),
        "quality_threshold": float(product.get("quality_score") or 0) >= 2,
        "no_duplicate_risk": product["id"] not in duplicate_ids,
        "pipeline_stage_valid": product.get("pipeline_stage") in {"listing", "published", "mockups", "review"},
        "upload_ready_status": product.get("status") == "upload_ready",
    }
    warnings = [name for name, passed in checks.items() if not passed]
    return {"product_id": str(product_id), "ready": all(checks.values()), "checks": checks, "warnings": warnings}


def generate_readiness_report() -> dict[str, object]:
    """Return readiness results for all non-archived products."""
    results = [evaluate_etsy_readiness(product["id"]) for product in read_products() if product.get("status") != "archived"]
    return {
        "ready_count": len([row for row in results if row["ready"]]),
        "not_ready_count": len([row for row in results if not row["ready"]]),
        "results": results,
    }

