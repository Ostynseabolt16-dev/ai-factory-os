"""Controlled production experiment tracking."""

from __future__ import annotations

import csv
import uuid

from ai_factory.config import PROJECT_ROOT
from ai_factory.signals.product_signal_engine import calculate_product_signal
from ai_factory.tasks.task_models import now_iso

EXPERIMENTS_CSV = PROJECT_ROOT / "experiments.csv"
EXPERIMENT_COLUMNS = ["experiment_id", "experiment_type", "created_at", "status", "control_group", "test_group", "winner", "notes"]
MAX_SMALL_TEST_BATCH_SIZE = 5


def _ensure() -> None:
    if not EXPERIMENTS_CSV.exists():
        with EXPERIMENTS_CSV.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=EXPERIMENT_COLUMNS).writeheader()


def _read() -> list[dict[str, str]]:
    _ensure()
    with EXPERIMENTS_CSV.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write(rows: list[dict[str, str]]) -> None:
    _ensure()
    with EXPERIMENTS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPERIMENT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def create_experiment(experiment_type: str, control_group: list[str], test_group: list[str], notes: str = "") -> str:
    """Create a local experiment record."""
    experiment_type = experiment_type.strip().lower()
    if experiment_type in {"limited_batch", "small_niche_test", "mockup_comparison", "pricing", "title_tag"}:
        if len(control_group) > MAX_SMALL_TEST_BATCH_SIZE or len(test_group) > MAX_SMALL_TEST_BATCH_SIZE:
            raise ValueError(f"Small validation experiments are limited to {MAX_SMALL_TEST_BATCH_SIZE} items per group.")
    experiment_id = str(uuid.uuid4())
    rows = _read()
    rows.append(
        {
            "experiment_id": experiment_id,
            "experiment_type": experiment_type,
            "created_at": now_iso(),
            "status": "open",
            "control_group": "|".join(control_group),
            "test_group": "|".join(test_group),
            "winner": "",
            "notes": notes,
        }
    )
    _write(rows)
    return experiment_id


def _group_score(group: str) -> float:
    ids = [item for item in group.split("|") if item.strip()]
    if not ids:
        return 0.0
    scores = []
    for product_id in ids:
        try:
            scores.append(float(calculate_product_signal(product_id)["signal_score"]))
        except ValueError:
            continue
    return round(sum(scores) / len(scores), 3) if scores else 0.0


def compare_experiment_results(experiment_id: str) -> dict[str, object]:
    """Compare control vs test groups with local signal scores."""
    for row in _read():
        if row["experiment_id"] == experiment_id:
            control = _group_score(row["control_group"])
            test = _group_score(row["test_group"])
            winner = "test_group" if test > control else "control_group" if control > test else "tie"
            return {"experiment_id": experiment_id, "control_score": control, "test_score": test, "winner": winner}
    raise ValueError(f"Experiment not found: {experiment_id}")


def close_experiment(experiment_id: str) -> dict[str, str]:
    """Close an experiment and store the winner."""
    comparison = compare_experiment_results(experiment_id)
    rows = _read()
    for row in rows:
        if row["experiment_id"] == experiment_id:
            row["status"] = "closed"
            row["winner"] = str(comparison["winner"])
            _write(rows)
            return row
    raise ValueError(f"Experiment not found: {experiment_id}")


def generate_experiment_summary() -> dict[str, object]:
    rows = _read()
    by_type: dict[str, int] = {}
    for row in rows:
        by_type[row["experiment_type"]] = by_type.get(row["experiment_type"], 0) + 1
    return {"total_experiments": len(rows), "open": len([r for r in rows if r["status"] == "open"]), "closed": len([r for r in rows if r["status"] == "closed"]), "by_type": by_type, "recent": rows[-5:]}

