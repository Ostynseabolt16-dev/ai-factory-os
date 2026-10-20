#!/usr/bin/env python3
"""Remove edge-connected near-black background from POD PNGs (keeps interior blacks)."""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

from PIL import Image


def knockout(path: Path, *, threshold: int = 15) -> Path:
    im = Image.open(path).convert("RGBA")
    px = im.load()
    w, h = im.size
    seen: set[tuple[int, int]] = set()
    q: deque[tuple[int, int]] = deque()

    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))

    while q:
        x, y = q.popleft()
        if (x, y) in seen or x < 0 or y < 0 or x >= w or y >= h:
            continue
        seen.add((x, y))
        r, g, b, a = px[x, y]
        if a == 0 or r > threshold or g > threshold or b > threshold:
            continue
        px[x, y] = (r, g, b, 0)
        q.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

    im.save(path)
    return path


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        knockout(Path(arg))
        print(f"Updated: {arg}")
