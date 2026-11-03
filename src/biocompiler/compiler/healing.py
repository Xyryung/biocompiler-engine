import time

import structlog

from biocompiler.compiler.extract import extract_code
from biocompiler.contracts.results import CompileAttempt, SimulationResult
from biocompiler.contracts.spec import ExperimentSpec
from biocompiler.providers.base import Provider
from biocompiler.sandbox.runner import Simulator

log = structlog.get_logger()


async def compile_and_heal(
    provider: Provider, spec: ExperimentSpec, simulator: Simulator, *, demo_failure: bool = False
) -> tuple[CompileAttempt, ...]:
    attempts = []
    code = error = ""
    for number in range(1, 4):
        start = time.perf_counter()
        try:
            raw = await provider.compile(spec, code, error)
            code = raw
            code = extract_code(raw)
            if demo_failure and number == 1:
                code = code.replace("p_0.pick_up_tip()", "p_0.pick_up_tip('INVALID_WELL')", 1)
            result = await simulator.simulate(code)
        except (ValueError, SyntaxError) as exc:
            result = SimulationResult(
                success=False,
                stderr=str(exc),
                backend="local-opentrons",
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        attempts.append(CompileAttempt(number=number, protocol=code, simulation=result))
        log.info("compile_attempt", attempt=number, success=result.success, error=result.stderr)
        if result.success:
            break
        error = result.stderr or "Simulator failed without diagnostic output"
    return tuple(attempts)
