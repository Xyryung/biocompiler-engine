"""Regenerate canonical fixtures. No network or model calls."""

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
minimal = {
    "experiment_name": "PETase reference assay simulation",
    "rationale": "Illustrate buffer transfer and timed incubation for a PET assay in simulation.",
    "pipettes": [{"load_name": "p300_single_gen2", "mount": "left", "tiprack_id": "tips"}],
    "labware": [
        {"id": "tips", "load_name": "opentrons_96_tiprack_300ul", "slot": 1},
        {"id": "buffer", "load_name": "nest_12_reservoir_15ml", "slot": 2},
        {"id": "assay_plate", "load_name": "corning_96_wellplate_360ul_flat", "slot": 3},
    ],
    "steps": [
        {
            "action": "transfer",
            "source": {"labware_id": "buffer", "well": "A1"},
            "dest": {"labware_id": "assay_plate", "well": "A1"},
            "volume_ul": 150,
        },
        {"action": "delay", "seconds": 300, "message": "Simulated incubation; no heating."},
    ],
}
realistic = copy.deepcopy(minimal)
realistic["steps"] = [
    {
        "action": "transfer",
        "source": {"labware_id": "buffer", "well": "A1"},
        "dest": {"labware_id": "assay_plate", "well": f"A{col}"},
        "volume_ul": 150,
        "mix_after": {"repetitions": 3, "volume_ul": 100},
    }
    for col in range(1, 7)
] + [minimal["steps"][-1]]
broken = copy.deepcopy(realistic)
broken["steps"][0]["dest"]["labware_id"] = "missing_plate"
for name, payload in {"minimal": minimal, "realistic": realistic, "broken": broken}.items():
    for directory in (ROOT / "tests/fixtures", ROOT / "src/biocompiler/resources"):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{name}.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
