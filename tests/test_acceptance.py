import json

import httpx2
import pytest

from biocompiler.acceptance import verify_planning, verify_stages
from biocompiler.contracts.results import SimulationResult
from biocompiler.providers.mock import MockProvider
from biocompiler.vision.synthetic import grid_masks
from tests.meta_http import MetaHTTP


class SuccessfulSimulator:
    async def simulate(self, code):
        return SimulationResult(
            success=True, stdout="Test simulation", backend="local-opentrons", duration_ms=0
        )


async def test_classifier_outage_is_not_accepted_as_a_live_refusal():
    class UnavailableRefusal(MockProvider):
        async def classify(self, goal, spec=None):
            if "clinical" in goal:
                raise RuntimeError("classifier unavailable")
            return await super().classify(goal, spec)

    with pytest.raises(RuntimeError, match="unavailable"):
        await verify_planning(UnavailableRefusal())


async def test_acceptance_keeps_passed_stage_and_can_retry_only_the_failed_one(tmp_path):
    class BadVision(MockProvider):
        async def segment(self, image, labware_id):
            original = grid_masks(labware_id)
            return tuple(original[0].model_copy(update={"well": m.well}) for m in original)

    report = await verify_stages(
        BadVision(), SuccessfulSimulator(), tmp_path, stages=("planning", "vision")
    )
    assert report["status"] == "failed"
    assert report["stages"]["planning"]["status"] == "passed"
    assert report["stages"]["vision"]["status"] == "failed"
    assert report["live"] is False
    planning = (tmp_path / "meta-planning.json").read_bytes()
    retry = await verify_stages(MockProvider(), SuccessfulSimulator(), tmp_path, stages=("vision",))
    assert retry["status"] == "passed"
    assert (tmp_path / "meta-planning.json").read_bytes() == planning
    assert json.loads((tmp_path / "meta-vision.json").read_text())["status"] == "passed"


async def test_invalid_key_stops_extra_model_calls_and_reports_safe_error(tmp_path):
    server = MetaHTTP()
    server.replies.append(httpx2.Response(401, json={"error": {"message": "secret-in-error-body"}}))
    provider = server.provider()
    try:
        result = await verify_stages(provider, SuccessfulSimulator(), tmp_path)
        assert result["status"] == "failed" and len(server.requests) == 1
        assert result["stages"]["planning"]["error"]["http_status"] == 401
        assert result["stages"]["compiler"]["status"] == "skipped"
        assert result["stages"]["vision"]["status"] == "skipped"
        assert "secret-in-error-body" not in json.dumps(result)
    finally:
        await provider.client.close()
