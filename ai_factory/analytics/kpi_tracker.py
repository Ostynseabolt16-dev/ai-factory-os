"""Local KPI tracking for AI Factory OS."""

from __future__ import annotations

import csv
from collections import Counter

from ai_factory.analytics.product_analytics import calculate_average_quality, estimate_total_revenue
from ai_factory.analytics.workflow_analytics import workflow_success_rate
from ai_factory.config import PROJECT_ROOT
from ai_factory.products.product_manager import read_products
from ai_factory.quality.duplicate_detector import generate_duplicate_report
from ai_factory.tasks.task_models import now_iso

KPI_HISTORY_CSV = PROJECT_ROOT / "kpi_history.csv"
KPI_COLUMNS = ["created_at", "metric", "value", "notes"]


def _ensure_history() -> None:
    if not KPI_HISTORY_CSV.exists():
        with KPI_HISTORY_CSV.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=KPI_COLUMNS).writeheader()


def _append(metric: str, value: float | int | str, notes: str = "") -> None:
    _ensure_history()
    with KPI_HISTORY_CSV.open("a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=KPI_COLUMNS).writerow(
            {"created_at": now_iso(), "metric": metric, "value": value, "notes": notes}
        )


def track_kpis() -> dict[str, object]:
    """Append current KPI metrics and return them."""
    products = read_products()
    status_counts = Counter(product.get("status") or "draft" for product in products)
    stage_counts = Counter(product.get("pipeline_stage") or "unknown" for product in products)
    total = len(products) or 1
    duplicate_count = len(generate_duplicate_report())
    metrics = {
        "workflow_throughput": workflow_success_rate(),
        "products_reviewed": status_counts.get("reviewed", 0),
        "mockups_ready": status_counts.get("mockup_ready", 0),
        "listings_prepared": len([p for p in products if p.get("title") and p.get("tags") and p.get("description")]),
        "average_quality": calculate_average_quality(),
        "estimated_revenue": estimate_total_revenue(),
        "duplicate_count": duplicate_count,
        "archive_rate": round(status_counts.get("archived", 0) / total, 4),
        "batch_success_rate": workflow_success_rate(),
        "workflow_completion_rate": workflow_success_rate(),
        "stage_distribution": dict(stage_counts),
    }
    for key, value in metrics.items():
        _append(key, value if not isinstance(value, dict) else str(value))
    return metrics

