"""Real market validation scoring."""

from __future__ import annotations

from ai_factory.analytics.revenue_tracker import generate_revenue_report
from ai_factory.listings.listing_tracker import read_listings
from ai_factory.signals.market_signal_ingestor import calculate_market_signal, generate_market_signal_report


def _level(score: float) -> str:
    if score >= 80:
        return "scaling_candidate"
    if score >= 55:
        return "validated"
    if score >= 30:
        return "promising"
    if score > 0:
        return "weak"
    return "unvalidated"


def calculate_validation_score(product_id: str | int) -> dict[str, object]:
    """Score product using real marketplace metrics only."""
    target = str(product_id)
    listings = [listing for listing in read_listings() if listing.get("product_id") == target]
    if not listings:
        return {"product_id": target, "validation_score": 0.0, "validation_level": "unvalidated", "reasoning": "No listing metrics yet."}
    score = sum(float(calculate_market_signal(listing)["market_signal_score"]) for listing in listings)
    repeat_bonus = max(0, sum(int(listing.get("orders") or 0) for listing in listings) - 1) * 10
    revenue = sum(float(listing.get("revenue") or 0) for listing in listings)
    score = min(100, score + repeat_bonus + revenue)
    return {"product_id": target, "validation_score": round(score, 3), "validation_level": _level(score), "reasoning": "Views/favorites/orders/revenue/listing age."}


def rank_validated_products() -> list[dict[str, object]]:
    product_ids = sorted({listing.get("product_id", "") for listing in read_listings() if listing.get("product_id")})
    return sorted((calculate_validation_score(product_id) for product_id in product_ids), key=lambda row: float(row["validation_score"]), reverse=True)


def generate_validation_report() -> dict[str, object]:
    rankings = rank_validated_products()
    return {
        "rankings": rankings,
        "market_signals": generate_market_signal_report(),
        "revenue": generate_revenue_report(),
    }

