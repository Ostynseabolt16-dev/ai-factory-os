#!/usr/bin/env python3
"""Recover streetwear PNGs from Cursor assets → designs/ → Printify-ready."""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections import deque
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path.home() / ".cursor/projects/Users-ostynseabolt-ai/assets"
DESIGNS = PROJECT_ROOT / "designs"
PREPARE = PROJECT_ROOT / "scripts/prepare_printify.py"
KNOCKOUT = PROJECT_ROOT / "scripts/knockout_connected_black_background.py"
# (source in assets, dest stem, color_mode)
# color_mode: mono = solid black POD export, color = keep car color, back = typographic back
RECOVER: list[tuple[str, str, str]] = [
    ("corvette_c5_streetwear_design.png", "corvette_c5_streetwear_design", "mono"),
    ("corvette_c5_yellow_streetwear_design.png", "corvette_c5_yellow_streetwear_design", "color"),
    ("corvette_c6_streetwear_design.png", "corvette_c6_streetwear_design", "mono"),
    ("corvette_c7_streetwear_design.png", "corvette_c7_streetwear_design", "mono"),
    ("corvette_c8_streetwear_design.png", "corvette_c8_streetwear_design", "mono"),
    ("corvette_c8_streetwear_back_design.png", "corvette_c8_streetwear_back_design", "back"),
    ("mustang_gt_streetwear_design.png", "mustang_gt_streetwear_design", "mono"),
    ("supra_mk4_streetwear_design.png", "supra_mk4_streetwear_design", "mono"),
    ("challenger_srt_streetwear_design.png", "challenger_srt_streetwear_design", "mono"),
    ("cab4dbf7-ea2d-46da-9dbb-b605a939a449.png", "skyline_r34_streetwear_design", "mono"),
]


def _corner_rgb(path: Path) -> tuple[int, int, int]:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    samples = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    return tuple(sum(c[i] for c in samples) // 4 for i in range(3))


def _is_bg(r: int, g: int, b: int) -> bool:
    avg = (r + g + b) / 3
    spread = max(r, g, b) - min(r, g, b)
    return avg > 175 and spread < 25


def _remove_checkerboard(path: Path) -> int:
    """Original 2-pass checkerboard removal: edge flood + global is_bg wipe."""
    im = Image.open(path).convert("RGBA")
    px = im.load()
    w, h = im.size
    transparent = [[False] * w for _ in range(h)]
    visited = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    for x in range(w):
        for y in (0, h - 1):
            if _is_bg(*px[x, y][:3]):
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if _is_bg(*px[x, y][:3]):
                q.append((x, y))

    while q:
        x, y = q.popleft()
        if x < 0 or x >= w or y < 0 or y >= h or visited[y][x]:
            continue
        if not _is_bg(*px[x, y][:3]):
            continue
        visited[y][x] = True
        transparent[y][x] = True
        q.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

    removed = 0
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            if transparent[y][x] or _is_bg(r, g, b):
                px[x, y] = (r, g, b, 0)
                removed += 1

    im.save(path)
    return removed


def _header_pure_white_count(path: Path) -> int:
    im = Image.open(path).convert("RGBA")
    px = im.load()
    w, h = im.size
    header_h = int(h * 0.42)
    return sum(
        1
        for y in range(header_h)
        for x in range(w)
        if px[x, y][3] > 0 and px[x, y][0] > 240 and px[x, y][1] > 240 and px[x, y][2] > 240
    )


def _process_transparency(path: Path, mode: str) -> str:
    r, g, b = _corner_rgb(path)
    avg = (r + g + b) / 3

    if avg > 128:
        n = _remove_checkerboard(path)
        return f"2-pass checkerboard removed ({n} px)"

    subprocess.run([sys.executable, str(KNOCKOUT), str(path)], check=True)
    return "black edge knockout"


def _prepare_printify(src: Path, dest: Path) -> None:
    subprocess.run(
        [sys.executable, str(PREPARE), str(src), "-o", str(dest)],
        check=True,
    )


def main() -> int:
    if not ASSETS.exists():
        print(f"Assets folder not found: {ASSETS}", file=sys.stderr)
        return 1

    DESIGNS.mkdir(parents=True, exist_ok=True)
    results: list[str] = []

    for src_name, stem, mode in RECOVER:
        src = ASSETS / src_name
        if not src.exists():
            print(f"SKIP missing: {src_name}")
            continue

        dest = DESIGNS / f"{stem}.png"
        shutil.copy2(src, dest)
        step = _process_transparency(dest, mode)

        header_white = _header_pure_white_count(dest)
        if header_white != 0:
            print(f"FAIL {stem}: header pure white = {header_white}", file=sys.stderr)
            return 1

        printify_out = DESIGNS / f"{stem}_UPLOAD_TO_PRINTIFY.png"
        _prepare_printify(dest, printify_out)
        results.append(f"  {stem}.png + {printify_out.name} ({step}, header_white=0)")

    print("\nRecovered:")
    print("\n".join(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
