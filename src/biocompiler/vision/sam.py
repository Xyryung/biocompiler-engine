"""Official SAM wire parser; map detections spatially, never by API order."""

import io

import numpy as np
from PIL import Image

from biocompiler.contracts.results import WellMask
from biocompiler.vision.synthetic import encode_rle


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
            raster = np.frombuffer(decode_mask_to_raster(record.mask), dtype=np.uint8)
            raster = raster.reshape(record.mask.height, record.mask.width)
            full = np.zeros((height, width), dtype=bool)
            x, y = int(record.bounds.left), int(record.bounds.top)
            h, w = raster.shape
            if raster.shape == full.shape:
                full = raster.astype(bool)
            elif x < 0 or y < 0 or x + w > width or y + h > height:
                raise ValueError("SAM mask lies outside the image")
            else:
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
    return tuple(output)
