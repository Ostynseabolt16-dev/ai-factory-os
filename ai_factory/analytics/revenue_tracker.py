"""Manual real revenue tracking."""

from __future__ import annotations

from ai_factory.listings.listing_tracker import update_listing_metrics, read_listings
from ai_factory.products.product_manager import mark_product_sold, read_products
from ai_factory.signals.market_signal_ingestor import update_product_signal_from_market


def calculate_platform_fee_estimate(revenue: float, *, rate: float = 0.12) -> float:
    return round(max(0.0, revenue) * rate, 2)


def calculate_profit_margin(revenue: float, fees: float) -> float:
    if revenue <= 0:
        return 0.0
    return round((revenue - fees) / revenue, 4)


def record_sale(product_id: str | int, *, listing_id: str = "", revenue: float = 0.0) -> dict[str, object]:
    """Manually record a real sale locally."""
    if listing_id:
        listing = next((row for row in read_listings() if row["listing_id"] == listing_id), None)
        current_orders = int(listing.get("orders") or 0) if listing else 0
        current_revenue = float(listing.get("revenue") or 0) if listing else 0.0
        update_listing_metrics(listing_id, orders=current_orders + 1, revenue=current_revenue + revenue)
    product = mark_product_sold(product_id, revenue_amount=revenue)
    market = update_product_signal_from_market(product_id)
    fees = calculate_platform_fee_estimate(float(product.get("actual_revenue") or product.get("revenue") or 0))
    return {"product": product, "market": market, "platform_fees_estimate": fees}


def calculate_real_revenue() -> float:
    return round(sum(float(product.get("actual_revenue") or product.get("revenue") or 0) for product in read_products()), 2)


def generate_revenue_report() -> dict[str, object]:
    total_revenue = calculate_real_revenue()
    fees = calculate_platform_fee_estimate(total_revenue)
    return {
        "actual_revenue": total_revenue,
        "platform_fees_estimate": fees,
        "estimated_profit": round(total_revenue - fees, 2),
        "profit_margin": calculate_profit_margin(total_revenue, fees),
        "sold_products": [product for product in read_products() if int(product.get("total_orders") or 0) > 0],
    }

