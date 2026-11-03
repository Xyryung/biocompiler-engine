"use client";

import { FormEvent, useState } from "react";
import type { Run, Sample } from "./types";

const EXAMPLE = "Design a PET-degrading enzyme assay stable at 45C.";

function download(name: string, text: string, type = "text/plain") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const link = document.createElement("a");
  link.href = url; link.download = name; link.click(); URL.revokeObjectURL(url);
}

function Chart({ samples }: { samples: Sample[] }) {
  const points = samples.map(s => `${45 + s.seconds / 300 * 510},${150 - s.signal * 95}`).join(" ");
  return <svg className="chart" viewBox="0 0 590 220" role="img" aria-label="Measured colour signal over time">
    {[0, 60, 120, 180].map(y => <line key={y} x1="45" x2="560" y1={y+15} y2={y+15} stroke="#253d45" />)}
    <text x="4" y="22">+1.0</text><text x="12" y="154">0</text><text x="4" y="199">−0.5</text>
    <polyline fill="none" stroke="#78dfbf" strokeWidth="3" points={points} />
    {samples.map(s => <circle key={s.seconds} cx={45+s.seconds/300*510} cy={150-s.signal*95} r="3" fill="#b1f4dc" />)}
    <text x="42" y="216">0s</text><text x="275" y="216">150s</text><text x="530" y="216">300s</text>
  </svg>;
}

