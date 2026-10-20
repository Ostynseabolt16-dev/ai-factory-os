"""Convert manual listing metrics into market signals."""

from __future__ import annotations

from datetime import datetime

from ai_factory.listings.listing_tracker import read_listings
from ai_factory.products.product_manager import read_products, write_products
from ai_factory.tasks.task_models import now_iso


def _age_days(created_at: str) -> int:
    try:
        return max(0, (datetime.fromisoformat(now_iso()) - datetime.fromisoformat(created_at)).days)
    except ValueError:
        return 0


def calculate_market_signal(listing: dict[str, str]) -> dict[str, object]:
    """Calculate real market signal from manual listing metrics."""
    views = int(listing.get("views") or 0)
    favorites = int(listing.get("favorites") or 0)
    orders = int(listing.get("orders") or 0)
    revenue = float(listing.get("revenue") or 0)
    conversion = orders / views if views else 0
    age = max(1, _age_days(listing.get("created_at", "")) + 1)
    engagement = (favorites * 2 + orders * 10 + revenue) / age
    score = min(100, views * 0.05 + favorites * 1.5 + orders * 20 + revenue * 2 + conversion * 100 + engagement)
    return {
        "listing_id": listing.get("listing_id", ""),
        "product_id": listing.get("product_id", ""),
        "market_signal_score": round(score, 3),
        "views": views,
        "favorites": favorites,
        "orders": orders,
        "revenue": revenue,
        "conversion_rate": round(conversion, 4),
        "listing_age_days": age,
    }


def update_product_signal_from_market(product_id: str | int) -> dict[str, object]:
    """Sync listing revenue/orders into products.csv for one product."""
    target = str(product_id)
    rows = read_products()
    product = next((row for row in rows if row.get("id") == target), None)

    listings = [listing for listing in read_listings() if listing.get("product_id") == target]
    total_orders = sum(int(listing.get("orders") or 0) for listing in listings)
    total_revenue = sum(float(listing.get("revenue") or 0) for listing in listings)

    if not listings:
        total_orders = int(product.get("total_orders") or 0) if product else 0
        total_revenue = float(product.get("actual_revenue") or product.get("revenue") or 0.0) if product else 0.0

    total_fees = round(total_revenue * 0.12, 2)
    estimated_profit = round(total_revenue - total_fees, 2)

    if product:
        product["actual_sales_count"] = str(total_orders)
        product["total_orders"] = str(total_orders)
        product["actual_revenue"] = f"{total_revenue:.2f}"
        product["revenue"] = f"{total_revenue:.2f}"
        product["platform_fees_estimate"] = f"{total_fees:.2f}"
        product["estimated_profit"] = f"{estimated_profit:.2f}"
        if total_orders and not product.get("first_sale_date"):
            product["first_sale_date"] = now_iso()
        if total_orders:
            product["last_sale_date"] = now_iso()
        write_products(rows)

    return {"product_id": target, "orders": total_orders, "revenue": round(total_revenue, 2), "estimated_profit": estimated_profit}


def generate_market_signal_report() -> dict[str, object]:
    signals = [calculate_market_signal(listing) for listing in read_listings()]
    return {
        "listing_count": len(signals),
        "strongest": sorted(signals, key=lambda item: float(item["market_signal_score"]), reverse=True)[:10],
        "weakest": sorted(signals, key=lambda item: float(item["market_signal_score"]))[:10],
    }

