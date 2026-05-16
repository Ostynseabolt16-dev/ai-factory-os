"""Workflow helpers for repairing weak products.

These functions only schedule tasks. They do not execute work, upload products,
or call paid APIs.
"""

from __future__ import annotations

from ai_factory.review.design_improvement import analyze_design_weaknesses
from ai_factory.workflows.workflow_engine import create_workflow


def create_product_repair_workflow(product_id: str | int, *, dry_run: bool = False) -> dict[str, object]:
    """Schedule a small repair sequence for one product."""
    product_id = str(product_id)
    analysis = analyze_design_weaknesses(product_id)
    blockers = set(analysis["upload_blockers"])
    specs: list[dict[str, object]] = []

    if {"missing title", "missing tags", "missing description"} & blockers:
        specs.append({"type": "generate_listing", "priority": "high", "payload": {"product_id": product_id}})
    if "missing mockups" in blockers:
        specs.append({"type": "generate_mockups", "priority": "high", "payload": {"product_id": product_id}})
    specs.append({"type": "review_product", "priority": "normal", "payload": {"product_id": product_id}})
    specs.append({"type": "analytics_refresh", "priority": "low", "payload": {"product_id": product_id}})

    return create_workflow(
        "product_repair",
        specs,
        dry_run=dry_run,
        notes=f"product_id={product_id}; blockers={','.join(sorted(blockers)) or 'none'}",
    )
