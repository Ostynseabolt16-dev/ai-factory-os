"""Local product analytics from products.csv."""

from __future__ import annotations

from collections import defaultdict

from ai_factory.products.product_manager import read_products


def _int_value(value: str, default: int = 0) -> int:
    raw = (value or "").strip()
    return int(raw) if raw.isdigit() else default


def _float_value(value: str, default: float = 0.0) -> float:
    try:
        return float((value or "").strip() or default)
    except ValueError:
        return default


def calculate_conversion_rate() -> float:
    """Estimate sold/listed conversion rate from local CSV state."""
    rows = read_products()
    listed_or_uploaded = [
        row for row in rows if row.get("status") in {"uploaded", "listed", "sold"}
    ]
    sold = [row for row in rows if row.get("status") == "sold" or _int_value(row.get("sales_count", "0")) > 0]
    if not listed_or_uploaded:
        return 0.0
    return round(len(sold) / len(listed_or_uploaded), 4)


def calculate_top_performing_niches(limit: int = 5) -> list[tuple[str, float]]:
    """Rank niches by local revenue."""
    revenue_by_niche: dict[str, float] = defaultdict(float)
    for row in read_products():
        niche = (row.get("niche") or "unknown").strip().lower()
        revenue_by_niche[niche] += _float_value(row.get("revenue", "0"))
    return sorted(revenue_by_niche.items(), key=lambda item: item[1], reverse=True)[:limit]


def calculate_average_quality() -> float:
    """Average quality_score across products that have a numeric score."""
    scores = [
        _int_value(row.get("quality_score", "0"))
        for row in read_products()
        if (row.get("quality_score") or "").strip().isdigit()
    ]
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


def estimate_total_revenue() -> float:
    """Sum local revenue from products.csv."""
    return round(sum(_float_value(row.get("revenue", "0")) for row in read_products()), 2)
