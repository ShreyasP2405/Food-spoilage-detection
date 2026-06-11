export type Status = "green" | "yellow" | "red";

export interface PredictRequest {
  temp_c: number;
  humidity_pct: number;
  co2_ppm: number;
  ethylene_ppm: number;
  methane_ppm: number;
  hours_since_harvest: number;
  ripeness_estimate: number;
}

export interface ContributingFactor {
  name: string;
  severity: "info" | "warning" | "critical";
  detail: string;
}

export interface PredictionResponse {
  rsl_days: number;
  status: Status;
  confidence: number;
  model_version: string;
  reason: string;
  contributing_factors: ContributingFactor[];
}

export interface SimulateTimelinePoint {
  t_hours: number;
  temp_c: number;
  humidity_pct: number;
  co2_ppm: number;
  ethylene_ppm: number;
  methane_ppm: number;
  rsl_days: number;
  status: Status;
}

export interface SimulateResponse {
  timeline: SimulateTimelinePoint[];
  model_version: string;
}

export interface BananaConstants {
  optimal: { temp_c_target: number; humidity_pct_target: number };
  danger_thresholds: Record<string, number>;
  shelf_life_days: Record<string, [number, number]>;
}

const BASE = "https://food-spoilage-api-docker.onrender.com";

export async function postPredict(req: PredictRequest): Promise<PredictionResponse> {
  const r = await fetch(`${BASE}/api/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!r.ok) throw new Error(`predict ${r.status}`);
  return r.json();
}

export async function getSimulate(opts: {
  temp_c: number;
  humidity_pct: number;
  hours: number;
  initial_ripeness?: number;
  sample_every_h?: number;
}): Promise<SimulateResponse> {
  const q = new URLSearchParams({
    temp_c: String(opts.temp_c),
    humidity_pct: String(opts.humidity_pct),
    hours: String(opts.hours),
    initial_ripeness: String(opts.initial_ripeness ?? 2.0),
    sample_every_h: String(opts.sample_every_h ?? 3.0),
  });
  const r = await fetch(`${BASE}/api/simulate?${q.toString()}`);
  if (!r.ok) throw new Error(`simulate ${r.status}`);
  return r.json();
}

export async function getReference(): Promise<BananaConstants> {
  const r = await fetch(`${BASE}/api/reference/banana`);
  if (!r.ok) throw new Error(`reference ${r.status}`);
  const d = await r.json();
  return d.constants;
}

export async function getHealth(): Promise<{
  status: string;
  model_loaded: boolean;
  model_kind: string;
  model_version: string;
}> {
  const r = await fetch(`${BASE}/api/health`);
  if (!r.ok) throw new Error(`health ${r.status}`);
  return r.json();
}

export interface CsvPredictionRow {
  row_index: number;
  temp_c: number;
  humidity_pct: number;
  co2_ppm: number;
  ethylene_ppm: number;
  methane_ppm: number;
  hours_since_harvest: number;
  ripeness_estimate: number;
  predicted_rsl_days: number;
  predicted_status: Status;
  prediction_reason: string;
  prediction_confidence: number;
  contributing_factor_count: number;
}

export interface CsvPredictionResponse {
  filename: string;
  n_rows: number;
  n_preview_rows: number;
  model_kind: string;
  model_version: string;
  status_counts: { green: number; yellow: number; red: number };
  rsl_stats: { min: number; max: number; mean: number; median: number };
  rows: CsvPredictionRow[];
  annotated_csv: string;
}

export async function postPredictCsv(file: File): Promise<CsvPredictionResponse> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${BASE}/api/predict-csv`, { method: "POST", body: fd });
  if (!r.ok) {
    let msg = `predict-csv ${r.status}`;
    try {
      const j = await r.json();
      msg = j.detail ?? msg;
    } catch (_) { /* ignore */ }
    throw new Error(msg);
  }
  return r.json();
}
