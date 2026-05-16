"""Revenue intelligence from local CSV data."""

from __future__ import annotations

from collections import defaultdict

from ai_factory.products.product_manager import read_products
from ai_factory.production.batch_manager import _read_batches, summarize_batch


def _float(value: str) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def _int(value: str) -> int:
    try:
        return int(float(value or 0))
    except ValueError:
        return 0


def revenue_by_niche() -> list[tuple[str, float]]:
    totals: dict[str, float] = defaultdict(float)
    for product in read_products():
        totals[(product.get("niche") or "unknown").lower()] += _float(product.get("revenue", "0"))
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)


def revenue_by_batch() -> list[tuple[str, float]]:
    totals: dict[str, float] = defaultdict(float)
    for product in read_products():
        batch_id = product.get("batch_id") or "unbatched"
        totals[batch_id] += _float(product.get("revenue", "0"))
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)


def top_conversion_products(limit: int = 10) -> list[dict[str, str]]:
    products = read_products()
    return sorted(products, key=lambda product: (_int(product.get("sales_count", "0")), _float(product.get("revenue", "0"))), reverse=True)[:limit]


def estimated_roi_by_niche() -> list[tuple[str, float]]:
    revenue: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for product in read_products():
        niche = (product.get("niche") or "unknown").lower()
        revenue[niche] += _float(product.get("revenue", "0"))
        counts[niche] += 1
    return sorted(((niche, round(revenue[niche] / counts[niche], 2)) for niche in counts), key=lambda item: item[1], reverse=True)


def underperforming_batches() -> list[dict[str, object]]:
    rows = []
    for batch in _read_batches():
        summary = summarize_batch(batch["batch_id"])
        if summary["product_count"] and summary["total_revenue"] == 0:
            rows.append(summary)
    return rows
