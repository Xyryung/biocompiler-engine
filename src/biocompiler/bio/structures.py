"""Validate model structures against the curated sequence before caching or serving."""

import math

RESIDUES = dict(
    zip(
        [
            "ALA",
            "ARG",
            "ASN",
            "ASP",
            "CYS",
            "GLN",
            "GLU",
            "GLY",
            "HIS",
            "ILE",
            "LEU",
            "LYS",
            "MET",
            "PHE",
            "PRO",
            "SER",
            "THR",
            "TRP",
            "TYR",
            "VAL",
        ],
        "ARNDCQEGHILKMFPSTWYV",
        strict=True,
    )
)


def validate_structure(pdb: str, sequence: str) -> int:
    residues = {}
    for line in pdb.splitlines():
        if not line.startswith("ATOM  "):
            continue
        if len(line) < 54:
            raise ValueError("Truncated PDB atom record")
        coordinates = [float(line[start : start + 8]) for start in (30, 38, 46)]
        if not all(math.isfinite(number) for number in coordinates):
            raise ValueError("PDB coordinates must be finite")
        if line[12:16].strip() == "CA":
            key = (line[21], line[22:27])
            if key in residues:
                raise ValueError("Duplicate alpha-carbon residue in PDB")
            residues[key] = RESIDUES.get(line[17:20], "X")
    if "".join(residues.values()) != sequence:
        raise ValueError("Predicted PDB sequence does not match the curated reference")
    return len(residues)
