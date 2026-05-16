"""Select the strongest small set of products for manual upload."""

from __future__ import annotations

from ai_factory.analytics.profitability_engine import score_product_profitability
from ai_factory.products.product_manager import read_products
from ai_factory.quality.duplicate_detector import generate_duplicate_report
from ai_factory.signals.product_signal_engine import calculate_product_signal
from ai_factory.signals.validation_score import calculate_validation_score


def _score(product: dict[str, str], duplicate_ids: set[str]) -> tuple[float, list[str]]:
    reasons: list[str] = []
    quality = float(product.get("quality_score") or 0)
    signal = float(calculate_product_signal(product["id"])["signal_score"])
    validation = float(calculate_validation_score(product["id"])["validation_score"])
    profitability = float(score_product_profitability(product)["profitability_score"])
    complete = all(product.get(field) for field in ["title", "tags", "description"])
    duplicate_penalty = 25 if product["id"] in duplicate_ids else 0

    if not complete:
        reasons.append("missing listing metadata")
    if product["id"] in duplicate_ids:
        reasons.append("duplicate risk")
    if quality < 2:
        reasons.append("low quality score")
    if not product.get("mockup_paths"):
        reasons.append("missing mockups")

    score = quality * 10 + signal + validation + profitability * 10 + (15 if complete else 0) - duplicate_penalty
    return round(max(0, score), 3), reasons


def select_products_for_listing(limit: int = 5) -> dict[str, list[dict[str, object]]]:
    """Return recommended uploads and rejected products with reasons."""
    duplicate_ids = {item["product_id"] for item in generate_duplicate_report()} | {item["duplicate_id"] for item in generate_duplicate_report()}
    scored = []
    rejected = []
    used_niches: set[str] = set()
    for product in read_products():
        if product.get("status") in {"archived", "sold"}:
            continue
        score, reasons = _score(product, duplicate_ids)
        row = {"product_id": product["id"], "niche": product.get("niche") or "unknown", "selection_score": score, "reasons": reasons}
        if reasons or score < 35:
            rejected.append({**row, "rejection_reasons": reasons or ["score below threshold"]})
        else:
            scored.append(row)

    ranked = sorted(scored, key=lambda item: float(item["selection_score"]), reverse=True)
    selected = []
    for item in ranked:
        niche = str(item["niche"])
        # Favor niche diversity for the first pass.
        if niche in used_niches and len(selected) < min(limit, 3):
            continue
        selected.append(item)
        used_niches.add(niche)
        if len(selected) >= limit:
            break

    return {"recommended_uploads": selected, "rejected_products": sorted(rejected, key=lambda item: float(item["selection_score"]))}

