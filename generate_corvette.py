#!/usr/bin/env python3
"""
Generate Corvette line designs (illustrated or typographic) and track in products.csv.

Examples:
  python generate_corvette.py C8 illustrated
  python generate_corvette.py C4,C7 illustrated
  python generate_corvette.py C5 typographic
  python generate_corvette.py --list
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from ai_factory.config import PROJECT_ROOT
from ai_factory.generation.openai_image import generate_automotive_design_to_designs
from ai_factory.products.product_manager import create_product_record
from ai_factory.visuals.factory_map import build_factory_map
from ai_factory.niches.corvette import (
    CORVETTE_GENERATIONS,
    NICHE,
    illustrated_design_prompt,
    listing_title_illustrated,
    listing_title_typographic,
    typographic_design_prompt,
)

_BY_CODE = {g.code.upper(): g for g in CORVETTE_GENERATIONS}


def _parse_codes(raw: str) -> list[str]:
    return [part.strip().upper() for part in raw.split(",") if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Corvette t-shirt PNGs for Etsy POD.")
    parser.add_argument(
        "codes",
        nargs="?",
        help="Generation codes: C4, C5, C6, C7, C8 (comma-separated). Omit with --list.",
    )
    parser.add_argument(
        "style",
        nargs="?",
        choices=("illustrated", "typographic"),
        default="illustrated",
        help="Design style (default: illustrated — matches first sales)",
    )
    parser.add_argument("--list", action="store_true", help="Show generations and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts only; no API calls.")
    args = parser.parse_args()

    if args.list:
        print("Corvette generations (niche:", NICHE, ")")
        for g in CORVETTE_GENERATIONS:
            print(f"  {g.code} ({g.years})")
            print(f"    illustrated title: {listing_title_illustrated(g.code)}")
            print(f"    typographic title: {listing_title_typographic(g.code)}")
        return 0

    if not args.codes:
        parser.error("Provide generation code(s) or use --list")

    codes = _parse_codes(args.codes)
    unknown = [c for c in codes if c not in _BY_CODE]
    if unknown:
        print(f"Unknown code(s): {', '.join(unknown)}. Known: {', '.join(_BY_CODE)}", file=sys.stderr)
        return 1

    for code in codes:
        gen = _BY_CODE[code]
        if args.style == "typographic":
            prompt = typographic_design_prompt(gen.code, gen.years)
            stem = gen.typographic_stem
            title = listing_title_typographic(gen.code)
        else:
            prompt = illustrated_design_prompt(gen.code, gen.years)
            stem = gen.illustrated_stem
            title = listing_title_illustrated(gen.code)

        print(f"\n[{gen.code}] {args.style}")
        print(f"  Etsy title: {title}")
        print(f"  Prompt: {prompt[:120]}...")

        if args.dry_run:
            continue

        try:
            path = generate_automotive_design_to_designs(prompt, stem=stem, style=args.style)
        except Exception as exc:
            print(f"  Error: {exc}", file=sys.stderr)
            continue

        rel = path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
        product_id = create_product_record(
            niche=NICHE,
            filename=Path(rel).name,
            image_path=rel,
            idea=prompt,
            title=title,
            quality_score=5,
            upload_priority="high",
            notes=f"corvette_{args.style}",
        )
        build_factory_map()
        print(f"  Saved: {path}")
        print(f"  products.csv #{product_id}")
        time.sleep(1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
