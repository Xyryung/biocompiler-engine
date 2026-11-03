"""Packaged fixtures also work from an installed wheel, outside the checkout."""

from importlib.resources import files

from biocompiler.contracts.spec import ExperimentSpec


def fixture_text(name: str = "realistic") -> str:
    if name not in {"minimal", "realistic", "broken"}:
        raise ValueError("Unknown fixture")
    return files("biocompiler").joinpath("resources", f"{name}.json").read_text(encoding="utf-8")


def fixture_spec(name: str = "realistic") -> ExperimentSpec:
    return ExperimentSpec.model_validate_json(fixture_text(name))
