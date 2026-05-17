"""CSV-backed product lifecycle manager for AI Factory OS.

This module is the source of truth for inventory state. It owns schema
migration, status validation, and common product queries.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

from ai_factory.config import PRODUCTS_CSV

ALLOWED_STATUSES = [
    "draft",
    "reviewed",
    "mockup_ready",
    "upload_ready",
    "uploaded",
    "listed",
    "sold",
    "archived",
]
ALLOWED_PIPELINE_STAGES = [
    "ideation",
    "generation",
    "review",
    "mockups",
    "listing",
    "published",
    "sales",
    "archived",
]
DEFAULT_STATUS = "draft"
DEFAULT_PLATFORM = "etsy"
MIN_UPLOAD_QUALITY_SCORE = 2

REQUIRED_COLUMNS = [
    "id",
    "batch_id",
    "niche",
    "filename",
    "status",
    "created_at",
    "quality_score",
    "trend_score",
    "saturation_score",
    "opportunity_score",
    "upload_priority",
    "title_quality_score",
    "tag_quality_score",
    "listing_completeness_score",
    "niche_confidence",
    "performance_rating",
    "platform",
    "title",
    "tags",
    "description",
    "estimated_category",
    "upload_date",
    "reviewed_at",
    "mockup_created_at",
    "listed_at",
    "sold_at",
    "last_updated_at",
    "pipeline_stage",
    "sales_count",
    "revenue",
    "actual_revenue",
    "actual_sales_count",
    "first_sale_date",
    "last_sale_date",
    "total_orders",
    "platform_fees_estimate",
    "estimated_profit",
    "notes",
]

VARIANT_COLUMNS = [
    "parent_product_id",
    "product_type",
]

# Keep older data instead of deleting it during migration.
LEGACY_COLUMNS = [
    "idea",
    "image_path",
    "mockup_paths",
]

CSV_COLUMNS = REQUIRED_COLUMNS + VARIANT_COLUMNS + LEGACY_COLUMNS


def _now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _normalize_status(status: str) -> str:
    status = (status or DEFAULT_STATUS).strip().lower()
    return status if status in ALLOWED_STATUSES else DEFAULT_STATUS


def _stage_for_status(status: str) -> str:
    return {
        "draft": "ideation",
        "reviewed": "review",
        "mockup_ready": "mockups",
        "upload_ready": "listing",
        "uploaded": "published",
        "listed": "published",
        "sold": "sales",
        "archived": "archived",
    }.get(status, "ideation")


def _normalize_stage(stage: str, status: str = DEFAULT_STATUS) -> str:
    stage = (stage or "").strip().lower()
    return stage if stage in ALLOWED_PIPELINE_STAGES else _stage_for_status(status)


def _clean_number(value: str | int | float, default: str = "0") -> str:
    raw = str(value).strip()
    return raw if raw else default


def _migrate_row(row: dict[str, str]) -> dict[str, str]:
    filename = (row.get("filename") or "").strip()
    image_path = (row.get("image_path") or "").strip()
    if not filename and image_path:
        filename = image_path

    migrated = {column: row.get(column, "") for column in CSV_COLUMNS}
    migrated["id"] = (row.get("id") or "").strip()
    migrated["batch_id"] = (row.get("batch_id") or "").strip()
    migrated["niche"] = (row.get("niche") or "").strip()
    migrated["filename"] = filename
    migrated["status"] = _normalize_status(row.get("status") or DEFAULT_STATUS)
    migrated["created_at"] = (row.get("created_at") or _now()).strip()
    migrated["quality_score"] = _clean_number(row.get("quality_score") or "0")
    migrated["trend_score"] = _clean_number(row.get("trend_score") or "0")
    migrated["saturation_score"] = _clean_number(row.get("saturation_score") or "0")
    migrated["opportunity_score"] = _clean_number(row.get("opportunity_score") or "0")
    migrated["upload_priority"] = row.get("upload_priority") or "low"
    migrated["title_quality_score"] = _clean_number(row.get("title_quality_score") or "0")
    migrated["tag_quality_score"] = _clean_number(row.get("tag_quality_score") or "0")
    migrated["listing_completeness_score"] = _clean_number(row.get("listing_completeness_score") or "0")
    migrated["niche_confidence"] = _clean_number(row.get("niche_confidence") or "0")
    migrated["performance_rating"] = row.get("performance_rating") or ""
    migrated["platform"] = (row.get("platform") or DEFAULT_PLATFORM).strip()
    migrated["title"] = row.get("title") or ""
    migrated["tags"] = row.get("tags") or ""
    migrated["description"] = row.get("description") or ""
    migrated["estimated_category"] = row.get("estimated_category") or ""
    migrated["upload_date"] = row.get("upload_date") or ""
    migrated["reviewed_at"] = row.get("reviewed_at") or ""
    migrated["mockup_created_at"] = row.get("mockup_created_at") or ""
    migrated["listed_at"] = row.get("listed_at") or ""
    migrated["sold_at"] = row.get("sold_at") or ""
    migrated["last_updated_at"] = row.get("last_updated_at") or migrated["created_at"]
    migrated["pipeline_stage"] = _normalize_stage(row.get("pipeline_stage") or "", migrated["status"])
    migrated["sales_count"] = _clean_number(row.get("sales_count") or "0")
    migrated["revenue"] = _clean_number(row.get("revenue") or "0")
    migrated["actual_revenue"] = _clean_number(row.get("actual_revenue") or migrated["revenue"])
    migrated["actual_sales_count"] = _clean_number(row.get("actual_sales_count") or migrated["sales_count"])
    migrated["first_sale_date"] = row.get("first_sale_date") or ""
    migrated["last_sale_date"] = row.get("last_sale_date") or migrated["sold_at"]
    migrated["total_orders"] = _clean_number(row.get("total_orders") or migrated["sales_count"])
    migrated["platform_fees_estimate"] = _clean_number(row.get("platform_fees_estimate") or "0")
    migrated["estimated_profit"] = _clean_number(row.get("estimated_profit") or "0")
    migrated["notes"] = row.get("notes") or ""
    migrated["parent_product_id"] = row.get("parent_product_id") or ""
    migrated["product_type"] = row.get("product_type") or "original"
    migrated["idea"] = row.get("idea") or ""
    migrated["image_path"] = image_path or filename
    migrated["mockup_paths"] = row.get("mockup_paths") or ""
    return migrated


def ensure_products_csv_schema(path: Path | None = None) -> None:
    """Create or safely migrate products.csv to the lifecycle schema."""
    path = path or PRODUCTS_CSV
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
        return

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        existing_columns = reader.fieldnames or []
        rows = list(reader)

    if existing_columns == CSV_COLUMNS and all(
        _normalize_status(row.get("status", "")) == (row.get("status") or DEFAULT_STATUS)
        for row in rows
    ):
        return

    migrated_rows = [_migrate_row(row) for row in rows]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(migrated_rows)


def read_products(path: Path | None = None) -> list[dict[str, str]]:
    """Read all product rows after ensuring schema exists."""
    path = path or PRODUCTS_CSV
    ensure_products_csv_schema(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_products(rows: list[dict[str, str]], path: Path | None = None) -> None:
    """Rewrite product rows with the lifecycle schema."""
    path = path or PRODUCTS_CSV
    ensure_products_csv_schema(path)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(_migrate_row(row))


def next_product_id(path: Path | None = None) -> int:
    """Return next numeric id."""
    rows = read_products(path)
    max_id = 0
    for row in rows:
        raw = (row.get("id") or "").strip()
        if raw.isdigit():
            max_id = max(max_id, int(raw))
    return max_id + 1


def create_product_record(
    *,
    batch_id: str | int = "",
    niche: str = "",
    filename: str = "",
    status: str = DEFAULT_STATUS,
    quality_score: int | str = 0,
    trend_score: int | str = 0,
    saturation_score: int | str = 0,
    opportunity_score: int | str = 0,
    upload_priority: str = "low",
    title_quality_score: int | str = 0,
    tag_quality_score: int | str = 0,
    listing_completeness_score: int | str = 0,
    niche_confidence: int | str = 0,
    platform: str = DEFAULT_PLATFORM,
    title: str = "",
    tags: str | list[str] = "",
    description: str = "",
    notes: str = "",
    pipeline_stage: str = "",
    parent_product_id: str | int = "",
    performance_rating: str = "",
    estimated_category: str = "",
    product_type: str = "original",
    idea: str = "",
    image_path: str = "",
    mockup_paths: str | list[str] = "",
    path: Path | None = None,
) -> int:
    """Append a new product lifecycle row and return its id."""
    path = path or PRODUCTS_CSV
    product_id = next_product_id(path)
    tags_value = "|".join(tags) if isinstance(tags, list) else tags
    mockups_value = "|".join(mockup_paths) if isinstance(mockup_paths, list) else mockup_paths
    filename = filename or image_path

    rows = read_products(path)
    rows.append(
        _migrate_row(
            {
                "id": str(product_id),
                "batch_id": str(batch_id),
                "niche": niche,
                "filename": filename,
                "status": status,
                "created_at": _now(),
                "quality_score": str(quality_score),
                "trend_score": str(trend_score),
                "saturation_score": str(saturation_score),
                "opportunity_score": str(opportunity_score),
                "upload_priority": upload_priority,
                "title_quality_score": str(title_quality_score),
                "tag_quality_score": str(tag_quality_score),
                "listing_completeness_score": str(listing_completeness_score),
                "niche_confidence": str(niche_confidence),
                "platform": platform,
                "title": title,
                "tags": tags_value,
                "description": description,
                "estimated_category": estimated_category,
                "performance_rating": performance_rating,
                "upload_date": "",
                "reviewed_at": "",
                "mockup_created_at": "",
                "listed_at": "",
                "sold_at": "",
                "last_updated_at": _now(),
                "pipeline_stage": pipeline_stage or _stage_for_status(status),
                "sales_count": "0",
                "revenue": "0",
                "actual_revenue": "0",
                "actual_sales_count": "0",
                "first_sale_date": "",
                "last_sale_date": "",
                "total_orders": "0",
                "platform_fees_estimate": "0",
                "estimated_profit": "0",
                "notes": notes,
                "parent_product_id": str(parent_product_id),
                "product_type": product_type if product_type in {"original", "variant"} else "original",
                "idea": idea,
                "image_path": image_path or filename,
                "mockup_paths": mockups_value,
            }
        )
    )
    write_products(rows, path)
    return product_id


def _find_product(rows: list[dict[str, str]], product_id: int | str) -> dict[str, str]:
    target = str(product_id)
    for row in rows:
        if (row.get("id") or "").strip() == target:
            return row
    raise ValueError(f"Product id not found: {product_id}")


def _int_value(value: str, default: int = 0) -> int:
    raw = (value or "").strip()
    return int(raw) if raw.isdigit() else default


def _float_value(value: str, default: float = 0.0) -> float:
    try:
        return float((value or "").strip() or default)
    except ValueError:
        return default


def is_upload_ready(product: dict[str, str], *, min_quality_score: int = MIN_UPLOAD_QUALITY_SCORE) -> bool:
    """Return whether a reviewed product has all listing fields needed for upload."""
    quality_score = _int_value(product.get("quality_score", "0"))
    return (
        product.get("status") == "reviewed"
        and quality_score >= min_quality_score
        and bool((product.get("title") or "").strip())
        and bool((product.get("tags") or "").strip())
        and bool((product.get("description") or "").strip())
    )


def update_product_status(product_id: int | str, status: str, path: Path | None = None) -> dict[str, str]:
    """Validate and update a product status."""
    status = status.strip().lower()
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status: {status}. Allowed: {', '.join(ALLOWED_STATUSES)}")

    rows = read_products(path)
    product = _find_product(rows, product_id)

    if status == "upload_ready" and not is_upload_ready(product):
        raise ValueError(
            "Product can become upload_ready only when status is reviewed, quality_score is high enough, "
            "and title/tags/description exist."
        )

    product["status"] = status
    product["pipeline_stage"] = _stage_for_status(status)
    product["last_updated_at"] = _now()
    if status == "reviewed" and not product.get("reviewed_at"):
        product["reviewed_at"] = product["last_updated_at"]
    if status == "mockup_ready" and not product.get("mockup_created_at"):
        product["mockup_created_at"] = product["last_updated_at"]
    if status == "listed" and not product.get("listed_at"):
        product["listed_at"] = product["last_updated_at"]
    write_products(rows, path)
    return product


def get_products_by_status(status: str, path: Path | None = None) -> list[dict[str, str]]:
    """Return products in a lifecycle status."""
    status = status.strip().lower()
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    return [row for row in read_products(path) if (row.get("status") or "").strip().lower() == status]


def update_product_fields(
    product_id: int | str,
    updates: dict[str, str | int | float | list[str]],
    path: Path | None = None,
) -> dict[str, str]:
    """Update arbitrary product fields and persist the result."""
    rows = read_products(path)
    product = _find_product(rows, product_id)
    for key, value in updates.items():
        if key not in CSV_COLUMNS:
            continue
        if isinstance(value, list):
            product[key] = "|".join(str(item).strip() for item in value if str(item).strip())
        else:
            product[key] = str(value).strip()
    product["last_updated_at"] = _now()
    write_products(rows, path)
    return product


def get_recent_products(limit: int = 10, path: Path | None = None) -> list[dict[str, str]]:
    """Return newest products by numeric id."""
    rows = read_products(path)
    return sorted(rows, key=lambda row: _int_value(row.get("id", "0")), reverse=True)[:limit]


def get_top_niches(path: Path | None = None, *, limit: int = 5) -> list[tuple[str, int]]:
    """Return top niches by product count."""
    counts = Counter(
        (row.get("niche") or "").strip().lower()
        for row in read_products(path)
        if (row.get("niche") or "").strip()
    )
    return counts.most_common(limit)


def mark_product_uploaded(product_id: int | str, path: Path | None = None) -> dict[str, str]:
    """Mark product uploaded locally. Does not call any upload API."""
    rows = read_products(path)
    product = _find_product(rows, product_id)
    product["status"] = "uploaded"
    product["pipeline_stage"] = _stage_for_status("uploaded")
    product["upload_date"] = _now()
    product["last_updated_at"] = product["upload_date"]
    write_products(rows, path)
    return product


def mark_product_sold(
    product_id: int | str,
    *,
    revenue_amount: float = 0.0,
    path: Path | None = None,
) -> dict[str, str]:
    """Mark product sold locally and increment sales/revenue."""
    rows = read_products(path)
    product = _find_product(rows, product_id)
    product["status"] = "sold"
    product["pipeline_stage"] = _stage_for_status("sold")
    product["sold_at"] = _now()
    product["last_updated_at"] = product["sold_at"]
    product["sales_count"] = str(_int_value(product.get("sales_count", "0")) + 1)
    product["revenue"] = f"{_float_value(product.get('revenue', '0')) + revenue_amount:.2f}"
    product["actual_sales_count"] = str(_int_value(product.get("actual_sales_count", "0")) + 1)
    product["actual_revenue"] = f"{_float_value(product.get('actual_revenue', '0')) + revenue_amount:.2f}"
    product["total_orders"] = str(_int_value(product.get("total_orders", "0")) + 1)
    if not product.get("first_sale_date"):
        product["first_sale_date"] = product["sold_at"]
    product["last_sale_date"] = product["sold_at"]
    write_products(rows, path)
    return product
