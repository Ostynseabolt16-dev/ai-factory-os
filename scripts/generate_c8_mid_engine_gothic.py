#!/usr/bin/env python3
"""Generate C8 mid-engine gothic streetwear master.

Uses the proven collection layout:
- Large distressed generation text behind the car
- Solid V8 bottom-left
- Local quote overlay in bottom-right for reliability
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_factory.generation.openai_image import generate_simple_image_to_file

C8_MID_ENGINE_PROMPT = """
Automotive streetwear t-shirt graphic, landscape 3:2, premium Etsy bestseller layout.

BACKGROUND — CRITICAL:
- Pure flat #FFFFFF white background only
- NO cream, NO beige, NO off-white, NO paper texture, NO vignette, NO gradient

STYLE: Smooth photoreal digital render. Clean glossy Torch Red paint with crisp reflections and strong shape definition. Sharp crisp details on the car. NO halftone dots, NO stipple grain, NO newspaper texture on the car body. Distressed weathered texture ONLY on the huge "C8" letters behind the car — NOT on the V8 letters.

LAYOUT (match proven C5/C6/C7 gothic car tee template):
- Huge distressed gothic blackletter "C8" behind the upper half of the car
- Bottom LEFT corner ONLY: solid black gothic "V8" — fully filled letterforms, ONE V8 only
- Leave bottom-RIGHT corner EMPTY white space — NO quote text, NO paragraph, NO small serif text (quote added locally in post)
- Car scaled slightly smaller in frame — generous clear white margin along bottom edge and bottom-right corner for quote overlay

CRITICAL V8 typography:
- Exactly ONE "V8" in the entire image
- V8 locked to bottom-left corner only
- NO strikethrough, NO horizontal line through V or 8, NO cut through letter stems
- NO duplicate V8, NO V8 in center, NO V8 on right side

CAR — MUST BE CORRECT GENERATION (2020+ C8 Stingray, MID-ENGINE):
- Mid-engine proportions: short hood and cabin-forward stance
- Distinct C8 boomerang-style side intake behind the door
- Angular C8 front fascia and headlights
- Front three-quarter view facing slightly left, lowered stance
- Entire body painted glossy Torch Red
- Gloss black multi-spoke wheels, performance tire stance
- Smooth debadged nose — NO emblem, NO crossed flags, NO wordmarks, NO logos
- NO side badges, NO Corvette text, NO Chevrolet bowtie anywhere

CRITICAL front bumper:
- NO license plate, NO plate bracket, NO rectangular plate pocket, NO plate filler panel
- Open grille details and clean continuous lower valance only

CRITICAL glass:
- Windshield and side windows: uniform dark smoke tint, solid opaque grey-black
- NO checkerboard pattern, NO transparency grid, NO flat placeholder inside cabin

CRITICAL body quality:
- NO motion blur, NO horizontal smear, NO clone artifacts on fenders
- Smooth continuous reflections on hood/front fender/door
- NO random horizontal white line through car or wheels

Centered composition, high contrast for small Etsy thumbnails. No mockup, no t-shirt, no watermark.
""".strip()

DEFAULT_OUT = Path("designs/c8_mid_engine_gothic_collection.png")
OVERLAY = ROOT / "scripts/overlay_collection_quote.py"
DEFAULT_QUOTE = [
    "Mid-engine precision,",
    "gothic streetwear attitude.",
    "Built to stop scrolls and",
    "turn every road into a runway.",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--draft-only", action="store_true")
    parser.add_argument("--skip-overlay", action="store_true", help="Skip local quote overlay")
    args = parser.parse_args()

    out = Path(f"designs/_c8_mid_engine_attempt{args.attempt}.png") if args.draft_only else args.out

    path = generate_simple_image_to_file(
        C8_MID_ENGINE_PROMPT,
        out,
        model="gpt-image-1",
        size="1536x1024",
    )
    print(f"OK  {path}")

    if not args.draft_only and not args.skip_overlay:
        subprocess.run(
            [
                sys.executable,
                str(OVERLAY),
                str(path),
                "--gen",
                "c7",
                "--lines",
                *DEFAULT_QUOTE,
            ],
            check=True,
            cwd=ROOT,
        )


if __name__ == "__main__":
    main()
