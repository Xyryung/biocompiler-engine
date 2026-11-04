import re

import pytest

from biocompiler.fixtures import fixture_spec
from biocompiler.providers.mock import MockProvider
from biocompiler.vision.analysis import analyze_plate
from biocompiler.vision.synthetic import HEIGHT, WIDTH, frame, grid_masks, png
from biocompiler.vision.validation import validate_plate_masks
from tests.meta_http import MetaHTTP, sam_plate_text, segmentation


def test_duplicate_masks_cannot_impersonate_96_separate_wells():
    original = grid_masks("plate")
    duplicates = tuple(original[0].model_copy(update={"well": m.well}) for m in original)
    with pytest.raises(ValueError, match="overlap or duplicate"):
        validate_plate_masks(duplicates, "plate", (WIDTH, HEIGHT))


def test_well_names_must_follow_their_physical_rows_and_columns():
    original = list(grid_masks("plate"))
    original[0] = original[0].model_copy(update={"well": "A2"})
    original[1] = original[1].model_copy(update={"well": "A1"})
    with pytest.raises(ValueError, match="ordered|labels"):
        validate_plate_masks(tuple(original), "plate", (WIDTH, HEIGHT))


@pytest.mark.parametrize(
    "change,message",
    [
        ({"rle": (WIDTH * HEIGHT,)}, "Empty"),
        ({"width": WIDTH - 1}, "dimensions"),
        ({"labware_id": "wrong-plate"}, "declared assay plate"),
    ],
)
def test_invalid_masks_are_rejected_before_colour_measurement(change, message):
    masks = list(grid_masks("plate"))
    masks[0] = masks[0].model_copy(update=change)
    with pytest.raises(ValueError, match=message):
        validate_plate_masks(tuple(masks), "plate", (WIDTH, HEIGHT))


async def test_pipeline_refuses_repeated_regions_even_from_a_custom_provider():
    class InvalidProvider(MockProvider):
        async def segment(self, image, labware_id):
            original = grid_masks(labware_id)
            return tuple(original[0].model_copy(update={"well": m.well}) for m in original)

    with pytest.raises(ValueError, match="overlap or duplicate"):
        await analyze_plate(InvalidProvider(), fixture_spec())


@pytest.mark.parametrize("corruption", ["duplicate", "wrong-raster-size", "out-of-bounds"])
async def test_real_sam_stream_rejects_invalid_detection_geometry(corruption):
    text = sam_plate_text()
    boxes = re.findall(r"<\|box;.*?\|>", text)
    if corruption == "duplicate":
        replacement = boxes[1]
    elif corruption == "wrong-raster-size":
        replacement = re.sub(r"x2=(\d+)", lambda m: f"x2={int(m[1]) + 1}", boxes[0])
    else:
        replacement = re.sub(r"x2=\d+", f"x2={WIDTH + 20}", boxes[0])
    server = MetaHTTP()
    response, body = segmentation(text.replace(boxes[0], replacement, 1))
    server.replies.append(response)
    provider = server.provider()
    try:
        with pytest.raises(ValueError):
            await provider.segment(png(frame(0)), "plate")
        assert body.closed
    finally:
        await provider.client.close()
