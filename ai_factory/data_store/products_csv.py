"""Compatibility wrappers for the CSV-backed product manager.

New code should use `ai_factory.products.product_manager` directly. These
functions keep existing generation and batch modules working.
"""

from __future__ import annotations

from pathlib import Path

from ai_factory.products.product_manager import (
    CSV_COLUMNS,
    DEFAULT_STATUS,
    create_product_record,
    ensure_products_csv_schema,
    next_product_id,
    read_products,
)
from ai_factory.visuals.factory_map import build_factory_map


def normalize_idea(idea: str) -> str:
    """Normalize idea text so duplicate checks are forgiving but simple."""
    return " ".join(idea.strip().lower().split())


def next_id(path: Path | None = None) -> int:
    """Return next numeric id (1-based) based on existing rows."""
    return next_product_id(path)


def existing_ideas(path: Path | None = None) -> set[str]:
    """Return normalized ideas already saved in the product CSV."""
    ideas: set[str] = set()
    for row in read_products(path):
        idea = normalize_idea(row.get("idea") or "")
        if idea:
            ideas.add(idea)
    return ideas


def append_design_row(
    *,
    niche: str,
    filename: str,
    quality_score: int = 0,
    status: str = DEFAULT_STATUS,
    batch_id: str | int = "",
    path: Path | None = None,
) -> int:
    """Append a design-only product row."""
    product_id = create_product_record(
        niche=niche,
        filename=filename,
        batch_id=batch_id,
        status=status,
        quality_score=quality_score,
        image_path=filename,
        path=path,
    )
    build_factory_map()
    return product_id


def read_product_rows(path: Path | None = None) -> list[dict[str, str]]:
    """Read products.csv rows after ensuring the current schema exists."""
    return read_products(path)


def append_product_row(
    *,
    product_id: int,
    created_at: str,
    idea: str,
    image_path: str,
    title: str,
    description: str,
    tags: list[str],
    status: str = DEFAULT_STATUS,
    mockup_paths: list[str] | None = None,
    quality_score: int = 0,
    batch_id: str | int = "",
    path: Path | None = None,
) -> Path:
    """
    Append one full product row.

    `product_id` and `created_at` are accepted for compatibility, but new ids
    are assigned by the product manager to avoid collisions.
    """
    _ = product_id, created_at
    target_path = path
    create_product_record(
        idea=idea,
        batch_id=batch_id,
        image_path=image_path,
        filename=Path(image_path).name,
        title=title,
        description=description,
        tags=tags,
        status=status,
        mockup_paths=mockup_paths or [],
        quality_score=quality_score,
        path=target_path,
    )
    ensure_products_csv_schema(target_path)
    build_factory_map()
    from ai_factory.config import PRODUCTS_CSV

    return target_path or PRODUCTS_CSV
