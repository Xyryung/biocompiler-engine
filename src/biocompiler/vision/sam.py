"""Official SAM wire parser; map detections spatially, never by API order."""

import io
import math

import numpy as np
from PIL import Image

from biocompiler.contracts.results import WellMask
from biocompiler.vision.synthetic import encode_rle
from biocompiler.vision.validation import validate_plate_masks


def map_records(records: tuple, image: bytes, labware_id: str) -> tuple[WellMask, ...]:
    from meta_sam_parser import SegmentationMaskRecord, decode_mask_to_raster

    width, height = Image.open(io.BytesIO(image)).size
    detections = [r for r in records if isinstance(r, SegmentationMaskRecord)]
    if len(detections) != 96 or len({r.object_id for r in detections}) != 96:
        raise ValueError("SAM must return exactly 96 distinct well masks")
    detections.sort(key=lambda r: (r.bounds.top + r.bounds.bottom) / 2)
    output = []
    for row in range(8):
        group = sorted(
            detections[row * 12 : (row + 1) * 12],
            key=lambda r: (r.bounds.left + r.bounds.right) / 2,
        )
        centers_y = [(r.bounds.top + r.bounds.bottom) / 2 for r in group]
        if max(centers_y) - min(centers_y) > height / 24:
            raise ValueError("SAM detections do not form an aligned 8 by 12 plate")
        for col, record in enumerate(group):
            bounds = record.bounds
            coordinates = (bounds.left, bounds.top, bounds.right, bounds.bottom)
            if (
                not all(math.isfinite(v) and int(v) == v for v in coordinates)
                or not 0 <= bounds.left < bounds.right <= width
                or not 0 <= bounds.top < bounds.bottom <= height
            ):
                raise ValueError("SAM bounds lie outside the source image")
            x, y = int(bounds.left), int(bounds.top)
            w, h = int(bounds.right - bounds.left), int(bounds.bottom - bounds.top)
            if (record.mask.width, record.mask.height) != (w, h):
                raise ValueError("SAM mask raster dimensions do not match its box")
            raster = np.frombuffer(decode_mask_to_raster(record.mask), dtype=np.uint8)
            raster = raster.reshape(record.mask.height, record.mask.width)
            if not raster.any():
                raise ValueError("SAM returned an empty well mask")
            full = np.zeros((height, width), dtype=bool)
            full[y : y + h, x : x + w] = raster
            output.append(
                WellMask(
                    labware_id=labware_id,
                    well=f"{chr(65 + row)}{col + 1}",
                    width=width,
                    height=height,
                    rle=encode_rle(full),
                )
            )
    result = tuple(output)
    validate_plate_masks(result, labware_id, (width, height))
    return result
