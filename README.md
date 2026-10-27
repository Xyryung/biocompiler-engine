# BioCompiler Engine

Natural-language biological goals compiled into validated, executable
laboratory protocols, closed by a computer-vision feedback loop.

Built for the Meta Global AI Developer Hackathon (Oct 26 - Nov 4, 2026),
Indie Developer track.

## What it does

A researcher writes a goal in plain language:

> Design a PET-degrading enzyme variant stable at 45C.

The system then:

1. **Plans.** Muse Spark emits a strict JSON experiment specification via
   structured outputs. Candidate sequences come from open-weight protein
   models (ESM-2 / ESMFold) hosted on an inference partner, not invented by a
   text model.
2. **Gates.** A biosafety classifier reviews every specification before
   anything is compiled.
3. **Compiles.** Muse Spark translates the specification into Opentrons
   Protocol API v2 Python. The script runs in a Modal sandbox against
   `opentrons_simulate`; stderr is fed back for a self-healing recompile loop.
4. **Observes.** SAM 3.1 segments each well of a 96-well plate in the assay
   video and tracks colorimetric change, feeding deviations back as protocol
   adjustments.

## Scope and honesty

Everything runs in **simulation**. There is no physical OT-2 robot in this
project. Plate imagery comes from public datasets or synthetic renders. The
target is the in-silico-to-wet-lab gap: design is fast, validation is not.

## Architecture

```
[goal text]
    -> bio/        spec generation + biosafety gate
    -> contracts/  validated ExperimentSpec (Pydantic)
    -> compiler/   spec -> Opentrons Protocol API v2 Python
    -> sandbox/    Modal + opentrons_simulate + self-healing loop
    -> vision/     SAM 3.1 well segmentation -> feedback
    -> api/        FastAPI, consumed by apps/web (Next.js)
```

Every model call routes through `providers/`, which exposes a `MockProvider`
for offline development and a `MetaProvider` for the live Meta Model API.
Set `BIOCOMPILER_PROVIDER` in `.env` to switch between them.

## Setup

Requires Python 3.12 (managed by uv) and Node 22+.

```bash
uv python install 3.12
uv sync --all-extras --dev
cp .env.example .env    # then fill in your keys
uv run uvicorn biocompiler.api.main:app --reload
```

Per-lane installs, if you only need one slice:

```bash
uv sync --extra bio       # protein models
uv sync --extra sandbox   # Modal
uv sync --extra vision    # SAM 3.1 pipeline
```

## Development

```bash
uv run ruff check .       # lint
uv run ruff format .      # format
uv run pytest -q          # tests
```

## Team

Indie Developer track, team of three. See `.github/CODEOWNERS` for lane
ownership.
