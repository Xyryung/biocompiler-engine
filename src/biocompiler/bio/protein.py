"""Partner ESMFold adapter. The LLM never supplies an amino acid sequence."""

import hashlib
import json
import time
from importlib.resources import files
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field

from biocompiler.bio.structures import validate_structure
from biocompiler.config import Settings
from biocompiler.contracts.results import ProteinResult


class PartnerPrediction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str = Field(pattern=r"(?i)^esm(?:fold|[-_]?2).*")
    structure_pdb: str = Field(min_length=20, max_length=2_000_000)


async def predict_reference(settings: Settings) -> ProteinResult:
    started = time.perf_counter()
    reference = json.loads(
        files("biocompiler")
        .joinpath("resources", "petase_reference.json")
        .read_text(encoding="utf-8")
    )
    common = {"reference": reference["accession"], "sequence_source": reference["source"]}
    if not settings.protein_endpoint:
        resource = files("biocompiler").joinpath("resources")
        metadata = json.loads(resource.joinpath("petase_esmfold.json").read_text(encoding="utf-8"))
        pdb = resource.joinpath("petase_esmfold.pdb").read_text(encoding="utf-8")
        sequence_hash = hashlib.sha256(reference["sequence"].encode()).hexdigest()
        structure_hash = hashlib.sha256(pdb.encode()).hexdigest()
        if (
            metadata["sequence_sha256"] != sequence_hash
            or metadata["structure_sha256"] != structure_hash
        ):
            raise ValueError("Cached ESMFold prediction integrity check failed")
        count = validate_structure(pdb, reference["sequence"])
        return ProteinResult(
            **common,
            source="cached-esmfold",
            model=metadata["model"],
            status="cached",
            cached=True,
            structure_pdb=pdb,
            prediction_url=metadata["endpoint"],
            generated_at=metadata["generated_at"],
            residue_count=count,
            sequence_sha256=sequence_hash,
            structure_sha256=structure_hash,
            latency_ms=metadata["request_latency_ms"],
            cost_usd=metadata["client_cost_usd"],
            cost_basis=metadata["cost_basis"],
            cache_lookup_ms=(time.perf_counter() - started) * 1000,
            note="Cached ESMFold prediction for the curated UniProt PETase reference. "
            "This is a real previously fetched model result, not live inference during this run. "
            "No new variant or experimental enzyme-performance claim is made.",
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
    count = validate_structure(prediction.structure_pdb, reference["sequence"])
    return ProteinResult(
        **common,
        source="partner-endpoint",
        model=prediction.model,
        status="predicted",
        structure_pdb=prediction.structure_pdb,
        prediction_url=settings.protein_endpoint,
        residue_count=count,
        sequence_sha256=hashlib.sha256(reference["sequence"].encode()).hexdigest(),
        structure_sha256=hashlib.sha256(prediction.structure_pdb.encode()).hexdigest(),
        latency_ms=(time.perf_counter() - start) * 1000,
        cost_usd=settings.protein_cost_usd,
        note="Partner prediction of the curated reference sequence, not a validated "
        "thermostable variant. Cost is the configured per-call estimate, if supplied.",
    )
