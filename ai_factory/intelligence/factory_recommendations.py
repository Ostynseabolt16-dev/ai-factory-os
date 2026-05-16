"""Local recommendation engine for Etsy listing improvements.

This module stays fully manual and local. It does not call external Etsy APIs
or perform automated uploads.
"""

from __future__ import annotations

import re
from typing import Iterable

from ai_factory.intelligence.listing_health import classify_listing_health, score_listing_health


def _int(value: str | int | float | None) -> int:
    try:
        return int(float(str(value or "").replace(",", "")))
    except (TypeError, ValueError):
        return 0


def _float(value: str | int | float | None) -> float:
    try:
        return float(str(value or "").replace("$", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return str(value).strip()


def _listing_label(listing: dict[str, str], product_title: str | None = None) -> str:
    title = _normalize_text(product_title or listing.get("listing_url") or listing.get("marketplace_listing_id") or listing.get("listing_id"))
    return title or "unknown listing"


def _best_emotional_hook(candidates: Iterable[str]) -> str:
    for candidate in candidates:
        words = [word for word in re.findall(r"[A-Za-z']+", candidate) if len(word) >= 5]
        if words:
            return words[0].title()
    return "Emotional connection"


def generate_factory_recommendations(
    listings: list[dict[str, str]],
    products: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    products = products or []
    product_map = {row.get("id", "") : row for row in products}
    if not listings:
        return {
            "top_listing_to_improve": "none yet",
            "listing_to_duplicate": "none yet",
            "listing_to_pause": "none yet",
            "best_emotional_hook": "collect more Etsy metrics",
            "strongest_thumbnail_style": "none yet",
            "next_recommended_variant": "none yet",
        }

    health_rows = []
    for listing in listings:
        health_rows.append(
            {
                "listing": listing,
                "score": score_listing_health(listing),
                "classification": classify_listing_health(listing),
                "title": _normalize_text(product_map.get(listing.get("product_id", ""), {}).get("title") or listing.get("marketplace_listing_id") or listing.get("listing_id")),
                "thumbnail_style": _normalize_text(listing.get("primary_thumbnail_style") or listing.get("thumbnail_test_notes")),
                "views": _int(listing.get("views")),
                "favorites": _int(listing.get("favorites")),
                "orders": _int(listing.get("orders")),
                "conversion": _float(listing.get("conversion_rate")),
            }
        )

    sorted_for_improve = sorted(
        [row for row in health_rows if row["classification"] in {"weak conversion", "thumbnail issue", "keyword issue"}],
        key=lambda row: (row["views"], row["favorites"], -row["score"]),
        reverse=True,
    )
    top_to_improve = sorted_for_improve[0] if sorted_for_improve else max(health_rows, key=lambda row: row["score"])

    duplicate_candidates = sorted(
        [row for row in health_rows if row["score"] >= 65 and row["orders"] >= 2],
        key=lambda row: (row["favorites"], row["conversion"], row["views"]),
        reverse=True,
    )
    listing_to_duplicate = duplicate_candidates[0] if duplicate_candidates else max(health_rows, key=lambda row: row["score"])

    pause_candidates = sorted(
        [row for row in health_rows if row["classification"] in {"dead listing", "weak conversion"} or row["score"] < 30],
        key=lambda row: (row["score"], row["views"]),
    )
    listing_to_pause = pause_candidates[0] if pause_candidates else min(health_rows, key=lambda row: row["score"])

    hook_titles = [row["title"] for row in health_rows if row["favorites"] >= 3 and row["views"] >= 20]
    hook = _best_emotional_hook(hook_titles) if hook_titles else "Real Etsy emotions"

    style_counts: dict[str, int] = {}
    for row in health_rows:
        style = row["thumbnail_style"].lower()
        if style:
            style_counts[style] = style_counts.get(style, 0) + 1
    strongest_thumbnail_style = max(style_counts.items(), key=lambda item: item[1])[0] if style_counts else "not tracked yet"

    variant_candidates = sorted(
        [row for row in health_rows if row["score"] >= 60 and row["orders"] >= 1],
        key=lambda row: (row["favorites"], row["conversion"], row["views"]),
        reverse=True,
    )
    next_variant = variant_candidates[0]["title"] if variant_candidates else listing_to_duplicate["title"]

    return {
        "top_listing_to_improve": _listing_label(top_to_improve["listing"], top_to_improve["title"]),
        "listing_to_duplicate": _listing_label(listing_to_duplicate["listing"], listing_to_duplicate["title"]),
        "listing_to_pause": _listing_label(listing_to_pause["listing"], listing_to_pause["title"]),
        "best_emotional_hook": hook,
        "strongest_thumbnail_style": strongest_thumbnail_style,
        "next_recommended_variant": next_variant,
    }
