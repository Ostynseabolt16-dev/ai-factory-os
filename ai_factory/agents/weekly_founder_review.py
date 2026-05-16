"""Concise weekly review for real Etsy execution."""

from __future__ import annotations

from ai_factory.analytics.profit_calculator import estimate_total_profit
from ai_factory.intelligence.winning_pattern_detector import detect_winning_patterns
from ai_factory.listings.etsy_metrics_importer import compare_listing_performance
from ai_factory.listings.listing_change_history import summarize_listing_changes
from ai_factory.maintenance.inventory_hygiene import generate_inventory_hygiene_report
from ai_factory.signals.early_win_detector import detect_high_view_low_conversion, detect_needs_better_thumbnail, detect_early_winners
from ai_factory.variants.emotional_variant_generator import suggest_cluster_variants


def generate_weekly_founder_review() -> dict[str, object]:
    """Return a weekly business review with the next manual actions."""
    performance = compare_listing_performance()
    patterns = detect_winning_patterns()
    hygiene = generate_inventory_hygiene_report()
    profit = estimate_total_profit()
    best = performance.get("best_listing")
    hook = (patterns.get("top_emotional_hook") or {}).get("value") or "Social Anxiety"
    winners = detect_early_winners()[:5]
    weak = detect_high_view_low_conversion()[:5]
    thumbnail_fixes = detect_needs_better_thumbnail()[:5]

    actions = []
    if thumbnail_fixes:
        actions.append("Improve the primary thumbnail for the highest-view listing with no engagement.")
    if weak:
        actions.append("Fix SEO, offer, price, or mockup order for high-view low-conversion listings.")
    if winners:
        actions.append("Create 1-3 nearby emotional variants for the strongest engaged listing.")
    if not actions:
        actions.append("Collect more Etsy metrics before changing more than one variable.")

    return {
        "winners": winners,
        "weak_listings": weak,
        "best_thumbnail_style": patterns.get("top_thumbnail_style"),
        "best_tags_or_keywords": patterns.get("top_keyword_cluster"),
        "products_to_archive": hygiene.get("cleanup_candidates", [])[:5],
        "products_to_duplicate_or_improve": suggest_cluster_variants(str(hook), "promising") if best else None,
        "estimated_weekly_profit": profit,
        "listing_change_summary": summarize_listing_changes(),
        "next_3_manual_actions": actions[:3],
        "winning_patterns": patterns,
    }
