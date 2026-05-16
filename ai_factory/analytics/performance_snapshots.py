"""Manual local performance snapshots."""

from __future__ import annotations

import csv
from pathlib import Path

from ai_factory.analytics.product_analytics import calculate_average_quality, estimate_total_revenue
from ai_factory.analytics.revenue_analytics import revenue_by_niche
from ai_factory.config import PROJECT_ROOT
from ai_factory.products.product_manager import read_products
from ai_factory.tasks.task_models import now_iso
from ai_factory.tasks.task_queue import get_completed_tasks, get_failed_tasks, get_pending_tasks

SNAPSHOTS_DIR = PROJECT_ROOT / "snapshots"


def _snapshot_dir() -> Path:
    base = SNAPSHOTS_DIR / now_iso().replace(":", "-")
    path = base
    counter = 2
    while path.exists():
        path = Path(f"{base}-{counter}")
        counter += 1
    path.mkdir(parents=True, exist_ok=False)
    return path


def create_performance_snapshot() -> Path:
    """Create inventory/revenue/task snapshot CSVs."""
    path = _snapshot_dir()
    products = read_products()

    with (path / "inventory_snapshot.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(
            [
                {"metric": "total_products", "value": len(products)},
                {"metric": "average_quality", "value": calculate_average_quality()},
            ]
        )

    with (path / "revenue_snapshot.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["niche", "revenue"])
        writer.writeheader()
        for niche, revenue in revenue_by_niche():
            writer.writerow({"niche": niche, "revenue": revenue})

    with (path / "task_snapshot.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(
            [
                {"metric": "pending_tasks", "value": len(get_pending_tasks())},
                {"metric": "completed_tasks", "value": len(get_completed_tasks())},
                {"metric": "failed_tasks", "value": len(get_failed_tasks())},
                {"metric": "estimated_revenue", "value": estimate_total_revenue()},
            ]
        )
    return path


def compare_snapshots() -> dict[str, object]:
    """Compare the two newest snapshot directories by file presence."""
    snapshots = sorted([path for path in SNAPSHOTS_DIR.iterdir() if path.is_dir()], reverse=True) if SNAPSHOTS_DIR.exists() else []
    if len(snapshots) < 2:
        return {"message": "Need at least two snapshots to compare.", "snapshot_count": len(snapshots)}
    newest, previous = snapshots[0], snapshots[1]
    return {
        "newest": newest.name,
        "previous": previous.name,
        "newest_files": sorted(path.name for path in newest.iterdir()),
        "previous_files": sorted(path.name for path in previous.iterdir()),
    }
