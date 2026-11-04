"""Bounded real Meta acceptance, with independent resumable stage reports."""

import argparse
import asyncio
import json
from pathlib import Path

from biocompiler.acceptance import STAGES, verify_stages
from biocompiler.config import Settings
from biocompiler.providers.meta import MetaProvider
from biocompiler.sandbox.runner import LocalSimulator


async def main(stage: str) -> int:
    settings = Settings(biocompiler_provider="meta")
    if settings.meta_base_url.rstrip("/") != "https://api.meta.ai/v1":
        raise ValueError("Live acceptance must use the official Meta endpoint")
    provider = MetaProvider(settings)
    output = Path(__file__).resolve().parents[1] / "artifacts/acceptance"
    try:
        report = await verify_stages(
            provider,
            LocalSimulator(),
            output,
            stages=STAGES if stage == "all" else (stage,),
            live=True,
        )
        if stage == "all":
            (output / "live-meta.json").write_text(
                json.dumps(report, indent=2) + "\n",
                encoding="utf-8",
            )
        for name, result in report["stages"].items():
            print(f"{name}: {result['status']} ({output / f'meta-{name}.json'})")
        return 0 if report["status"] == "passed" else 1
    finally:
        await provider.client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("all", *STAGES), default="all")
    arguments = parser.parse_args()
    raise SystemExit(asyncio.run(main(arguments.stage)))
