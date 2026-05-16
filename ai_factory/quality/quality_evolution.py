"""Quality trend tracking over time."""

from __future__ import annotations

import csv
from collections import defaultdict

from ai_factory.config import PROJECT_ROOT
from ai_factory.products.product_manager import read_products
from ai_factory.production.batch_manager import _read_batches, summarize_batch
from ai_factory.tasks.task_models import now_iso

QUALITY_HISTORY_CSV = PROJECT_ROOT / "quality_history.csv"
QUALITY_COLUMNS = ["created_at", "metric", "entity", "value", "notes"]


def _ensure_history() -> None:
    if not QUALITY_HISTORY_CSV.exists():
        with QUALITY_HISTORY_CSV.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=QUALITY_COLUMNS).writeheader()


def _float(value: str) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def _append(metric: str, entity: str, value: float, notes: str = "") -> None:
    _ensure_history()
    with QUALITY_HISTORY_CSV.open("a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=QUALITY_COLUMNS).writerow(
            {"created_at": now_iso(), "metric": metric, "entity": entity, "value": round(value, 3), "notes": notes}
        )


def _read_history() -> list[dict[str, str]]:
    _ensure_history()
    with QUALITY_HISTORY_CSV.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def track_quality_snapshot() -> dict[str, object]:
    """Append current quality metrics to quality_history.csv."""
    by_niche: dict[str, list[float]] = defaultdict(list)
    by_type: dict[str, list[float]] = defaultdict(list)
    for product in read_products():
        quality = _float(product.get("quality_score", "0"))
        by_niche[product.get("niche") or "unknown"].append(quality)
        by_type[product.get("product_type") or "original"].append(quality)

    niche_averages = {key: sum(values) / len(values) for key, values in by_niche.items() if values}
    type_averages = {key: sum(values) / len(values) for key, values in by_type.items() if values}
    for key, value in niche_averages.items():
        _append("average_quality_by_niche", key, value)
    for key, value in type_averages.items():
        _append("average_quality_by_product_type", key, value)

    low_batches = []
    best_batches = []
    for batch in _read_batches():
        summary = summarize_batch(batch["batch_id"])
        quality = float(summary.get("average_quality", 0))
        if quality <= 1:
            low_batches.append(batch["batch_id"])
            _append("low_performing_batch", batch["batch_id"], quality)
        if quality >= 3:
            best_batches.append(batch["batch_id"])
            _append("best_performing_batch", batch["batch_id"], quality)

    return {"niche_averages": niche_averages, "product_type_averages": type_averages, "low_batches": low_batches, "best_batches": best_batches}


def detect_quality_regression() -> dict[str, object]:
    """Detect simple regression from last two quality entries."""
    rows = [row for row in _read_history() if row.get("metric") == "average_quality_by_niche"]
    if len(rows) < 2:
        return {"regression": False, "reason": "not enough history"}
    previous = _float(rows[-2]["value"])
    current = _float(rows[-1]["value"])
    return {"regression": current < previous, "previous": previous, "current": current}


def detect_quality_improvement() -> dict[str, object]:
    rows = [row for row in _read_history() if row.get("metric") == "average_quality_by_niche"]
    if len(rows) < 2:
        return {"improvement": False, "reason": "not enough history"}
    previous = _float(rows[-2]["value"])
    current = _float(rows[-1]["value"])
    return {"improvement": current > previous, "previous": previous, "current": current}


def generate_quality_summary() -> dict[str, object]:
    snapshot = track_quality_snapshot()
    return {
        "snapshot": snapshot,
        "regression": detect_quality_regression(),
        "improvement": detect_quality_improvement(),
    }

