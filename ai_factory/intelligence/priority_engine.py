"""Priority scoring for products, batches, and workflows."""

from __future__ import annotations

from datetime import datetime

from ai_factory.analytics.profitability_engine import score_batch_profitability, score_product_profitability
from ai_factory.products.product_manager import read_products
from ai_factory.production.batch_manager import _read_batches
from ai_factory.signals.product_signal_engine import calculate_batch_signal, calculate_product_signal
from ai_factory.tasks.task_models import now_iso
from ai_factory.workflows.workflow_engine import get_workflow_history


def _level(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 55:
        return "high"
    if score >= 25:
        return "normal"
    return "low"


def _age_score(created_at: str) -> float:
    try:
        created = datetime.fromisoformat(created_at)
        now = datetime.fromisoformat(now_iso())
        return min(20, (now - created).days * 2)
    except ValueError:
        return 0


def calculate_product_priority(product: dict[str, str]) -> dict[str, object]:
    signal = float(calculate_product_signal(product["id"])["signal_score"])
    profit = float(score_product_profitability(product)["profitability_score"])
    incomplete = 15 if not (product.get("title") and product.get("tags") and product.get("description")) else 0
    stage_bonus = {"draft": 10, "reviewed": 20, "upload_ready": 30}.get(product.get("status"), 0)
    score = min(100, signal * 0.5 + profit * 5 + incomplete + stage_bonus + _age_score(product.get("created_at", "")))
    return {"entity_type": "product", "entity_id": product["id"], "priority_score": round(score, 3), "priority": _level(score)}


def calculate_batch_priority(batch: dict[str, str]) -> dict[str, object]:
    signal = float(calculate_batch_signal(batch["batch_id"])["signal_score"])
    profit = float(score_batch_profitability(batch["batch_id"])["profitability_score"])
    score = min(100, signal * 0.7 + profit * 2 + _age_score(batch.get("created_at", "")))
    return {"entity_type": "batch", "entity_id": batch["batch_id"], "priority_score": round(score, 3), "priority": _level(score)}


def calculate_workflow_priority(workflow: dict[str, str]) -> dict[str, object]:
    failed = int(workflow.get("failed_tasks") or 0)
    completed = int(workflow.get("completed_tasks") or 0)
    task_count = int(workflow.get("task_count") or 0)
    score = failed * 30 + (task_count - completed) * 10 + _age_score(workflow.get("created_at", ""))
    return {"entity_type": "workflow", "entity_id": workflow["workflow_id"], "priority_score": round(min(100, score), 3), "priority": _level(score)}


def generate_priority_queue() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    items.extend(calculate_product_priority(product) for product in read_products())
    items.extend(calculate_batch_priority(batch) for batch in _read_batches())
    items.extend(calculate_workflow_priority(workflow) for workflow in get_workflow_history())
    return sorted(items, key=lambda item: float(item["priority_score"]), reverse=True)

