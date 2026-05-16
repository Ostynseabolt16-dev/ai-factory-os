"""Founder Decision Center.

Produces actionable business guidance from local state only. No task creation,
task execution, uploads, OpenAI calls, or paid APIs.
"""

from __future__ import annotations

from ai_factory.agents.founder_intelligence import (
    generate_growth_opportunities,
    generate_pipeline_bottlenecks,
    generate_quality_alerts,
    generate_risk_report,
)
from ai_factory.analytics.profitability_engine import top_profitable_products, worst_products
from ai_factory.signals.validation_score import rank_validated_products
from ai_factory.intelligence.revenue_optimizer import (
    recommend_batch_sizes,
    recommend_best_niches,
    recommend_listing_improvements,
    recommend_products_to_archive,
)


def _decision(priority: str, action: str, reasoning: str, suggested_task: str, expected_impact: str) -> dict[str, str]:
    return {
        "priority": priority,
        "action": action,
        "reasoning": reasoning,
        "suggested_task": suggested_task,
        "expected_impact": expected_impact,
    }


def generate_daily_execution_plan() -> list[dict[str, str]]:
    plan = [
        _decision("high", "Clear queued work with dry-run first.", "Dry-run preserves safety while improving throughput.", "run_next_task(dry_run=True)", "Better operational flow."),
        _decision("normal", "Review low-quality draft inventory.", "Drafts block the pipeline and hide weak products.", "review_product", "Cleaner inventory."),
    ]
    opportunities = generate_growth_opportunities()
    if opportunities:
        plan.append(
            _decision("normal", "Create variants from top product signals.", "Profitability scoring found expansion candidates.", "create_variant", "More shots on goal in proven directions.")
        )
    return plan


def generate_weekly_focus() -> list[dict[str, str]]:
    return [
        _decision("high", "Run one small batch in the best niche.", "Small batches limit risk while increasing learning speed.", "batch_generation", "More measurable experiments."),
        _decision("normal", "Create a state snapshot after each production session.", "Snapshots preserve operating history.", "create_state_snapshot", "Better trend visibility."),
    ]


def generate_scaling_readiness_report() -> dict[str, object]:
    risks = generate_risk_report()
    bottlenecks = generate_pipeline_bottlenecks()
    top_products = top_profitable_products(limit=3)
    ready = not risks and bool(top_products)
    return {
        "ready_to_scale": ready,
        "risks": risks,
        "bottlenecks": bottlenecks,
        "top_products": top_products,
        "recommendation": "Scale small batches only." if ready else "Do not scale yet; clean risks and validate product signals first.",
    }


def generate_inventory_cleanup_plan() -> list[dict[str, str]]:
    weak = worst_products(limit=5)
    archive_recs = recommend_products_to_archive()
    return [
        _decision(
            str(rec["priority"]),
            f"Inspect product {rec['entity']} for archive/improvement.",
            str(rec["reasoning"]),
            "archive_product",
            "Less clutter and fewer weak SKUs.",
        )
        for rec in archive_recs[:5]
    ] or [
        _decision("low", "No cleanup candidates found.", "Inventory does not show obvious archive candidates.", "analytics_refresh", "Maintain visibility.")
    ]


def generate_revenue_priority_actions() -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    validated = rank_validated_products()
    if validated:
        top = validated[0]
        actions.append(_decision("high", f"Push product {top['product_id']} if validation level is strong enough.", str(top["reasoning"]), "manual_upload_review", "Focus on real-world signal, not volume."))
    for rec in recommend_best_niches()[:3]:
        actions.append(_decision(str(rec["priority"]), str(rec["action"]), str(rec["reasoning"]), "batch_generation", "More products in stronger niches."))
    for rec in recommend_listing_improvements()[:3]:
        actions.append(_decision(str(rec["priority"]), str(rec["action"]), str(rec["reasoning"]), "generate_listing", "Improved upload readiness."))
    for rec in recommend_batch_sizes():
        actions.append(_decision(str(rec["priority"]), str(rec["action"]), str(rec["reasoning"]), "batch_generation", "Better throughput control."))
    return actions

