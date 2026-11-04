import base64

import numpy as np
from PIL import ImageDraw

from biocompiler.contracts.results import (
    AdjustmentEvent,
    ColorSample,
    VisionResult,
    WellSeries,
)
from biocompiler.contracts.spec import ExperimentSpec
from biocompiler.providers.base import Provider
from biocompiler.vision.synthetic import TIMES, decode_rle, frame, png
from biocompiler.vision.validation import validate_plate_masks


async def analyze_plate(provider: Provider, spec: ExperimentSpec) -> VisionResult:
    plates = [lw for lw in spec.labware if lw.load_name == "corning_96_wellplate_360ul_flat"]
    if len(plates) != 1:
        raise ValueError("Vision requires exactly one 96-well assay plate")
    plate = plates[0]
    first = frame(0)
    masks = await provider.segment(png(first), plate.id)
    rasters = validate_plate_masks(masks, plate.id, first.size)
    images = [(t, np.asarray(frame(t))) for t in TIMES]
    series = []
    events = []
    active = {
        ref.well for step in spec.steps for ref in step.well_refs if ref.labware_id == plate.id
    }
    for mask, raster in zip(masks, rasters, strict=True):
        samples = []
        for seconds, image in images:
            red, green, blue = image[raster].mean(axis=0)
            samples.append(
                ColorSample(
                    seconds=seconds,
                    red=float(red),
                    green=float(green),
                    blue=float(blue),
                    signal=float((red - blue) / 255),
                )
            )
        series.append(WellSeries(labware_id=plate.id, well=mask.well, samples=tuple(samples)))
        # One event at first crossing. Compare progress since baseline, not raw colour.
        for sample in samples[1:]:
            observed = sample.signal - samples[0].signal
            threshold = 0.5 * sample.seconds / 300
            if mask.well in active and sample.seconds >= 180 and observed < threshold:
                events.append(
                    AdjustmentEvent(
                        labware_id=plate.id,
                        well=mask.well,
                        seconds=sample.seconds,
                        observed=observed,
                        threshold=threshold,
                        suggestion="Review the delayed colour response; "
                        "consider a longer observation window. "
                        "Requires researcher review; no protocol change was applied.",
                    )
                )
                break
    overlay = frame(300)
    draw = ImageDraw.Draw(overlay)
    flagged = {e.well for e in events}
    for mask in masks:
        yy, xx = np.where(decode_rle(mask))
        bounds = (int(xx.min()) - 2, int(yy.min()) - 2, int(xx.max()) + 2, int(yy.max()) + 2)
        color = (255, 168, 82) if mask.well in flagged else (86, 227, 178)
        draw.ellipse(bounds, outline=color, width=2)
        draw.text(
            (bounds[0], bounds[1] + 11),
            mask.well,
            fill=(250, 250, 250),
            stroke_width=1,
            stroke_fill=(10, 20, 30),
        )
    return VisionResult(
        source="synthetic-grid" if provider.name == "mock" else "meta-sam-3.1",
        masks=masks,
        series=tuple(series),
        adjustments=tuple(events),
        overlay_data_url="data:image/png;base64," + base64.b64encode(png(overlay)).decode(),
    )
