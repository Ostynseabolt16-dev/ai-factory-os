#!/usr/bin/env python3
"""
Product pipeline: `ideas.txt` -> PNGs + Etsy copy -> append `products.csv`.

Run from project root:  python main.py

Pieces live in modules so other scripts stay unchanged:
  - Image:        ai_factory/generation/openai_image.py
  - Listing text: ai_factory/listings/listing_llm.py
  - Mockups:      ai_factory/mockups/mockup_generator.py
  - CSV rows:     ai_factory/data_store/products_csv.py
"""

from __future__ import annotations

from datetime import datetime

from ai_factory.config import PROJECT_ROOT
from ai_factory.data_store.products_csv import append_product_row, next_id
from ai_factory.generation.structured_generation import generate_structured_product_from_idea, generate_and_cache_concept_image
from ai_factory.mockups import generate_product_mockups
from ai_factory.orchestration.batch import run_batch_from_ideas_file


def run_interactive_pipeline() -> None:
    """Generate one product manually. Kept for one-off testing."""
    idea = input("Enter your product idea: ").strip()
    if not idea:
        print("No idea entered. Exiting.")
        return

    product_id = next_id()
    stem = f"product_{product_id:04d}"

    print(f"\n[1/3] Generating validated product concept for: {idea}")
    product = generate_structured_product_from_idea(idea)

    print(f"[2/3] Generating image → designs/{stem}.png …")
    image_path = generate_and_cache_concept_image(product, stem=stem)
    image_rel = image_path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    mockup_paths = generate_product_mockups(product_id, image_path)
    mockup_rel_paths = [
        path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
        for path in mockup_paths
    ]

    created_at = datetime.now().replace(microsecond=0).isoformat()

    print("[3/3] Saving row to products.csv …")
    append_product_row(
        product_id=product_id,
        created_at=created_at,
        idea=product["idea"],
        image_path=image_rel,
        title=product["title"],
        description=product["description"],
        tags=product["tags"],
        status="draft",
        mockup_paths=mockup_rel_paths,
        confidence_score=product["confidence_score"],
        image_prompt=product["image_prompt"],
        generation_hash="",
    )

    print("\nDone.")
    print(f"  id:          {product_id}")
    print(f"  image:       {image_rel}")
    print(f"  title:       {title[:80]}{'…' if len(title) > 80 else ''}")
    print(f"  tags:        {len(tags_str_list)} tags")
    print(f"  mockups:     {len(mockup_rel_paths)} files")
    print("  status:      draft")
    print(f"\nOpen {PROJECT_ROOT / 'products.csv'} to review or edit before listing.")


if __name__ == "__main__":
    try:
        run_batch_from_ideas_file()
    except KeyboardInterrupt:
        print("\nCanceled.")
    except RuntimeError as exc:
        print(f"\nSetup error: {exc}")
