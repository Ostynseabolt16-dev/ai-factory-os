#!/usr/bin/env python3
"""Professional polish for c5_variant_B_blackwheels_plate master art."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

REGIONS = {
    "plate": (0.468, 0.538, 0.532, 0.572),
    "windshield": (0.438, 0.402, 0.588, 0.492),
    "headlight_left": (0.378, 0.422, 0.442, 0.502),
    "headlight_right": (0.454, 0.422, 0.514, 0.502),
    "bumper_light_left": (0.325, 0.531, 0.350, 0.542),
    "bumper_light_right": (0.433, 0.536, 0.462, 0.551),
}


def _lum(rgb: np.ndarray) -> np.ndarray:
    return rgb[..., 0].astype(np.float32) + rgb[..., 1] + rgb[..., 2]


def _neutral(rgb: np.ndarray) -> np.ndarray:
    return (rgb.max(axis=-1) - rgb.min(axis=-1)) < 36


def _box(size: tuple[int, int], norm: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    w, h = size
    return (
        max(0, int(norm[0] * w)),
        max(0, int(norm[1] * h)),
        min(w, int(norm[2] * w)),
        min(h, int(norm[3] * h)),
    )


def _mask(h: int, w: int, y0: int, y1: int, x0: int, x1: int, blur: int) -> np.ndarray:
    m = np.zeros((h, w), dtype=np.float32)
    m[y0:y1, x0:x1] = 1.0
    if blur <= 0:
        return m
    img = Image.fromarray((m * 255).astype(np.uint8))
    return np.asarray(img.filter(ImageFilter.GaussianBlur(blur)), dtype=np.float32) / 255.0


def polish_plate(rgba: np.ndarray) -> None:
    h, w = rgba.shape[:2]
    x0, y0, x1, y1 = _box((w, h), REGIONS["plate"])
    mask = _mask(h, w, y0, y1, x0, x1, blur=3)
    rgb = rgba[..., :3].astype(np.float32)

    xx = np.linspace(-1.0, 1.0, max(x1 - x0, 1), dtype=np.float32)[None, :]
    yy = np.linspace(0.0, 1.0, max(y1 - y0, 1), dtype=np.float32)[:, None]
    curve = np.clip(1.0 - np.abs(xx) * 0.7, 0.0, 1.0) * np.clip(1.0 - np.abs(yy - 0.3) * 2.0, 0.0, 1.0)
    target = np.array([10, 11, 13], dtype=np.float32) + np.array([32, 34, 36], dtype=np.float32) * curve[..., None]

    patch = rgb[y0:y1, x0:x1]
    m = mask[y0:y1, x0:x1]
    u8 = np.clip(patch, 0, 255).astype(np.uint8)
    replace = _neutral(u8) & (_lum(u8) >= 60) & (_lum(u8) <= 215)
    for c in range(3):
        patch[..., c] = patch[..., c] * (1.0 - m * replace) + target[..., c] * (m * replace)
    rgba[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)


def polish_windshield(rgba: np.ndarray) -> None:
    h, w = rgba.shape[:2]
    x0, y0, x1, y1 = _box((w, h), REGIONS["windshield"])
    mask = _mask(h, w, y0, y1, x0, x1, blur=4)
    rgb = rgba[..., :3].astype(np.float32)
    patch = rgb[y0:y1, x0:x1]
    m = mask[y0:y1, x0:x1]
    tint = np.array([12, 14, 18], dtype=np.float32)
    u8 = np.clip(patch, 0, 255).astype(np.uint8)
    strength = np.clip((_lum(u8) - 45) / 100.0, 0.0, 1.0) * m * _neutral(u8)
    for c in range(3):
        patch[..., c] = patch[..., c] * (1.0 - strength) + tint[c] * strength
    rgba[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)


def _fill_lights(
    rgba: np.ndarray,
    norm: tuple[float, float, float, float],
    color: tuple[int, int, int],
    *,
    blur: int,
    lum_min: float,
    hard: bool = False,
) -> None:
    h, w = rgba.shape[:2]
    x0, y0, x1, y1 = _box((w, h), norm)
    mask = _mask(h, w, y0, y1, x0, x1, blur=blur)
    patch = rgba[y0:y1, x0:x1]
    m = mask[y0:y1, x0:x1]
    u8 = patch[..., :3]
    lum = _lum(u8)
    if hard:
        sel = m > 0.35
    else:
        sel = m > 0.25
        sel &= (lum >= lum_min) | (patch[..., 3] < 255)
    patch[sel, 0] = color[0]
    patch[sel, 1] = color[1]
    patch[sel, 2] = color[2]
    patch[sel, 3] = 255


def polish_lights(rgba: np.ndarray) -> None:
    _fill_lights(rgba, REGIONS["headlight_left"], (255, 255, 255), blur=2, lum_min=105)
    _fill_lights(rgba, REGIONS["headlight_right"], (255, 255, 255), blur=2, lum_min=105)
    _fill_lights(rgba, REGIONS["bumper_light_left"], (237, 235, 230), blur=0, lum_min=0, hard=True)
    _fill_lights(rgba, REGIONS["bumper_light_right"], (237, 235, 230), blur=0, lum_min=0, hard=True)


def polish_c5_master(image: Image.Image) -> Image.Image:
    rgba = np.array(image.convert("RGBA"))
    polish_plate(rgba)
    polish_windshield(rgba)
    polish_lights(rgba)
    return Image.fromarray(rgba)


def main() -> None:
    parser = argparse.ArgumentParser(description="Polish C5 variant B master car art.")
    parser.add_argument("input", nargs="?", type=Path, default=Path("designs/c5_variant_B_blackwheels_plate.png"))
    parser.add_argument("--backup-dir", type=Path, default=Path("designs/backups"))
    parser.add_argument("--from-backup", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    input_path = args.input if args.input.is_absolute() else repo / args.input
    backup_path = args.backup_dir / f"{input_path.stem}_pre_polish{input_path.suffix}"
    args.backup_dir.mkdir(parents=True, exist_ok=True)
    if not backup_path.exists():
        shutil.copy2(input_path, backup_path)
    if args.from_backup:
        shutil.copy2(backup_path, input_path)

    polished = polish_c5_master(Image.open(input_path))
    polished.save(input_path, format="PNG", optimize=True)
    print(f"OK  polished {input_path}")
    print(f"    backup {backup_path}")


if __name__ == "__main__":
    main()
