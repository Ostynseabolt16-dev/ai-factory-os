"""Higher-level Founder intelligence.

All functions are read-only and return structured recommendations. They do not
schedule tasks, execute tasks, upload products, or call paid APIs.
"""

from __future__ import annotations

from ai_factory.analytics.profitability_engine import top_profitable_products, worst_products
from ai_factory.analytics.workflow_analytics import bottleneck_stage_detection
from ai_factory.products.product_manager import read_products
from ai_factory.quality.duplicate_detector import generate_duplicate_report
from ai_factory.tasks.task_queue import get_failed_tasks, get_pending_tasks


def _recommend(action: str, task_type: str, payload: dict, priority: str, reasoning: str) -> dict[str, object]:
    return {
        "action_text": action,
        "suggested_task_type": task_type,
        "suggested_payload": payload,
        "suggested_priority": priority,
        "reasoning": reasoning,
    }


def generate_daily_focus() -> dict[str, object]:
    products = read_products()
    pending = get_pending_tasks()
    if pending:
        return {
            "focus": "Clear queued tasks with dry-run first.",
            "recommendations": [
                _recommend("Run next task in dry-run mode.", "analytics_refresh", {}, "low", "There is queued work waiting and dry-run keeps execution safe.")
            ],
        }
    drafts = [product for product in products if product.get("status") == "draft"]
    if drafts:
        return {
            "focus": "Review draft inventory.",
            "recommendations": [
                _recommend("Review oldest draft product.", "review_product", {"product_id": drafts[0]["id"]}, "normal", "Drafts cannot progress until reviewed.")
            ],
        }
    return {"focus": "Refresh analytics.", "recommendations": [_recommend("Refresh analytics.", "analytics_refresh", {}, "low", "System needs fresh operating metrics.")]}


def generate_growth_opportunities() -> list[dict[str, object]]:
    top = top_profitable_products(limit=3)
    opportunities: list[dict[str, object]] = []
    for item in top:
        product_id = str(item["product_id"])
        opportunities.append(
            _recommend(
                "Create a controlled variant of a high-potential product.",
                "create_variant",
                {"product_id": product_id, "variant_type": "style"},
                "normal",
                f"Product {product_id} has profitability score {item['profitability_score']}.",
            )
        )
    return opportunities


def generate_risk_report() -> list[dict[str, object]]:
    risks: list[dict[str, object]] = []
    duplicate_count = len(generate_duplicate_report())
    if duplicate_count:
        risks.append(
            _recommend(
                "Inspect duplicate products before generating more.",
                "analytics_refresh",
                {},
                "high",
                f"{duplicate_count} duplicate or near-duplicate signal(s) detected.",
            )
        )
    failed = get_failed_tasks()
    if failed:
        risks.append(
            _recommend(
                "Investigate failed task history.",
                "analytics_refresh",
                {},
                "high",
                f"{len(failed)} failed task(s) currently in queue.",
            )
        )
    weak = worst_products(limit=3)
    for item in weak:
        risks.append(
            _recommend(
                "Consider archiving a low-potential product.",
                "archive_product",
                {"product_id": item["product_id"]},
                "low",
                f"Profitability score is {item['profitability_score']}.",
            )
        )
    return risks


def generate_pipeline_bottlenecks() -> dict[str, object]:
    products = read_products()
    counts: dict[str, int] = {}
    for product in products:
        stage = product.get("pipeline_stage") or "unknown"
        counts[stage] = counts.get(stage, 0) + 1
    bottleneck = max(counts.items(), key=lambda item: item[1])[0] if counts else "none"
    return {"stage_counts": counts, "workflow_bottleneck": bottleneck_stage_detection(), "product_bottleneck": bottleneck}


def generate_quality_alerts() -> list[dict[str, object]]:
    alerts: list[dict[str, object]] = []
    for product in read_products():
        try:
            score = int(float(product.get("quality_score") or 0))
        except ValueError:
            score = 0
        if score == 0 and product.get("status") == "draft":
            alerts.append(
                _recommend(
                    "Archive or improve low-quality draft.",
                    "archive_product",
                    {"product_id": product["id"]},
                    "low",
                    "Quality score is zero and product is still draft.",
                )
            )
    return alerts
