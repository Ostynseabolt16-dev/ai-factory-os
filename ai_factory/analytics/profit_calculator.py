"""Lightweight Etsy/Printify profit calculator.

These are simple estimates for decision-making, not accounting software.
"""

from __future__ import annotations

from ai_factory.listings.listing_tracker import read_listings


def estimate_listing_profit(
    listing: dict[str, str],
    *,
    etsy_fee_rate: float = 0.12,
    printify_base_cost: float = 0.0,
    shipping_cost: float = 0.0,
    ad_spend: float = 0.0,
) -> dict[str, object]:
    """Estimate net profit for one listing from manually entered costs."""
    revenue = max(0.0, float(listing.get("revenue") or 0))
    etsy_fees = round(revenue * etsy_fee_rate, 2)
    costs = round(etsy_fees + printify_base_cost + shipping_cost + ad_spend, 2)
    net = round(revenue - costs, 2)
    margin = round(net / revenue, 4) if revenue else 0.0
    return {
        "listing_id": listing.get("listing_id", ""),
        "product_id": listing.get("product_id", ""),
        "revenue": round(revenue, 2),
        "etsy_fees": etsy_fees,
        "printify_base_cost": round(printify_base_cost, 2),
        "shipping_cost": round(shipping_cost, 2),
        "ad_spend": round(ad_spend, 2),
        "estimated_net_profit": net,
        "profit_margin": margin,
    }


def estimate_total_profit(
    *,
    etsy_fee_rate: float = 0.12,
    default_printify_base_cost: float = 0.0,
    default_shipping_cost: float = 0.0,
    default_ad_spend: float = 0.0,
) -> dict[str, object]:
    """Estimate total profit across tracked listings using simple defaults."""
    estimates = [
        estimate_listing_profit(
            listing,
            etsy_fee_rate=etsy_fee_rate,
            printify_base_cost=default_printify_base_cost * int(listing.get("orders") or 0),
            shipping_cost=default_shipping_cost * int(listing.get("orders") or 0),
            ad_spend=default_ad_spend,
        )
        for listing in read_listings()
    ]
    return {
        "estimated_revenue": round(sum(float(item["revenue"]) for item in estimates), 2),
        "estimated_net_profit": round(sum(float(item["estimated_net_profit"]) for item in estimates), 2),
        "listings": estimates,
    }
