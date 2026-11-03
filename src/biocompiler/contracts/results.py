"""Serializable stage results shared with the dashboard."""

from typing import Literal

from pydantic import Field

from biocompiler.contracts.spec import ExperimentSpec, StrictModel


class SafetyDecision(StrictModel):
    decision: Literal["allow", "refuse", "uncertain"]
    reason: str = Field(min_length=1, max_length=2000)


class SimulationResult(StrictModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    backend: Literal["local-opentrons", "modal-opentrons"]
    duration_ms: float = Field(ge=0)


class CompileAttempt(StrictModel):
    number: int = Field(ge=1, le=3)
    protocol: str
    simulation: SimulationResult


class WellMask(StrictModel):
    labware_id: str
    well: str = Field(pattern=r"^[A-H](?:[1-9]|1[0-2])$")
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    # Row-major run lengths, starting with background. Compact and lossless.
    rle: tuple[int, ...]


class ColorSample(StrictModel):
    seconds: float
    red: float
    green: float
    blue: float
    signal: float


class WellSeries(StrictModel):
    labware_id: str
    well: str
    samples: tuple[ColorSample, ...]


class AdjustmentEvent(StrictModel):
    labware_id: str
    well: str
    seconds: float
    observed: float
    threshold: float
    suggestion: str
    applied: Literal[False] = False


class VisionResult(StrictModel):
    source: Literal["synthetic-grid", "meta-sam-3.1"]
    imagery: Literal["synthetic"] = "synthetic"
    masks: tuple[WellMask, ...]
    series: tuple[WellSeries, ...]
    adjustments: tuple[AdjustmentEvent, ...]
    overlay_data_url: str


class ProteinResult(StrictModel):
    source: Literal["reference-only", "partner-endpoint"]
    reference: str
    model: str
    status: Literal["not-configured", "predicted"]
    sequence_source: str
    structure_pdb: str | None = None
    latency_ms: float | None = None
    cost_usd: float | None = None
    note: str


class CompileResult(StrictModel):
    run_id: str
    status: Literal["success", "simulation_failed"]
    simulation_only: Literal[True] = True
    provider: Literal["mock", "meta"]
    goal: str
    safety: SafetyDecision
    spec: ExperimentSpec
    protocol: str
    simulation: SimulationResult
    attempts: tuple[CompileAttempt, ...]
    vision: VisionResult
    protein: ProteinResult
