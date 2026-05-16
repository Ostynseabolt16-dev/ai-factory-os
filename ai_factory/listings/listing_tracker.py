"""Manual marketplace listing tracker.

This module tracks listings that a human uploads manually. It never uploads,
scrapes, or calls marketplace APIs.
"""

from __future__ import annotations

import csv
import uuid

from ai_factory.config import PROJECT_ROOT
from ai_factory.tasks.task_models import now_iso

LISTINGS_CSV = PROJECT_ROOT / "listings.csv"
LISTING_STATUSES = ["draft", "uploaded", "active", "paused", "sold", "removed"]
LISTING_COLUMNS = [
    "listing_id",
    "product_id",
    "platform",
    "marketplace_listing_id",
    "created_at",
    "listing_url",
    "listing_status",
    "views",
    "favorites",
    "orders",
    "conversion_rate",
    "revenue",
    "last_checked_at",
    "primary_thumbnail_style",
    "thumbnail_version",
    "thumbnail_test_notes",
    "clickthrough_observations",
    "notes",
]


def _ensure() -> None:
    if not LISTINGS_CSV.exists():
        with LISTINGS_CSV.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=LISTING_COLUMNS).writeheader()
        return
    with LISTINGS_CSV.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        existing = f.seekable() and rows
    if not existing and LISTINGS_CSV.stat().st_size == 0:
        with LISTINGS_CSV.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=LISTING_COLUMNS).writeheader()
        return
    with LISTINGS_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames and all(column in reader.fieldnames for column in LISTING_COLUMNS):
            return
    with LISTINGS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LISTING_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in LISTING_COLUMNS})


def _read() -> list[dict[str, str]]:
    _ensure()
    with LISTINGS_CSV.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write(rows: list[dict[str, str]]) -> None:
    _ensure()
    with LISTINGS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LISTING_COLUMNS)
        writer.writeheader()
        writer.writerows({col: row.get(col, "") for col in LISTING_COLUMNS} for row in rows)


def _rate(orders: int, views: int) -> float:
    return round(orders / views, 4) if views else 0.0


def create_listing_record(
    product_id: str | int,
    *,
    platform: str = "etsy",
    marketplace_listing_id: str = "",
    listing_url: str = "",
    listing_status: str = "uploaded",
    notes: str = "",
) -> str:
    """Create a manual listing tracking row."""
    if listing_status not in LISTING_STATUSES:
        raise ValueError(f"Invalid listing status: {listing_status}")
    listing_id = str(uuid.uuid4())
    rows = _read()
    rows.append(
        {
            "listing_id": listing_id,
            "product_id": str(product_id),
            "platform": platform,
            "marketplace_listing_id": marketplace_listing_id,
            "created_at": now_iso(),
            "listing_url": listing_url,
            "listing_status": listing_status,
            "views": "0",
            "favorites": "0",
            "orders": "0",
            "conversion_rate": "0",
            "revenue": "0",
            "last_checked_at": "",
            "primary_thumbnail_style": "",
            "thumbnail_version": "v1",
            "thumbnail_test_notes": "",
            "clickthrough_observations": "",
            "notes": notes,
        }
    )
    _write(rows)
    return listing_id


def update_listing_metrics(
    listing_id: str,
    *,
    views: int | None = None,
    favorites: int | None = None,
    orders: int | None = None,
    revenue: float | None = None,
    notes: str | None = None,
) -> dict[str, str]:
    """Manually update marketplace metrics."""
    rows = _read()
    for row in rows:
        if row["listing_id"] == listing_id:
            if views is not None:
                row["views"] = str(max(0, views))
            if favorites is not None:
                row["favorites"] = str(max(0, favorites))
            if orders is not None:
                row["orders"] = str(max(0, orders))
            if revenue is not None:
                row["revenue"] = f"{max(0.0, revenue):.2f}"
            if notes is not None:
                row["notes"] = notes
            row["conversion_rate"] = str(_rate(int(row["orders"] or 0), int(row["views"] or 0)))
            row["last_checked_at"] = now_iso()
            _write(rows)
            return row
    raise ValueError(f"Listing id not found: {listing_id}")


def update_thumbnail_test(
    listing_id: str,
    *,
    primary_thumbnail_style: str = "",
    thumbnail_version: str = "",
    thumbnail_test_notes: str = "",
    clickthrough_observations: str = "",
) -> dict[str, str]:
    """Track manual thumbnail experiment observations for one listing."""
    rows = _read()
    for row in rows:
        if row["listing_id"] == listing_id:
            if primary_thumbnail_style:
                row["primary_thumbnail_style"] = primary_thumbnail_style
            if thumbnail_version:
                row["thumbnail_version"] = thumbnail_version
            if thumbnail_test_notes:
                row["thumbnail_test_notes"] = thumbnail_test_notes
            if clickthrough_observations:
                row["clickthrough_observations"] = clickthrough_observations
            row["last_checked_at"] = now_iso()
            _write(rows)
            return row
    raise ValueError(f"Listing id not found: {listing_id}")


def _set_status(listing_id: str, status: str) -> dict[str, str]:
    rows = _read()
    for row in rows:
        if row["listing_id"] == listing_id:
            row["listing_status"] = status
            row["last_checked_at"] = now_iso()
            _write(rows)
            return row
    raise ValueError(f"Listing id not found: {listing_id}")


def mark_listing_sold(listing_id: str, *, revenue: float = 0.0) -> dict[str, str]:
    row = update_listing_metrics(listing_id, orders=1, revenue=revenue)
    return _set_status(row["listing_id"], "sold")


def pause_listing(listing_id: str) -> dict[str, str]:
    return _set_status(listing_id, "paused")


def remove_listing(listing_id: str) -> dict[str, str]:
    return _set_status(listing_id, "removed")


def read_listings() -> list[dict[str, str]]:
    return _read()


def generate_listing_report() -> dict[str, object]:
    rows = _read()
    return {
        "total_listings": len(rows),
        "active": len([row for row in rows if row["listing_status"] == "active"]),
        "uploaded": len([row for row in rows if row["listing_status"] == "uploaded"]),
        "sold": len([row for row in rows if row["listing_status"] == "sold"]),
        "total_views": sum(int(row.get("views") or 0) for row in rows),
        "total_favorites": sum(int(row.get("favorites") or 0) for row in rows),
        "total_orders": sum(int(row.get("orders") or 0) for row in rows),
        "total_revenue": round(sum(float(row.get("revenue") or 0) for row in rows), 2),
        "recent": rows[-5:],
    }

