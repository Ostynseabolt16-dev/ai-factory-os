#!/usr/bin/env python3
"""Generate C7 variant B streetwear master — ad-optimized, debadged, correct C7 body."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_factory.generation.openai_image import generate_simple_image_to_file

C7_PROMPT = """
Automotive streetwear t-shirt graphic, pure white background, landscape 3:2, premium Etsy bestseller layout.

STYLE: Smooth photoreal digital render. Clean glossy black paint with soft natural highlights. Sharp crisp details on the car. NO halftone dots, NO stipple grain, NO newspaper texture on the car body. Distressed weathered texture ONLY on the gothic letter graphics, never on the car paint.

LAYOUT (match proven C5 gothic car tee template):
- Huge distressed gothic blackletter "C7" behind the upper half of the car
- Bottom left corner: distressed gothic "V8"
- Bottom right corner: LEAVE A CLEAN EMPTY PURE WHITE SPACE for local typography overlay later
- ABSOLUTELY NO small paragraph text, NO slogan text, NO quote text, NO AI-generated tiny words
- Only text allowed in the image: large "C7" behind the car and bottom-left "V8"
- Keep the lower-right quote area plain white with no grey artifacts, no ghost text, no faded letters

CAR — MUST BE CORRECT GENERATION (2014-2019 C7 Stingray, FRONT-ENGINE):
- Long hood and short rear deck (this is NOT a mid-engine C8)
- Angular C7 LED headlight shape, trapezoidal side intake cove behind front wheel
- Center hood vent, aggressive front splitter, coupe body
- Front three-quarter view facing slightly left, lowered stance
- Gloss black multi-spoke aftermarket wheels, debadged
- NO Chevrolet badges, NO crossed flags, NO Corvette wordmarks, NO logos anywhere

CRITICAL front bumper:
- NO license plate, NO plate bracket, NO rectangular plate pocket, NO plate filler panel
- Open mesh grille and clean continuous lower valance only

CRITICAL glass:
- Windshield and side windows: uniform dark smoke tint, solid opaque grey-black
- NO checkerboard pattern, NO transparency grid, NO grey flat placeholder inside cabin

CRITICAL body quality:
- NO motion blur, NO horizontal smear, NO clone artifacts on fenders
- Smooth continuous reflections on hood and front fender
- NO horizontal white line through the car, wheels, bumper, splitter, side skirt, or shadow
- Do not place any graphic, glow, line, underline, or separator across the car body

Centered composition, high contrast for small Etsy thumbnail. Leave enough clean white space below/right of the car for local quote overlay. No mockup, no t-shirt, no watermark.
""".strip()

DEFAULT_OUT = Path("designs/c7_variant_B_collection.png")
BACKUP_WRONG = Path("designs/backups/c7_variant_B_wrong_c8_body.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--attempt", type=int, default=1, help="Suffix for draft filename if not promoting")
    parser.add_argument("--draft-only", action="store_true", help="Save as _c7_gen_attemptN.png only")
    args = parser.parse_args()

    if args.draft_only:
        out = Path(f"designs/_c7_gen_attempt{args.attempt}.png")
    else:
        out = args.out
        if out.exists() and not BACKUP_WRONG.exists():
            BACKUP_WRONG.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(out, BACKUP_WRONG)
            print(f"Backed up previous master -> {BACKUP_WRONG}")

    path = generate_simple_image_to_file(
        C7_PROMPT,
        out,
        model="gpt-image-1",
        size="1536x1024",
    )
    print(f"OK  {path}")


if __name__ == "__main__":
    main()
