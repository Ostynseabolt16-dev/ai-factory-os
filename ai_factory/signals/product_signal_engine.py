"""Product, niche, variant, and batch signal scoring."""

from __future__ import annotations

import csv
from collections import defaultdict

from ai_factory.analytics.profitability_engine import score_product_profitability
from ai_factory.config import PROJECT_ROOT
from ai_factory.products.product_manager import read_products
from ai_factory.production.batch_manager import get_batch_products, summarize_batch
from ai_factory.quality.duplicate_detector import generate_duplicate_report
from ai_factory.tasks.task_models import now_iso

SIGNAL_HISTORY_CSV = PROJECT_ROOT / "signal_history.csv"
SIGNAL_COLUMNS = ["created_at", "entity_type", "entity_id", "signal_score", "signal_level", "reasoning"]


def _ensure_history() -> None:
    if not SIGNAL_HISTORY_CSV.exists():
        with SIGNAL_HISTORY_CSV.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=SIGNAL_COLUMNS).writeheader()


def _append(entity_type: str, entity_id: str, score: float, level: str, reasoning: str) -> None:
    _ensure_history()
    with SIGNAL_HISTORY_CSV.open("a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=SIGNAL_COLUMNS).writerow(
            {
                "created_at": now_iso(),
                "entity_type": entity_type,
                "entity_id": entity_id,
                "signal_score": round(score, 3),
                "signal_level": level,
                "reasoning": reasoning,
            }
        )


def _level(score: float) -> str:
    if score >= 85:
        return "exceptional"
    if score >= 65:
        return "strong"
    if score >= 35:
        return "moderate"
    return "weak"


def _product(product_id: str | int) -> dict[str, str]:
    target = str(product_id)
    for product in read_products():
        if product.get("id") == target:
            return product
    raise ValueError(f"Product id not found: {product_id}")


def _metadata_score(product: dict[str, str]) -> float:
    fields = ["title", "tags", "description", "filename", "niche"]
    return sum(1 for field in fields if product.get(field)) / len(fields) * 20


def _duplicate_ids() -> set[str]:
    return {item["product_id"] for item in generate_duplicate_report()} | {item["duplicate_id"] for item in generate_duplicate_report()}


def calculate_product_signal(product_id: str | int) -> dict[str, object]:
    """Calculate a local signal score for one product."""
    product = _product(product_id)
    quality = min(25, float(product.get("quality_score") or 0) * 5)
    profitability = min(25, float(score_product_profitability(product)["profitability_score"]) * 10)
    metadata = _metadata_score(product)
    stage_bonus = {"review": 5, "mockups": 10, "listing": 15, "published": 20, "sales": 25}.get(product.get("pipeline_stage"), 0)
    duplicate_penalty = 15 if product.get("id") in _duplicate_ids() else 0
    review_bonus = 10 if product.get("status") in {"reviewed", "mockup_ready", "upload_ready", "uploaded", "listed", "sold"} else 0
    score = max(0, min(100, quality + profitability + metadata + stage_bonus + review_bonus - duplicate_penalty))
    level = _level(score)
    reasoning = f"quality={quality}; profitability={profitability}; metadata={metadata}; stage_bonus={stage_bonus}; duplicate_penalty={duplicate_penalty}"
    _append("product", str(product_id), score, level, reasoning)
    return {"product_id": str(product_id), "signal_score": round(score, 3), "signal_level": level, "reasoning": reasoning}


def calculate_batch_signal(batch_id: str) -> dict[str, object]:
    """Calculate a signal score for a production batch."""
    products = get_batch_products(batch_id)
    if not products:
        score = 0.0
    else:
        score = sum(float(calculate_product_signal(product["id"])["signal_score"]) for product in products) / len(products)
    summary = summarize_batch(batch_id)
    score = min(100, score + min(20, float(summary.get("total_revenue", 0)) * 2))
    level = _level(score)
    _append("batch", batch_id, score, level, "Average product signal plus revenue signal.")
    return {"batch_id": batch_id, "signal_score": round(score, 3), "signal_level": level, "batch_summary": summary}


def calculate_niche_signal(niche: str) -> dict[str, object]:
    """Calculate average product signal for a niche."""
    products = [p for p in read_products() if (p.get("niche") or "unknown").lower() == niche.lower()]
    if not products:
        score = 0.0
    else:
        score = sum(float(calculate_product_signal(product["id"])["signal_score"]) for product in products) / len(products)
    level = _level(score)
    _append("niche", niche, score, level, "Average product signal for niche.")
    return {"niche": niche, "signal_score": round(score, 3), "signal_level": level, "product_count": len(products)}


def rank_products_by_signal() -> list[dict[str, object]]:
    return sorted((calculate_product_signal(product["id"]) for product in read_products()), key=lambda item: float(item["signal_score"]), reverse=True)


def rank_niches_by_signal() -> list[dict[str, object]]:
    niches = {(product.get("niche") or "unknown").lower() for product in read_products()}
    return sorted((calculate_niche_signal(niche) for niche in niches), key=lambda item: float(item["signal_score"]), reverse=True)

