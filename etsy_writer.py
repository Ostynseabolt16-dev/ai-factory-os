#!/usr/bin/env python3
"""Etsy listing text helper — wires to `ai_factory.listings` when you add LLM templates."""

# TODO: print JSON or clipboard-friendly block for pasting into Etsy

from ai_factory.listings.etsy_copy import draft_listing_from_idea

if __name__ == "__main__":
    idea = input("Design / niche idea for listing: ")
    payload = draft_listing_from_idea(idea)
    print(payload)
