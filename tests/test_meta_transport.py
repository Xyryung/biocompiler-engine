import base64
import json

import httpx2
import pytest
from jsonschema import Draft202012Validator
from meta_sam_parser import ResponsesStreamError
from openai import AuthenticationError
from pydantic import ValidationError

from biocompiler.bio.planner import plan_experiment
from biocompiler.bio.safety import SafetyRefusal, require_safe
from biocompiler.compiler.codegen import render_protocol
from biocompiler.compiler.extract import extract_code
from biocompiler.compiler.healing import compile_and_heal
from biocompiler.fixtures import fixture_spec, fixture_text
from biocompiler.sandbox.runner import LocalSimulator
from biocompiler.vision.synthetic import frame, png
from tests.meta_http import MetaHTTP, completion, sam_plate_text, segmentation


async def test_real_sdk_serializes_strict_schema_and_retries_invalid_plan():
    server = MetaHTTP()
    server.replies.extend(
        [completion("not JSON"), completion(fixture_text("broken")), completion(fixture_text())]
    )
    provider = server.provider()
    try:
        result = await plan_experiment(provider, "PET degradation assay")
        assert result == fixture_spec()
        assert len(server.requests) == 3
        for path, request in server.requests:
            assert path == "/v1/chat/completions" and request["temperature"] == 0
            schema = request["response_format"]["json_schema"]
            assert schema["strict"] is True
            Draft202012Validator.check_schema(schema["schema"])
            Draft202012Validator(schema["schema"]).validate(result.model_dump(mode="json"))
        last = json.loads(server.requests[-1][1]["messages"][1]["content"])
        assert "unknown labware" in last["previous_validation_error"]
    finally:
        await provider.client.close()


async def test_real_sdk_planner_stops_at_three_invalid_responses():
    server = MetaHTTP()
    server.replies.extend(completion(fixture_text("broken")) for _ in range(3))
    provider = server.provider()
    try:
        with pytest.raises(ValidationError, match="unknown labware"):
            await plan_experiment(provider, "PET degradation assay")
        assert len(server.requests) == 3
    finally:
        await provider.client.close()


@pytest.mark.parametrize("status", [401, 429, 503])
async def test_real_sdk_http_failures_fail_closed_without_hidden_retries(status):
    server = MetaHTTP()
    server.replies.append(
        httpx2.Response(
            status,
            json={"error": {"message": "test credential should not escape", "type": "api_error"}},
        )
    )
    provider = server.provider()
    try:
        with pytest.raises(SafetyRefusal, match="could not be determined"):
            await require_safe(provider, "PET degradation assay")
        assert len(server.requests) == 1
    finally:
        await provider.client.close()


async def test_real_sdk_authentication_failure_never_falls_back_to_mock():
    server = MetaHTTP()
    server.replies.append(httpx2.Response(401, json={"error": {"message": "invalid test key"}}))
    provider = server.provider()
    try:
        with pytest.raises(AuthenticationError):
            await provider.plan("PET degradation assay")
        assert len(server.requests) == 1
    finally:
        await provider.client.close()


@pytest.mark.parametrize(
    "reply",
    [
        completion("", refusal="refused"),
        completion(None),
        completion(""),
        completion("{}", finish_reason="length"),
        completion("{}", choices=False),
    ],
)
async def test_real_sdk_unusable_completions_do_not_pass_the_gate(reply):
    server = MetaHTTP()
    server.replies.append(reply)
    provider = server.provider()
    try:
        with pytest.raises(SafetyRefusal):
            await require_safe(provider, "PET degradation assay")
        assert len(server.requests) == 1
    finally:
        await provider.client.close()


async def test_compiler_repairs_real_sdk_output_using_actual_simulator_error():
    server = MetaHTTP()
    code = render_protocol(fixture_spec())
    broken = code.replace("p_0.pick_up_tip()", "p_0.pick_up_tip('INVALID_WELL')", 1)
    server.replies.extend(
        [
            completion(f"```python\n{broken}```"),
            completion(f"Here is the repaired module:\n```python\n{code}```"),
        ]
    )
    provider = server.provider()
    try:
        attempts = await compile_and_heal(provider, fixture_spec(), LocalSimulator())
        assert len(attempts) == 2 and attempts[-1].simulation.success
        assert not attempts[0].simulation.success
        repair = json.loads(server.requests[-1][1]["messages"][1]["content"])
        assert "INVALID_WELL" in repair["simulation_error"]
        assert repair["previous_code"] == broken
        assert repair["spec"] == fixture_spec().model_dump(mode="json")
    finally:
        await provider.client.close()


async def test_real_sdk_sam_stream_maps_96_sparse_ids_and_closes_transport():
    server = MetaHTTP()
    response, body = segmentation(sam_plate_text())
    server.replies.append(response)
    provider = server.provider()
    image = png(frame(0))
    try:
        masks = await provider.segment(image, "plate")
        assert len(masks) == 96 and masks[0].well == "A1" and masks[-1].well == "H12"
        path, request = server.requests[0]
        assert path == "/v1/responses" and request["stream"] is True
        assert request["model"] == "sam-3.1"
        assert request["metadata"]["mask_encoding"] == "one_bit"
        data_url = request["input"][0]["content"][1]["image_url"]
        assert base64.b64decode(data_url.split(",", 1)[1]) == image
        assert body.closed
    finally:
        await provider.client.close()


@pytest.mark.parametrize("terminal", [None, "incomplete"])
async def test_real_sdk_sam_truncated_stream_never_becomes_a_success(terminal):
    server = MetaHTTP()
    response, body = segmentation(sam_plate_text(), terminal=terminal)
    server.replies.append(response)
    provider = server.provider()
    try:
        with pytest.raises((ValueError, ResponsesStreamError)):
            await provider.segment(png(frame(0)), "plate")
        assert body.closed
    finally:
        await provider.client.close()


async def test_sam_parser_diagnostics_are_not_silently_ignored():
    server = MetaHTTP()
    response, body = segmentation(sam_plate_text() + "<0f>malformed-record\n")
    server.replies.append(response)
    provider = server.provider()
    try:
        with pytest.raises(ValueError, match="malformed"):
            await provider.segment(png(frame(0)), "plate")
        assert body.closed
    finally:
        await provider.client.close()


def test_unfenced_prose_after_code_is_extracted_without_dropping_broken_steps():
    code = render_protocol(fixture_spec())
    assert extract_code(f"It uses `from opentrons import protocol_api`:\n{code}") == code
    assert (
        extract_code(f"Here is the module:\n{code}\nExplanation: This runs in simulation.") == code
    )
    broken = code + "    this is not valid python\n"
    with pytest.raises(ValueError):
        extract_code(broken + "\nExplanation: This must not hide the broken final step.")


async def test_real_sdk_timeout_fails_closed_without_retrying():
    server = MetaHTTP()
    server.replies.append(httpx2.ReadTimeout("deliberate transport timeout"))
    provider = server.provider()
    try:
        with pytest.raises(SafetyRefusal):
            await require_safe(provider, "PET degradation assay")
        assert len(server.requests) == 1
    finally:
        await provider.client.close()


async def test_real_sdk_safety_response_is_parsed_and_validated():
    server = MetaHTTP()
    server.replies.append(completion(json.dumps({"decision": "allow", "reason": "PET assay"})))
    provider = server.provider()
    try:
        decision = await require_safe(provider, "PET degradation assay", fixture_spec())
        assert decision.decision == "allow"
        payload = json.loads(server.requests[0][1]["messages"][1]["content"])
        assert payload["spec"] == fixture_spec().model_dump(mode="json")
    finally:
        await provider.client.close()
