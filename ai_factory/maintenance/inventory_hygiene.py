"""Inventory hygiene diagnostics."""

from __future__ import annotations

from datetime import datetime

from ai_factory.products.product_manager import read_products
from ai_factory.production.batch_manager import _read_batches, summarize_batch
from ai_factory.quality.duplicate_detector import generate_duplicate_report
from ai_factory.tasks.task_models import now_iso
from ai_factory.workflows.workflow_engine import get_workflow_history
from ai_factory.signals.validation_score import calculate_validation_score


def _age_days(created_at: str) -> int:
    try:
        return (datetime.fromisoformat(now_iso()) - datetime.fromisoformat(created_at)).days
    except ValueError:
        return 0


def find_stale_products(days: int = 14) -> list[dict[str, str]]:
    return [product for product in read_products() if product.get("status") == "draft" and _age_days(product.get("created_at", "")) >= days]


def find_cleanup_candidates() -> list[dict[str, str]]:
    duplicate_ids = {item["product_id"] for item in generate_duplicate_report()}
    candidates = []
    for product in read_products():
        try:
            quality = float(product.get("quality_score") or 0)
        except ValueError:
            quality = 0
        validation = calculate_validation_score(product.get("id", ""))
        if quality <= 0 or product.get("id") in duplicate_ids or validation["validation_level"] in {"unvalidated", "weak"}:
            candidates.append(product)
    return candidates


def find_orphan_variants() -> list[dict[str, str]]:
    ids = {product["id"] for product in read_products()}
    return [product for product in read_products() if product.get("product_type") == "variant" and product.get("parent_product_id") not in ids]


def generate_inventory_hygiene_report() -> dict[str, object]:
    duplicates = generate_duplicate_report()
    low_batches = [summarize_batch(batch["batch_id"]) for batch in _read_batches() if float(summarize_batch(batch["batch_id"]).get("average_quality", 0)) <= 1]
    workflows = get_workflow_history()
    abandoned = [workflow for workflow in workflows if workflow.get("status") == "pending"]
    incomplete = [p for p in read_products() if not (p.get("title") and p.get("tags") and p.get("description"))]
    low_signal = [p for p in read_products() if calculate_validation_score(p.get("id", ""))["validation_level"] in {"unvalidated", "weak"}]
    return {
        "stale_products": find_stale_products(),
        "cleanup_candidates": find_cleanup_candidates(),
        "orphan_variants": find_orphan_variants(),
        "duplicate_count": len(duplicates),
        "low_quality_batches": low_batches,
        "abandoned_workflows": abandoned,
        "incomplete_listings": incomplete,
        "low_signal_inventory": low_signal,
    }

