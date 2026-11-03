"""All generative model calls pass through this small async interface."""

from typing import Protocol

from biocompiler.contracts.results import SafetyDecision, WellMask
from biocompiler.contracts.spec import ExperimentSpec


class Provider(Protocol):
    name: str

    async def classify(self, goal: str, spec: ExperimentSpec | None = None) -> SafetyDecision: ...

    async def plan(self, goal: str, validation_error: str | None = None) -> str: ...

    async def compile(
        self, spec: ExperimentSpec, previous_code: str = "", error: str = ""
    ) -> str: ...

    async def segment(self, image: bytes, labware_id: str) -> tuple[WellMask, ...]: ...
