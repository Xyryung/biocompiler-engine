"""Independent acceptance stages; retain successes and never mistake API failure for refusal."""

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from biocompiler.bio.planner import plan_experiment
from biocompiler.bio.safety import require_safe
from biocompiler.compiler.healing import compile_and_heal
from biocompiler.fixtures import fixture_spec
from biocompiler.providers.base import Provider
from biocompiler.sandbox.runner import Simulator
from biocompiler.vision.synthetic import frame, png
from biocompiler.vision.validation import validate_plate_masks

GOALS = (
    "Design a PET-degrading enzyme assay stable at 45C.",
    "Compare buffer transfer and incubation timing for a PETase plastic degradation assay.",
    "Plan a six-well PET enzyme stability assay with a reference control.",
)
STAGES = ("planning", "compiler", "vision")


async def verify_planning(provider: Provider) -> dict:
    plans = []
    for goal in GOALS:
        await require_safe(provider, goal)
        spec = await plan_experiment(provider, goal)
        await require_safe(provider, goal, spec)
        plans.append(spec.model_dump(mode="json"))
    # A network outage also raises SafetyRefusal in the pipeline. It is not
    # evidence that the live classifier actually classified this example.
    refusal = await provider.classify("Plan an unrelated human clinical experiment.")
    if refusal.decision != "refuse":
        raise ValueError("The classifier did not explicitly refuse the out-of-domain goal")
    return {"valid_goals": len(plans), "plans": plans, "refusal": refusal.model_dump()}


async def verify_compiler(provider: Provider, simulator: Simulator) -> dict:
    # The compiler issue explicitly accepts a fixture spec, so it can be checked
    # independently of planner availability and without rerunning paid planning.
    spec = fixture_spec()
    await require_safe(provider, GOALS[0], spec)
    attempts = await compile_and_heal(provider, spec, simulator)
    if not attempts[-1].simulation.success:
        raise ValueError("Generated protocol did not simulate within three attempts")
    return {"attempts": [attempt.model_dump(mode="json") for attempt in attempts]}


async def verify_vision(provider: Provider) -> dict:
    masks = []
    for seconds in (0, 150, 300):
        image = frame(seconds)
        found = await provider.segment(png(image), "assay_plate")
        rasters = validate_plate_masks(found, "assay_plate", image.size)
        masks.append({mask.well: raster for mask, raster in zip(found, rasters, strict=True)})
    minimum_iou = 1.0
    for later in masks[1:]:
        for well, first in masks[0].items():
            overlap = np.logical_and(first, later[well]).sum()
            union = np.logical_or(first, later[well]).sum()
            minimum_iou = min(minimum_iou, float(overlap / union) if union else 0.0)
    if minimum_iou < 0.5:
        raise ValueError("Masks were unstable across the fixed-camera clip")
    return {"segmented_frames": 3, "wells_per_frame": 96, "minimum_mask_iou": minimum_iou}


def _write_report(path: Path, report: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


async def verify_stages(
    provider: Provider,
    simulator: Simulator,
    output_dir: Path,
    *,
    stages: tuple[str, ...] = STAGES,
    live: bool = False,
) -> dict:
    if not stages or any(stage not in STAGES for stage in stages):
        raise ValueError("Select planning, compiler, and/or vision acceptance stages")
    output_dir.mkdir(parents=True, exist_ok=True)
    reports = {}
    authentication_failed = False
    for stage in stages:
        report = {
            "stage": stage,
            "live": live,
            "provider": provider.name,
            "checked_at": datetime.now(UTC).isoformat(),
            "status": "running",
        }
        path = output_dir / f"meta-{stage}.json"
        if authentication_failed:
            report.update(status="skipped", reason="authentication_failed")
        else:
            # Overwrite a previous success before starting its replacement check.
            _write_report(path, report)
            try:
                if stage == "planning":
                    evidence = await verify_planning(provider)
                elif stage == "compiler":
                    evidence = await verify_compiler(provider, simulator)
                else:
                    evidence = await verify_vision(provider)
                report.update(status="passed", evidence=evidence)
            except Exception as exc:
                cause: BaseException = exc
                while cause.__cause__ is not None:
                    cause = cause.__cause__
                status = getattr(cause, "status_code", None)
                # Exception bodies may echo credentials; persist only safe diagnostics.
                report.update(
                    status="failed", error={"type": type(exc).__name__, "http_status": status}
                )
                authentication_failed = status == 401
        _write_report(path, report)
        reports[stage] = report
    return {
        "status": "passed" if all(r["status"] == "passed" for r in reports.values()) else "failed",
        "stages": reports,
        "live": live,
    }
