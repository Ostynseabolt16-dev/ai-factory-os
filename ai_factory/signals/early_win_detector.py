"""Detect early traction before sales scale."""

from __future__ import annotations

from ai_factory.listings.listing_tracker import read_listings
from ai_factory.signals.market_signal_ingestor import calculate_market_signal


def _level(signal: dict[str, object]) -> str:
    favorites = int(signal["favorites"])
    views = int(signal["views"])
    orders = int(signal["orders"])
    conversion = float(signal["conversion_rate"])
    per_day_views = views / max(1, int(signal["listing_age_days"]))

    if orders >= 2 or conversion >= 0.04 or favorites >= 20:
        return "breakout_watch"
    if orders >= 1 or favorites >= 8 or per_day_views >= 50:
        return "promising"
    if favorites >= 3 or per_day_views >= 15:
        return "emerging"
    return "weak traction"


def detect_early_winners() -> list[dict[str, object]]:
    """Return listings with early positive engagement signals."""
    winners = []
    for listing in read_listings():
        signal = calculate_market_signal(listing)
        level = _level(signal)
        if level != "weak traction":
            winners.append({**signal, "early_win_level": level})
    return sorted(winners, key=lambda row: float(row["market_signal_score"]), reverse=True)


def identify_fast_favorite_gainers() -> list[dict[str, object]]:
    """Find listings gaining favorites quickly relative to listing age."""
    results = []
    for listing in read_listings():
        signal = calculate_market_signal(listing)
        favorites_per_day = int(signal["favorites"]) / max(1, int(signal["listing_age_days"]))
        if favorites_per_day >= 1:
            results.append({**signal, "favorites_per_day": round(favorites_per_day, 3)})
    return sorted(results, key=lambda row: float(row["favorites_per_day"]), reverse=True)


def detect_high_view_low_conversion() -> list[dict[str, object]]:
    """Find listings getting attention but not converting."""
    results = []
    for listing in read_listings():
        signal = calculate_market_signal(listing)
        if int(signal["views"]) >= 50 and float(signal["conversion_rate"]) < 0.01:
            results.append({**signal, "issue": "high views but low conversion"})
    return sorted(results, key=lambda row: int(row["views"]), reverse=True)


def detect_strong_ctr_candidates() -> list[dict[str, object]]:
    """Approximate CTR candidates using favorites per view as an early proxy."""
    results = []
    for listing in read_listings():
        signal = calculate_market_signal(listing)
        views = max(1, int(signal["views"]))
        favorite_rate = int(signal["favorites"]) / views
        if views >= 20 and favorite_rate >= 0.08:
            results.append({**signal, "favorite_rate": round(favorite_rate, 4), "issue": "strong engagement proxy"})
    return sorted(results, key=lambda row: float(row["favorite_rate"]), reverse=True)


def detect_needs_better_thumbnail() -> list[dict[str, object]]:
    """Find listings where views exist but engagement is weak."""
    results = []
    for listing in read_listings():
        signal = calculate_market_signal(listing)
        views = int(signal["views"])
        favorites = int(signal["favorites"])
        orders = int(signal["orders"])
        if views >= 25 and favorites == 0 and orders == 0:
            results.append({**signal, "recommendation": "test closer, clearer primary thumbnail"})
    return sorted(results, key=lambda row: int(row["views"]), reverse=True)

