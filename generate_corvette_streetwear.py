#!/usr/bin/env python3
"""
Generate Corvette streetwear fronts like your sold C5 (Printify style).

Requires OPENAI_API_KEY in .env with billing enabled (platform.openai.com).

Examples:
  .venv/bin/python generate_corvette_streetwear.py C8
  .venv/bin/python generate_corvette_streetwear.py C8 --dry-run
  .venv/bin/python generate_corvette_streetwear.py C4,C7 --no-export

After generation, files land in designs/ and products.csv gets a row.
Run export step automatically unless --no-export (white bg -> black on transparent).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from ai_factory.config import DESIGNS_DIR, PROJECT_ROOT
from ai_factory.generation.openai_image import generate_simple_image_to_file
from ai_factory.niches.corvette import (
    CORVETTE_GENERATIONS,
    NICHE,
    listing_title_illustrated,
    streetwear_front_prompt,
)
from ai_factory.products.product_manager import create_product_record
from ai_factory.visuals.factory_map import build_factory_map

_BY_CODE = {g.code.upper(): g for g in CORVETTE_GENERATIONS}


def _parse_codes(raw: str) -> list[str]:
    return [p.strip().upper() for p in raw.split(",") if p.strip()]


def _export_pod(path: Path) -> None:
    script = PROJECT_ROOT / "scripts" / "export_pod_solid_black.py"
    subprocess.run([sys.executable, str(script), str(path)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate sold-style Corvette streetwear PNGs.")
    parser.add_argument("codes", help="C4,C5,C6,C7,C8 (comma-separated)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts only")
    parser.add_argument("--no-export", action="store_true", help="Skip white->transparent export")
    args = parser.parse_args()

    codes = _parse_codes(args.codes)
    unknown = [c for c in codes if c not in _BY_CODE]
    if unknown:
        print(f"Unknown: {unknown}. Known: {', '.join(_BY_CODE)}", file=sys.stderr)
        return 1

    for code in codes:
        gen = _BY_CODE[code]
        prompt = streetwear_front_prompt(gen.code, gen.years)
        stem = f"corvette_{gen.code.lower()}_streetwear_design"
        title = listing_title_illustrated(gen.code)
        out = DESIGNS_DIR / f"{stem}.png"

        print(f"\n[{gen.code}]")
        print(f"  Title: {title}")
        print(f"  Out:   {out}")
        print(f"  Prompt: {prompt[:200]}...")

        if args.dry_run:
            continue

        try:
            generate_simple_image_to_file(prompt, out, background="opaque")
        except Exception as exc:
            print(f"  API error: {exc}", file=sys.stderr)
            print("  Fix: platform.openai.com → Billing → raise limit / add payment method.", file=sys.stderr)
            continue

        if not args.no_export:
            _export_pod(out)

        rel = out.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
        pid = create_product_record(
            niche=NICHE,
            title=title,
            idea=prompt,
            filename=out.name,
            image_path=rel,
            status="uploaded",
            pipeline_stage="published",
            upload_priority="high",
            quality_score=5,
            notes=f"streetwear_front {gen.code}",
        )
        build_factory_map()
        print(f"  Saved + tracked as product #{pid}")
        time.sleep(1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
