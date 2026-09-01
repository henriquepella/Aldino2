// Espelha os schemas Pydantic do backend (app/schemas).

export interface ColumnInfo {
  name: string;
  dtype: string;
  is_numeric: boolean;
  n_total: number;
  n_missing: number;
  n_unique: number;
  min?: number | null;
  max?: number | null;
  mean?: number | null;
  std?: number | null;
  sample_values: unknown[];
  role_guess: string;
}

export interface CoordinateCandidate {
  column: string;
  score: number;
  reasons: string[];
}

export interface DetectionResult {
  columns: ColumnInfo[];
  coord_x?: string | null;
  coord_y?: string | null;
  coord_kind: "lonlat" | "utm" | "planar" | "unknown";
  coord_confidence: number;
  candidates_x: CoordinateCandidate[];
  candidates_y: CoordinateCandidate[];
  crs_suggested?: string | null;
  crs_label: string;
  crs_confidence: number;
  crs_reason: string;
  crs_alternatives: { epsg: string; label: string }[];
  numeric_variables: string[];
  id_like_columns: string[];
  primary_guess?: string | null;
  secondary_guess: string[];
  explanatory_guess: string[];
  aux_drift_guess?: string | null;
  notes: string[];
}

export interface DatasetConfig {
  x_col: string;
  y_col: string;
  crs: string;
  crs_label: string;
  id_col?: string | null;
  primary: string;
  secondary: string[];
  explanatory: string[];
  aux_drift?: string | null;
  bivariate_pairs: [string, string][];
  negatives_allowed: boolean;
  advanced: Record<string, unknown>;
}

export interface DiagnosticItem {
  item: string;
  value: string;
  status: "ok" | "warn" | "error";
  detail: string;
}

export interface RowFlag {
  row_index: number;
  issues: string[];
  severity: "warn" | "error";
}

export interface ValidationResult {
  summary: DiagnosticItem[];
  counts: Record<string, number>;
  column_missing: Record<string, number>;
  row_flags: RowFlag[];
  crs_ok: boolean;
  can_proceed: boolean;
  notes: string[];
}

export interface DatasetOut {
  id: string;
  project_id: string;
  version: number;
  original_filename: string;
  file_size: number;
  row_count: number;
  col_count: number;
  columns: ColumnInfo[];
  detection?: DetectionResult | null;
  config?: DatasetConfig | null;
  validation?: ValidationResult | null;
  is_active: boolean;
  created_at: string;
}

export interface ProjectOut {
  id: string;
  owner_id: string;
  name: string;
  client: string;
  technical_lead: string;
  description: string;
  variable_units: string;
  analysis_date: string;
  crs: string;
  crs_label: string;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  dataset_count: number;
  run_count: number;
  latest_run_id?: string | null;
}

export type RunStatus = "pending" | "running" | "done" | "failed" | "cancelled";

export interface StepState {
  key: string;
  title: string;
  status: "pending" | "running" | "ok" | "skipped" | "failed";
  reason?: string | null;
  n_tables: number;
  n_figures: number;
  metrics: Record<string, unknown>;
}

export interface LogLine {
  t: string;
  step: string;
  msg: string;
}

export interface RunOut {
  id: string;
  project_id: string;
  dataset_id: string;
  status: RunStatus;
  mode: string;
  progress: number;
  current_step: string;
  steps: StepState[];
  log: LogLine[];
  metrics_summary: Record<string, any>;
  manifest: Record<string, any>;
  lib_versions: Record<string, string>;
  error: string;
  started_at?: string | null;
  finished_at?: string | null;
  created_at: string;
}

export interface TablePayload {
  name: string;
  title: string;
  caption: string;
  columns: { key: string; label: string }[];
  rows: Record<string, string | number | null>[];
  highlight_rows: number[];
  meta: Record<string, unknown>;
}

export interface ArtifactOut {
  id: string;
  run_id: string;
  kind: "table" | "figure" | "map" | "report" | "export" | "package" | "data";
  step_key: string;
  name: string;
  title: string;
  caption: string;
  mime: string;
  size: number;
  url: string;
  data: {
    payload?: TablePayload;
    variants?: Record<string, string>;
    meta?: Record<string, unknown>;
    kind?: string;
    highlight_rows?: number[];
  };
}

export interface StepResultOut {
  key: string;
  title: string;
  status: "ok" | "skipped" | "failed";
  reason?: string | null;
  interpretation?: string | null;
  metrics: Record<string, any>;
  params_used: Record<string, unknown>;
  tables: ArtifactOut[];
  figures: ArtifactOut[];
}

export interface RunResultsOut {
  run: RunOut;
  steps: StepResultOut[];
  report_url?: string | null;
  package_url?: string | null;
}

export interface CreateRunBody {
  dataset_id: string;
  mode?: "full" | "custom";
  advanced?: Record<string, unknown>;
  steps?: string[] | null;
}
