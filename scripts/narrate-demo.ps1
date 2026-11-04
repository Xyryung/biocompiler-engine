# Optional synthesized narration for the real screen recording, not a human voice.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$demoDirectory = Join-Path (Split-Path -Parent $PSScriptRoot) 'artifacts\demo'
New-Item -ItemType Directory -Path $demoDirectory -Force | Out-Null
$segments = @(
    @{start=0; text='BioCompiler is a simulation-only experiment workspace. No physical robot or wet-lab experiment is connected. All plate imagery here is synthetic.'},
    @{start=15; text='Biological ideas need a validated execution plan. We demonstrate that handoff with PET plastic degradation assays.'},
    @{start=30; text='One request checks scope, builds a specification, compiles Python, and runs the actual Opentrons simulator. This recording uses deterministic offline model responses.'},
    @{start=45; text='The contract checks deck slots, well references, volumes, and compatible tips. The plan explicitly states that temperature stability is not measured by this simulation.'},
    @{start=60; text='The JSON specification is validated before compilation. Unknown fields and broken references fail loudly, with at most two planning retries.'},
    @{start=75; text='The generated Python declares protocol metadata, labware, instruments, and tip handling. It uses the documented Protocol API.'},
    @{start=90; text='Now we inject a deliberately invalid tip well. The first attempt fails. Its diagnostic goes back to the compiler, and the second attempt passes. The cap is three attempts.'},
    @{start=106; text='These are actual simulator logs, including both the failed attempt and the repair. There is no connection to laboratory hardware.'},
    @{start=118; text='Ninety-six masks map to named wells. This fixed-camera synthetic sequence tracks colour over time. Well A three crosses the review threshold. The signal suggests review; it does not automatically change a protocol.'},
    @{start=135; text='This is a real ESMFold reference prediction, cached from the public endpoint. Its residues match the UniProt sequence. Download the predicted structure here. It is not a new variant or measured enzyme performance.'},
    @{start=150; text='An unrelated request is stopped before planning or compilation. An uncertain or unavailable classifier also fails closed. BioCompiler connects intent to reproducible simulation evidence.'}
)
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speaker.SelectVoice('Microsoft Zira Desktop')
$speaker.Rate = 1
$speaker.Volume = 100
try {
    for ($i = 0; $i -lt $segments.Count; $i++) {
        $filename = 'narration-{0:D2}.wav' -f $i
        $speaker.SetOutputToWaveFile((Join-Path $demoDirectory $filename))
        $speaker.Speak($segments[$i].text)
        $speaker.SetOutputToNull()
        $segments[$i].file = $filename
    }
} finally { $speaker.Dispose() }
$segments | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $demoDirectory 'narration.json') -Encoding utf8
Write-Output 'Synthesized narration created. Review before submission.'
