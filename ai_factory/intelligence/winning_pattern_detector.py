"""Read-only detector for repeatable winning product patterns."""

from __future__ import annotations

from collections import Counter, defaultdict

from ai_factory.listings.listing_tracker import read_listings
from ai_factory.products.product_manager import read_products
from ai_factory.signals.market_signal_ingestor import calculate_market_signal
from ai_factory.signals.thumbnail_analyzer import _styles_from_listing


def _product_map() -> dict[str, dict[str, str]]:
    return {product.get("id", ""): product for product in read_products()}


def _keywords(product: dict[str, str]) -> list[str]:
    raw = "|".join([product.get("niche", ""), product.get("title", ""), product.get("tags", "")])
    return [word.strip(".,|-/& ").lower() for word in raw.replace("|", " ").split() if len(word.strip(".,|-/& ")) > 3]


def detect_winning_patterns() -> dict[str, object]:
    """Identify hooks, thumbnail styles, and keyword clusters with strongest signals."""
    products = _product_map()
    hook_scores: dict[str, list[float]] = defaultdict(list)
    style_scores: dict[str, list[float]] = defaultdict(list)
    keyword_scores: dict[str, list[float]] = defaultdict(list)
    mockup_order_scores: dict[str, list[float]] = defaultdict(list)
    conversion_patterns = []

    for listing in read_listings():
        signal = calculate_market_signal(listing)
        score = float(signal["market_signal_score"])
        product = products.get(listing.get("product_id", ""), {})
        hook = product.get("niche") or "unknown"
        hook_scores[hook].append(score)
        for style in _styles_from_listing(listing):
            style_scores[style].append(score)
        for keyword in Counter(_keywords(product)).keys():
            keyword_scores[keyword].append(score)
        mockup_order = listing.get("thumbnail_version") or "unknown"
        mockup_order_scores[mockup_order].append(score)
        if int(signal["views"]) >= 20:
            conversion_patterns.append(
                {
                    "listing_id": listing.get("listing_id"),
                    "product_id": listing.get("product_id"),
                    "conversion_rate": signal["conversion_rate"],
                    "favorites": signal["favorites"],
                    "views": signal["views"],
                    "thumbnail_style": listing.get("primary_thumbnail_style") or "unknown",
                    "emotional_hook": hook,
                }
            )

    def best(scores: dict[str, list[float]]) -> dict[str, object] | None:
        if not scores:
            return None
        ranked = sorted(
            (
                {"value": key, "average_signal": round(sum(values) / len(values), 3), "sample_count": len(values)}
                for key, values in scores.items()
            ),
            key=lambda item: float(item["average_signal"]),
            reverse=True,
        )
        return ranked[0]

    return {
        "top_emotional_hook": best(hook_scores),
        "top_thumbnail_style": best(style_scores),
        "top_keyword_cluster": best(keyword_scores),
        "top_mockup_order": best(mockup_order_scores),
        "strongest_conversion_pattern": sorted(
            conversion_patterns,
            key=lambda row: (float(row["conversion_rate"]), int(row["favorites"])),
            reverse=True,
        )[:5],
    }
