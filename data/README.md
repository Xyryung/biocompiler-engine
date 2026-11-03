# Synthetic plate sequence

`synthetic/frame_000.png` through `frame_300.png` are 11 frames at 30-second
intervals, generated entirely by `scripts/generate_plate_data.py` and
`biocompiler.vision.synthetic`. License: the repository's MIT license. No external
photographs, personal data, or laboratory measurements are included.

Regenerate or extract all frames locally, without network access:

```sh
uv run python scripts/generate_plate_data.py
```

An aligned, fixed-camera 8 × 12 plate has a deterministic blue-to-yellow colour
change. A3 deliberately lags to exercise the feedback threshold. Synthetic
geometry supplies the offline masks; SAM 3.1 supplies masks only when the Meta
provider is selected. These are separate, explicitly labelled sources. Masks
from the first frame are held fixed across this fixed-camera clip; arbitrary
camera motion and real-video tracking are outside the current demo.

The API computes its imagery with the same generator, so an installed wheel
does not depend on a checkout's `data/` directory. The included PNG sequence is
the source evidence for the vision lane. `manifest.json` records timestamps.

The curated PETase sequence in `src/biocompiler/resources/petase_reference.json`
comes from [UniProt A0A0K8P6T7](https://www.uniprot.org/uniprotkb/A0A0K8P6T7/entry),
retrieved on 2026-11-03. UniProt data is licensed under
[CC BY 4.0](https://www.uniprot.org/help/license). It is a known reference sequence,
not an LLM-designed sequence, cached ESM prediction, or new variant.