export default function Dashboard() {
  const [goal, setGoal] = useState(EXAMPLE);
  const [demoFailure, setDemoFailure] = useState(false);
  const [busy, setBusy] = useState(false);
  const [run, setRun] = useState<Run | null>(null);
  const [error, setError] = useState<{ refused: boolean; message: string } | null>(null);
  const [well, setWell] = useState("A3");
  const [specTab, setSpecTab] = useState<"summary" | "json">("summary");
  const selected = run?.vision.series.find(s => s.well === well);

  async function compile(event: FormEvent) {
    event.preventDefault();
    if (!goal.trim() || busy) return;
    setBusy(true); setRun(null); setError(null);
    try {
      const response = await fetch("/api/compile", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ goal, demo_failure: demoFailure }) });
      const result = await response.json();
      if (result.run_id) setRun(result);
      else setError({ refused: result.status === "refused", message: result.error?.message || "The run could not be completed." });
    } catch {
      setError({ refused: false, message: "Connection interrupted. Try the run again." });
    } finally { setBusy(false); }
  }

  return <>
    <header className="topbar"><a className="brand" href="/" aria-label="BioCompiler home"><span className="brandmark">b<span>c</span></span>BioCompiler<span className="engine">ENGINE</span></a><div className="topright"><span className="pill"><i />Simulation workspace</span><a href="https://github.com/Xyryung/biocompiler-engine" target="_blank" rel="noreferrer">Repository ↗</a></div></header>
    <main>
      <div className="intro"><div><div className="eyebrow">FROM INTENT TO EXPERIMENT</div><h1>A shorter path to <em>discovery.</em></h1><p>Plan a PET assay. Compile the protocol. Observe what changes.</p></div><div className="scope"><span className="scopeicon">◈</span><div><strong>Simulation only</strong><small>No robot connected. Plate imagery is synthetic.</small></div></div></div>
      <div className="workflow" aria-label="Pipeline stages">{["Define", "Safety gate", "Plan", "Compile + simulate", "Observe"].map((s,i) => <div key={s} className={run ? "complete" : ""}><span>{run ? "✓" : `0${i+1}`}</span>{s}{i<4 && <b>→</b>}</div>)}</div>

      <section className="panel goalpanel" aria-labelledby="goal-heading"><div className="sectionhead"><h2 id="goal-heading"><span className="index">01</span>Research goal</h2><span className="muted">PET degradation · OT-2</span></div><form onSubmit={compile}><label className="sr-only" htmlFor="goal">Research goal</label><textarea id="goal" value={goal} onChange={e=>setGoal(e.target.value)} maxLength={2000} minLength={5} required disabled={busy} /><div className="formfooter"><div className="examples"><button type="button" onClick={()=>{setGoal(EXAMPLE); setDemoFailure(false);}} disabled={busy}>↗ Example assay</button><button type="button" onClick={()=>{setGoal("Help me plan an unrelated human clinical experiment."); setDemoFailure(false);}} disabled={busy}>Test safety refusal</button><label><input type="checkbox" checked={demoFailure} onChange={e=>setDemoFailure(e.target.checked)} disabled={busy} />Demonstrate recovery <span className="muted">(mock only)</span></label></div><button className="primary" disabled={busy || goal.trim().length < 5}>{busy ? <><span className="spinner" />Running pipeline…</> : <>Compile experiment <span>↗</span></>}</button></div></form></section>

      {error && <section className={`notice ${error.refused ? "refused" : "failed"}`} role="alert"><span>{error.refused ? "◇" : "!"}</span><div><h2>{error.refused ? "Stopped by the safety gate" : "Run could not complete"}</h2><p>{error.message}</p>{error.refused && <small>No protocol was compiled or simulated.</small>}</div></section>}
      {busy && <div className="running" role="status"><span className="spinner" />Validating scope, planning, simulating, and reading the synthetic plate. Results appear when the run completes.</div>}

      {!run && !busy && !error && <div className="empty"><div className="emptyglyph">⌘</div><h2>Your next experiment starts here.</h2><p>One run brings the specification, executable protocol,<br/>simulation evidence, and plate observations into view.</p><span>MANDATORY SAFETY GATE · AT MOST 3 COMPILE ATTEMPTS</span></div>}

      {run && <>
        <div className="runbar"><div><span className={`status ${run.status === "success" ? "success" : "failure"}`}>{run.status === "success" ? "● Simulation passed" : "● Simulation failed"}</span><span className="muted">Run {run.run_id.slice(0,8)}</span></div><div><span className="tag">{run.provider === "mock" ? "OFFLINE MOCK" : "LIVE META"}</span><span className="muted">{run.attempts.length} attempt{run.attempts.length>1 ? "s" : ""} · {(run.simulation.duration_ms/1000).toFixed(2)}s simulation</span><button onClick={()=>download(`run-${run.run_id}.json`,JSON.stringify(run,null,2),"application/json")}>Export run ↓</button></div></div>
        <div className="resultsgrid">
          <section className="panel specpanel" aria-labelledby="spec-heading"><div className="sectionhead"><h2 id="spec-heading"><span className="index">02</span>Experiment specification</h2><div className="tabs"><button className={specTab==="summary"?"active":""} onClick={()=>setSpecTab("summary")}>Overview</button><button className={specTab==="json"?"active":""} onClick={()=>setSpecTab("json")}>JSON</button></div></div>{specTab==="json" ? <pre className="code specjson">{JSON.stringify(run.spec,null,2)}</pre> : <div className="panelbody"><span className="eyebrow">VALIDATED PLAN</span><h3>{run.spec.experiment_name}</h3><p>{run.spec.rationale}</p><div className="stats"><div><strong>{run.spec.steps.length}</strong><span>protocol steps</span></div><div><strong>{run.spec.labware.length}</strong><span>deck positions</span></div><div><strong>96</strong><span>observed wells</span></div></div><div className="safetyline">✓ {run.safety.reason}</div><div className="provenance"><strong>Protein model provenance</strong><p>{run.protein.note}</p><a href={run.protein.sequence_source} target="_blank" rel="noreferrer">UniProt {run.protein.reference} ↗</a>{run.protein.status==="predicted" && <p>{run.protein.model} · {run.protein.latency_ms?.toFixed(0)} ms · {run.protein.cost_usd===null ? "cost not configured" : `$${run.protein.cost_usd.toFixed(4)} estimated`}</p>}</div></div>}</section>
          <section className="panel protocolpanel" aria-labelledby="protocol-heading"><div className="sectionhead"><h2 id="protocol-heading"><span className="index">03</span>Generated protocol</h2><button onClick={()=>download("pet-assay.py",run.protocol)}>Download .py ↓</button></div><div className="filebar"><span>◉ pet-assay.py</span><span>Python · Protocol API 2.19</span></div><pre className="code protocolcode">{run.protocol.split("\n").map((line,i)=><div className="codeline" key={i}><span className="lineno">{i+1}</span><code>{line || " "}</code></div>)}</pre></section>
          <section className="panel simulationpanel" aria-labelledby="simulation-heading"><div className="sectionhead"><h2 id="simulation-heading"><span className="index">04</span>Simulation evidence</h2><span className="muted">{run.simulation.backend}</span></div><div className="attempts">{run.attempts.map(attempt=><details key={attempt.number} open={attempt.number===run.attempts.length || !attempt.simulation.success}><summary><span className={attempt.simulation.success?"good":"bad"}>{attempt.simulation.success?"✓":"↻"}</span>Attempt {attempt.number}<span className="muted">{attempt.simulation.success?"Passed":"Failed — diagnostic sent for repair"}</span><span>{(attempt.simulation.duration_ms/1000).toFixed(2)}s</span></summary><pre className="terminal">{attempt.simulation.stdout || "No simulator output."}</pre>{attempt.simulation.stderr && <details className="stderr" open={!attempt.simulation.success}><summary>{attempt.simulation.success?"Simulator warnings":"Failure diagnostic"}</summary><pre className="terminal">{attempt.simulation.stderr}</pre></details>}</details>)}</div></section>
          <section className="panel visionpanel" aria-labelledby="vision-heading"><div className="sectionhead"><h2 id="vision-heading"><span className="index">05</span>Plate observations</h2><span className="tag">SYNTHETIC IMAGERY</span></div><div className="visionbody"><div><img className="plate" src={run.vision.overlay_data_url} alt="96-well plate segmentation overlay; delayed well A3 is highlighted in amber" /><div className="imagecaption"><span><i className="dot"/>Mapped well</span><span><i className="dot amber"/>Review suggested</span><span>{run.vision.source}</span></div></div><div className="charthead"><div><strong>Colour response</strong><small>Signal (R − B) / 255 · fixed camera</small></div><label>Well <select value={well} onChange={e=>setWell(e.target.value)}>{run.vision.series.map(s=><option key={s.well}>{s.well}</option>)}</select></label></div>{selected && <Chart samples={selected.samples} />}{run.vision.adjustments.map(event=><div className="adjustment" key={`${event.labware_id}:${event.well}`}><span>↳</span><div><strong>{event.well} · slower response at {event.seconds}s</strong><p>{event.suggestion}</p><small>REVIEW SIGNAL · NOT APPLIED</small></div></div>)}</div></section>
        </div>
      </>}
      <footer><span>BioCompiler Engine / Meta Global AI Developer Hackathon</span><span>Simulation evidence, with provenance.</span></footer>
    </main>
  </>;
}
