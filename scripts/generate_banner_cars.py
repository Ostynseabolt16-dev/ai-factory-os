#!/usr/bin/env python3
"""Generate transparent C5/C6/C7 car PNGs for the Etsy shop banner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_factory.generation.openai_image import generate_simple_image_to_file

BANNER_DIR = ROOT / "designs" / "banner"

BANNER_CAR_BASE = """
Etsy shop banner hero asset — isolated car ONLY on a fully transparent background.

COMPOSITION (flanking cars — C5 and C7):
- Single car, nothing else — NO text, NO letters, NO logos, NO watermark, NO floor shadow, NO ground reflection, NO scenery
- Front three-quarter view, car angled slightly toward the viewer's left
- Car centered with generous transparent padding on all sides (car occupies ~65% of frame height)
- Full vehicle visible: complete front bumper, both visible wheels, full roofline, rear quarter — nothing cut off
- Landscape 3:2 framing

STYLE:
- Smooth photoreal digital render, crisp clean edges
- NO halftone dots, NO stipple grain, NO newspaper texture on paint
- Soft natural highlights, premium automotive catalog quality
- Debadged — NO Chevrolet badges, NO crossed flags, NO Corvette wordmarks, NO license plate

GLASS:
- Windshield, side windows, rear glass: uniform dark smoke tint, solid opaque charcoal-black
- NO grey interior visible, NO checkerboard, NO transparency artifacts in cabin

BUMPER:
- NO license plate, NO plate bracket, NO rectangular plate pocket
""".strip()

C6_FRONT_BASE = """
Etsy shop banner hero asset — isolated car ONLY on a fully transparent background.

COMPOSITION (center hero — straight-on front view):
- Single car, nothing else — NO text, NO letters, NO logos, NO watermark, NO floor shadow, NO ground reflection, NO scenery
- Straight-on front view facing the camera directly — symmetrical grille and headlights, NOT three-quarter, NOT angled
- Car centered with generous transparent padding on all sides (car occupies ~55% of frame width and height)
- Full vehicle visible: complete front bumper, both front wheels, full hood width — nothing cut off
- Landscape 3:2 framing

STYLE:
- Smooth photoreal digital render, crisp clean edges
- NO halftone dots, NO stipple grain, NO newspaper texture on paint
- Soft natural highlights, premium automotive catalog quality
- Debadged — NO Chevrolet badges, NO crossed flags, NO Corvette wordmarks, NO license plate

GLASS:
- Windshield: uniform dark smoke tint, solid opaque charcoal-black
- NO grey interior visible, NO checkerboard, NO transparency artifacts

BUMPER:
- NO license plate, NO plate bracket, NO rectangular plate pocket
""".strip()

C5_PROMPT = f"""
{BANNER_CAR_BASE}

CAR — 1997-2004 Chevrolet Corvette C5:
- Bright glossy Velocity Yellow / Millennium Yellow body paint
- Pop-up headlights in UP position, lenses clean and solid
- Gloss black multi-spoke mesh aftermarket wheels, black rims, lowered stance
- Long hood, rounded C5 body lines, side gills behind front wheels
- Car LARGE and close in frame — occupies ~65% of frame height, not zoomed out or distant
- NO horizon line, NO grey gradient strip, NO edge bar at top of image
""".strip()

C6_PROMPT = f"""
{C6_FRONT_BASE}

CAR — 2005-2013 Chevrolet Corvette C6:
- Glossy Arctic White / pure white body paint with soft subtle reflections
- Fixed exposed headlamps, C6 split grille, hood vents — symmetrical front view
- Gloss black multi-spoke aftermarket wheels, black rims, lowered stance
- Distinct C6 proportions — longer nose than C5, NOT a C7
""".strip()

C7_PROMPT = f"""
{BANNER_CAR_BASE}

CAR — 2014-2019 Chevrolet Corvette C7 Stingray (front-engine, NOT C8):
- Glossy jet black paint with soft silver-white reflections
- Angular C7 LED headlight shape, trapezoidal side intake, center hood vent
- Silver multi-spoke wheels, aggressive front splitter, lowered stance
- Long hood, short rear deck — front-engine C7 proportions
""".strip()

CARS: dict[str, tuple[str, Path]] = {
    "c5": (C5_PROMPT, BANNER_DIR / "etsy_banner_c5_yellow.png"),
    "c6": (C6_PROMPT, BANNER_DIR / "etsy_banner_c6_white.png"),
    "c7": (C7_PROMPT, BANNER_DIR / "etsy_banner_c7_black.png"),
}

PROFILE_C5_PROMPT = """
Etsy shop profile icon — isolated car ONLY on a fully transparent background, square 1:1 composition.

COMPOSITION:
- Single 1997-2004 Corvette C5 ONLY — bright glossy Velocity Yellow / Millennium Yellow paint
- Front three-quarter view, car angled slightly toward viewer's left
- Car centered and LARGE — occupies ~74% of frame height, close premium studio hero shot
- Pop-up headlights UP with clean lenses, gloss black multi-spoke wheels, lowered stance
- Full vehicle visible: front bumper, both wheels, roofline, rear quarter, rear wing — nothing cropped
- NO text, NO logos, NO watermark, NO floor shadow, NO ground reflection, NO horizon line

BODY MODS (must be clearly visible):
- Aggressive aftermarket front splitter — wide carbon-fiber lip extending forward from the front bumper, track-day look, low and sharp but proportional
- Small rear wing / spoiler on the trunk — compact pedestal or ducktail style, subtle not a huge GT wing, clearly visible from this 3/4 angle

STYLE:
- Smooth photoreal digital render, crisp clean edges, premium automotive catalog quality
- Dramatic studio lighting with crisp body highlights and subtle rim light on edges
- NO halftone, NO grain, NO license plate
- Debadged — NO Chevrolet badges, NO crossed flags, NO Corvette wordmarks
- Windshield and glass: dark smoke tint, opaque charcoal-black interior
""".strip()

PROFILE_HERO_OUT = BANNER_DIR / "etsy_profile_c5_hero.png"


def generate_profile_hero(*, force: bool = False) -> Path:
    if PROFILE_HERO_OUT.exists() and not force:
        print(f"Skip profile (exists): {PROFILE_HERO_OUT}")
        return PROFILE_HERO_OUT
    BANNER_DIR.mkdir(parents=True, exist_ok=True)
    path = generate_simple_image_to_file(
        PROFILE_C5_PROMPT,
        PROFILE_HERO_OUT,
        model="gpt-image-1",
        size="1024x1024",
        background="transparent",
    )
    print(f"OK  {path}")
    return path


def generate_car(key: str, *, force: bool = False) -> Path:
    if key not in CARS:
        raise ValueError(f"Unknown car {key!r}; choose from {', '.join(CARS)}")
    prompt, out = CARS[key]
    if out.exists() and not force:
        print(f"Skip {key} (exists): {out}")
        return out
    BANNER_DIR.mkdir(parents=True, exist_ok=True)
    path = generate_simple_image_to_file(
        prompt,
        out,
        model="gpt-image-1",
        size="1536x1024",
        background="transparent",
    )
    print(f"OK  {path}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--car",
        choices=[*CARS, "all"],
        default="all",
        help="Which banner car to generate (default: all)",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Generate 1024×1024 profile hero (yellow C5)",
    )
    parser.add_argument("--force", action="store_true", help="Regenerate even if file exists")
    args = parser.parse_args()

    if args.profile:
        generate_profile_hero(force=args.force)
        return

    keys = list(CARS) if args.car == "all" else [args.car]
    for key in keys:
        generate_car(key, force=args.force)


if __name__ == "__main__":
    main()
