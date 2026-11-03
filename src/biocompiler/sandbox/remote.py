"""Modal 1.6 sandbox with cached image, no secrets, and blocked network."""

import time

from biocompiler.contracts.results import SimulationResult
from biocompiler.sandbox.policy import validate_protocol


class ModalSimulator:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def simulate(self, code: str) -> SimulationResult:
        import modal

        validate_protocol(code)
        start = time.perf_counter()
        image = modal.Image.debian_slim(python_version="3.12").pip_install("opentrons==8.8.2")
        app = await modal.App.lookup.aio("biocompiler-simulation", create_if_missing=True)
        sandbox = await modal.Sandbox.create.aio(
            "python",
            "-I",
            "-c",
            "import sys,io; from opentrons.simulate import simulate; "
            "r,_=simulate(io.StringIO(sys.stdin.read())); "
            "print('\\n'.join(s['payload']['text'] for s in r))",
            app=app,
            image=image,
            timeout=self.timeout,
            block_network=True,
        )
        try:
            sandbox.stdin.write(code)
            sandbox.stdin.write_eof()
            await sandbox.stdin.drain.aio()
            await sandbox.wait.aio()
            stdout = await sandbox.stdout.read.aio()
            stderr = await sandbox.stderr.read.aio()
            return SimulationResult(
                success=sandbox.returncode == 0,
                stdout=stdout[-40000:],
                stderr=stderr[-20000:],
                backend="modal-opentrons",
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        finally:
            await sandbox.terminate.aio()
