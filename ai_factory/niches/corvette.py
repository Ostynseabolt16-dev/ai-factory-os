"""Corvette t-shirt line — prompts and titles aligned with proven Etsy sales."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CorvetteGeneration:
    code: str
    years: str
    illustrated_stem: str
    typographic_stem: str


# Generations to expand; C5/C6 are live sellers — prioritize gaps + C8.
CORVETTE_GENERATIONS: tuple[CorvetteGeneration, ...] = (
    CorvetteGeneration("C4", "1984-1996", "corvette_c4_illustrated", "corvette_c4_typographic"),
    CorvetteGeneration("C5", "1997-2004", "corvette_c5_illustrated", "corvette_c5_typographic"),
    CorvetteGeneration("C6", "2005-2013", "corvette_c6_illustrated", "corvette_c6_typographic"),
    CorvetteGeneration("C7", "2014-2019", "corvette_c7_illustrated", "corvette_c7_typographic"),
    CorvetteGeneration("C8", "2020-present", "corvette_c8_illustrated", "corvette_c8_typographic"),
)

NICHE = "corvette_classic_car_tee"

# Title patterns from first Etsy sales (Jun 2026).
LISTING_TITLE_ILLUSTRATED = (
    "Corvette {code} Illustrated Car Tee | Classic Sports Car Graphic T-Shirt"
)
LISTING_TITLE_ILLUSTRATED_ALT = "Corvette {code} Sports Car T-Shirt | Classic Car Graphic Tee"
LISTING_TITLE_TYPOGRAPHIC = "Corvette {code} Typographic Tee | Classic American Muscle Shirt"


def illustrated_design_prompt(code: str, years: str) -> str:
    return (
        f"Side-profile illustrated Chevrolet Corvette {code} ({years}) sports car, "
        "clean vector line art, classic American muscle car graphic for t-shirt, "
        "centered composition, limited palette, bold outlines, no text, no mockup, "
        "commercial print-ready automotive illustration"
    )


def typographic_design_prompt(code: str, years: str) -> str:
    return (
        f"Corvette {code} typographic t-shirt design, gothic letter CORVETTE, large {code}, "
        f"production years {years}, short tagline about American muscle, "
        "high contrast monochrome, centered, no car illustration, streetwear automotive"
    )


def listing_title_illustrated(code: str, *, variant: int = 0) -> str:
    template = LISTING_TITLE_ILLUSTRATED if variant == 0 else LISTING_TITLE_ILLUSTRATED_ALT
    return template.format(code=code)


def listing_title_typographic(code: str) -> str:
    return LISTING_TITLE_TYPOGRAPHIC.format(code=code)
