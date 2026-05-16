"""Local thumbnail performance heuristics.

Thumbnail styles are inferred from listing notes. Suggested note keywords:
close-up, far, white background, desk scene, large stickers, small stickers,
bright, muted.
"""

from __future__ import annotations

from collections import defaultdict

from ai_factory.listings.listing_tracker import read_listings
from ai_factory.signals.market_signal_ingestor import calculate_market_signal

STYLE_KEYWORDS = {
    "close_up": ["close-up", "closeup", "zoom", "large stickers"],
    "far_mockup": ["far", "zoomed out", "small stickers"],
    "white_background": ["white background", "plain", "flat"],
    "desk_scene": ["desk", "planner", "laptop", "lifestyle"],
    "bright": ["bright", "colorful", "high contrast"],
    "muted": ["muted", "pastel", "soft"],
}


def _styles_from_notes(notes: str) -> list[str]:
    lowered = (notes or "").lower()
    styles = [style for style, terms in STYLE_KEYWORDS.items() if any(term in lowered for term in terms)]
    return styles or ["unspecified"]


def _styles_from_listing(listing: dict[str, str]) -> list[str]:
    fields = " ".join(
        [
            listing.get("primary_thumbnail_style", ""),
            listing.get("thumbnail_test_notes", ""),
            listing.get("clickthrough_observations", ""),
            listing.get("notes", ""),
        ]
    )
    return _styles_from_notes(fields)


def analyze_thumbnail_performance() -> dict[str, object]:
    """Compare thumbnail styles using manually entered listing metrics."""
    style_scores: dict[str, list[float]] = defaultdict(list)
    listing_results = []
    for listing in read_listings():
        signal = calculate_market_signal(listing)
        styles = _styles_from_listing(listing)
        for style in styles:
            style_scores[style].append(float(signal["market_signal_score"]))
        listing_results.append({**signal, "thumbnail_styles": styles})

    summaries = [
        {
            "style": style,
            "average_signal": round(sum(scores) / len(scores), 3),
            "sample_count": len(scores),
        }
        for style, scores in style_scores.items()
    ]
    ranked = sorted(summaries, key=lambda item: float(item["average_signal"]), reverse=True)
    strongest = ranked[0] if ranked else None
    weakest = ranked[-1] if ranked else None
    suggestion = "Add thumbnail style notes to listings, then compare after views/favorites arrive."
    if weakest and weakest["style"] in {"far_mockup", "unspecified"}:
        suggestion = "Test a closer thumbnail with larger sticker visibility."
    elif strongest:
        suggestion = f"Create the next thumbnail test using the current strongest style: {strongest['style']}."

    return {
        "strongest_thumbnail_style": strongest,
        "weakest_thumbnail_style": weakest,
        "suggested_next_thumbnail_experiment": suggestion,
        "listing_results": listing_results,
    }
