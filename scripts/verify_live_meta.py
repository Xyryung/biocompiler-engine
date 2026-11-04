"""Bounded acceptance checks for issues #1/#7/#10/#14 using real Meta credentials.

No mock fallback. Writes a report only after every real check succeeds.
"""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from biocompiler.bio.planner import plan_experiment
from biocompiler.bio.safety import SafetyRefusal, require_safe
from biocompiler.compiler.healing import compile_and_heal
from biocompiler.config import Settings
from biocompiler.providers.meta import MetaProvider
from biocompiler.sandbox.runner import LocalSimulator
from biocompiler.vision.synthetic import decode_rle, frame, png

GOALS = (
    "Design a PET-degrading enzyme assay stable at 45C.",
    "Compare buffer transfer and incubation timing for a PETase plastic degradation assay.",
    "Plan a six-well PET enzyme stability assay with a reference control.",
)


async def main() -> None:
    settings = Settings(biocompiler_provider="meta")
    if settings.meta_base_url.rstrip("/") != "https://api.meta.ai/v1":
        raise ValueError("Live acceptance must use the official Meta endpoint")
    provider = MetaProvider(settings)
    plans = []
    try:
        for goal in GOALS:
            await require_safe(provider, goal)
            spec = await plan_experiment(provider, goal)
            await require_safe(provider, goal, spec)
            plans.append(spec)
        attempts = await compile_and_heal(provider, plans[0], LocalSimulator())
        if not attempts[-1].simulation.success:
            raise ValueError("Live-generated protocol did not simulate within three attempts")
        try:
            await require_safe(provider, "Plan an unrelated human clinical experiment.")
        except SafetyRefusal:
            pass
        else:
            raise ValueError("Live classifier did not refuse the out-of-domain goal")
        plate = next(
            lw for lw in plans[0].labware if lw.load_name == "corning_96_wellplate_360ul_flat"
        )
        masks = []
        for seconds in (0, 150, 300):
            found = await provider.segment(png(frame(seconds)), plate.id)
            if len(found) != 96:
                raise ValueError("Live SAM did not return all 96 wells")
            masks.append({mask.well: decode_rle(mask) for mask in found})
        minimum_iou = 1.0
        for later in masks[1:]:
            for well, first in masks[0].items():
                overlap = np.logical_and(first, later[well]).sum()
                union = np.logical_or(first, later[well]).sum()
                minimum_iou = min(minimum_iou, float(overlap / union) if union else 0.0)
        if minimum_iou < 0.5:
            raise ValueError("Live SAM masks were unstable across the fixed-camera clip")
        report = {
            "checked_at": datetime.now(UTC).isoformat(),
            "provider": "meta",
            "live": True,
            "model": settings.meta_model,
            "segmentation_model": settings.meta_sam_model,
            "valid_goals": len(plans),
            "out_of_domain_refused": True,
            "plans": [spec.model_dump(mode="json") for spec in plans],
            "compile_attempts": [a.model_dump(mode="json") for a in attempts],
            "segmented_frames": 3,
            "wells_per_frame": 96,
            "minimum_mask_iou": minimum_iou,
        }
        output = Path(__file__).resolve().parents[1] / "artifacts/acceptance/live-meta.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Real Meta acceptance succeeded: {output}")
    finally:
        await provider.client.close()


if __name__ == "__main__":
    asyncio.run(main())
