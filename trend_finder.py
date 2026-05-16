#!/usr/bin/env python3
"""Scrape public Etsy search titles for inspiration (best-effort; layout may change)."""

# TODO: switch to saved HTML export or Etsy APIs if scraping becomes brittle

from ai_factory.research.etsy_trends import print_trend_report

if __name__ == "__main__":
    print_trend_report()
