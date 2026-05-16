"""Persist products (designs + listing metadata) — CSV first."""

from ai_factory.data_store.products_csv import (
    CSV_COLUMNS,
    DEFAULT_STATUS,
    append_design_row,
    append_product_row,
    ensure_products_csv_schema,
    existing_ideas,
    next_id,
    normalize_idea,
    read_product_rows,
)

__all__ = [
    "CSV_COLUMNS",
    "DEFAULT_STATUS",
    "append_design_row",
    "append_product_row",
    "ensure_products_csv_schema",
    "existing_ideas",
    "next_id",
    "normalize_idea",
    "read_product_rows",
]
