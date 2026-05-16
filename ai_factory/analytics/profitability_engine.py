"""Local profitability scoring heuristics."""

from __future__ import annotations

from ai_factory.analytics.revenue_analytics import revenue_by_batch
from ai_factory.products.product_manager import read_products
from ai_factory.production.batch_manager import summarize_batch


def _float(value: str) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def score_product_profitability(product: dict[str, str]) -> dict[str, float | str]:
    """Estimate product profitability from local fields only."""
    quality = _float(product.get("quality_score", "0"))
    sales = _float(product.get("sales_count", "0"))
    revenue = _float(product.get("revenue", "0"))
    has_listing = bool(product.get("title") and product.get("tags") and product.get("description"))
    has_mockups = bool(product.get("mockup_paths"))
    niche_score = 1.2 if product.get("niche") else 0.8
    quality_multiplier = 1 + min(quality, 5) * 0.15
    estimated_margin = revenue * 0.6 if revenue else 4.0
    estimated_conversion_rate = min(0.2, 0.02 + quality * 0.01 + (0.02 if has_listing else 0) + (0.02 if has_mockups else 0))
    estimated_monthly_sales = max(sales, quality * 0.4 + (1 if has_listing and has_mockups else 0))
    competition_penalty = 0.85 if "unknown" in (product.get("niche") or "unknown").lower() else 1.0
    profitability_score = round(
        estimated_margin * estimated_conversion_rate * estimated_monthly_sales * quality_multiplier * niche_score * competition_penalty,
        3,
    )
    return {
        "product_id": product.get("id", ""),
        "estimated_margin": round(estimated_margin, 2),
        "estimated_conversion_rate": round(estimated_conversion_rate, 4),
        "estimated_monthly_sales": round(estimated_monthly_sales, 2),
        "quality_multiplier": round(quality_multiplier, 2),
        "competition_penalty": round(competition_penalty, 2),
        "niche_score": round(niche_score, 2),
        "profitability_score": profitability_score,
    }


def score_batch_profitability(batch_id: str) -> dict[str, object]:
    """Estimate batch profitability by summing product scores."""
    products = [product for product in read_products() if product.get("batch_id") == batch_id]
    product_scores = [score_product_profitability(product) for product in products]
    summary = summarize_batch(batch_id)
    total_score = round(sum(float(item["profitability_score"]) for item in product_scores), 3)
    return {"batch_id": batch_id, "product_count": len(products), "profitability_score": total_score, "batch_summary": summary}


def top_profitable_products(limit: int = 10) -> list[dict[str, float | str]]:
    """Return highest estimated profitability products."""
    scored = [score_product_profitability(product) for product in read_products()]
    return sorted(scored, key=lambda item: float(item["profitability_score"]), reverse=True)[:limit]


def worst_products(limit: int = 10) -> list[dict[str, float | str]]:
    """Return lowest estimated profitability products."""
    scored = [score_product_profitability(product) for product in read_products()]
    return sorted(scored, key=lambda item: float(item["profitability_score"]))[:limit]
