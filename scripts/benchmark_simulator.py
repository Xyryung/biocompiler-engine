"""Measure the accepted local simulator fallback with actual valid/broken protocols."""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from biocompiler.compiler.codegen import render_protocol
from biocompiler.fixtures import fixture_spec
from biocompiler.sandbox.runner import LocalSimulator


async def main() -> None:
    code = render_protocol(fixture_spec())
    simulator = LocalSimulator()
    first = await simulator.simulate(code)
    second = await simulator.simulate(code)
    broken = await simulator.simulate(
        code.replace("p_0.pick_up_tip()", "p_0.pick_up_tip('INVALID_WELL')", 1)
    )
    assert first.success and second.success and not broken.success and broken.stderr
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "backend": "local-opentrons",
        "opentrons_version": "8.8.2",
        "fallback": "Explicitly allowed in issue #11",
        "first_process_ms": first.duration_ms,
        "second_process_ms": second.duration_ms,
        "valid_success": True,
        "broken_success": broken.success,
        "broken_stderr": broken.stderr,
        "note": "Fresh local subprocesses; these are not Modal image cold/warm measurements.",
    }
    output = Path(__file__).resolve().parents[1] / "artifacts/acceptance/simulator.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
