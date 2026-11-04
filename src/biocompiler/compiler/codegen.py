"""Small deterministic Protocol API v2 backend used by the offline provider."""

from biocompiler.contracts.spec import DelayStep, ExperimentSpec, WellRef

COMPILER_PROMPT = """Compile the supplied validated PET assay spec into an OT-2 Python protocol.
Return only Python. Import only `from opentrons import protocol_api`. Set metadata with
apiLevel '2.19'. Define exactly `def run(protocol: protocol_api.ProtocolContext):`.
Unroll steps, no loops/helpers/control flow. Use simple named labware and pipette variables.
Use load_labware, load_instrument, well indexing, pick_up_tip, transfer, distribute,
consolidate, mix, delay, drop_tip, and comment only. Pick up a tip before each liquid step,
use new_tip='never', and drop it afterwards. Use exactly the declared deck and volumes.
Do not add modules, heating, sequences, imports, file/network operations, or measurements.
If an error is supplied, fix the code while preserving the original specification.
"""


def render_protocol(spec: ExperimentSpec) -> str:
    names = {lw.id: f"lw_{i}" for i, lw in enumerate(spec.labware)}
    lines = [
        "from opentrons import protocol_api",
        "",
        f"metadata = {{'protocolName': {spec.experiment_name!r}, 'apiLevel': '2.19'}}",
        "",
        "def run(protocol: protocol_api.ProtocolContext):",
        "    protocol.comment('SIMULATION ONLY: no robot or temperature control.')",
    ]
    for lw in spec.labware:
        lines.append(
            f"    {names[lw.id]} = protocol.load_labware({lw.load_name!r}, {str(lw.slot)!r})"
        )
    for i, pip in enumerate(spec.pipettes):
        lines.append(
            f"    p_{i} = protocol.load_instrument({pip.load_name!r}, {pip.mount.value!r}, "
            f"tip_racks=[{names[pip.tiprack_id]}])"
        )

    def ref(well: WellRef) -> str:
        return f"{names[well.labware_id]}[{well.well!r}]"

    for step in spec.steps:
        if isinstance(step, DelayStep):
            lines.append(
                f"    protocol.delay(seconds={step.seconds}, msg={step.message or 'Incubation'!r})"
            )
            continue
        # Contract validation ensures the first pipette can handle each step.
        lines.append("    p_0.pick_up_tip()")
        if step.action == "transfer":
            lines.append(
                f"    p_0.transfer({step.volume_ul}, {ref(step.source)}, {ref(step.dest)}, "
                "new_tip='never')"
            )
            if step.mix_after:
                lines.append(
                    f"    p_0.mix({step.mix_after.repetitions}, {step.mix_after.volume_ul}, "
                    f"{ref(step.dest)})"
                )
        elif step.action == "distribute":
            dests = ", ".join(ref(w) for w in step.dests)
            lines.append(
                f"    p_0.distribute({step.volume_ul}, {ref(step.source)}, [{dests}], "
                "new_tip='never')"
            )
        else:
            sources = ", ".join(ref(w) for w in step.sources)
            lines.append(
                f"    p_0.consolidate({step.volume_ul}, [{sources}], {ref(step.dest)}, "
                "new_tip='never')"
            )
        lines.append("    p_0.drop_tip()")
    return "\n".join(lines) + "\n"
