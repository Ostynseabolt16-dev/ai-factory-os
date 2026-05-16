"""Local CSV health checks for AI Factory OS."""

from __future__ import annotations

import csv

from ai_factory.config import PRODUCTS_CSV, TASK_QUEUE_CSV
from ai_factory.products.product_manager import CSV_COLUMNS as PRODUCT_COLUMNS
from ai_factory.products.product_manager import ensure_products_csv_schema, read_products
from ai_factory.tasks.task_models import TASK_COLUMNS
from ai_factory.tasks.task_queue import _read_tasks


def _read_header(path) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        return next(reader, [])


def validate_products_csv() -> dict[str, object]:
    """Validate product CSV shape and rows."""
    ensure_products_csv_schema()
    rows = read_products()
    header = _read_header(PRODUCTS_CSV)
    missing = [column for column in PRODUCT_COLUMNS if column not in header]
    return {"path": str(PRODUCTS_CSV), "rows": len(rows), "missing_columns": missing, "ok": not missing}


def validate_task_queue_csv() -> dict[str, object]:
    """Validate task queue CSV shape and rows."""
    rows = _read_tasks()
    header = _read_header(TASK_QUEUE_CSV)
    missing = [column for column in TASK_COLUMNS if column not in header]
    return {"path": str(TASK_QUEUE_CSV), "rows": len(rows), "missing_columns": missing, "ok": not missing}


def repair_missing_columns() -> dict[str, object]:
    """Run schema repair/migration for local CSV files."""
    ensure_products_csv_schema()
    _read_tasks()
    return {"products": validate_products_csv(), "tasks": validate_task_queue_csv()}


def detect_duplicate_products() -> list[dict[str, str]]:
    """Detect products with duplicate filenames."""
    seen: dict[str, str] = {}
    duplicates: list[dict[str, str]] = []
    for row in read_products():
        filename = (row.get("filename") or "").strip().lower()
        if not filename:
            continue
        if filename in seen:
            duplicates.append({"filename": filename, "first_id": seen[filename], "duplicate_id": row.get("id", "")})
        else:
            seen[filename] = row.get("id", "")
    return duplicates


def summarize_csv_health() -> dict[str, object]:
    """Return a short health summary for local CSV storage."""
    product_health = validate_products_csv()
    task_health = validate_task_queue_csv()
    duplicates = detect_duplicate_products()
    return {
        "products_ok": product_health["ok"],
        "tasks_ok": task_health["ok"],
        "product_rows": product_health["rows"],
        "task_rows": task_health["rows"],
        "duplicate_products": len(duplicates),
        "duplicates": duplicates,
    }
