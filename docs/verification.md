# Verification evidence — November 3, 2026

The tested product is the offline simulation workflow. No authenticated live
Meta, SAM, Modal, or protein-partner calls are claimed.

| Check | Result |
| --- | --- |
| Python tests | 46 passed, including actual OT-2 simulation, injected failure/recovery, fail-closed refusal, planner retries, three-attempt cap, timeout cleanup, credential stripping, immutable contracts, and shuffled SAM spatial mapping |
| Browser tests | 5 passed against production Next.js and actual FastAPI: full run/download, healing, refusal, network failure, mobile/blank input |
| Python lint / formatting | Ruff passes |
| Python types | mypy passes on all 30 source modules; CI no longer ignores errors |
| Frontend types / build / formatting | TypeScript, production Next.js build, Prettier pass |
| npm production audit | No vulnerabilities reported at test time |
| Python distribution | Wheel and source distribution build; installed wheel simulated successfully from an isolated environment with packaged fixtures |
| GitHub Actions | Both Python and dashboard jobs passed on the initial implementation; inspect the [latest PR checks](https://github.com/Xyryung/biocompiler-engine/pull/18/checks) for subsequent revisions |
| Recorded demo | Actual dashboard actions, 165 seconds, 1920 × 1080, H.264 video / AAC audio, explicitly synthesized Windows system-voice narration |

The browser screenshot is generated at `artifacts/dashboard-1080p.png` and
uploaded by CI as `dashboard-evidence`. The local demo is
`artifacts/demo/biocompiler-demo.mp4`; `recording.json` and `media-validation.json`
record provenance and media properties. Generated media is intentionally ignored
by Git; preserve or upload it separately when submitting.

The recording includes normal compilation, a deliberate invalid-well failure and
successful repair, vision observations, and a safety refusal. A human should
watch/listen before submission. Its date is November 3, never backdated to the
November 2 backup target. Remaining acceptance requirements are listed in
[the issue matrix](issue-status.md) and [submission checklist](submission-checklist.md).
