"""Etsy HTML scrape for inspiration — use responsibly (see ToS)."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

# TODO: add retry/backoff, cache responses, and respect Etsy's robots.txt / rate limits.

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

DEFAULT_SEARCH_URL = "https://www.etsy.com/search?q=shirt"


def fetch_etsy_search_titles(
    url: str = DEFAULT_SEARCH_URL,
    *,
    limit: int = 20,
    min_length: int = 5,
) -> list[str]:
    """Return listing title strings from a public Etsy search results page (best-effort)."""
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    titles = soup.find_all("h3")
    out: list[str] = []
    for tag in titles[: limit * 2]:  # scan a bit extra; filter below
        text = tag.get_text(strip=True)
        if len(text) >= min_length:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def print_trend_report(url: str = DEFAULT_SEARCH_URL, *, limit: int = 20) -> None:
    """CLI-style printout matching legacy `trend_finder.py` (one HTTP request)."""
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    print("Status:", response.status_code)

    soup = BeautifulSoup(response.text, "html.parser")
    titles = soup.find_all("h3")
    print("\nTRENDING ETSY SHIRT IDEAS:\n")
    shown = 0
    for tag in titles:
        text = tag.get_text(strip=True)
        if len(text) > 5:
            print("-", text)
            shown += 1
        if shown >= limit:
            break
