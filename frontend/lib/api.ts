import type {
  CreateRunBody,
  DatasetConfig,
  DatasetOut,
  ProjectOut,
  RunOut,
  RunResultsOut,
  ValidationResult,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type ReqOpts = Omit<RequestInit, "body"> & {
  body?: unknown;
  form?: URLSearchParams;
  raw?: boolean;
};

async function request<T>(path: string, opts: ReqOpts = {}): Promise<T> {
  const headers = new Headers(opts.headers);

  let body: BodyInit | undefined;
  if (opts.form) {
    headers.set("Content-Type", "application/x-www-form-urlencoded");
    body = opts.form.toString();
  } else if (opts.body instanceof FormData) {
    body = opts.body;
  } else if (opts.body != null) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(opts.body);
  }

  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers, body });

  if (!res.ok) {
    let msg = res.statusText;
    try {
      const j = await res.json();
      msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, msg);
  }
  if (opts.raw) return res as unknown as T;
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  // ---- meta ----
  versions: () => request<{ libraries: Record<string, string> }>("/meta/versions"),
  templateUrl: () => `${API_BASE}/meta/template.xlsx`,

  // ---- projects ----
  listProjects: () => request<ProjectOut[]>("/projects"),
  getProject: (id: string) => request<ProjectOut>(`/projects/${id}`),
  createProject: (body: Partial<ProjectOut>) =>
    request<ProjectOut>("/projects", { method: "POST", body }),
  updateProject: (id: string, body: Partial<ProjectOut>) =>
    request<ProjectOut>(`/projects/${id}`, { method: "PATCH", body }),
  deleteProject: (id: string) => request<void>(`/projects/${id}`, { method: "DELETE" }),
  duplicateProject: (id: string) =>
    request<ProjectOut>(`/projects/${id}/duplicate`, { method: "POST" }),

  // ---- datasets ----
  listDatasets: (projectId: string) =>
    request<DatasetOut[]>(`/projects/${projectId}/datasets`),
  uploadDataset: (projectId: string, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<DatasetOut>(`/projects/${projectId}/datasets`, { method: "POST", body: fd });
  },
  getDataset: (id: string) => request<DatasetOut>(`/datasets/${id}`),
  setDatasetConfig: (id: string, config: DatasetConfig) =>
    request<DatasetOut>(`/datasets/${id}/config`, { method: "PATCH", body: { config } }),
  validateDataset: (id: string) =>
    request<ValidationResult>(`/datasets/${id}/validate`, { method: "POST" }),
  cleanDataset: (
    id: string,
    body: {
      drop_row_indices?: number[];
      drop_duplicates?: boolean;
      drop_missing_in_coords?: boolean;
      drop_missing_in_primary?: boolean;
    },
  ) => request<DatasetOut>(`/datasets/${id}/clean`, { method: "POST", body }),

  // ---- runs ----
  listRuns: (projectId: string) => request<RunOut[]>(`/projects/${projectId}/runs`),
  createRun: (projectId: string, body: CreateRunBody) =>
    request<RunOut>(`/projects/${projectId}/runs`, { method: "POST", body }),
  getRun: (id: string) => request<RunOut>(`/runs/${id}`),
  cancelRun: (id: string) => request<RunOut>(`/runs/${id}/cancel`, { method: "POST" }),
  getResults: (id: string) => request<RunResultsOut>(`/runs/${id}/results`),
  reportUrl: (id: string) => `${API_BASE}/runs/${id}/report.pdf`,
  packageUrl: (id: string) => `${API_BASE}/runs/${id}/package.zip`,
  tablesXlsxUrl: (id: string) => `${API_BASE}/runs/${id}/tables.xlsx`,
  artifactUrl: (runId: string, artifactId: string) =>
    `${API_BASE}/runs/${runId}/artifacts/${artifactId}`,
};

/** Faz download de um arquivo do backend. */
export async function downloadFile(url: string, filename: string) {
  const res = await fetch(url);
  if (!res.ok) throw new ApiError(res.status, "Falha no download");
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
}
