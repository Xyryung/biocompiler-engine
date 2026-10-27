"""Shared experiment contracts for the BioCompiler pipeline.

Every module in this project speaks these types and nothing else. The bio
lane produces an ExperimentSpec, the compiler lane consumes one, and the
sandbox and vision lanes report against the labware ids declared here.

Design rules, so changes stay deliberate:

1. `extra="forbid"`. When an LLM returns a field we did not ask for, we
   want a loud ValidationError, not a silently ignored key. Structured
   output is only as good as the thing validating it.
2. `frozen=True`. A spec that has passed the biosafety gate must not be
   mutable afterwards. Freezing makes "validate once, trust thereafter"
   true rather than aspirational.
3. Cross-references are validated here, not in the compiler. If a step
   points at a labware id that was never declared, this is where it fails.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Mount(StrEnum):
    LEFT = "left"
    RIGHT = "right"


class StrictModel(BaseModel):
    """Base for every contract type: no extra keys, immutable once built."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class LabwareSpec(StrictModel):
    """A piece of labware loaded onto a deck slot.

    OT-2 deck slots run 1 through 11; slot 12 is the fixed trash and is
    never user-loadable, which is why the upper bound is 11.
    """

    id: str = Field(
        min_length=1, description="Stable handle used by steps to refer to this labware."
    )
    load_name: str = Field(
        min_length=1, description="Opentrons load name, e.g. 'corning_96_wellplate_360ul_flat'."
    )
    slot: int = Field(ge=1, le=11)


class PipetteSpec(StrictModel):
    load_name: str = Field(min_length=1, description="e.g. 'p300_single_gen2'.")
    mount: Mount
    tiprack_id: str = Field(
        min_length=1, description="id of a LabwareSpec entry holding this pipette's tips."
    )


class WellRef(StrictModel):
    """A single well on a declared piece of labware.

    The pattern covers the A1-H12 grid shared by 96-well plates, 12-channel
    reservoirs and standard tipracks. A 384-well plate would need rows
    beyond H and is deliberately out of scope.
    """

    labware_id: str = Field(min_length=1)
    well: str = Field(pattern=r"^[A-H](?:[1-9]|1[0-2])$")


class MixSpec(StrictModel):
    repetitions: int = Field(ge=1, le=20)
    volume_ul: float = Field(gt=0)


class TransferStep(StrictModel):
    """One source well to one destination well."""

    action: Literal["transfer"] = "transfer"
    source: WellRef
    dest: WellRef
    volume_ul: float = Field(gt=0, le=1000)
    mix_after: MixSpec | None = None

    @property
    def well_refs(self) -> list[WellRef]:
        return [self.source, self.dest]


class DistributeStep(StrictModel):
    """One source well out to many destinations."""

    action: Literal["distribute"] = "distribute"
    source: WellRef
    dests: list[WellRef] = Field(min_length=1, max_length=96)
    volume_ul: float = Field(gt=0, le=1000)

    @property
    def well_refs(self) -> list[WellRef]:
        return [self.source, *self.dests]


class ConsolidateStep(StrictModel):
    """Many source wells into one destination."""

    action: Literal["consolidate"] = "consolidate"
    sources: list[WellRef] = Field(min_length=1, max_length=96)
    dest: WellRef
    volume_ul: float = Field(gt=0, le=1000)

    @property
    def well_refs(self) -> list[WellRef]:
        return [*self.sources, self.dest]


class DelayStep(StrictModel):
    """Pause the protocol. Capped at two hours so a hallucinated
    incubation time cannot produce a simulation that never terminates."""

    action: Literal["delay"] = "delay"
    seconds: int = Field(ge=1, le=7200)
    message: str | None = None

    @property
    def well_refs(self) -> list[WellRef]:
        return []


Step = Annotated[
    TransferStep | DistributeStep | ConsolidateStep | DelayStep,
    Field(discriminator="action"),
]


class ExperimentSpec(StrictModel):
    """The single contract between the bio lane and the compiler lane."""

    experiment_name: str = Field(min_length=1, max_length=120)
    rationale: str = Field(
        default="",
        max_length=2000,
        description="Why the planner chose this assay. Shown in the UI, never compiled.",
    )
    pipettes: list[PipetteSpec] = Field(min_length=1, max_length=2)
    labware: list[LabwareSpec] = Field(min_length=1, max_length=11)
    steps: list[Step] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def _check_internal_consistency(self) -> ExperimentSpec:
        labware_ids = [lw.id for lw in self.labware]
        if len(set(labware_ids)) != len(labware_ids):
            raise ValueError("labware ids must be unique")

        slots = [lw.slot for lw in self.labware]
        if len(set(slots)) != len(slots):
            raise ValueError("two pieces of labware cannot occupy the same deck slot")

        mounts = [p.mount for p in self.pipettes]
        if len(set(mounts)) != len(mounts):
            raise ValueError("two pipettes cannot share a mount")

        known = set(labware_ids)

        for pipette in self.pipettes:
            if pipette.tiprack_id not in known:
                raise ValueError(
                    f"pipette {pipette.load_name!r} references "
                    f"unknown tiprack id {pipette.tiprack_id!r}"
                )

        for index, step in enumerate(self.steps):
            for ref in step.well_refs:
                if ref.labware_id not in known:
                    raise ValueError(
                        f"step {index} references unknown labware id {ref.labware_id!r}"
                    )

        return self
