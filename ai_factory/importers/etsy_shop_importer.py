"""Manual Etsy shop listing importer for AI Factory OS.

This importer reads a user-provided Etsy listing CSV export and maps it into
local `listings.csv` and `products.csv` rows. It does not call Etsy APIs,
perform uploads, or run background tasks. It is manual, read-only from Etsy
exports, and safe for local CSV memory.
"""

from __future__ import annotations

import csv
import re
import uuid
from pathlib import Path

from ai_factory.products.product_manager import create_product_record, read_products
from ai_factory.tasks.task_models import now_iso
from ai_factory.etsy.marketplace_sync import (
    deduplicate_marketplace_rows,
    marketplace_listing_id_or_fallback,
)
from ai_factory.visuals.factory_map import build_factory_map
from ai_factory.listings.listing_tracker import (
    LISTING_COLUMNS,
    LISTINGS_CSV,
    LISTING_STATUSES,
    _ensure,
    read_listings,
)

ETSY_ID_KEYS = [
    "listing id",
    "listing_id",
    "listingid",
    "id",
    "etsy listing id",
    "marketplace listing id",
]
ETSY_TITLE_KEYS = [
    "title",
    "listing title",
    "name",
]
ETSY_STATE_KEYS = [
    "state",
    "status",
    "listing state",
    "availability",
]
ETSY_URL_KEYS = [
    "url",
    "listing url",
    "link",
    "listing_url",
]
ETSY_VIEWS_KEYS = [
    "views",
    "num views",
    "view count",
    "times viewed",
]
ETSY_FAVORITES_KEYS = [
    "favorites",
    "num favorers",
    "favorite count",
    "likes",
]
ETSY_ORDERS_KEYS = [
    "orders",
    "sales",
    "quantity sold",
    "num orders",
    "sold",
]
ETSY_REVENUE_KEYS = [
    "revenue",
    "revenue amount",
    "price",
    "price amount",
    "amount",
]
ETSY_TAGS_KEYS = [
    "tags",
    "tag 1",
    "tag1",
    "tag 2",
    "tag2",
    "materials",
]
ETSY_NICHE_KEYS = [
    "shop section",
    "section",
    "section name",
    "category",
    "subcategory",
]
ETSY_DESCRIPTION_KEYS = [
    "description",
    "item description",
    "details",
]
ETSY_THUMBNAIL_KEYS = [
    "thumbnail style",
    "primary_thumbnail_style",
    "thumbnail",
    "photo style",
]

STATUS_MAP: dict[str, str] = {
    "active": "active",
    "published": "active",
    "public": "active",
    "enabled": "active",
    "inactive": "uploaded",
    "draft": "uploaded",
    "sold out": "removed",
    "removed": "removed",
    "expired": "removed",
    "deleted": "removed",
    "paused": "paused",
}


def _lookup(row: dict[str, str], keys: list[str]) -> str:
    for key in keys:
        if key in row and row[key] is not None:
            value = str(row[key]).strip()
            if value:
                return value
    return ""


def _safe_int(value: str | int | float | None) -> int:
    try:
        return int(float(str(value or "").replace(",", "")))
    except (ValueError, TypeError):
        return 0


def _safe_float(value: str | int | float | None) -> float:
    try:
        return float(str(value or "").replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


def _normalize_tag_string(value: str) -> str:
    if not value:
        return ""
    normalized = [item.strip() for item in re.split(r"[,|;]+", value) if item.strip()]
    return "|".join(normalized)


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9-_]+", "-", text.strip().lower())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "etsy-product"


def _normalize_status(value: str) -> str:
    value = (value or "").strip().lower()
    return STATUS_MAP.get(value, "uploaded")


def _guess_niche(row: dict[str, str], title: str, tags: str) -> str:
    niche = _lookup(row, ETSY_NICHE_KEYS)
    if niche:
        return niche
    if tags:
        first_tag = tags.split("|")[0]
        return first_tag
    if title:
        return title.split(" ")[0]
    return "etsy"


def _normalize_export_row(raw: dict[str, str]) -> dict[str, str]:
    title = _lookup(raw, ETSY_TITLE_KEYS)
    marketplace_listing_id = _lookup(raw, ETSY_ID_KEYS)
    listing_url = _lookup(raw, ETSY_URL_KEYS)
    state = _lookup(raw, ETSY_STATE_KEYS)
    views = _safe_int(_lookup(raw, ETSY_VIEWS_KEYS))
    favorites = _safe_int(_lookup(raw, ETSY_FAVORITES_KEYS))
    orders = _safe_int(_lookup(raw, ETSY_ORDERS_KEYS))
    revenue = _safe_float(_lookup(raw, ETSY_REVENUE_KEYS))
    tags = _normalize_tag_string(_lookup(raw, ETSY_TAGS_KEYS))
    if not tags and "materials" in raw:
        tags = _normalize_tag_string(raw.get("materials", ""))
    description = _lookup(raw, ETSY_DESCRIPTION_KEYS)
    thumbnail_style = _lookup(raw, ETSY_THUMBNAIL_KEYS)
    status = _normalize_status(state)
    conversion_rate = round(orders / views, 4) if views else 0.0
    return {
        "title": title,
        "niche": _guess_niche(raw, title, tags),
        "marketplace_listing_id": marketplace_listing_id,
        "listing_url": listing_url,
        "listing_status": status,
        "views": str(views),
        "favorites": str(favorites),
        "orders": str(orders),
        "conversion_rate": str(conversion_rate),
        "revenue": f"{revenue:.2f}",
        "primary_thumbnail_style": thumbnail_style,
        "tags": tags,
        "description": description,
        "notes": "Imported from Etsy export",
    }


