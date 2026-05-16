"""Operational health scoring for AI Factory OS."""

from __future__ import annotations

import csv

from ai_factory.analytics.product_analytics import calculate_average_quality
from ai_factory.analytics.profitability_engine import top_profitable_products
from ai_factory.analytics.workflow_analytics import workflow_success_rate
from ai_factory.config import PROJECT_ROOT
from ai_factory.products.product_manager import read_products
from ai_factory.quality.duplicate_detector import generate_duplicate_report
from ai_factory.tasks.task_history import task_success_rate
from ai_factory.tasks.task_models import now_iso

SCORE_HISTORY_CSV = PROJECT_ROOT / "operational_score_history.csv"
SCORE_COLUMNS = ["created_at", "overall_score", "category_scores", "weaknesses", "strengths", "recommendations"]


def _ensure() -> None:
    if not SCORE_HISTORY_CSV.exists():
        with SCORE_HISTORY_CSV.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=SCORE_COLUMNS).writeheader()


def generate_operational_scorecard() -> dict[str, object]:
    products = read_products()
    total = len(products) or 1
    listings_ready = len([p for p in products if p.get("title") and p.get("tags") and p.get("description")])
    duplicates = len(generate_duplicate_report())
    avg_quality = calculate_average_quality()
    category_scores = {
        "workflow_efficiency": round(workflow_success_rate() * 100, 2),
        "inventory_quality": min(100, avg_quality * 20),
        "production_consistency": 60 if products else 0,
        "signal_strength": float(top_profitable_products(limit=1)[0]["profitability_score"]) if products else 0,
        "duplicate_ratio": max(0, 100 - duplicates / total * 100),
        "listing_readiness": round(listings_ready / total * 100, 2),
        "profitability_potential": min(100, float(top_profitable_products(limit=1)[0]["profitability_score"]) * 20) if products else 0,
        "task_reliability": round(task_success_rate() * 100, 2),
    }
    overall = round(sum(category_scores.values()) / len(category_scores), 2)
    weaknesses = [name for name, score in category_scores.items() if score < 50]
    strengths = [name for name, score in category_scores.items() if score >= 75]
    recommendations = ["Improve weak categories before scaling."] if weaknesses else ["System is healthy enough for small controlled batches."]

    result = {
        "overall_score": overall,
        "category_scores": category_scores,
        "weaknesses": weaknesses,
        "strengths": strengths,
        "recommendations": recommendations,
    }
    _ensure()
    with SCORE_HISTORY_CSV.open("a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=SCORE_COLUMNS).writerow(
            {
                "created_at": now_iso(),
                "overall_score": overall,
                "category_scores": str(category_scores),
                "weaknesses": "|".join(weaknesses),
                "strengths": "|".join(strengths),
                "recommendations": "|".join(recommendations),
            }
        )
    return result

