"""Marketplace sync utilities for AI Factory OS.

These helpers are designed to support local marketplace imports and
future connectors for Shopify, TikTok Shop, Gumroad, and other marketplaces.
"""

from __future__ import annotations
import re


def deduplicate_marketplace_rows(
    rows: list[dict[str, str]],
    id_key: str = "marketplace_listing_id",
    title_key: str = "title",
) -> tuple[list[dict[str, str]], int]:
    """Remove duplicate marketplace export rows while preserving first sighting."""
    deduped_rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    duplicates = 0

    for row in rows:
        marketplace_listing_id = (row.get(id_key) or "").strip()
        title = (row.get(title_key) or "").strip().lower()

        if marketplace_listing_id:
            if marketplace_listing_id in seen_ids:
                duplicates += 1
                continue
            seen_ids.add(marketplace_listing_id)
            deduped_rows.append(row)
            continue

        if title:
            if title in seen_titles:
                duplicates += 1
                continue
            seen_titles.add(title)
            deduped_rows.append(row)
            continue

        # Preserve rows that cannot be deduplicated by ID or title for later validation.
        deduped_rows.append(row)

    return deduped_rows, duplicates


def marketplace_listing_id_or_fallback(normalized: dict[str, str], index: int) -> str:
    """Return an external listing id when available, otherwise build a stable fallback."""
    marketplace_listing_id = (normalized.get("marketplace_listing_id") or "").strip()
    if marketplace_listing_id:
        return marketplace_listing_id

    title = (normalized.get("title") or "").strip()
    if title:
        cleaned = re.sub(r"[^A-Za-z0-9]+", "-", title.lower()).strip("-")
        return cleaned or f"etsy-import-{index}"

    return f"etsy-import-{index}"
