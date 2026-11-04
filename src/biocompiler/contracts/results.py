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
    source: Literal["cached-esmfold", "partner-endpoint"]
    reference: str
    model: str
    status: Literal["cached", "predicted"]
    sequence_source: str
    structure_pdb: str | None = None
    cached: bool = False
    prediction_url: str | None = None
    generated_at: str | None = None
    residue_count: int = Field(default=0, ge=0)
    sequence_sha256: str = ""
    structure_sha256: str = ""
    cache_lookup_ms: float | None = Field(default=None, ge=0)
    latency_ms: float | None = None
    cost_usd: float | None = None
    cost_basis: str = "Configured partner estimate; internal provider cost is unknown."
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
