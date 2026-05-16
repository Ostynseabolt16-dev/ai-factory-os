"""Bulk design generation helpers.

This module is the first "Design Agent" building block: it turns a niche and
amount into multiple generated PNG designs while keeping the old CLI behavior.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from ai_factory.config import PROJECT_ROOT
from ai_factory.data_store.products_csv import append_design_row
from ai_factory.generation.openai_image import generate_kawaii_design_to_designs

STYLES = [
    "kawaii",
    "retro",
    "cute",
    "vaporwave",
    "cartoon",
    "minimalist",
    "sticker style",
    "bold vector",
]


def _safe_stem(text: str) -> str:
    """Create a simple filename stem from a niche."""
    stem = text.strip().replace(" ", "_")
    stem = re.sub(r"[^a-zA-Z0-9._-]", "", stem)
    return stem or "bulk_design"


def calculate_quality_score(prompt: str) -> int:
    """Simple keyword-based product quality score."""
    score = 0
    prompt_lower = prompt.lower()

    if "retro" in prompt_lower:
        score += 2

    if "bold" in prompt_lower:
        score += 1

    return score


def generate_bulk_designs(niche: str, amount: int, *, batch_id: str = "") -> list[Path]:
    """
    Generate several design PNGs for a niche.

    Returns the paths that generated successfully. If one design fails, the
    batch continues so a single API error does not kill the whole run.
    """
    niche = niche.strip()
    if not niche:
        raise ValueError("Niche must not be empty.")
    if amount < 0:
        raise ValueError("Amount must be 0 or greater.")

    saved_paths: list[Path] = []
    stem_base = _safe_stem(niche)

    for index in range(amount):
        style = STYLES[index % len(STYLES)]
        prompt = f"{style} {niche} t-shirt design"
        quality_score = calculate_quality_score(prompt)
        number = index + 1

        print(f"\nGenerating #{number}: {prompt}")

        try:
            path = generate_kawaii_design_to_designs(
                prompt,
                stem=f"{stem_base}_{number}",
            )
        except Exception as exc:
            print(f"Error: {exc}")
            continue

        saved_paths.append(path)
        filename = path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
        product_id = append_design_row(
            niche=niche,
            filename=filename,
            quality_score=quality_score,
            batch_id=batch_id,
        )
        print(f"Saved: {path}")
        print(f"Tracked product #{product_id} in products.csv (quality score: {quality_score})")
        time.sleep(1)

    return saved_paths


def run_bulk_generator_cli() -> None:
    """Interactive CLI wrapper for manual design generation."""
    print("\n=== BULK DESIGN GENERATOR ===\n")

    niche = input("Enter niche: ")
    amount = int(input("How many designs?: "))

    saved_paths = generate_bulk_designs(niche, amount)

    print(f"\nDONE GENERATING DESIGNS ({len(saved_paths)} saved)\n")


if __name__ == "__main__":
    run_bulk_generator_cli()