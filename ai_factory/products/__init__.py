"""Product inventory and listing preparation."""

from ai_factory.products.product_manager import (
    ALLOWED_STATUSES,
    CSV_COLUMNS,
    DEFAULT_STATUS,
    create_product_record,
    ensure_products_csv_schema,
    get_products_by_status,
    get_recent_products,
    get_top_niches,
    is_upload_ready,
    mark_product_sold,
    mark_product_uploaded,
    read_products,
    update_product_status,
)
from ai_factory.products.listing_generator import score_listing_quality

__all__ = [
    "ALLOWED_STATUSES",
    "CSV_COLUMNS",
    "DEFAULT_STATUS",
    "create_product_record",
    "ensure_products_csv_schema",
    "get_products_by_status",
    "get_recent_products",
    "get_top_niches",
    "is_upload_ready",
    "mark_product_sold",
    "mark_product_uploaded",
    "read_products",
    "score_listing_quality",
    "update_product_status",
]
