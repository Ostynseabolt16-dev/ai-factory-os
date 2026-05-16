"""Read-only JSON operational snapshots."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from ai_factory.analytics.profitability_engine import top_profitable_products
from ai_factory.analytics.revenue_analytics import revenue_by_niche
from ai_factory.analytics.workflow_analytics import workflow_completion_distribution
from ai_factory.config import PROJECT_ROOT
from ai_factory.products.product_manager import read_products
from ai_factory.quality.duplicate_detector import generate_duplicate_report
from ai_factory.tasks.task_models import now_iso
from ai_factory.tasks.task_queue import get_completed_tasks, get_failed_tasks, get_pending_tasks, get_running_tasks

SNAPSHOT_HISTORY_DIR = PROJECT_ROOT / "snapshots" / "history"


def _safe_name() -> str:
    return now_iso().replace(":", "-")


def create_state_snapshot() -> Path:
    """Create a timestamped read-only JSON snapshot."""
    products = read_products()
    stage_distribution = Counter(product.get("pipeline_stage") or "unknown" for product in products)
    quality_scores = []
    for product in products:
        try:
            quality_scores.append(float(product.get("quality_score") or 0))
        except ValueError:
            pass

    payload = {
        "created_at": now_iso(),
        "task_counts": {
            "pending": len(get_pending_tasks()),
            "running": len(get_running_tasks()),
            "completed": len(get_completed_tasks()),
            "failed": len(get_failed_tasks()),
        },
        "workflow_counts": workflow_completion_distribution(),
        "product_stage_distribution": dict(stage_distribution),
        "profitability_summaries": top_profitable_products(limit=5),
        "top_niches": revenue_by_niche()[:5],
        "risk_indicators": {"duplicate_count": len(generate_duplicate_report())},
        "quality_average": round(sum(quality_scores) / len(quality_scores), 3) if quality_scores else 0,
        "revenue_estimates": revenue_by_niche(),
    }

    SNAPSHOT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOT_HISTORY_DIR / f"{_safe_name()}.json"
    counter = 2
    while path.exists():
        path = SNAPSHOT_HISTORY_DIR / f"{_safe_name()}-{counter}.json"
        counter += 1
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path

