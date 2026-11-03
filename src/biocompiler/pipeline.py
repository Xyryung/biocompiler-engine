from uuid import uuid4

import structlog

from biocompiler.bio.planner import plan_experiment
from biocompiler.bio.protein import predict_reference
from biocompiler.bio.safety import require_safe
from biocompiler.compiler.healing import compile_and_heal
from biocompiler.config import Settings
from biocompiler.contracts.results import CompileResult
from biocompiler.providers.base import Provider
from biocompiler.sandbox.runner import Simulator
from biocompiler.vision.analysis import analyze_plate

log = structlog.get_logger()


class PipelineError(Exception):
    def __init__(self, stage: str, cause: Exception):
        self.stage = stage
        self.cause = cause
        super().__init__(f"{stage} failed: {type(cause).__name__}")


async def run_pipeline(
    goal: str,
    provider: Provider,
    simulator: Simulator,
    settings: Settings,
    *,
    demo_failure: bool = False,
) -> CompileResult:
    run_id = uuid4().hex
    # Refusals are never wrapped: the API has a deliberate 403 state for them.
    await require_safe(provider, goal)
    stage = "planning"
    try:
        spec = await plan_experiment(provider, goal)
    except Exception as exc:
        raise PipelineError(stage, exc) from exc
    safety = await require_safe(provider, goal, spec)
    try:
        stage = "compilation"
        attempts = await compile_and_heal(provider, spec, simulator, demo_failure=demo_failure)
        stage = "vision"
        vision = await analyze_plate(provider, spec)
        stage = "protein"
        protein = await predict_reference(settings)
    except Exception as exc:
        log.error("pipeline_failed", run_id=run_id, stage=stage, kind=type(exc).__name__)
        raise PipelineError(stage, exc) from exc
    last = attempts[-1]
    result = CompileResult(
        run_id=run_id,
        status="success" if last.simulation.success else "simulation_failed",
        provider=settings.biocompiler_provider,
        goal=goal,
        safety=safety,
        spec=spec,
        protocol=last.protocol,
        simulation=last.simulation,
        attempts=attempts,
        vision=vision,
        protein=protein,
    )
    log.info("pipeline_completed", run_id=run_id, status=result.status, attempts=len(attempts))
    return result
