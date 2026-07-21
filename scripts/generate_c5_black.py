#!/usr/bin/env python3
"""Generate Black C5 streetwear master — color variant, correct C5 body.

After generation, always run overlay_collection_quote.py (AI quote layout is unreliable).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_factory.generation.openai_image import generate_simple_image_to_file

C5_BLACK_PROMPT = """
Automotive streetwear t-shirt graphic, landscape 3:2, premium Etsy bestseller layout.

BACKGROUND — CRITICAL:
- Pure flat #FFFFFF white background only
- NO cream, NO beige, NO off-white, NO paper texture, NO vignette, NO gradient

STYLE: Smooth photoreal digital render. Clean glossy factory Black paint — deep jet black with soft silver-white edge highlights and natural reflections so the car reads clearly on white (NOT grey, NOT charcoal matte, NOT dark blue-black). Sharp crisp details on the car. NO halftone dots, NO stipple grain, NO newspaper texture on the car body. Distressed weathered texture ONLY on the huge "C5" letters behind the car — NOT on the V8 letters.

LAYOUT (match proven C5/C7 gothic car tee template):
- Huge distressed gothic blackletter "C5" behind the upper half of the car
- Bottom LEFT corner ONLY: solid black gothic "V8" — fully filled letterforms, ONE V8 only
- V8 anchored in the bottom-left 20% of the canvas — below the front wheel, left of the car nose shadow
- NO V8 in the center of the image, NO V8 on the right side, NO V8 near the bottom-right corner, NO duplicate V8 text anywhere
- Leave bottom-RIGHT corner EMPTY white space — NO quote text, NO paragraph, NO small serif text
- Car scaled slightly smaller in frame — generous clear white margin along entire bottom edge and bottom-right corner for text overlay

CRITICAL composition:
- Position car higher in frame with extra empty white space below the rear bumper and behind the rear wheel
- Bottom-right quadrant must stay mostly empty white — quote will be placed there in post-production

CRITICAL V8 typography:
- Exactly ONE "V8" in the entire image — NO second V8, NO third V8
- V8 must be solid filled black gothic letters
- NO strikethrough, NO horizontal line through V or 8, NO cut through letter stems
- NO distressed void or white gap running horizontally through the middle of V8
- The interior of the "8" counter may be white (same as background) but letters must read as solid black shapes

CAR — MUST BE CORRECT GENERATION (1997-2004 C5 Corvette, FRONT-ENGINE):
- Smooth rounded late-90s American sports coupe — long hood, low wide fastback
- Fixed exposed headlights (NOT pop-up headlights — this is a C5 not a C4)
- Wide low stance, curved fenders, integrated rear spoiler lip
- Front three-quarter view facing slightly left, lowered stance
- Entire body painted glossy factory Black — hood, fenders, doors, roof all black with visible silver highlight streaks on hood and fenders
- Chrome/silver machined Z06-style split five-spoke wheels with polished lip — bright reflective rims (NOT black wheels, NOT dark gray wheels)
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
- Smooth continuous reflections on hood and front fender — silver highlight edges must define the silhouette on white background

Centered composition, high contrast for small Etsy thumbnail — black car with bright wheel and body highlights pops on white. No mockup, no t-shirt, no watermark.
""".strip()

DEFAULT_OUT = Path("designs/corvette/c5_black_collection.png")
OVERLAY = ROOT / "scripts/overlay_collection_quote.py"

# Match C5 Torch Red / Yellow C5 messaging — split for 4-line stagger overlay
C5_COLLECTION_LINES = [
    "Low, wide, and unapologetically aggressive.",
    "Where raw American horsepower meets",
    "precision attitude — built to dominate",
    "streets and tracks alike.",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--draft-only", action="store_true")
    parser.add_argument("--skip-overlay", action="store_true", help="Skip quote overlay step")
    args = parser.parse_args()

    out = Path(f"designs/_c5_black_attempt{args.attempt}.png") if args.draft_only else args.out

    path = generate_simple_image_to_file(
        C5_BLACK_PROMPT,
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
                "c5",
                *("--lines", *C5_COLLECTION_LINES),
            ],
            check=True,
            cwd=ROOT,
        )


if __name__ == "__main__":
    main()
