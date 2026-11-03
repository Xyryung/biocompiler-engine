import asyncio

from biocompiler.compiler.codegen import render_protocol
from biocompiler.fixtures import fixture_spec
from biocompiler.sandbox.runner import LocalSimulator


async def test_timed_out_process_is_killed_and_diagnostic_returned(monkeypatch):
    class HungProcess:
        killed = False

        async def communicate(self):
            if not self.killed:
                await asyncio.Event().wait()
            return b"", b""

        def kill(self):
            self.killed = True

    process = HungProcess()
    seen = {}

    async def spawn(*args, **kwargs):
        seen.update(kwargs)
        return process

    monkeypatch.setenv("META_API_KEY", "must-not-reach-subprocess")
    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    simulator = LocalSimulator(timeout=1)
    result = await simulator.simulate(render_protocol(fixture_spec()))
    assert not result.success and process.killed
    assert "terminated" in result.stderr
    assert "META_API_KEY" not in seen["env"]
