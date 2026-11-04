# Verification evidence — November 3, 2026

The tested product is the offline simulation workflow with a real cached ESMFold
prediction. No authenticated Meta, SAM, Modal, or partner-hosted inference is claimed.

| Check | Result |
| --- | --- |
| Python tests | 79 passed, including actual OT-2 simulation, fail-closed refusal, retries/caps, timeout cleanup, immutable contracts, ESMFold cache validation, installed-SDK HTTP/SSE contracts, and negative plate-geometry cases |
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

Transport tests use the real installed SDK and parser but synthetic HTTP responses;
they are deliberately not counted as authenticated Meta or SAM inference. The four
live-dependent issues remain open while credentials are deferred.

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
