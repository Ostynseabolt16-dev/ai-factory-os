#!/usr/bin/env python3
"""Render a clean side-profile C8 line-art PNG for POD (no API)."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_factory.config import DESIGNS_DIR, PROJECT_ROOT

OUT = DESIGNS_DIR / "corvette_c8_illustrated.png"
SIZE = 2048
INK = (24, 28, 34, 255)
INK_MID = (70, 76, 86, 200)
ACCENT = (196, 30, 45, 255)


_BOUNDS = (0.05, 0.35, 0.96, 0.86)  # min_x, min_y, max_x, max_y for all artwork


def _scale(points: list[tuple[float, float]], w: int, h: int, margin: float = 0.08) -> list[tuple[int, int]]:
    """Map normalized coords into the canvas using fixed art bounds (not per-call bbox)."""
    min_x, min_y, max_x, max_y = _BOUNDS
    span_x = max_x - min_x
    span_y = max_y - min_y
    inner_w = w * (1 - 2 * margin)
    inner_h = h * (1 - 2 * margin)
    scale = min(inner_w / span_x, inner_h / span_y)
    off_x = (w - span_x * scale) / 2 - min_x * scale
    off_y = (h - span_y * scale) / 2 - min_y * scale + h * 0.02
    return [(int(x * scale + off_x), int(y * scale + off_y)) for x, y in points]


def _outline(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], color, width: int) -> None:
    closed = points + [points[0]]
    for i in range(len(closed) - 1):
        draw.line([closed[i], closed[i + 1]], fill=color, width=width)


def render_c8_side_profile() -> Path:
    """C8 side profile facing right — line-art for light shirts."""
    silhouette = [
        (0.06, 0.76), (0.05, 0.70), (0.06, 0.64), (0.10, 0.58), (0.16, 0.53), (0.24, 0.49),
        (0.34, 0.46), (0.42, 0.43), (0.48, 0.39), (0.54, 0.36), (0.62, 0.35), (0.70, 0.36),
        (0.78, 0.39), (0.85, 0.44), (0.90, 0.50), (0.94, 0.57), (0.96, 0.64), (0.96, 0.72),
        (0.93, 0.78), (0.86, 0.82), (0.76, 0.84), (0.62, 0.85), (0.46, 0.85), (0.30, 0.84),
        (0.18, 0.81), (0.10, 0.78),
    ]
    glass = [
        (0.34, 0.46), (0.42, 0.39), (0.52, 0.35), (0.64, 0.34), (0.74, 0.37), (0.80, 0.43), (0.82, 0.48),
    ]
    intake = [(0.56, 0.48), (0.64, 0.46), (0.66, 0.52), (0.58, 0.54), (0.56, 0.48)]

    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    stroke = max(18, SIZE // 64)
    thin = max(8, SIZE // 128)

    sil = _scale(silhouette, SIZE, SIZE)
    _outline(draw, sil, INK, stroke)

    _outline(draw, _scale(intake, SIZE, SIZE), INK_MID, thin)
    draw.line(_scale(glass, SIZE, SIZE), fill=INK_MID, width=thin, joint="curve")

    for cx, cy, r_norm in ((0.22, 0.84, 0.058), (0.78, 0.84, 0.060)):
        x, y = _scale([(cx, cy)], SIZE, SIZE)[0]
        r = int(r_norm * SIZE)
        draw.ellipse((x - r, y - r, x + r, y + r), outline=INK, width=stroke)
        ir = int(r * 0.42)
        draw.ellipse((x - ir, y - ir, x + ir, y + ir), outline=INK_MID, width=thin)

    draw.line(_scale([(0.91, 0.52), (0.94, 0.56)], SIZE, SIZE), fill=ACCENT, width=thin + 2)
    draw.line(_scale([(0.07, 0.70), (0.08, 0.74)], SIZE, SIZE), fill=ACCENT, width=thin + 2)

    DESIGNS_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG")
    return OUT.resolve()


if __name__ == "__main__":
    path = render_c8_side_profile()
    print(f"Saved: {path.relative_to(PROJECT_ROOT.resolve())}")
