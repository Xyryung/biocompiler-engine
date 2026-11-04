import hashlib
import json
from importlib.resources import files

import pytest

from biocompiler.bio.structures import validate_structure


def test_cached_structure_is_a_real_sequence_bound_prediction():
    resources = files("biocompiler").joinpath("resources")
    ref = json.loads(resources.joinpath("petase_reference.json").read_text())
    meta = json.loads(resources.joinpath("petase_esmfold.json").read_text())
    pdb = resources.joinpath("petase_esmfold.pdb").read_text()
    assert validate_structure(pdb, ref["sequence"]) == 290
    assert hashlib.sha256(pdb.encode()).hexdigest() == meta["structure_sha256"]
    assert hashlib.sha256(ref["sequence"].encode()).hexdigest() == meta["sequence_sha256"]
    assert "ESMFOLD" in pdb and meta["request_latency_ms"] > 0


def test_structure_for_another_sequence_is_rejected():
    resources = files("biocompiler").joinpath("resources")
    pdb = resources.joinpath("petase_esmfold.pdb").read_text()
    with pytest.raises(ValueError, match="does not match"):
        validate_structure(pdb, "WRONGSEQUENCE")
    with pytest.raises(ValueError, match="Truncated"):
        validate_structure("ATOM  invalid", "A")
