"""Partner ESMFold adapter. The LLM never supplies an amino acid sequence."""

import json
import time
from importlib.resources import files
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field

from biocompiler.config import Settings
from biocompiler.contracts.results import ProteinResult


class PartnerPrediction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str = Field(pattern=r"(?i)^esm(?:fold|[-_]?2).*")
    structure_pdb: str = Field(min_length=20, max_length=2_000_000)


async def predict_reference(settings: Settings) -> ProteinResult:
    reference = json.loads(
        files("biocompiler")
        .joinpath("resources", "petase_reference.json")
        .read_text(encoding="utf-8")
    )
    common = {"reference": reference["accession"], "sequence_source": reference["source"]}
    if not settings.protein_endpoint:
        return ProteinResult(
            **common,
            source="reference-only",
            model="none",
            status="not-configured",
            note="Curated UniProt PETase reference only. No ESM prediction or designed variant "
            "is available in offline mode. Connect a partner endpoint to obtain one.",
        )
    if urlparse(settings.protein_endpoint).scheme != "https":
        raise ValueError("PROTEIN_ENDPOINT must use HTTPS")
    if not settings.protein_api_key.get_secret_value():
        raise ValueError("PROTEIN_API_KEY is required for a partner endpoint")
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=60, follow_redirects=False) as client:
        response = await client.post(
            settings.protein_endpoint,
            headers={"Authorization": f"Bearer {settings.protein_api_key.get_secret_value()}"},
            json={"sequence": reference["sequence"]},
        )
        response.raise_for_status()
        prediction = PartnerPrediction.model_validate(response.json())
    if "ATOM " not in prediction.structure_pdb:
        raise ValueError("Protein partner did not return an atom-containing PDB structure")
    return ProteinResult(
        **common,
        source="partner-endpoint",
        model=prediction.model,
        status="predicted",
        structure_pdb=prediction.structure_pdb,
        latency_ms=(time.perf_counter() - start) * 1000,
        cost_usd=settings.protein_cost_usd,
        note="Partner prediction of the curated reference sequence, not a validated "
        "thermostable variant. Cost is the configured per-call estimate, if supplied.",
    )
