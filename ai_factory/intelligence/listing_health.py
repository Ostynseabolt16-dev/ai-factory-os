"""Etsy listing health scoring and classification for AI Factory OS.

This module is local-only and uses manual metrics imported from Etsy exports.
No APIs, scraping, automation, or external calls are made.
"""

from __future__ import annotations

from datetime import datetime


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


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            continue
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def listing_age_days(listing: dict[str, str]) -> int | None:
    created_at = listing.get("created_at") or listing.get("last_checked_at")
    parsed = _parse_iso(created_at)
    if not parsed:
        return None
    delta = datetime.now() - parsed
    return max(0, int(delta.days))


def score_listing_health(listing: dict[str, str]) -> int:
    views = _int(listing.get("views"))
    favorites = _int(listing.get("favorites"))
    orders = _int(listing.get("orders"))
    conversion = _float(listing.get("conversion_rate"))
    age = listing_age_days(listing) or 0

    conversion_score = min(1.0, conversion / 0.08)
    view_score = min(1.0, views / 200)
    favorite_score = min(1.0, favorites / 20)
    age_score = 1.0 if age <= 14 else 0.85 if age <= 30 else 0.65 if age <= 60 else 0.45

    score = conversion_score * 40 + view_score * 20 + favorite_score * 20 + age_score * 20
    return min(100, max(0, int(round(score))))


def classify_listing_health(listing: dict[str, str]) -> str:
    views = _int(listing.get("views"))
    favorites = _int(listing.get("favorites"))
    orders = _int(listing.get("orders"))
    conversion = _float(listing.get("conversion_rate"))
    age = listing_age_days(listing) or 0

    if age >= 45 and orders == 0 and views < 30:
        return "dead listing"
    if views >= 50 and conversion < 0.02:
        return "weak conversion"
    if views >= 30 and favorites <= 2 and conversion < 0.03:
        return "thumbnail issue"
    if views < 20 and favorites <= 1 and orders == 0:
        return "keyword issue"
    if orders >= 3 and conversion >= 0.04 and favorites >= 4:
        return "strong traction"
    if views >= 40 and favorites >= 3 and orders == 0:
        return "keyword issue"
    return "stable"


def summarize_listing_health(listings: list[dict[str, str]]) -> dict[str, object]:
    rows = []
    counts: dict[str, int] = {
        "strong traction": 0,
        "weak conversion": 0,
        "thumbnail issue": 0,
        "keyword issue": 0,
        "dead listing": 0,
        "stable": 0,
    }
    for listing in listings:
        classification = classify_listing_health(listing)
        score = score_listing_health(listing)
        counts[classification] = counts.get(classification, 0) + 1
        rows.append({
            "listing_id": listing.get("listing_id", ""),
            "marketplace_listing_id": listing.get("marketplace_listing_id", ""),
            "platform": listing.get("platform", ""),
            "listing_status": listing.get("listing_status", ""),
            "views": _int(listing.get("views")),
            "favorites": _int(listing.get("favorites")),
            "orders": _int(listing.get("orders")),
            "conversion_rate": float(listing.get("conversion_rate") or 0.0),
            "revenue": _float(listing.get("revenue")),
            "age_days": listing_age_days(listing) or 0,
            "score": score,
            "classification": classification,
        })

    sorted_by_score = sorted(rows, key=lambda row: row["score"], reverse=True)
    sorted_by_weak = sorted(rows, key=lambda row: row["score"])

    return {
        "total_listings": len(listings),
        "average_score": round(sum(row["score"] for row in rows) / max(1, len(rows)), 1) if rows else 0,
        "counts": counts,
        "top_strongest": sorted_by_score[:3],
        "top_weakest": sorted_by_weak[:3],
        "health_rows": rows,
    }
