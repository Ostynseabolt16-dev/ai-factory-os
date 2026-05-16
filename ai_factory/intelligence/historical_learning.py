"""Historical learning from local AI Factory OS data.

This module uses only CSV-backed local state. It does not call OpenAI, scrape
websites, upload products, or schedule tasks.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

from ai_factory.analytics.profitability_engine import score_product_profitability
from ai_factory.config import PROJECT_ROOT
from ai_factory.products.product_manager import read_products
from ai_factory.production.batch_manager import _read_batches, summarize_batch
from ai_factory.quality.duplicate_detector import generate_duplicate_report
from ai_factory.tasks.task_history import most_common_failures, read_task_history
from ai_factory.tasks.task_models import now_iso
from ai_factory.workflows.workflow_engine import get_workflow_history

LEARNING_HISTORY_CSV = PROJECT_ROOT / "learning_history.csv"
LEARNING_COLUMNS = ["created_at", "learning_type", "entity", "score", "notes"]


def _ensure_learning_history() -> None:
    if not LEARNING_HISTORY_CSV.exists():
        with LEARNING_HISTORY_CSV.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=LEARNING_COLUMNS).writeheader()


def _append_learning(learning_type: str, entity: str, score: float, notes: str) -> None:
    _ensure_learning_history()
    with LEARNING_HISTORY_CSV.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LEARNING_COLUMNS)
        writer.writerow(
            {
                "created_at": now_iso(),
                "learning_type": learning_type,
                "entity": entity,
                "score": round(score, 3),
                "notes": notes,
            }
        )


def _float(value: str) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def _tags(product: dict[str, str]) -> list[str]:
    return [tag.strip().lower() for tag in (product.get("tags") or "").split("|") if tag.strip()]


def learn_from_products() -> dict[str, object]:
    """Learn niche/tag/product quality patterns from products.csv."""
    products = read_products()
    quality_by_niche: dict[str, list[float]] = defaultdict(list)
    profit_by_niche: dict[str, list[float]] = defaultdict(list)
    tag_quality: dict[str, list[float]] = defaultdict(list)
    low_quality_patterns: Counter[str] = Counter()

    for product in products:
        niche = (product.get("niche") or "unknown").strip().lower()
        quality = _float(product.get("quality_score", "0"))
        profitability = float(score_product_profitability(product)["profitability_score"])
        quality_by_niche[niche].append(quality)
        profit_by_niche[niche].append(profitability)
        if quality <= 0:
            low_quality_patterns[niche] += 1
        for tag in _tags(product):
            tag_quality[tag].append(quality)

    best_quality = sorted(
        ((niche, sum(scores) / len(scores)) for niche, scores in quality_by_niche.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    best_profit = sorted(
        ((niche, sum(scores) / len(scores)) for niche, scores in profit_by_niche.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    high_tags = sorted(
        ((tag, sum(scores) / len(scores)) for tag, scores in tag_quality.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    weak_tags = sorted(
        ((tag, sum(scores) / len(scores)) for tag, scores in tag_quality.items()),
        key=lambda item: item[1],
    )

    if best_quality:
        _append_learning("best_quality_niche", best_quality[0][0], best_quality[0][1], "Highest average quality niche.")
    if best_profit:
        _append_learning("best_profitability_niche", best_profit[0][0], best_profit[0][1], "Highest average profitability niche.")
    for niche, count in low_quality_patterns.most_common(3):
        _append_learning("low_quality_pattern", niche, count, "Repeated low-quality product pattern.")

    return {
        "best_quality_niches": best_quality[:5],
        "best_profitability_niches": best_profit[:5],
        "high_performing_tags": high_tags[:10],
        "weak_performing_tags": weak_tags[:10],
        "low_quality_patterns": low_quality_patterns.most_common(5),
    }


def learn_from_batches() -> dict[str, object]:
    """Learn batch-level quality/conversion estimates."""
    batch_scores = []
    for batch in _read_batches():
        summary = summarize_batch(batch["batch_id"])
        score = float(summary.get("average_quality", 0)) + float(summary.get("total_revenue", 0))
        batch_scores.append((batch["batch_id"], score, summary))
    batch_scores.sort(key=lambda item: item[1], reverse=True)
    if batch_scores:
        _append_learning("best_batch", batch_scores[0][0], batch_scores[0][1], "Highest current batch score.")
    return {"best_batches": batch_scores[:5], "weak_batches": batch_scores[-5:]}


def learn_from_workflows() -> dict[str, object]:
    """Learn workflow failure/completion patterns."""
    workflows = get_workflow_history()
    status_counts = Counter(row.get("status", "unknown") for row in workflows)
    type_counts = Counter(row.get("workflow_type", "unknown") for row in workflows)
    if status_counts:
        _append_learning("workflow_status_pattern", status_counts.most_common(1)[0][0], status_counts.most_common(1)[0][1], "Most common workflow status.")
    return {"workflow_status_counts": dict(status_counts), "workflow_type_counts": dict(type_counts)}


def learn_from_failures() -> dict[str, object]:
    """Learn from task failures and duplicate trends."""
    failures = most_common_failures()
    duplicates = generate_duplicate_report()
    history = read_task_history()
    failure_types = Counter(row.get("type", "unknown") for row in history if row.get("success") == "False")
    for error, count in failures[:3]:
        _append_learning("common_failure", error, count, "Repeated task failure.")
    if duplicates:
        _append_learning("duplicate_trend", "duplicate_products", len(duplicates), "Duplicate signals detected.")
    return {"common_failures": failures, "failure_task_types": failure_types.most_common(5), "duplicate_count": len(duplicates)}


def generate_learning_summary() -> dict[str, object]:
    """Run local learning passes and return a combined summary."""
    return {
        "products": learn_from_products(),
        "batches": learn_from_batches(),
        "workflows": learn_from_workflows(),
        "failures": learn_from_failures(),
    }

