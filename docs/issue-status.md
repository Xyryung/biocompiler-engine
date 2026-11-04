# Acceptance matrix

All 17 original issues have been audited against their own acceptance criteria.
Thirteen have verified implementations/deliverables, including the explicitly
allowed cached-protein and local-simulator fallbacks. Four (#1, #7, #10, #14)
still need authenticated Meta acceptance evidence. They stay open until those
calls succeed; `scripts/verify_live_meta.py` performs the bounded checks.

| Issue | Implemented evidence | Remaining acceptance |
| --- | --- | --- |
| #1 Provider interface | Async protocol, packaged mock fixtures, Meta adapter, factory tests, real SDK HTTP serialization/error tests without external calls | Successful authenticated Meta call |
| #2 FastAPI | Compile, health, OpenAPI, JSON errors, structured logs | None for mock mode |
| #3 End-to-end | Real Opentrons pipeline under 30s; refusal integration test; Python and dashboard CI passed on PR #18 | Recheck latest PR revision before merge |
| #4 Team / CODEOWNERS | Four confirmed members have admin/write; shared repository ownership; test PR #19 automatically requested all three other team members | Implemented and verified on the feature base |
| #5 Docs / submission | Reproducible README, demo script, checklist, confirmed account attribution; official terms/waiver reviewed | Issue deliverables verified; contest submission itself is a separate step |
| #6 Fixtures | Minimal, realistic, invalid JSON payloads in test and wheel resources, available to the shared team through PR #18 | Verified |
| #7 Planner | Pydantic validation, strict-schema HTTP contracts, initial call + two retries, readable rationale tests, independent planning acceptance report | Live planner call requires #1 credentials |
| #8 Safety | Two mandatory gates, raised/logged refusals, uncertain/error fail closed, recorded refusal | Issue criteria verified; application scope gate only |
| #9 Protein endpoint | Real public ESMFold API prediction for all 290 reference residues; verified cache, API endpoint, measured latency/cost, backbone preview and PDB download | Cached fallback explicitly permitted by the issue; fresh partner hosting remains optional |
| #10 Compiler | Protocol API 2.19, tip handling, safe prose/fence extraction, installed-SDK response repair against actual simulator errors, independent compiler acceptance | Live Muse Spark output requires #1 credentials |
| #11 Sandbox | Explicit accepted local Opentrons fallback, valid/broken runs, measured first/second process timings, timeout and DSL restrictions | Modal remains an optional deployment choice |
| #12 Healing | Actual injected error recovers; capped failure history tested | None for mock mode |
| #13 Plate source | 11 committed generated PNGs, manifest, MIT provenance, offline extraction | None |
| #14 Segmentation | Official SAM parser through actual SDK SSE decoding; shuffled spatial mapping; duplicate/overlap/bounds/grid checks; truncated or malformed streams rejected; overlay | Live SAM validation; fixed-camera clip only |
| #15 Feedback | RGB series, first-crossing structured event, well-labelled chart | No automatic re-drive; intentionally the documented signal-first scope |
| #16 Dashboard | Next.js production build; five panes from real backend; browser tests | None for mock mode |
| #17 Video | Actual 165-second 1080p dashboard recording, synthesized narration, recording/render scripts and shot list | Deliverable recorded Nov 3; Nov 2 backup milestone was missed and is not backdated |

Review-routing evidence: [PR #19](https://github.com/Xyryung/biocompiler-engine/pull/19)
and [recorded requests](evidence/codeowners.json). Actual local simulator timings:
[benchmark](evidence/simulator.json). Protein prediction: bundled PDB and
`src/biocompiler/resources/petase_esmfold.json` with measured latency and hashes.
