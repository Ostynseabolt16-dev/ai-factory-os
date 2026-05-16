"""Create local product variant records.

These functions do not generate new images. They create traceable draft records
that preserve parent_product_id so future generation can be scheduled explicitly.
"""

from __future__ import annotations

from ai_factory.pipeline.product_pipeline import duplicate_product_as_variant
from ai_factory.products.product_manager import read_products, write_products
from ai_factory.tasks.audit_log import audit_log


def _update_variant_notes(variant_id: int, note: str) -> int:
    rows = read_products()
    for row in rows:
        if row.get("id") == str(variant_id):
            row["notes"] = f"{row.get('notes', '')} {note}".strip()
            write_products(rows)
            return variant_id
    raise ValueError(f"Variant id not found after creation: {variant_id}")


def create_color_variant(product_id: str | int) -> int:
    """Create a draft color variant record."""
    variant_id = duplicate_product_as_variant(product_id)
    audit_log(f"Created color variant {variant_id} from {product_id}", event="variant")
    return _update_variant_notes(variant_id, "Variant type: color.")


def create_text_variant(product_id: str | int) -> int:
    """Create a draft text/slogan variant record."""
    variant_id = duplicate_product_as_variant(product_id)
    audit_log(f"Created text variant {variant_id} from {product_id}", event="variant")
    return _update_variant_notes(variant_id, "Variant type: text.")


def create_style_variant(product_id: str | int) -> int:
    """Create a draft style variant record."""
    variant_id = duplicate_product_as_variant(product_id)
    audit_log(f"Created style variant {variant_id} from {product_id}", event="variant")
    return _update_variant_notes(variant_id, "Variant type: style.")
