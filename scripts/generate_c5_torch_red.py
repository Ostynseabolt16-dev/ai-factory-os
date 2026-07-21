#!/usr/bin/env python3
"""Generate Torch Red C5 streetwear master — color variant, correct C5 body."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_factory.generation.openai_image import generate_simple_image_to_file

C5_TORCH_RED_PROMPT = """
Automotive streetwear t-shirt graphic, landscape 3:2, premium Etsy bestseller layout.

BACKGROUND — CRITICAL:
- Pure flat #FFFFFF white background only
- NO cream, NO beige, NO off-white, NO paper texture, NO vignette, NO gradient

STYLE: Smooth photoreal digital render. Clean glossy factory Torch Red paint — vivid classic Corvette red with soft natural highlights and deep rich tone (NOT orange, NOT burgundy, NOT candy apple). Sharp crisp details on the car. NO halftone dots, NO stipple grain, NO newspaper texture on the car body. Distressed weathered texture ONLY on the huge "C5" letters behind the car — NOT on the V8 letters.

LAYOUT (match proven C5/C7 gothic car tee template):
- Huge distressed gothic blackletter "C5" behind the upper half of the car
- Bottom left corner: solid black gothic "V8" — fully filled letterforms
- Bottom right corner: italic serif three lines — copy EXACTLY, letter-for-letter, no typos:
  "Low, wide, and unapologetically aggressive.
  Where raw American horsepower meets precision attitude —
  built to dominate streets and tracks alike."

CRITICAL V8 typography:
- V8 must be solid filled black gothic letters
- NO strikethrough, NO horizontal line through V or 8, NO cut through letter stems
- NO distressed void or white gap running horizontally through the middle of V8
- The interior of the "8" counter may be white (same as background) but letters must read as solid black shapes

CAR — MUST BE CORRECT GENERATION (1997-2004 C5 Corvette, FRONT-ENGINE):
- Smooth rounded late-90s American sports coupe — long hood, low wide fastback
- Fixed exposed headlights (NOT pop-up headlights — this is a C5 not a C4)
- Wide low stance, curved fenders, integrated rear spoiler lip
- Front three-quarter view facing slightly left, lowered stance
- Entire body painted glossy Torch Red — hood, fenders, doors, roof all red
- Gloss black Z06-style split five-spoke wheels with machined lip, debadged wheels
- Smooth debadged nose — NO emblem, NO badge, NO crossed flags, NO logo blob on hood or bumper
- NO side fender badges, NO Corvette wordmarks on body, NO Chevrolet bowtie anywhere
- Subtle low-profile gloss black front splitter lip under the bumper — clean straight edge, OEM+ track style, NOT huge carbon wing, NOT exaggerated

CRITICAL front bumper:
- NO license plate, NO plate bracket, NO rectangular plate pocket, NO plate filler panel
- Open mesh grille and clean continuous lower valance with integrated black splitter lip

CRITICAL headlights:
- Clean headlight bezels and lenses — NO floating dark specks, NO stray black pixels in white background near headlights
- Smooth continuous edges where headlight meets fender and hood — NO black dots or smudges in the white space beside the headlights

CRITICAL glass:
- Windshield and side windows: uniform dark smoke tint, solid opaque grey-black
- NO checkerboard pattern, NO transparency grid, NO grey flat placeholder inside cabin

CRITICAL body quality:
- NO motion blur, NO horizontal smear, NO clone artifacts on fenders
- Smooth continuous reflections on hood and front fender

Centered composition, high contrast for small Etsy thumbnail — red car pops on white. No mockup, no t-shirt, no watermark.
""".strip()

DEFAULT_OUT = Path("designs/corvette/c5_torch_red_collection.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--attempt", type=int, default=1, help="Suffix for draft filename if --draft-only")
    parser.add_argument("--draft-only", action="store_true", help="Save as _c5_torch_red_attemptN.png only")
    args = parser.parse_args()

    if args.draft_only:
        out = Path(f"designs/_c5_torch_red_attempt{args.attempt}.png")
    else:
        out = args.out

    path = generate_simple_image_to_file(
        C5_TORCH_RED_PROMPT,
        out,
        model="gpt-image-1",
        size="1536x1024",
    )
    print(f"OK  {path}")


if __name__ == "__main__":
    main()
