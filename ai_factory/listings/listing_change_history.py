"""Append-only listing change history.

Use this to track manual listing experiments so Etsy changes can be compared
against later views, favorites, and orders.
"""

from __future__ import annotations

import csv

from ai_factory.config import PROJECT_ROOT
from ai_factory.listings.listing_tracker import read_listings
from ai_factory.tasks.task_models import now_iso

LISTING_CHANGE_HISTORY_CSV = PROJECT_ROOT / "listing_change_history.csv"
CHANGE_COLUMNS = [
    "changed_at",
    "listing_id",
    "product_id",
    "title_before",
    "title_after",
    "tags_before",
    "tags_after",
    "thumbnail_before",
    "thumbnail_after",
    "reason_for_change",
]


def _ensure() -> None:
    if not LISTING_CHANGE_HISTORY_CSV.exists():
        with LISTING_CHANGE_HISTORY_CSV.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=CHANGE_COLUMNS).writeheader()


def record_listing_change(
    listing_id: str,
    *,
    title_before: str = "",
    title_after: str = "",
    tags_before: str = "",
    tags_after: str = "",
    thumbnail_before: str = "",
    thumbnail_after: str = "",
    reason_for_change: str = "",
) -> dict[str, str]:
    """Append one manual listing change experiment."""
    listing = next((row for row in read_listings() if row.get("listing_id") == listing_id), None)
    if not listing:
        raise ValueError(f"Listing id not found: {listing_id}")
    row = {
        "changed_at": now_iso(),
        "listing_id": listing_id,
        "product_id": listing.get("product_id", ""),
        "title_before": title_before,
        "title_after": title_after,
        "tags_before": tags_before,
        "tags_after": tags_after,
        "thumbnail_before": thumbnail_before,
        "thumbnail_after": thumbnail_after,
        "reason_for_change": reason_for_change,
    }
    _ensure()
    with LISTING_CHANGE_HISTORY_CSV.open("a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=CHANGE_COLUMNS).writerow(row)
    return row


def read_listing_change_history() -> list[dict[str, str]]:
    _ensure()
    with LISTING_CHANGE_HISTORY_CSV.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def summarize_listing_changes() -> dict[str, object]:
    rows = read_listing_change_history()
    return {
        "total_changes": len(rows),
        "recent_changes": rows[-10:],
        "thumbnail_changes": [row for row in rows if row.get("thumbnail_before") or row.get("thumbnail_after")][-10:],
        "seo_changes": [row for row in rows if row.get("title_before") or row.get("tags_before")][-10:],
    }
