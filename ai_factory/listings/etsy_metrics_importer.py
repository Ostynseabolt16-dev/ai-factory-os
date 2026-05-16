"""Manual Etsy metrics import helpers.

No scraping, Etsy API calls, browser automation, or background jobs. These
helpers only normalize metrics that a human copies from Etsy and update local
CSV records.
"""

from __future__ import annotations

from ai_factory.listings.listing_tracker import read_listings, update_listing_metrics
from ai_factory.signals.market_signal_ingestor import calculate_market_signal, update_product_signal_from_market


def _to_int(value: int | str | None) -> int:
    try:
        return max(0, int(str(value or "0").replace(",", "").strip()))
    except ValueError:
        return 0


def _to_float(value: float | str | None) -> float:
    try:
        return max(0.0, float(str(value or "0").replace("$", "").replace(",", "").strip()))
    except ValueError:
        return 0.0


def import_listing_metrics(
    listing_id: str,
    *,
    views: int | str | None = None,
    favorites: int | str | None = None,
    orders: int | str | None = None,
    revenue: float | str | None = None,
    notes: str | None = None,
) -> dict[str, object]:
    """Import one manually copied Etsy metrics row."""
    updated = update_listing_metrics(
        listing_id,
        views=_to_int(views) if views is not None else None,
        favorites=_to_int(favorites) if favorites is not None else None,
        orders=_to_int(orders) if orders is not None else None,
        revenue=_to_float(revenue) if revenue is not None else None,
        notes=notes,
    )
    product_signal = update_product_signal_from_market(updated["product_id"])
    market_signal = calculate_market_signal(updated)
    return {"listing": updated, "market_signal": market_signal, "product_signal": product_signal}


def bulk_update_metrics(metric_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Update several listings from manually entered metric dictionaries."""
    results = []
    for row in metric_rows:
        listing_id = str(row.get("listing_id") or "").strip()
        if not listing_id:
            results.append({"error": "missing listing_id", "row": row})
            continue
        results.append(
            import_listing_metrics(
                listing_id,
                views=row.get("views"),
                favorites=row.get("favorites"),
                orders=row.get("orders"),
                revenue=row.get("revenue"),
                notes=str(row.get("notes") or "") or None,
            )
        )
    return results


def compare_listing_performance() -> dict[str, object]:
    """Rank tracked listings by real market behavior."""
    signals = [calculate_market_signal(listing) for listing in read_listings()]
    ranked = sorted(signals, key=lambda item: float(item["market_signal_score"]), reverse=True)
    return {
        "best_listing": ranked[0] if ranked else None,
        "weakest_listing": ranked[-1] if ranked else None,
        "ranked_listings": ranked,
    }
