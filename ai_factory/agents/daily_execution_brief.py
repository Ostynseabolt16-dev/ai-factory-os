"""Daily execution brief for real Etsy validation.

Read-only guidance for what to improve next. No tasks are created here.
"""

from __future__ import annotations

from ai_factory.listings.etsy_seo_optimizer import score_seo_strength
from ai_factory.listings.listing_tracker import read_listings
from ai_factory.products.product_manager import read_products
from ai_factory.signals.early_win_detector import (
    detect_high_view_low_conversion,
    detect_needs_better_thumbnail,
    detect_early_winners,
    identify_fast_favorite_gainers,
)
from ai_factory.signals.market_signal_ingestor import calculate_market_signal
from ai_factory.variants.emotional_variant_generator import generate_emotional_variants


def _product_map() -> dict[str, dict[str, str]]:
    return {product.get("id", ""): product for product in read_products()}


def generate_daily_execution_brief() -> dict[str, object]:
    """Return today's highest-leverage listing improvement plan."""
    products = _product_map()
    listings = read_listings()
    signals = [calculate_market_signal(listing) for listing in listings]
    ranked = sorted(signals, key=lambda item: float(item["market_signal_score"]), reverse=True)
    seo_fixes = []
    for product in products.values():
        seo = score_seo_strength(product)
        if not seo["passed"]:
            seo_fixes.append({"product_id": product.get("id"), "seo": seo})

    top_signal = ranked[0] if ranked else None
    top_product = products.get(str(top_signal["product_id"])) if top_signal else None
    base_concept = (top_product or {}).get("niche") or "Social Anxiety"

    return {
        "todays_top_product_to_improve": top_signal,
        "listings_needing_thumbnail_changes": detect_needs_better_thumbnail()[:5],
        "listings_needing_seo_fixes": seo_fixes[:5],
        "listings_gaining_traction": detect_early_winners()[:5],
        "fast_favorite_gainers": identify_fast_favorite_gainers()[:5],
        "products_to_pause": detect_high_view_low_conversion()[:5],
        "next_experiment_recommendation": generate_emotional_variants(base_concept, limit=3),
    }
