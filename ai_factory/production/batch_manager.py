"""Production batch tracking for experiments.

A batch is one niche, one generation run, one measurable experiment cycle.
"""

from __future__ import annotations

import csv
import uuid
from pathlib import Path

from ai_factory.config import PROJECT_ROOT
from ai_factory.products.product_manager import read_products, write_products
from ai_factory.quality.duplicate_detector import generate_duplicate_report
from ai_factory.tasks.audit_log import audit_log
from ai_factory.tasks.task_models import now_iso

BATCHES_CSV = PROJECT_ROOT / "production_batches.csv"
BATCH_COLUMNS = [
    "batch_id",
    "niche",
    "created_at",
    "status",
    "product_count",
    "average_quality",
    "uploaded_count",
    "sold_count",
    "total_revenue",
    "notes",
]


def _ensure_batches() -> None:
    if not BATCHES_CSV.exists():
        with BATCHES_CSV.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=BATCH_COLUMNS).writeheader()


def _read_batches() -> list[dict[str, str]]:
    _ensure_batches()
    with BATCHES_CSV.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_batches(rows: list[dict[str, str]]) -> None:
    _ensure_batches()
    with BATCHES_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=BATCH_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in BATCH_COLUMNS})


def create_batch(niche: str, amount: int, notes: str = "") -> str:
    """Create a production batch record and return batch_id."""
    if not niche.strip():
        raise ValueError("Niche is required.")
    if amount <= 0:
        raise ValueError("Amount must be greater than 0.")

    batch_id = str(uuid.uuid4())
    rows = _read_batches()
    rows.append(
        {
            "batch_id": batch_id,
            "niche": niche.strip(),
            "created_at": now_iso(),
            "status": "active",
            "product_count": str(amount),
            "average_quality": "0",
            "uploaded_count": "0",
            "sold_count": "0",
            "total_revenue": "0",
            "notes": notes,
        }
    )
    _write_batches(rows)
    audit_log(f"Created production batch {batch_id} niche={niche} amount={amount}", event="batch")
    return batch_id


def add_product_to_batch(batch_id: str, product_id: str | int) -> None:
    """Attach an existing product row to a batch."""
    rows = read_products()
    target = str(product_id)
    for row in rows:
        if row.get("id") == target:
            row["batch_id"] = batch_id
            write_products(rows)
            audit_log(f"Added product {product_id} to batch {batch_id}", event="batch")
            return
    raise ValueError(f"Product id not found: {product_id}")


def get_batch_products(batch_id: str) -> list[dict[str, str]]:
    """Return products assigned to a batch."""
    return [row for row in read_products() if row.get("batch_id") == batch_id]


def summarize_batch(batch_id: str) -> dict[str, object]:
    """Compute current batch performance from product rows."""
    products = get_batch_products(batch_id)
    scores = []
    revenue = 0.0
    uploaded = 0
    sold = 0
    for product in products:
        try:
            scores.append(float(product.get("quality_score") or 0))
        except ValueError:
            pass
        try:
            revenue += float(product.get("revenue") or 0)
        except ValueError:
            pass
        if product.get("status") in {"uploaded", "listed", "sold"}:
            uploaded += 1
        try:
            sales_count = int(float(product.get("sales_count") or 0))
        except ValueError:
            sales_count = 0
        if product.get("status") == "sold" or sales_count > 0:
            sold += 1

    average = round(sum(scores) / len(scores), 2) if scores else 0.0
    summary = {
        "batch_id": batch_id,
        "product_count": len(products),
        "average_quality": average,
        "uploaded_count": uploaded,
        "sold_count": sold,
        "total_revenue": round(revenue, 2),
    }

    rows = _read_batches()
    for row in rows:
        if row.get("batch_id") == batch_id:
            row.update({key: str(value) for key, value in summary.items() if key != "batch_id"})
            break
    _write_batches(rows)
    return summary


def archive_batch(batch_id: str) -> dict[str, str]:
    """Archive a batch record; product statuses are not changed."""
    rows = _read_batches()
    for row in rows:
        if row.get("batch_id") == batch_id:
            row["status"] = "archived"
            _write_batches(rows)
            audit_log(f"Archived batch {batch_id}", event="batch")
            return row
    raise ValueError(f"Batch id not found: {batch_id}")


def generate_batch_report(batch_id: str) -> dict[str, object]:
    """Return batch score, profitability estimate, signal estimate, and risk metrics."""
    products = get_batch_products(batch_id)
    summary = summarize_batch(batch_id)
    quality_values = []
    for product in products:
        try:
            quality_values.append(float(product.get("quality_score") or 0))
        except ValueError:
            quality_values.append(0)
    distribution = {
        "low": len([q for q in quality_values if q < 1]),
        "medium": len([q for q in quality_values if 1 <= q < 3]),
        "high": len([q for q in quality_values if q >= 3]),
    }
    duplicate_ids = {item["product_id"] for item in generate_duplicate_report()} | {item["duplicate_id"] for item in generate_duplicate_report()}
    duplicate_count = len([product for product in products if product.get("id") in duplicate_ids])
    product_count = len(products) or 1
    signal = float(summary.get("average_quality", 0)) * 20 + float(summary.get("total_revenue", 0)) * 5 - duplicate_count * 10
    return {
        "batch_id": batch_id,
        "summary": summary,
        "batch_score": round(max(0, min(100, signal)), 3),
        "profitability_estimate": round(float(summary.get("total_revenue", 0)) + float(summary.get("average_quality", 0)) * product_count, 3),
        "signal_estimate": round(max(0, min(100, signal)), 3),
        "quality_distribution": distribution,
        "duplicate_density": round(duplicate_count / product_count, 3),
    }


def rank_batches() -> list[dict[str, object]]:
    """Rank batches by current batch report score."""
    return sorted((generate_batch_report(batch["batch_id"]) for batch in _read_batches()), key=lambda item: float(item["batch_score"]), reverse=True)
