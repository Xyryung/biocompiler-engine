# BioCompiler Engine

A **simulation-only** PET assay workspace: a natural-language goal becomes a
validated plan, an Opentrons OT-2 protocol, real simulator output, and synthetic
96-well colour observations. There is no physical robot, wet-lab experiment,
validated thermostable variant, or measured enzyme performance.

## Run from a clean clone

Install [uv](https://docs.astral.sh/uv/) and Node.js 22 or newer. From the repo root:

```sh
uv python install 3.12
uv sync --locked --all-extras --dev
uv run uvicorn biocompiler.api.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```sh
cd apps/web
npm ci
npm run dev
```

Open **http://127.0.0.1:3000**. Compile the example, enable **Demonstrate recovery**,
or select **Test safety refusal**. No keys, cloud services, GPU, or downloaded model
weights are needed. The first local simulation may take several seconds.
API docs: **http://127.0.0.1:8000/docs**. Health: **http://127.0.0.1:8000/health**.
An `.env` file is optional; copy `.env.example` to `.env` to change configuration.
In PowerShell use `Copy-Item .env.example .env`; in a POSIX shell use `cp`.

```sh
curl -X POST http://127.0.0.1:8000/compile -H "Content-Type: application/json" \
  -d '{"goal":"Design a PET-degrading enzyme assay stable at 45C."}'
```

In PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/compile -Method Post -ContentType application/json -Body '{"goal":"Design a PET-degrading enzyme assay stable at 45C."}'
```

## What runs

1. A mandatory fail-closed scope gate checks the goal before planning and checks
   the validated specification again before compilation. Refusals raise and
   return a deliberate HTTP 403 state. There is no safety bypass.
2. The planner emits `ExperimentSpec` JSON; unknown fields, invalid references,
   nonfinite volumes, incompatible tips, deck collisions, well capacities and
   pipette ranges are rejected. Validation retries at most twice.
3. The compiler emits Python Protocol API 2.19 with explicit tip handling.
   Opentrons **8.8.2** is pinned because newer `opentrons` releases removed OT-2
   simulation support. The simulator really executes `opentrons.simulate`.
4. On failure, code and stderr return to the compiler, with an absolute cap of
   three compile attempts. Every attempt appears in the dashboard. The optional
   mock-only recovery demo injects an invalid tip-well name in attempt one.
5. Eleven synthetic plate frames produce 96 mapped masks, per-well RGB series,
   a segmentation overlay, and a review signal when an active well lags. A3 is
   deliberately delayed. Suggestions are **not automatically applied**.

The dashboard receives all results from one `POST /compile`; it also exports the
run JSON and generated `.py`. Planning errors return structured HTTP 502 JSON;
exhausted simulation attempts return HTTP 422 with the full attempt history.

## Providers and provenance

| Component | Offline default | Optional live integration |
| --- | --- | --- |
| Planning and compilation | deterministic fixtures/templates, labelled `mock` | Muse Spark via the OpenAI-compatible Meta API |
| Scope classifier | conservative keyword demo gate | structured Muse Spark classifier, fails closed |
| Well segmentation | exact known synthetic geometry | SAM 3.1 Responses stream, official `meta-sam-parser` |
| Simulation | real local Opentrons subprocess | Modal sandbox, cached image, network blocked |
| Protein structure | curated UniProt reference only; no prediction | HTTPS partner ESMFold adapter |

To select Meta, set `BIOCOMPILER_PROVIDER=meta` and `META_API_KEY` (or
`MODEL_API_KEY`) in `.env`. `META_BASE_URL`, `META_MODEL`, and `META_SAM_MODEL`
configure the service. Requests use bounded timeouts and no hidden SDK retries.
See Meta's [structured output](https://dev.meta.ai/docs/cookbook/structured-output)
and [SAM segmentation](https://dev.meta.ai/docs/media-segmentation) documentation.
Live calls require your credentials and have **not** been validated by the
offline test suite. No silent fallback substitutes mock outputs for live failures.

For Modal, set `BIOCOMPILER_SIMULATOR=modal` and authenticate with `modal setup`
or the documented Modal token environment variables. The local simulator accepts
only a straight-line allowlist of Opentrons calls and runs a timed subprocess
without API credentials. It is **not an OS security boundary**. The Modal option
adds filesystem/process isolation and blocks network access. Neither path
connects to robot hardware.

For proteins, deploy an ESMFold inference adapter on your partner, then set
`PROTEIN_ENDPOINT` and `PROTEIN_API_KEY`. Contract:

```json
POST {"sequence": "<curated UniProt reference>"}
200  {"model": "esmfold-v1", "structure_pdb": "<PDB containing ATOM records>"}
```

The server selects the reference sequence; Muse Spark cannot supply one. Returned
provenance includes source, model, latency, and an optional configured cost
estimate (`PROTEIN_COST_USD`). No cached prediction is bundled, and no model-hosting
or live latency/cost claim is made without a successful authenticated call.

The safety gate is an application scope restriction for this simulated demo,
not a validated biological risk assessment. Real experiments require expert
review. The current vision path assumes the provided aligned, fixed-camera
synthetic sequence; it does not claim general plate recognition or moving-camera
tracking. See [data provenance](data/README.md).

## Verification

```sh
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q
uv build
cd apps/web
npm ci
npm run build
npm run typecheck
npx playwright install chromium
npm run test:e2e
```

Browser tests start both servers against the production build. In Linux CI,
install browser OS dependencies with `npx playwright install --with-deps chromium`.
CI enforces lint, format, types, real simulator integration, the frontend build,
and desktop/mobile browser scenarios. It uploads a dashboard screenshot.

`uv run python scripts/generate_fixtures.py` regenerates packaged and test specs;
`uv run python scripts/generate_plate_data.py` regenerates offline PNG frames.

## Demo and submission

- [Three-minute recording script](docs/demo-script.md)
- [Submission checklist and unresolved external requirements](docs/submission-checklist.md)
- [Issue acceptance matrix](docs/issue-status.md)

This project targets the Meta Global AI Developer Hackathon indie developer track.
The [public event page](https://dev.meta.ai/events/global-hackathon) lists November 4,
2026, 9 PM ET as the submission deadline. The complete entrant rules must still be
checked in the participant portal; the public landing page is not those rules.

Team accounts observed with repository access: `Xyryung` (admin), `MateoDG2006`,
`GusEh06`, and `yukki2126` (write). CODEOWNERS uses the owner as fallback until
unconfirmed lane assignments are supplied. The protected main branch requires
one human approval. Project code and synthetic imagery: MIT; UniProt data: CC BY 4.0;
SAM parser: its upstream SAM License.
