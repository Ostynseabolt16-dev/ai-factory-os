"""Central product lifecycle coordinator.

All product state changes go through product_manager APIs. This module adds
transition rules and audit logs so lifecycle movement stays traceable.
"""

from __future__ import annotations

from ai_factory.products.product_manager import (
    create_product_record,
    read_products,
    update_product_status,
)
from ai_factory.review.review_engine import review_product as review_product_local
from ai_factory.tasks.audit_log import audit_log

ALLOWED_TRANSITIONS = {
    "draft": {"reviewed", "archived"},
    "reviewed": {"mockup_ready", "upload_ready", "archived"},
    "mockup_ready": {"upload_ready", "archived"},
    "upload_ready": {"uploaded", "archived"},
    "uploaded": {"listed", "sold", "archived"},
    "listed": {"sold", "archived"},
    "sold": {"archived"},
    "archived": set(),
}


def _get_product(product_id: str | int) -> dict[str, str]:
    target = str(product_id)
    for product in read_products():
        if product.get("id") == target:
            return product
    raise ValueError(f"Product id not found: {product_id}")


def _validate_transition(product: dict[str, str], new_status: str) -> None:
    current = product.get("status") or "draft"
    if new_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid transition: {current} -> {new_status}")


def review_product(product_id: str | int) -> dict[str, object]:
    """Review a draft product and move it to reviewed only if it passes."""
    product = _get_product(product_id)
    _validate_transition(product, "reviewed")
    review = review_product_local(product_id)
    if not review["passed"]:
        audit_log(f"Product {product_id} review failed score={review['score']}", event="pipeline")
        return {"product_id": str(product_id), "status": product.get("status"), "review": review}

    updated = update_product_status(product_id, "reviewed")
    audit_log(f"Product {product_id} moved draft -> reviewed", event="pipeline")
    return {"product_id": str(product_id), "status": updated["status"], "review": review}


def mark_mockup_ready(product_id: str | int) -> dict[str, str]:
    """Move reviewed product to mockup_ready."""
    product = _get_product(product_id)
    _validate_transition(product, "mockup_ready")
    updated = update_product_status(product_id, "mockup_ready")
    audit_log(f"Product {product_id} moved {product.get('status')} -> mockup_ready", event="pipeline")
    return updated


def mark_upload_ready(product_id: str | int) -> dict[str, str]:
    """Move reviewed/mockup_ready product to upload_ready after manager readiness checks."""
    product = _get_product(product_id)
    if product.get("status") == "mockup_ready":
        update_product_status(product_id, "reviewed")
        product = _get_product(product_id)
    _validate_transition(product, "upload_ready")
    updated = update_product_status(product_id, "upload_ready")
    audit_log(f"Product {product_id} moved to upload_ready", event="pipeline")
    return updated


def archive_product(product_id: str | int) -> dict[str, str]:
    """Archive a product from any non-archived stage allowed by transition table."""
    product = _get_product(product_id)
    _validate_transition(product, "archived")
    updated = update_product_status(product_id, "archived")
    audit_log(f"Product {product_id} archived from {product.get('status')}", event="pipeline")
    return updated


def duplicate_product_as_variant(product_id: str | int) -> int:
    """Duplicate a product row as a draft variant with lineage preserved."""
    product = _get_product(product_id)
    variant_id = create_product_record(
        niche=product.get("niche", ""),
        filename=product.get("filename", ""),
        status="draft",
        quality_score=product.get("quality_score", "0"),
        platform=product.get("platform", "etsy"),
        title=product.get("title", ""),
        tags=product.get("tags", ""),
        description=product.get("description", ""),
        notes=f"Variant of product {product_id}. {product.get('notes', '')}".strip(),
        parent_product_id=str(product_id),
        product_type="variant",
        idea=product.get("idea", ""),
        image_path=product.get("image_path", ""),
        mockup_paths=product.get("mockup_paths", ""),
    )
    audit_log(f"Created variant product {variant_id} from parent {product_id}", event="pipeline")
    return variant_id