def _find_existing_product(title: str, products: list[dict[str, str]]) -> dict[str, str] | None:
    if not title:
        return None
    normalized_title = title.strip().lower()
    for row in products:
        if (row.get("platform") or "").strip().lower() == "etsy" and (row.get("title") or "").strip().lower() == normalized_title:
            return row
    return None


def _find_existing_listing(marketplace_listing_id: str, listings: list[dict[str, str]]) -> dict[str, str] | None:
    if not marketplace_listing_id:
        return None
    for row in listings:
        if (row.get("marketplace_listing_id") or "").strip() == marketplace_listing_id:
            return row
    return None


def _build_listing_row(product_id: str, normalized: dict[str, str]) -> dict[str, str]:
    return {
        "listing_id": str(uuid.uuid4()),
        "product_id": str(product_id),
        "platform": "etsy",
        "marketplace_listing_id": normalized["marketplace_listing_id"],
        "created_at": now_iso(),
        "listing_url": normalized["listing_url"],
        "listing_status": normalized["listing_status"],
        "views": normalized["views"],
        "favorites": normalized["favorites"],
        "orders": normalized["orders"],
        "conversion_rate": normalized["conversion_rate"],
        "revenue": normalized["revenue"],
        "last_checked_at": now_iso(),
        "primary_thumbnail_style": normalized["primary_thumbnail_style"],
        "thumbnail_version": "imported",
        "thumbnail_test_notes": "Imported from Etsy export",
        "clickthrough_observations": "",
        "notes": normalized["notes"],
    }


def _rewrite_listings(rows: list[dict[str, str]]) -> None:
    _ensure()
    with LISTINGS_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LISTING_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in LISTING_COLUMNS})


def _normalize_export_data(csv_path: Path) -> list[dict[str, str]]:
    raw_rows: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            normalized_row = {k.strip().lower(): (v or "").strip() for k, v in row.items()}
            raw_rows.append(normalized_row)
    return [_normalize_export_row(row) for row in raw_rows]


def import_existing_etsy_listings(csv_path: str | Path) -> dict[str, object]:
    csv_path = Path(csv_path)
    if not csv_path.exists() or not csv_path.is_file():
        raise FileNotFoundError(f"Etsy export CSV not found: {csv_path}")

    products = read_products()
    listings = read_listings()

    imported = 0
    updated = 0
    created_products = 0
    skipped = 0
    malformed_rows = 0
    deduplicated_rows = 0
    errors: list[str] = []

    normalized_rows = _normalize_export_data(csv_path)
    deduped_rows, deduplicated_rows = deduplicate_marketplace_rows(normalized_rows)

    for index, normalized in enumerate(deduped_rows, start=1):
        try:
            title = normalized["title"]
            marketplace_listing_id = normalized["marketplace_listing_id"]
            if not title:
                errors.append(f"Row {index}: missing required title")
                skipped += 1
                continue

            # duplicates already removed by dedup step above

            existing_listing = _find_existing_listing(marketplace_listing_id, listings)
            product = _find_existing_product(title, products)
            if existing_listing and existing_listing.get("product_id"):
                product_id = existing_listing["product_id"]
            elif product:
                product_id = product["id"]
            else:
                product_id = str(create_product_record(
                    niche=normalized["niche"],
                    filename=_slugify(title),
                    status="uploaded",
                    quality_score=0,
                    platform="etsy",
                    title=title,
                    tags=normalized["tags"],
                    description=normalized["description"],
                    notes="Imported from Etsy export",
                    idea=title,
                    image_path=_slugify(title) + ".png",
                ))
                products = read_products()
                created_products += 1

            if existing_listing:
                existing_listing["product_id"] = product_id
                existing_listing["listing_url"] = normalized["listing_url"]
                existing_listing["listing_status"] = normalized["listing_status"]
                existing_listing["views"] = normalized["views"]
                existing_listing["favorites"] = normalized["favorites"]
                existing_listing["orders"] = normalized["orders"]
                existing_listing["conversion_rate"] = normalized["conversion_rate"]
                existing_listing["revenue"] = normalized["revenue"]
                existing_listing["last_checked_at"] = now_iso()
                existing_listing["primary_thumbnail_style"] = normalized["primary_thumbnail_style"]
                existing_listing["thumbnail_test_notes"] = "Imported from Etsy export"
                existing_listing["notes"] = normalized["notes"]
                updated += 1
            else:
                listing_row = _build_listing_row(product_id, normalized)
                listing_row["listing_id"] = marketplace_listing_id_or_fallback(normalized, index)
                listings.append(listing_row)
                imported += 1

        except Exception as exc:
            malformed_rows += 1
            skipped += 1
            errors.append(f"Row {index}: {exc}")

    if imported or updated or created_products:
        _rewrite_listings(listings)
        build_factory_map()

    return {
        "source": str(csv_path),
        "new_listings": imported,
        "updated_listings": updated,
        "new_products": created_products,
        "deduplicated_rows": deduplicated_rows,
        "malformed_rows": malformed_rows,
        "skipped_rows": skipped,
        "errors": errors,
    }
