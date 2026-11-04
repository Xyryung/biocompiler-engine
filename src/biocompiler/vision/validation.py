"""Validate the aligned plate geometry before measuring any colour signal."""

import numpy as np

from biocompiler.contracts.results import WellMask
from biocompiler.vision.synthetic import decode_rle


def validate_plate_masks(
    masks: tuple[WellMask, ...], labware_id: str, size: tuple[int, int]
) -> tuple[np.ndarray, ...]:
    expected = {f"{row}{col}" for row in "ABCDEFGH" for col in range(1, 13)}
    if (
        len(masks) != 96
        or {mask.well for mask in masks} != expected
        or any(mask.labware_id != labware_id for mask in masks)
    ):
        raise ValueError("Segmentation must map all 96 wells to the declared assay plate")
    width, height = size
    occupied = np.zeros((height, width), dtype=bool)
    centers = np.zeros((8, 12, 2), dtype=float)
    rasters = []
    for mask in masks:
        if (mask.width, mask.height) != size:
            raise ValueError("Well mask dimensions do not match the source image")
        raster = decode_rle(mask)
        area = int(raster.sum())
        if not area:
            raise ValueError("Empty well mask")
        if int(np.logical_and(occupied, raster).sum()) / area > 0.05:
            raise ValueError("Well masks overlap or duplicate the same region")
        occupied |= raster
        yy, xx = np.where(raster)
        row, col = ord(mask.well[0]) - ord("A"), int(mask.well[1:]) - 1
        centers[row, col] = (float(xx.mean()), float(yy.mean()))
        rasters.append(raster)
    columns = np.median(centers[:, :, 0], axis=0)
    rows = np.median(centers[:, :, 1], axis=1)
    for axis in (columns, rows):
        gaps = np.diff(axis)
        spacing = float(np.median(gaps))
        if spacing <= 1 or np.any(gaps < spacing * 0.5) or np.any(gaps > spacing * 1.5):
            raise ValueError("Wells must form an ordered, uniformly spaced 8 by 12 grid")
    if np.any(np.abs(centers[:, :, 0] - columns) > np.median(np.diff(columns)) * 0.25) or np.any(
        np.abs(centers[:, :, 1] - rows[:, None]) > np.median(np.diff(rows)) * 0.25
    ):
        raise ValueError("Well labels do not match the aligned plate rows and columns")
    return tuple(rasters)
