"""Revenue optimization recommendations from local state."""

from __future__ import annotations

from ai_factory.analytics.profitability_engine import score_product_profitability, top_profitable_products, worst_products
from ai_factory.analytics.workflow_analytics import workflow_success_rate
from ai_factory.intelligence.historical_learning import generate_learning_summary
from ai_factory.products.product_manager import read_products
from ai_factory.quality.duplicate_detector import generate_duplicate_report


def _recommend(action: str, entity: str, priority: str, reasoning: str) -> dict[str, object]:
    return {"action": action, "entity": entity, "priority": priority, "reasoning": reasoning}


def recommend_best_niches() -> list[dict[str, object]]:
    """Recommend niches to produce more of."""
    summary = generate_learning_summary()
    niches = summary["products"]["best_profitability_niches"]  # type: ignore[index]
    return [
        _recommend("Produce more products in this niche.", niche, "high" if score > 0 else "normal", f"Average profitability score: {round(score, 3)}")
        for niche, score in niches[:5]
    ]


def recommend_best_product_types() -> list[dict[str, object]]:
    """Recommend product types using local product_type profitability."""
    totals: dict[str, list[float]] = {}
    for product in read_products():
        product_type = product.get("product_type") or "original"
        totals.setdefault(product_type, []).append(float(score_product_profitability(product)["profitability_score"]))
    ranked = sorted(((key, sum(values) / len(values)) for key, values in totals.items()), key=lambda item: item[1], reverse=True)
    return [_recommend("Favor this product type.", product_type, "normal", f"Average profitability score: {round(score, 3)}") for product_type, score in ranked]


def recommend_batch_sizes() -> list[dict[str, object]]:
    """Recommend simple batch sizing based on workflow reliability."""
    success = workflow_success_rate()
    if success >= 0.8:
        size = "5-10"
        reasoning = "Workflow success is strong enough for moderate batches."
    elif success >= 0.5:
        size = "3-5"
        reasoning = "Workflow success is mixed; keep batches controlled."
    else:
        size = "1-3"
        reasoning = "Workflow success is low or unproven; keep experiments small."
    return [_recommend("Use this batch size range.", size, "normal", reasoning)]


def recommend_listing_improvements() -> list[dict[str, object]]:
    """Recommend products that need listing improvements."""
    recommendations = []
    for product in read_products():
        missing = [field for field in ["title", "tags", "description"] if not product.get(field)]
        if missing:
            recommendations.append(
                _recommend(
                    "Improve missing listing metadata.",
                    product.get("id", ""),
                    "normal",
                    f"Missing: {', '.join(missing)}",
                )
            )
    return recommendations[:10]


def recommend_products_to_archive() -> list[dict[str, object]]:
    """Recommend low-profit, duplicate-risk products to archive."""
    duplicate_ids = {item["product_id"] for item in generate_duplicate_report()}
    recommendations = []
    for item in worst_products(limit=10):
        product_id = str(item["product_id"])
        priority = "high" if product_id in duplicate_ids else "low"
        recommendations.append(
            _recommend(
                "Consider archiving or improving this product.",
                product_id,
                priority,
                f"Profitability score: {item['profitability_score']}; duplicate risk: {product_id in duplicate_ids}",
            )
        )
    return recommendations

