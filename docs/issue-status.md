# Acceptance matrix

All 17 original issues have verified implementations/deliverables, including the
explicitly allowed cached-protein and local-simulator fallbacks. Authenticated
Muse Spark and SAM checks now pass, and a real-provider FastAPI compile run
returned HTTP 200 with successful simulation and 96 SAM masks. The November 2
video backup milestone was missed; the actual delivered take is dated November 3.

| Issue | Implemented evidence | Remaining acceptance |
| --- | --- | --- |
| #1 Provider interface | Async protocol, mock and Meta factories; actual authenticated Muse Spark calls and real-provider API run | Verified |
| #2 FastAPI | Compile, health, OpenAPI, JSON errors, structured logs | None for mock mode |
| #3 End-to-end | Real Opentrons pipeline under 30s; refusal integration test; Python and dashboard CI passed on PR #18 | Recheck latest PR revision before merge |
| #4 Team / CODEOWNERS | Four confirmed members have admin/write; shared repository ownership; test PR #19 automatically requested all three other team members | Implemented and verified on the feature base |
| #5 Docs / submission | Reproducible README, demo script, checklist, confirmed account attribution; official terms/waiver reviewed | Issue deliverables verified; contest submission itself is a separate step |
| #6 Fixtures | Minimal, realistic, invalid JSON payloads in test and wheel resources, available to the shared team through PR #18 | Verified |
| #7 Planner | Three distinct goals produced validated specifications through actual Muse Spark; strict-schema/retry/error tests pass | Verified |
| #8 Safety | Two mandatory gates, raised/logged refusals, uncertain/error fail closed, recorded refusal | Issue criteria verified; application scope gate only |
| #9 Protein endpoint | Real public ESMFold API prediction for all 290 reference residues; verified cache, API endpoint, measured latency/cost, backbone preview and PDB download | Cached fallback explicitly permitted by the issue; fresh partner hosting remains optional |
| #10 Compiler | Actual Muse Spark output passed real Opentrons simulation on attempt one; tip handling and prose/fence extraction verified | Verified |
| #11 Sandbox | Explicit accepted local Opentrons fallback, valid/broken runs, measured first/second process timings, timeout and DSL restrictions | Modal remains an optional deployment choice |
| #12 Healing | Actual injected error recovers; capped failure history tested | None for mock mode |
| #13 Plate source | 11 committed generated PNGs, manifest, MIT provenance, offline extraction | None |
| #14 Segmentation | Real SAM with calibrated prompts returned 96 wells in each of three frames; minimum cross-frame IoU 0.971166; real-provider overlay generated | Verified for the calibrated synthetic plate |
| #15 Feedback | RGB series, first-crossing structured event, well-labelled chart | No automatic re-drive; intentionally the documented signal-first scope |
| #16 Dashboard | Next.js production build; five panes from real backend; browser tests | None for mock mode |
| #17 Video | Actual 165-second 1080p dashboard recording, synthesized narration, recording/render scripts and shot list | Deliverable recorded Nov 3; Nov 2 backup milestone was missed and is not backdated |

Review-routing evidence: [PR #19](https://github.com/Xyryung/biocompiler-engine/pull/19)
and [recorded requests](evidence/codeowners.json). Actual local simulator timings:
[benchmark](evidence/simulator.json). Protein prediction: bundled PDB and
`src/biocompiler/resources/petase_esmfold.json` with measured latency and hashes.

Live evidence: [planning](evidence/meta-planning.json),
[compiler](evidence/meta-compiler.json), [SAM stability](evidence/meta-vision.json),
and [complete API response](evidence/meta-api-run.json). The implementation is in
PR #18; merging to protected main still requires a human approval.
