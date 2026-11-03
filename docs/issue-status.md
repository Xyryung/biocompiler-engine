# Acceptance matrix

The implementation covers the code portions of all 17 original issues. External
acceptance requirements remain explicit; an implemented adapter is not a live
service verification. Do not close partially satisfied issues as complete.

| Issue | Implemented evidence | Remaining acceptance |
| --- | --- | --- |
| #1 Provider interface | Async protocol, packaged mock fixtures, Meta adapter, factory tests | Successful authenticated Meta call |
| #2 FastAPI | Compile, health, OpenAPI, JSON errors, structured logs | None for mock mode |
| #3 End-to-end | Real Opentrons pipeline under 30s; refusal integration test; Python and dashboard CI passed on PR #18 | Recheck latest PR revision before merge |
| #4 Team / CODEOWNERS | Four existing accounts have admin/write; fallback routing file | Confirm lanes/fourth member; verify routing after base-branch merge |
| #5 Docs / submission | Reproducible README, demo script, checklist, account attribution | Full participant rules and preferred legal names |
| #6 Fixtures | Minimal, realistic, invalid JSON payloads in test and wheel resources | Available through shared PR to all lanes |
| #7 Planner | Pydantic validation, initial call + two retries, readable rationale tests | Live planner call requires #1 credentials |
| #8 Safety | Two mandatory gates, raised/logged refusals, uncertain/error fail closed | Demo gate is not a validated biological risk classifier |
| #9 Protein endpoint | Curated UniProt reference, HTTPS ESMFold partner adapter, provenance tests | Hosting/credentials and real prediction, latency/cost; no invented cached prediction |
| #10 Compiler | Protocol API 2.19, metadata, tip handling, prose/fence extraction | Live Muse Spark output requires #1 credentials |
| #11 Sandbox | Actual local simulator fallback, timeout and DSL restrictions; Modal isolated adapter | Optional Modal authentication/cold timing |
| #12 Healing | Actual injected error recovers; capped failure history tested | None for mock mode |
| #13 Plate source | 11 committed generated PNGs, manifest, MIT provenance, offline extraction | None |
| #14 Segmentation | 96 exact synthetic masks; official SAM parser and shuffled spatial mapping tests; overlay | Live SAM validation; fixed-camera clip only |
| #15 Feedback | RGB series, first-crossing structured event, well-labelled chart | No automatic re-drive; intentionally the documented signal-first scope |
| #16 Dashboard | Next.js production build; five panes from real backend; browser tests | None for mock mode |
| #17 Video | Actual 165-second 1080p dashboard recording, synthesized narration, recording/render scripts and shot list | Human playback review; cannot retroactively meet Nov 2 backup date |
