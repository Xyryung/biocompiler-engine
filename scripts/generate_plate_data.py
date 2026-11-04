"""Generate the committed synthetic plate sequence and extraction manifest."""

import json
from pathlib import Path

from biocompiler.vision.synthetic import TIMES, frame

root = Path(__file__).resolve().parents[1] / "data" / "synthetic"
root.mkdir(parents=True, exist_ok=True)
for seconds in TIMES:
    frame(seconds).save(root / f"frame_{int(seconds):03d}.png")
(root / "manifest.json").write_text(
    json.dumps(
        {
            "source": "scripts/generate_plate_data.py",
            "license": "MIT (project-generated pixels)",
            "synthetic": True,
            "times_seconds": TIMES,
            "fixed_camera": True,
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
