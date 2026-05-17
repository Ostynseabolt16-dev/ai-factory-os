"""Batch product generation from `ideas.txt`.

This stays intentionally small: read ideas, skip blanks/duplicates, generate
one product at a time, and append successful products to `products.csv`.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_factory.config import PRODUCTS_CSV, PROJECT_ROOT
from ai_factory.data_store.products_csv import (
    append_product_row,
    existing_ideas,
    next_id,
    normalize_idea,
)
from ai_factory.generation.structured_generation import (
    generate_structured_products_from_ideas,
    generate_and_cache_concept_image,
    rank_generated_products,
)
from ai_factory.products.product_manager import sanitize_products_csv
from ai_factory.mockups import generate_product_mockups

# Edit this value or set DAILY_LIMIT in .env / shell to control each batch run.
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "10"))
IDEAS_FILE = PROJECT_ROOT / "ideas.txt"


def load_ideas(path: Path = IDEAS_FILE) -> list[str]:
    """Read non-blank ideas from `ideas.txt`."""
    if not path.exists():
        raise FileNotFoundError(f"Could not find ideas file: {path}")

    ideas: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            idea = line.strip()
            if idea:
                ideas.append(idea)
    return ideas


def _ideas_to_generate(ideas: list[str], *, limit: int) -> list[str]:
    """Skip ideas already present in products.csv and cap the batch size."""
    already_done = existing_ideas(PRODUCTS_CSV)
    seen_this_run: set[str] = set()
    selected: list[str] = []

    for idea in ideas:
        normalized = normalize_idea(idea)
        if not normalized:
            continue
        if normalized in already_done or normalized in seen_this_run:
            continue

        selected.append(idea)
        seen_this_run.add(normalized)

        if len(selected) >= limit:
            break

    return selected


def _save_structured_product(product: dict[str, Any]) -> int:
    product_id = next_id()
    stem = f"product_{product_id:04d}"

    image_path = generate_and_cache_concept_image(product, stem=stem)
    image_rel = image_path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    mockup_paths = generate_product_mockups(product_id, image_path)
    mockup_rel_paths = [
        path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
        for path in mockup_paths
    ]

    append_product_row(
        product_id=product_id,
        created_at=datetime.now().replace(microsecond=0).isoformat(),
        idea=product["idea"],
        image_path=image_rel,
        title=product["title"],
        description=product["description"],
        tags=product["tags"],
        status="draft",
        mockup_paths=mockup_rel_paths,
        quality_score=0,
        confidence_score=product["confidence_score"],
        image_prompt=product["image_prompt"],
        generation_hash=product.get("generation_hash", ""),
        batch_id="",
    )

    return product_id


def run_batch_from_ideas_file(
    *,
    ideas_path: Path = IDEAS_FILE,
    daily_limit: int = DAILY_LIMIT,
) -> None:
    """Generate products from `ideas.txt`, continuing if one idea fails."""
    sanitize_products_csv()
    ideas = load_ideas(ideas_path)
    candidate_limit = max(daily_limit * 2, daily_limit + 5)
    selected = _ideas_to_generate(ideas, limit=candidate_limit)
    total = len(selected)

    print(f"Loaded {len(ideas)} non-blank ideas from {ideas_path.name}.")
    print(f"Daily limit: {daily_limit}")
    print(f"Candidate concepts selected: {total}")

    if total == 0:
        print("No new ideas to generate. Everything is blank, duplicate, or already in products.csv.")
        return

    candidates = generate_structured_products_from_ideas(selected)
    if not candidates:
        print("No valid structured concepts could be generated from the selected ideas.")
        return

    ranked = rank_generated_products(candidates, top_n=daily_limit)
    print(f"Validated and ranked {len(candidates)} structured concept(s). Generating top {len(ranked)} products.")

    successes = 0
    failures = 0

    for index, product in enumerate(ranked, start=1):
        print(f"\n[{index}/{len(ranked)}] generating: {product['title']}")
        try:
            product_id = _save_structured_product(product)
        except Exception as exc:  # Keep batch moving if one product fails.
            failures += 1
            print(f"[{index}/{len(ranked)}] failed: {exc}")
            continue

        successes += 1
        print(f"[{index}/{len(ranked)}] saved product #{product_id} to products.csv")

    print("\nBatch complete.")
    print(f"  successful: {successes}")
    print(f"  failed:     {failures}")
    print(f"  csv:        {PROJECT_ROOT / 'products.csv'}")
