import json
from dataclasses import replace

import httpx
import numpy as np
import pytest
from meta_sam_parser import CompletedOutcome, image_segmentation_format
from pydantic import ValidationError

from biocompiler.bio.protein import predict_reference
from biocompiler.config import Settings
from biocompiler.contracts.results import SafetyDecision
from biocompiler.contracts.spec import ExperimentSpec
from biocompiler.fixtures import fixture_spec, fixture_text
from biocompiler.providers.meta import MetaProvider, strict_schema
from biocompiler.providers.mock import MockProvider
from biocompiler.vision.analysis import analyze_plate
from biocompiler.vision.sam import map_records
from biocompiler.vision.synthetic import decode_rle, encode_rle, frame, grid_masks, png


def test_packaged_and_test_fixtures_agree():
    from pathlib import Path

    for name in ("minimal", "realistic", "broken"):
        assert fixture_text(name) == Path(f"tests/fixtures/{name}.json").read_text(encoding="utf-8")
    with pytest.raises(ValidationError, match="unknown labware"):
        fixture_spec("broken")


def test_deep_immutability_and_finite_volumes():
    spec = fixture_spec()
    assert isinstance(spec.steps, tuple)
    with pytest.raises(ValidationError):
        spec.steps[0].volume_ul = 1
    payload = spec.model_dump(mode="json")
    payload["steps"][0]["volume_ul"] = float("nan")
    with pytest.raises(ValidationError):
        ExperimentSpec.model_validate(payload)


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("volume_ul", 301, "pipette range"),
        ("volume_ul", 5, "pipette range"),
    ],
)
def test_pipette_ranges(field, value, message):
    payload = fixture_spec().model_dump(mode="json")
    payload["steps"][0][field] = value
    with pytest.raises(ValidationError, match=message):
        ExperimentSpec.model_validate(payload)


async def test_offline_vision_stable_96_wells_and_threshold():
    provider = MockProvider()
    first = await provider.segment(png(frame(0)), "assay_plate")
    last = await provider.segment(png(frame(300)), "assay_plate")
    assert first == last and len(first) == 96
    assert {m.well for m in first} == {f"{r}{c}" for r in "ABCDEFGH" for c in range(1, 13)}
    for mask in first:
        assert encode_rle(decode_rle(mask)) == mask.rle
    result = await analyze_plate(provider, fixture_spec())
    assert len(result.series[0].samples) == 11
    assert result.series[0].samples[-1].signal > result.series[0].samples[0].signal
    assert [(e.well, e.seconds) for e in result.adjustments] == [("A3", 180)]
    assert result.overlay_data_url.startswith("data:image/png;base64,")


def test_invalid_rle_rejected():
    bad = grid_masks("plate")[0].model_copy(update={"rle": (10,)})
    with pytest.raises(ValueError, match="run lengths"):
        decode_rle(bad)


def test_sam_uses_spatial_mapping_for_shuffled_ids():
    from meta_sam_parser import SegmentationMaskRecord

    parser = image_segmentation_format().create_parser()
    parser.push(
        "<0f>51<|box;x1=1;y1=1;x2=5;y2=5;w=640;h=440|><|mask;x=0;y=0;data=5,5,!!!!!(QO(0lu8?|>\n"
    )
    result = parser.finish(CompletedOutcome()).result
    mask = next(r for r in result.records if isinstance(r, SegmentationMaskRecord))
    records = []
    for row in range(8):
        for col in range(12):
            bounds = replace(
                mask.bounds,
                left=60 + col * 44,
                right=65 + col * 44,
                top=50 + row * 44,
                bottom=55 + row * 44,
            )
            records.append(replace(mask, object_id=str(1000 - row * 12 - col), bounds=bounds))
    np.random.default_rng(42).shuffle(records)
    mapped = map_records(tuple(records), png(frame(0)), "plate")
    assert mapped[0].well == "A1" and mapped[-1].well == "H12"
    yy, xx = np.where(decode_rle(mapped[0]))
    assert 60 <= xx.min() <= xx.max() < 65 and 50 <= yy.min() <= yy.max() < 55
    with pytest.raises(ValueError, match="exactly 96"):
        map_records(tuple(records[:-1]), png(frame(0)), "plate")


async def test_meta_adapter_uses_installed_sdk_and_strict_wire_schema(monkeypatch):
    provider = MetaProvider(Settings(_env_file=None, meta_api_key="not-a-real-key"))
    calls = []
    from types import SimpleNamespace

    async def create(**kwargs):
        calls.append(kwargs)
        content = json.dumps({"decision": "allow", "reason": "in-domain"})
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content, refusal=None))]
        )

    monkeypatch.setattr(provider.client.chat.completions, "create", create)
    assert (await provider.classify("PET enzyme assay")).decision == "allow"
    wire = calls[0]
    assert wire["model"] == "muse-spark-1.3"
    assert wire["response_format"]["json_schema"]["strict"] is True
    assert strict_schema(SafetyDecision)["additionalProperties"] is False
    assert "oneOf" not in json.dumps(strict_schema(ExperimentSpec))
    await provider.client.close()


async def test_protein_endpoint_reference_and_provenance(monkeypatch):
    offline = await predict_reference(Settings(_env_file=None))
    assert offline.source == "cached-esmfold" and offline.cached
    assert offline.structure_pdb and offline.residue_count == 290
    assert offline.cache_lookup_ms >= 0 and offline.latency_ms > 0
    calls = []

    async def post(self, url, **kwargs):
        calls.append(kwargs)
        assert len(kwargs["json"]["sequence"]) == 290
        return httpx.Response(
            200,
            json={"model": "esmfold-v1", "structure_pdb": offline.structure_pdb},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    settings = Settings(
        _env_file=None, protein_endpoint="https://example.test/predict", protein_api_key="test"
    )
    result = await predict_reference(settings)
    assert result.status == "predicted" and result.latency_ms >= 0
    assert result.cost_usd is None
    assert calls[0]["headers"]["Authorization"] == "Bearer test"


async def test_remote_errors_do_not_leak_secrets(client=None):
    # Adapter validation fails before sending credentials to an insecure endpoint.
    with pytest.raises(ValueError, match="HTTPS"):
        await predict_reference(
            Settings(
                _env_file=None, protein_endpoint="http://example.test", protein_api_key="secret"
            )
        )
