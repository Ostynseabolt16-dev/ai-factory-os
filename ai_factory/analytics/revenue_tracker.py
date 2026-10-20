"""Manual real revenue tracking."""

from __future__ import annotations

import re

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


def _extract_order_metadata(order_text: str) -> dict[str, object]:
    lines = [line.strip() for line in order_text.splitlines()]

    order_id_match = re.search(r"(?:#|order_id=)(\d{6,})", order_text)
    order_id = order_id_match.group(1) if order_id_match else ""

    revenue_match = re.search(r"\$(\d+(?:\.\d{2})?)", order_text)
    revenue = round(float(revenue_match.group(1)), 2) if revenue_match else 0.0

    customer = ""
    for line in lines:
        if line and not line.startswith("[") and not line.startswith("#") and not line.startswith("$") and not line.startswith("-") and not line.startswith("Ship") and not line.startswith("Ordered") and not line.startswith("Save up") and not line.startswith("Check out"):
            if line.lower().startswith("ship to"):
                continue
            customer = line
            break

    title = ""
    title_keywords = ("tee", "shirt", "sticker", "mug", "tote", "graphic", "illustrated", "hoodie", "bag")
    for line in lines:
        lowered = line.lower()
        if not line or line.startswith("-"):
            continue
        if re.match(r"^(Ship by|Ordered|Standard Shipping|Ship to|Save up|Check out|\[|#\d+|\$\d)", line):
            continue
        if lowered.startswith("http"):
            continue
        if line.endswith(")") and "etsy.com" in line:
            continue
        if any(keyword in lowered for keyword in title_keywords):
            title = line
            break

    if not title:
        for line in lines:
            lowered = line.lower()
            if not line or line.startswith("-"):
                continue
            if re.match(r"^(Ship by|Ordered|Standard Shipping|Ship to|Save up|Check out|\[|#\d+|\$\d)", line):
                continue
            if lowered.startswith("http"):
                continue
            if line.endswith(")") and "etsy.com" in line:
                continue
            title = line
            break

    return {
        "order_id": order_id,
        "customer": customer,
        "title": title,
        "revenue": revenue,
    }


def record_sale_from_order_text(order_text: str, *, listing_id: str = "") -> dict[str, object]:
    """Record a sale from pasted Etsy order text by matching the product title."""
    metadata = _extract_order_metadata(order_text)
    title = str(metadata.get("title") or "").strip()

    if not title:
        return {"recorded": False, "reason": "No product title found", **metadata}

    product_candidates = [
        product
        for product in read_products()
        if title.lower() in str(product.get("title") or "").lower()
    ]

    if not product_candidates:
        return {"recorded": False, "reason": "No matching product found", **metadata}

    product = product_candidates[0]
    product_id = str(product.get("id") or "")
    resolved_listing_id = listing_id or next(
        (row.get("listing_id", "") for row in read_listings() if str(row.get("product_id") or "") == product_id),
        "",
    )

    result = record_sale(product_id, listing_id=resolved_listing_id, revenue=float(metadata.get("revenue") or 0.0))
    return {
        "recorded": True,
        "order_id": metadata.get("order_id"),
        "customer": metadata.get("customer"),
        "title": title,
        "revenue": float(metadata.get("revenue") or 0.0),
        "product_id": product_id,
        "listing_id": resolved_listing_id,
        "sale_result": result,
    }


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

