# Verification evidence — November 3, 2026

The offline suite and authenticated Meta acceptance have both passed. The live
checks used Muse Spark 1.3 and SAM 3.1 against the official Meta endpoint; the
FastAPI pipeline also returned HTTP 200 with the real provider, actual local
Opentrons simulation, 96 SAM masks, and the verified cached ESMFold prediction.
Modal and fresh partner-hosted protein inference remain optional alternatives.

| Check | Result |
| --- | --- |
| Python tests | 80 passed, including actual OT-2 simulation, fail-closed refusal, retries/caps, timeout cleanup, immutable contracts, ESMFold cache validation, installed-SDK HTTP/SSE contracts, calibrated 16-object batching and negative plate-geometry cases |
| Browser tests | 5 passed against production Next.js and actual FastAPI: full run/download, healing, refusal, network failure, mobile/blank input |
| Python lint / formatting | Ruff passes |
| Python types | mypy passes on all 33 source modules; CI no longer ignores errors |
| Frontend types / build / formatting | TypeScript, production Next.js build, Prettier pass |
| npm production audit | No vulnerabilities reported at test time |
| Python distribution | Wheel and source distribution build; installed wheel simulated successfully from an isolated environment with packaged fixtures |
| GitHub Actions | Both Python and dashboard jobs passed on the initial implementation; inspect the [latest PR checks](https://github.com/Xyryung/biocompiler-engine/pull/18/checks) for subsequent revisions |
| Recorded demo | Actual dashboard actions, 165 seconds, 1920 × 1080, H.264 video / AAC audio, explicitly synthesized Windows system-voice narration |
| Protein-model acceptance (#9) | Public ESMFold returned a real 290-residue reference structure in 735.779 ms; all residues match UniProt; cache/checksums and client cost are recorded in the bundled metadata |
| Review routing (#4) | [Test PR #19](https://github.com/Xyryung/biocompiler-engine/pull/19) automatically requested MateoDG2006, yukki2126, and Xyryung; the verification PR was then closed |
| Simulator fallback (#11) | Actual fresh local processes measured 2882.053 ms and 2344.649 ms; both valid runs passed and the deliberately broken run returned its error |
| Meta transport preparation (#1/#7/#10/#14) | Installed SDK exercised through an in-process HTTP transport: strict JSON schema, invalid-plan retries, 401/429/503 and timeout errors, empty/refused/truncated completions, actual simulator repair, fragmented SAM SSE, missing terminal events and malformed records |
| Plate geometry | Duplicate/overlapping regions, mismatched crop dimensions, out-of-frame boxes, wrong labware, empty masks and inconsistent physical well labels are rejected before colour measurement |
| Acceptance runner | Planning/compiler/vision reports are independent and atomic; successful stages survive a later failure, failed stages can be retried alone, and authentication failures stop extra calls without writing remote error bodies |
| Authenticated Muse Spark planning | Three goals produced valid specifications; the out-of-domain clinical goal was explicitly refused. See [live planning report](evidence/meta-planning.json) |
| Authenticated Muse Spark compilation | Generated protocol passed actual Opentrons simulation on its first attempt. See [live compiler report](evidence/meta-compiler.json) |
| Authenticated SAM 3.1 | 96 wells in each of three independently segmented frames; minimum IoU 0.9711664482. Calibrated box/point prompts use six batches of up to 16 wells per frame. See [live vision report](evidence/meta-vision.json) |
| Complete live-provider API run | HTTP 200, provider `meta`, simulation successful on attempt one, 96 SAM masks and one review event. See [full response](evidence/meta-api-run.json) |

Transport tests use synthetic HTTP responses and remain separate from the live
acceptance reports above. Free-form concept prompting found no objects on this
synthetic plate; calibrated point/box prompts successfully produced actual SAM
masks. The calibration requirement is explicit in the API implementation and UI.

New background-server startup was rejected by automatic approval review with
the generic reason `blocked by policy`. The full FastAPI route was therefore
verified in process with real external model calls. Browser interaction is covered
by the production-app CI suite; a new live browser session is not claimed.

The browser screenshot is generated at `artifacts/dashboard-1080p.png` and
uploaded by CI as `dashboard-evidence`. The local demo is
`artifacts/demo/biocompiler-demo.mp4`; `recording.json` and `media-validation.json`
record provenance and media properties. Raw captures are ignored by Git. The
final MP4 and metadata are committed under `docs/demo/` for team handoff.

The recording includes normal compilation, a deliberate invalid-well failure and
successful repair, vision observations, and a safety refusal. A human should
watch/listen before submission. Its date is November 3, never backdated to the
November 2 backup target. Remaining acceptance requirements are listed in
[the issue matrix](issue-status.md) and [submission checklist](submission-checklist.md).
