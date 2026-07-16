#!/usr/bin/env python3
"""Generate Atomic Orange C6 streetwear master — color variant, correct C6 body.

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

C6_ATOMIC_ORANGE_PROMPT = """
Automotive streetwear t-shirt graphic, landscape 3:2, premium Etsy bestseller layout.

BACKGROUND — CRITICAL:
- Pure flat #FFFFFF white background only
- NO cream, NO beige, NO off-white, NO paper texture, NO vignette, NO gradient

STYLE: Smooth photoreal digital render. Clean glossy factory Atomic Orange paint — vivid bright orange with warm red undertone, high-impact Corvette factory color (NOT yellow, NOT rust, NOT copper brown). Sharp crisp details on the car. NO halftone dots, NO stipple grain, NO newspaper texture on the car body. Distressed weathered texture ONLY on the huge "C6" letters behind the car — NOT on the V8 letters.

LAYOUT (match proven C6/C7 gothic car tee template):
- Huge distressed gothic blackletter "C6" behind the upper half of the car
- Bottom LEFT corner ONLY: solid black gothic "V8" — fully filled letterforms, ONE V8 only
- V8 anchored in the bottom-left 20% of the canvas — below the front wheel, left of the car nose shadow
- NO V8 in the center of the image, NO V8 on the right side, NO V8 near the bottom-right corner, NO duplicate V8 text anywhere
- Leave bottom-RIGHT corner EMPTY white space — NO quote text, NO paragraph, NO small serif text
- Car scaled slightly smaller in frame — generous clear white margin along entire bottom edge and bottom-right corner for text overlay

CRITICAL composition:
- Position car higher in frame with extra empty white space below the rear bumper and behind the rear wheel
- Bottom-right quadrant must stay mostly empty white — quote will be placed there in post-production

CRITICAL V8 placement — ONE V8 ONLY:
- Exactly ONE "V8" in the entire image — NO second V8, NO third V8, NO V8 under the car center, NO V8 between wheels
- V8 locked to bottom-LEFT corner only (left edge of canvas, below front bumper)
- The center and bottom-right of the image must contain ZERO V8 letters — only white background there
- V8 must be solid filled black gothic letters
- NO strikethrough, NO horizontal line through V or 8, NO cut through letter stems
- NO distressed void or white gap running horizontally through the middle of V8
- The interior of the "8" counter may be white (same as background) but letters must read as solid black shapes

CAR — MUST BE CORRECT GENERATION (2005-2013 C6, FRONT-ENGINE):
- Long hood and short rear deck (this is NOT a mid-engine C8)
- Exposed sharp C6 headlights, muscular fender curves, coupe body
- Front three-quarter view facing slightly left, lowered stance
- Entire body painted glossy Atomic Orange — hood, fenders, doors, roof all orange
- Chrome/silver machined Spyder-style wide split five-spoke wheels with polished lip — bright reflective rims (NOT black wheels, NOT dark gray wheels)
- Small gloss BLACK rear lip spoiler on the decklid — carbon-black or gloss black wing, clearly black (NOT orange, NOT body color, NOT painted to match body)
- Smooth debadged nose — NO emblem, NO badge, NO crossed flags, NO logo blob on hood or bumper
- NO side fender badges, NO Corvette wordmarks on body, NO Chevrolet bowtie anywhere
- Subtle low-profile gloss black front splitter lip under the bumper — clean straight edge, OEM+ track style

CRITICAL front bumper:
- NO license plate, NO plate bracket, NO rectangular plate pocket, NO plate filler panel
- Open mesh grille and clean continuous lower valance with integrated black splitter lip

CRITICAL glass:
- Windshield and side windows: uniform dark smoke tint, solid opaque grey-black
- NO checkerboard pattern, NO transparency grid, NO grey flat placeholder inside cabin

CRITICAL body quality:
- NO motion blur, NO horizontal smear, NO clone artifacts on fenders
- Smooth continuous reflections on hood and front fender

Centered composition, high contrast for small Etsy thumbnail — orange car pops on white. No mockup, no t-shirt, no watermark.
""".strip()

DEFAULT_OUT = Path("designs/c6_atomic_orange_collection.png")
OVERLAY = ROOT / "scripts/overlay_collection_quote.py"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--draft-only", action="store_true")
    parser.add_argument("--skip-overlay", action="store_true", help="Skip quote overlay step")
    args = parser.parse_args()

    out = Path(f"designs/_c6_atomic_orange_attempt{args.attempt}.png") if args.draft_only else args.out

    path = generate_simple_image_to_file(
        C6_ATOMIC_ORANGE_PROMPT,
        out,
        model="gpt-image-1",
        size="1536x1024",
    )
    print(f"OK  {path}")

    if not args.draft_only and not args.skip_overlay:
        subprocess.run(
            [sys.executable, str(OVERLAY), str(path), "--gen", "c6"],
            check=True,
            cwd=ROOT,
        )


if __name__ == "__main__":
    main()
