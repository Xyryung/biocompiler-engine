"""Deterministic 96-well imagery, with known geometry and a delayed well.

All pixels are generated here; no third-party photographs or model predictions.
"""

import io
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

from biocompiler.contracts.results import WellMask

WIDTH, HEIGHT = 640, 440
RADIUS, SPACING = 15, 44
TIMES = tuple(float(t) for t in range(0, 301, 30))


def center(row: int, col: int) -> tuple[int, int]:
    return 78 + col * SPACING, 66 + row * SPACING


def encode_rle(mask: np.ndarray) -> tuple[int, ...]:
    flat = mask.ravel().astype(bool)
    changes = np.flatnonzero(flat[1:] != flat[:-1]) + 1
    runs = np.diff(np.concatenate(([0], changes, [flat.size]))).tolist()
    if flat[0]:
        runs.insert(0, 0)
    return tuple(runs)


def decode_rle(mask: WellMask) -> np.ndarray:
    if any(n < 0 for n in mask.rle) or sum(mask.rle) != mask.width * mask.height:
        raise ValueError("Invalid mask run lengths")
    values = np.arange(len(mask.rle)) % 2
    return np.repeat(values, mask.rle).reshape(mask.height, mask.width).astype(bool)


@lru_cache(maxsize=8)
def grid_masks(labware_id: str) -> tuple[WellMask, ...]:
    yy, xx = np.ogrid[:HEIGHT, :WIDTH]
    masks = []
    for row in range(8):
        for col in range(12):
            x, y = center(row, col)
            raster = (xx - x) ** 2 + (yy - y) ** 2 <= (RADIUS - 2) ** 2
            masks.append(
                WellMask(
                    labware_id=labware_id,
                    well=f"{chr(65 + row)}{col + 1}",
                    width=WIDTH,
                    height=HEIGHT,
                    rle=encode_rle(raster),
                )
            )
    return tuple(masks)


def frame(seconds: float) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), (17, 27, 39))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (35, 30, 622, 418), 18, fill=(32, 47, 62), outline=(80, 103, 120), width=2
    )
    for row in range(8):
        for col in range(12):
            x, y = center(row, col)
            # A3 intentionally lags; other wells provide a normal progression.
            rate = 0.10 if (row, col) == (0, 2) else 0.75 + ((row + col) % 4) * 0.05
            progress = min(seconds / 300, 1) * rate
            color = (int(45 + 185 * progress), int(100 + 95 * progress), int(190 - 145 * progress))
            draw.ellipse(
                (x - RADIUS, y - RADIUS, x + RADIUS, y + RADIUS),
                fill=color,
                outline=(100, 125, 142),
            )
    for col in range(12):
        draw.text((center(0, col)[0] - 5, 40), str(col + 1), fill=(205, 217, 228))
    for row in range(8):
        draw.text((48, center(row, 0)[1] - 5), chr(65 + row), fill=(205, 217, 228))
    draw.text(
        (38, 423), f"SYNTHETIC DATA  |  {int(seconds):03d}s  |  fixed camera", fill=(190, 205, 216)
    )
    return image


def png(image: Image.Image) -> bytes:
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()
