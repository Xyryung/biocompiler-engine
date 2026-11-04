"""Deterministic offline provider; never impersonates a live model."""

import re

from biocompiler.contracts.results import SafetyDecision, WellMask
from biocompiler.contracts.spec import ExperimentSpec
from biocompiler.fixtures import fixture_spec


class MockProvider:
    name = "mock"

    async def classify(self, goal: str, spec: ExperimentSpec | None = None) -> SafetyDecision:
        text = goal.casefold()
        denied = re.search(
            r"pathogen|virus|viral|toxin|weapon|virulen|infect|bacteri|human|animal|"
            r"ignore|bypass|skip|override|ignora|omite|saltar|pat[oó]gen|veneno|explosiv",
            text,
        )
        domain = re.search(r"\bpet\b|petase|petasa|polyethylene terephthalate", text)
        intent = re.search(
            r"degrad|assay|enzym|enzim|stabil|estabil|thermo|t[eé]rm|plastic|pl[aá]stic", text
        )
        decision = "refuse" if denied or not domain else ("allow" if intent else "uncertain")
        return SafetyDecision(
            decision=decision,
            reason=(
                "In-domain, simulation-only PET degradation assay."
                if decision == "allow"
                else "Only unambiguous PET plastic degradation simulations are supported."
            ),
        )

    async def plan(self, goal: str, validation_error: str | None = None) -> str:
        spec = fixture_spec()
        return spec.model_copy(
            update={
                "rationale": (
                    f"For the goal '{goal[:500]}', compare a reference PETase assay "
                    "across six wells. Buffer handling and a timed pause illustrate the workflow. "
                    "Temperature control "
                    "and enzyme performance are not measured by this liquid-handling simulation. "
                    "This offline plan is a fixture, not a model-designed variant."
                )
            }
        ).model_dump_json()

    async def compile(self, spec: ExperimentSpec, previous_code: str = "", error: str = "") -> str:
        from biocompiler.compiler.codegen import render_protocol

        return render_protocol(spec)

    async def segment(self, image: bytes, labware_id: str) -> tuple[WellMask, ...]:
        from biocompiler.vision.synthetic import grid_masks

        return grid_masks(labware_id)
