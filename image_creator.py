#!/usr/bin/env python3
"""
CLI: interactive kawaii PNG → `designs/` (legacy entrypoint).

Implementation lives in `ai_factory.generation` for reuse by batch jobs and agents.
"""

# TODO: add argparse for non-interactive runs: --idea "..." --out-dir designs/

from ai_factory.generation.openai_image import generate_kawaii_design_to_designs

if __name__ == "__main__":
    idea = input("Design idea: ")
    path = generate_kawaii_design_to_designs(idea)
    print(f"Image saved as {path}")