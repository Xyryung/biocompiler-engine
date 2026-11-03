# BioCompiler demo: target 2:45

Record at 1920 × 1080. Keep API credentials and terminal environment out of frame.
Use the default mock provider and local real Opentrons simulator. Say "offline
mock" explicitly; do not imply live Muse Spark, SAM, or ESMFold inference.

| Time | On screen | Narration |
| --- | --- | --- |
| 0:00–0:15 | Dashboard, scope badge | "BioCompiler is a simulation-only experiment workspace. No physical robot or wet-lab experiment is connected. All plate imagery here is synthetic." |
| 0:15–0:30 | Research goal | "Biological ideas need a validated execution plan. We demonstrate that handoff with PET plastic degradation assays." |
| 0:30–0:48 | Type the PET goal and compile | "One request checks scope, builds a validated specification, compiles Python, and runs the actual Opentrons simulator. This take uses deterministic offline responses." |
| 0:48–1:08 | Spec overview and JSON | "The contract checks deck slots, well references, volumes, and compatible tips. The plan states that temperature stability is not measured by this simulation." |
| 1:08–1:25 | Generated code | "The protocol declares metadata, labware, instruments, and tip handling. The language model integration plans and explains; it never invents protein sequences." |
| 1:25–1:45 | Recovery option, second compile | "Here we inject a deliberate invalid well. Attempt one fails, its diagnostic returns to the compiler, and attempt two passes. The loop stops after at most three attempts." |
| 1:45–2:13 | Simulation and vision panes | "The output is real simulator evidence. Ninety-six masks map to named wells. This fixed-camera synthetic sequence tracks colour over time. A3 crosses the review threshold. The signal proposes review; it does not change a protocol automatically." |
| 2:13–2:30 | Protein provenance | "The reference sequence is curated from UniProt. ESMFold hosting remains an external integration; this offline take does not claim a protein prediction or a validated variant." |
| 2:30–2:42 | Safety refusal | "An unrelated request is stopped before planning or compilation. An uncertain or unavailable classifier also fails closed." |
| 2:42–2:45 | Dashboard scope badge | "A reproducible bridge from intent to simulation evidence." |

## Recording

Use `apps/web/scripts/record-demo.mjs` with both servers running. It records the
actual local dashboard, including normal compilation, recovery, and refusal;
it does not replace API responses. `scripts/narrate-demo.ps1` creates optional
Windows system-voice narration. `scripts/render_demo.py` combines the recording
and narration into an MP4 and checks duration. Generated media lives in ignored
`artifacts/demo/`; preserve it separately for submission.

The requested November 2 backup date has already passed as of November 3, 2026.
Any recording made now must carry its actual date. Review pronunciation, timing,
and audio before submitting; synthesized narration must not be represented as a
human voice recording.
