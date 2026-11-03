from pydantic import ValidationError

from biocompiler.contracts.spec import ExperimentSpec
from biocompiler.providers.base import Provider


async def plan_experiment(provider: Provider, goal: str) -> ExperimentSpec:
    error = None
    # Initial call plus at most two retries. Preserve the final ValidationError.
    for attempt in range(3):
        payload = await provider.plan(goal, error)
        try:
            return ExperimentSpec.model_validate_json(payload)
        except ValidationError as exc:
            if attempt == 2:
                raise
            error = str(exc)
    raise AssertionError("Unreachable")
