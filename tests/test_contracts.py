import pytest
from pydantic import ValidationError

from biocompiler.contracts.spec import (
    DelayStep,
    ExperimentSpec,
    Mount,
    TransferStep,
)


def _minimal_spec(**overrides) -> dict:
    base = {
        "experiment_name": "PETase thermostability assay",
        "pipettes": [
            {"load_name": "p300_single_gen2", "mount": "left", "tiprack_id": "tiprack_300"}
        ],
        "labware": [
            {"id": "tiprack_300", "load_name": "opentrons_96_tiprack_300ul", "slot": 1},
            {"id": "buffer", "load_name": "nest_12_reservoir_15ml", "slot": 2},
            {"id": "assay_plate", "load_name": "corning_96_wellplate_360ul_flat", "slot": 3},
        ],
        "steps": [
            {
                "action": "transfer",
                "source": {"labware_id": "buffer", "well": "A1"},
                "dest": {"labware_id": "assay_plate", "well": "A1"},
                "volume_ul": 150,
                "mix_after": {"repetitions": 3, "volume_ul": 100},
            },
            {"action": "delay", "seconds": 300},
        ],
    }
    base.update(overrides)
    return base


def test_valid_spec_parses():
    spec = ExperimentSpec.model_validate(_minimal_spec())
    assert spec.pipettes[0].mount is Mount.LEFT
    assert isinstance(spec.steps[0], TransferStep)
    assert isinstance(spec.steps[1], DelayStep)


def test_spec_is_frozen():
    spec = ExperimentSpec.model_validate(_minimal_spec())
    with pytest.raises(ValidationError):
        spec.experiment_name = "something else"


def test_extra_keys_are_rejected():
    payload = _minimal_spec()
    payload["hallucinated_field"] = "whatever the model invented"
    with pytest.raises(ValidationError):
        ExperimentSpec.model_validate(payload)


def test_unknown_labware_reference_is_rejected():
    payload = _minimal_spec()
    payload["steps"][0]["dest"]["labware_id"] = "nonexistent_plate"
    with pytest.raises(ValidationError, match="unknown labware id"):
        ExperimentSpec.model_validate(payload)


def test_duplicate_deck_slots_are_rejected():
    payload = _minimal_spec()
    payload["labware"][1]["slot"] = 1
    with pytest.raises(ValidationError, match="same deck slot"):
        ExperimentSpec.model_validate(payload)


def test_tiprack_reference_must_resolve():
    payload = _minimal_spec()
    payload["pipettes"][0]["tiprack_id"] = "missing_rack"
    with pytest.raises(ValidationError, match="unknown tiprack"):
        ExperimentSpec.model_validate(payload)


def test_bad_well_name_is_rejected():
    payload = _minimal_spec()
    payload["steps"][0]["source"]["well"] = "Z99"
    with pytest.raises(ValidationError):
        ExperimentSpec.model_validate(payload)


def test_negative_volume_is_rejected():
    payload = _minimal_spec()
    payload["steps"][0]["volume_ul"] = -5
    with pytest.raises(ValidationError):
        ExperimentSpec.model_validate(payload)
