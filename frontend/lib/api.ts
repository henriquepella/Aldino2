import type {
  CreateRunBody,
  DatasetConfig,
  DatasetOut,
  ProjectOut,
  RunOut,
  RunResultsOut,
  Token,
  UserOut,
  ValidationResult,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "/api";

const TOKEN_KEY = "geo_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(t: string | null) {
  if (typeof window === "undefined") return;
  try {
    if (t) window.localStorage.setItem(TOKEN_KEY, t);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

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
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

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

  if (res.status === 401 && typeof window !== "undefined") {
    setToken(null);
  }
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
  // ---- auth ----
  register: (email: string, password: string, full_name = "") =>
    request<Token>("/auth/register", { method: "POST", body: { email, password, full_name } }),
  login: (email: string, password: string) =>
    request<Token>("/auth/login", {
      method: "POST",
      form: new URLSearchParams({ username: email, password }),
    }),
  me: () => request<UserOut>("/auth/me"),

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

/** Faz download autenticado de um arquivo (o backend exige Bearer). */
export async function downloadFile(url: string, filename: string) {
  const token = getToken();
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
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

/** URL de imagem/artefato com token em querystring (para <img src>). */
export function authedAssetUrl(url: string): string {
  const token = getToken();
  if (!token) return url;
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}token=${encodeURIComponent(token)}`;
}
