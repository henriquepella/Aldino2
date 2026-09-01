"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { api } from "./api";
import type {
  CreateRunBody,
  DatasetConfig,
  DatasetOut,
  ProjectOut,
  RunOut,
  RunResultsOut,
} from "./types";

// ---------------- Projects ----------------
export function useProjects() {
  return useQuery({ queryKey: ["projects"], queryFn: api.listProjects });
}

export function useProject(id: string) {
  return useQuery({ queryKey: ["project", id], queryFn: () => api.getProject(id), enabled: !!id });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<ProjectOut>) => api.createProject(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useUpdateProject(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<ProjectOut>) => api.updateProject(id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["project", id] });
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteProject(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useDuplicateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.duplicateProject(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

// ---------------- Datasets ----------------
export function useDatasets(projectId: string | undefined) {
  return useQuery({
    queryKey: ["datasets", projectId],
    queryFn: () => api.listDatasets(projectId!),
    enabled: !!projectId,
  });
}

/** Retorna o dataset ativo mais recente do projeto (maior versão). */
export function useActiveDataset(projectId: string | undefined) {
  const q = useDatasets(projectId);
  const active = (q.data ?? []).find((d) => d.is_active) ?? q.data?.[0];
  return { ...q, dataset: active, datasetId: active?.id };
}

export function useDataset(id: string | undefined, opts?: Partial<UseQueryOptions<DatasetOut>>) {
  return useQuery({
    queryKey: ["dataset", id],
    queryFn: () => api.getDataset(id!),
    enabled: !!id,
    ...opts,
  });
}

export function useUploadDataset(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => api.uploadDataset(projectId, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["project", projectId] });
      qc.invalidateQueries({ queryKey: ["projects"] });
      qc.invalidateQueries({ queryKey: ["datasets", projectId] });
    },
  });
}

export function useSetDatasetConfig(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (config: DatasetConfig) => api.setDatasetConfig(id, config),
    onSuccess: (d) => {
      qc.invalidateQueries({ queryKey: ["dataset", id] });
      qc.invalidateQueries({ queryKey: ["datasets", d.project_id] });
    },
  });
}

export function useCleanDataset(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Parameters<typeof api.cleanDataset>[1]) => api.cleanDataset(id, body),
    onSuccess: (d) => {
      qc.invalidateQueries({ queryKey: ["dataset", id] });
      qc.invalidateQueries({ queryKey: ["datasets", d.project_id] });
    },
  });
}

// ---------------- Runs ----------------
export function useRuns(projectId: string) {
  return useQuery({
    queryKey: ["runs", projectId],
    queryFn: () => api.listRuns(projectId),
    enabled: !!projectId,
  });
}

const isLive = (s?: string) => s === "pending" || s === "running";

export function useRun(id: string | undefined) {
  return useQuery({
    queryKey: ["run", id],
    queryFn: () => api.getRun(id!),
    enabled: !!id,
    refetchInterval: (q) => (isLive((q.state.data as RunOut | undefined)?.status) ? 2000 : false),
  });
}

export function useRunResults(id: string | undefined, live = false) {
  return useQuery({
    queryKey: ["run-results", id],
    queryFn: () => api.getResults(id!),
    enabled: !!id,
    refetchInterval: (q) =>
      live && isLive((q.state.data as RunResultsOut | undefined)?.run.status) ? 3000 : false,
  });
}

export function useCreateRun(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateRunBody) => api.createRun(projectId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["runs", projectId] }),
  });
}

export function useCancelRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.cancelRun(id),
    onSuccess: (r) => qc.invalidateQueries({ queryKey: ["run", r.id] }),
  });
}

export function useLibraryVersions() {
  return useQuery({ queryKey: ["versions"], queryFn: api.versions, staleTime: Infinity });
}
