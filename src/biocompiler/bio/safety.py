"""Mandatory fail-closed gate before planning and again before compilation."""

import structlog

from biocompiler.contracts.results import SafetyDecision
from biocompiler.contracts.spec import ExperimentSpec
from biocompiler.providers.base import Provider

log = structlog.get_logger()


class SafetyRefusal(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


async def require_safe(
    provider: Provider, goal: str, spec: ExperimentSpec | None = None
) -> SafetyDecision:
    try:
        decision = await provider.classify(goal, spec)
        if not isinstance(decision, SafetyDecision):
            raise TypeError("Classifier returned an invalid decision")
    except Exception as exc:
        log.warning(
            "safety_refusal", reason="Classifier unavailable or invalid", kind=type(exc).__name__
        )
        raise SafetyRefusal("Safety could not be determined; this run was stopped.") from exc
    if decision.decision != "allow":
        log.warning("safety_refusal", reason=decision.reason)
        raise SafetyRefusal(decision.reason)
    return decision
