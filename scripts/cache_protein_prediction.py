"""Fetch and validate a real ESMFold prediction for the fixed benign reference.

Network access is explicit here; normal offline runs only read the bundled cache.
The public ESM Atlas endpoint is documented by facebookresearch/esm.
"""

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from biocompiler.bio.structures import validate_structure

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = ROOT / "src/biocompiler/resources"
ENDPOINT = "https://api.esmatlas.com/foldSequence/v1/pdb/"


def main() -> None:
    reference = json.loads((RESOURCE / "petase_reference.json").read_text(encoding="utf-8"))
    start = time.perf_counter()
    response = httpx.post(
        ENDPOINT,
        content=reference["sequence"],
        headers={"Content-Type": "text/plain"},
        timeout=120,
        follow_redirects=False,
    )
    elapsed = (time.perf_counter() - start) * 1000
    response.raise_for_status()
    pdb = response.text.replace("\r\n", "\n")
    count = validate_structure(pdb, reference["sequence"])
    metadata = {
        "reference": reference["accession"],
        "model": "esmfold-v1",
        "endpoint": ENDPOINT,
        "generated_at": datetime.now(UTC).isoformat(),
        "request_latency_ms": round(elapsed, 3),
        "residue_count": count,
        "sequence_sha256": hashlib.sha256(reference["sequence"].encode()).hexdigest(),
        "structure_sha256": hashlib.sha256(pdb.encode()).hexdigest(),
        "client_cost_usd": 0.0,
        "cost_basis": "Public unauthenticated request; no billed project account. "
        "The service's internal compute cost is not published.",
        "method_source": "https://github.com/facebookresearch/esm#esmfold",
        "sequence_source": reference["source"],
        "note": "Real ESMFold reference prediction, cached for the issue #9 fallback. "
        "Not a designed variant or experimental validation.",
    }
    (RESOURCE / "petase_esmfold.pdb").write_text(pdb, encoding="utf-8", newline="\n")
    (RESOURCE / "petase_esmfold.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
