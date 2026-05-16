#!/usr/bin/env python3
"""
Minimal one-off image generation → `shirt_design.png` in the current working directory.

Kept separate from `image_creator.py` so you can use a simpler prompt without the kawaii style block.
"""

# TODO: merge with `image_creator` via flags once you standardize output naming

from pathlib import Path

from ai_factory.generation.openai_image import generate_simple_image_to_file

if __name__ == "__main__":
    prompt = input("Describe shirt image: ")
    out = Path("shirt_design.png")
    generate_simple_image_to_file(prompt, out)
    print(f"Image saved as {out}")
