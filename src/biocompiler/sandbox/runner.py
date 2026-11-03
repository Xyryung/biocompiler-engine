import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Protocol

from biocompiler.config import Settings
from biocompiler.contracts.results import SimulationResult
from biocompiler.sandbox.policy import validate_protocol


class Simulator(Protocol):
    async def simulate(self, code: str) -> SimulationResult: ...


class LocalSimulator:
    """Restricted protocols in a timed subprocess. Never a robot connection."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def simulate(self, code: str) -> SimulationResult:
        start = time.perf_counter()
        stdout = stderr = ""
        success = False
        try:
            validate_protocol(code)
            with tempfile.TemporaryDirectory(prefix="biocompiler-") as directory:
                path = Path(directory) / "protocol.py"
                path.write_text(code, encoding="utf-8")
                # No API keys or other inherited credentials in generated code's process.
                env = {
                    k: v
                    for k, v in os.environ.items()
                    if k.upper()
                    in {
                        "SYSTEMROOT",
                        "WINDIR",
                        "PATH",
                        "TEMP",
                        "TMP",
                        "LOCALAPPDATA",
                    }
                }
                env["OT_API_FF_enableOT3HardwareController"] = "false"
                env["USERPROFILE"] = directory
                env["HOME"] = directory
                creationflags = 0x08000000 if sys.platform == "win32" else 0
                proc = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-I",
                    "-X",
                    "utf8",
                    "-m",
                    "opentrons.simulate",
                    str(path),
                    cwd=directory,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    creationflags=creationflags,
                )
                try:
                    out, err = await asyncio.wait_for(proc.communicate(), self.timeout)
                except (TimeoutError, asyncio.CancelledError):
                    proc.kill()
                    await proc.communicate()
                    raise
                stdout = out.decode(errors="replace")[-40_000:]
                stderr = err.decode(errors="replace")[-20_000:]
                success = proc.returncode == 0
        except TimeoutError:
            stderr = f"Simulation exceeded {self.timeout} seconds and was terminated."
        except (ValueError, SyntaxError, OSError) as exc:
            stderr = str(exc)
        return SimulationResult(
            success=success,
            stdout=stdout,
            stderr=stderr,
            backend="local-opentrons",
            duration_ms=(time.perf_counter() - start) * 1000,
        )


def get_simulator(settings: Settings) -> Simulator:
    if settings.biocompiler_simulator == "modal":
        from biocompiler.sandbox.remote import ModalSimulator

        return ModalSimulator(settings.simulation_timeout_seconds)
    return LocalSimulator(settings.simulation_timeout_seconds)
