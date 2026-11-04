export type Sample = {
  seconds: number;
  red: number;
  green: number;
  blue: number;
  signal: number;
};
export type Simulation = {
  success: boolean;
  stdout: string;
  stderr: string;
  backend: string;
  duration_ms: number;
};
export type Run = {
  run_id: string;
  status: "success" | "simulation_failed";
  provider: "mock" | "meta";
  goal: string;
  safety: { decision: string; reason: string };
  spec: {
    experiment_name: string;
    rationale: string;
    steps: { action: string }[];
    labware: unknown[];
  };
  protocol: string;
  simulation: Simulation;
  attempts: { number: number; protocol: string; simulation: Simulation }[];
  vision: {
    source: string;
    imagery: string;
    masks: unknown[];
    overlay_data_url: string;
    series: { labware_id: string; well: string; samples: Sample[] }[];
    adjustments: {
      labware_id: string;
      well: string;
      seconds: number;
      suggestion: string;
      applied: boolean;
    }[];
  };
  protein: {
    source: string;
    reference: string;
    model: string;
    status: string;
    sequence_source: string;
    note: string;
    latency_ms: number | null;
    cost_usd: number | null;
    structure_pdb: string | null;
    cached: boolean;
    prediction_url: string | null;
    generated_at: string | null;
    residue_count: number;
    cache_lookup_ms: number | null;
    cost_basis: string;
  };
};
