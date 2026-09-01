"use client";

import { use, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  FileSpreadsheet,
  FileText,
  LayoutDashboard,
  MinusCircle,
  Package,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  EmptyState,
  MetricCard,
  RunProgress,
  STEP_ORDER,
  StepStatusBadge,
} from "@/components/results";
import { api, ApiError, downloadFile } from "@/lib/api";
import { useRun, useRunResults, useRuns } from "@/lib/hooks";
import { fmtInt, fmtNum } from "@/lib/format";
import type { RunOut } from "@/lib/types";
import { cn } from "@/lib/utils";

const TITLE_BY_KEY = new Map(STEP_ORDER.map((s) => [s.key, s.title]));
function stepTitle(key: string): string {
  return TITLE_BY_KEY.get(key) ?? key;
}

function num(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

export default function DashboardPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: projectId } = use(params);
  const runsQ = useRuns(projectId);

  const [storedRunId, setStoredRunId] = useState<string | null>(null);
  useEffect(() => {
    try {
      setStoredRunId(sessionStorage.getItem(`run:${projectId}`));
    } catch {
      setStoredRunId(null);
    }
  }, [projectId]);

  const runId = useMemo(() => {
    const runs = runsQ.data ?? [];
    if (storedRunId && runs.some((r) => r.id === storedRunId)) return storedRunId;
    if (storedRunId && runsQ.isLoading) return storedRunId;
    const done = runs
      .filter((r) => r.status === "done")
      .sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
    if (done[0]) return done[0].id;
    const live = runs
      .filter((r) => r.status === "running" || r.status === "pending")
      .sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
    return live[0]?.id ?? null;
  }, [runsQ.data, runsQ.isLoading, storedRunId]);

  const runQ = useRun(runId ?? undefined);

  if (runsQ.isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    );
  }

  if (runsQ.isError) {
    return (
      <p className="text-sm text-destructive">
        Não foi possível carregar as execuções deste projeto. Tente novamente mais tarde.
      </p>
    );
  }

  if (!runId) {
    return (
      <EmptyState
        icon={LayoutDashboard}
        title="Nenhuma análise executada"
        description="Execute a análise geoestatística completa para visualizar o painel de resultados."
        action={
          <Button asChild>
            <Link href={`/projects/${projectId}/run`}>Executar análise</Link>
          </Button>
        }
      />
    );
  }

  return (
    <DashboardContent
      projectId={projectId}
      runId={runId}
      run={runQ.data}
      runLoading={runQ.isLoading}
      runError={runQ.error}
    />
  );
}

function DashboardContent({
  projectId,
  runId,
  run,
  runLoading,
  runError,
}: {
  projectId: string;
  runId: string;
  run: RunOut | undefined;
  runLoading: boolean;
  runError: unknown;
}) {
  const resultsQ = useRunResults(runId, true);
  const results = resultsQ.data;
  const activeRun = results?.run ?? run;

  if (runLoading && !activeRun) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    );
  }

  if (runError && !activeRun) {
    const msg =
      runError instanceof ApiError
        ? runError.message
        : "Não foi possível carregar esta execução.";
    return <p className="text-sm text-destructive">{msg}</p>;
  }

  if (!activeRun) {
    return <p className="text-sm text-muted-foreground">Carregando resultados…</p>;
  }

  const isLive = activeRun.status === "running" || activeRun.status === "pending";
  const m = activeRun.metrics_summary ?? {};
  const units = typeof m.units === "string" && m.units ? ` ${m.units}` : "";
  const primary = typeof m.primary === "string" ? m.primary : "variável principal";

  const moranP = num(m.morans_p);
  const moranAccent =
    moranP == null ? "default" : moranP < 0.05 ? "success" : "warning";
  const moranHint =
    moranP == null
      ? "Autocorrelação espacial global"
      : moranP < 0.05
        ? `Significativo (p = ${fmtNum(moranP, 3)})`
        : `Não significativo (p = ${fmtNum(moranP, 3)})`;

  return (
    <div className="space-y-8">
      {/* Cabeçalho + ações */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Painel de resultados</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {activeRun.status === "done"
              ? "Síntese da análise geoestatística completa."
              : activeRun.status === "failed"
                ? "A execução falhou antes de concluir."
                : activeRun.status === "cancelled"
                  ? "Execução cancelada."
                  : "Execução em andamento — os resultados aparecem conforme concluem."}
          </p>
        </div>
        <DownloadActions runId={runId} disabled={activeRun.status !== "done"} />
      </div>

      {/* Progresso quando ainda rodando */}
      {isLive ? (
        <Card>
          <CardContent className="pt-5">
            <RunProgress run={activeRun} />
          </CardContent>
        </Card>
      ) : null}

      {activeRun.status === "failed" && activeRun.error ? (
        <Card className="border-destructive/40">
          <CardContent className="pt-5 text-sm text-destructive">{activeRun.error}</CardContent>
        </Card>
      ) : null}

      {/* Métricas principais */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Visão geral
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard label="Nº de pontos" value={fmtInt(num(m.n_points))} />
          <MetricCard label="Nº de variáveis" value={fmtInt(num(m.n_variables))} />
          <MetricCard
            label="Extensão espacial"
            value={
              num(m.extent_width_m) != null && num(m.extent_height_m) != null ? (
                <span className="text-lg">
                  {fmtNum(num(m.extent_width_m), 0)} × {fmtNum(num(m.extent_height_m), 0)} m
                </span>
              ) : (
                "—"
              )
            }
            hint="Largura × altura"
          />
          <MetricCard
            label="Moran's I"
            value={fmtNum(num(m.morans_i), 3)}
            accent={moranAccent}
            hint={moranHint}
          />
        </div>
      </section>

      {/* Estatística da principal */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          {primary}
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <MetricCard label="Média" value={`${fmtNum(num(m.mean), 3)}${units}`} />
          <MetricCard label="Mediana" value={`${fmtNum(num(m.median), 3)}${units}`} />
          <MetricCard label="Desvio padrão" value={`${fmtNum(num(m.std), 3)}${units}`} />
          <MetricCard label="Mínimo" value={`${fmtNum(num(m.min), 3)}${units}`} />
          <MetricCard label="Máximo" value={`${fmtNum(num(m.max), 3)}${units}`} />
        </div>
      </section>

      {/* Melhor método geoestatístico */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Melhor método
        </h2>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {typeof m.best_method === "string" && m.best_method
                ? m.best_method
                : "Ainda não determinado"}
            </CardTitle>
            {typeof m.best_variogram_model === "string" && m.best_variogram_model ? (
              <p className="text-sm text-muted-foreground">
                Modelo de variograma: {m.best_variogram_model}
              </p>
            ) : null}
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-3">
              <MetricCard label="RMSE" value={fmtNum(num(m.best_method_rmse), 4)} />
              <MetricCard label="MAE" value={fmtNum(num(m.best_method_mae), 4)} />
              <MetricCard label="R²" value={fmtNum(num(m.best_method_r2), 3)} />
            </div>
            {(num(m.kriging_rmse) != null ||
              num(m.kriging_mae) != null ||
              num(m.kriging_r2) != null) ? (
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                <MetricCard label="Krigagem — RMSE" value={fmtNum(num(m.kriging_rmse), 4)} />
                <MetricCard label="Krigagem — MAE" value={fmtNum(num(m.kriging_mae), 4)} />
                <MetricCard label="Krigagem — R²" value={fmtNum(num(m.kriging_r2), 3)} />
              </div>
            ) : null}
          </CardContent>
        </Card>
      </section>

      {/* Andamento das análises */}
      <StepsOverview projectId={projectId} run={activeRun} />
    </div>
  );
}

function DownloadActions({ runId, disabled }: { runId: string; disabled: boolean }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const go = useCallback(
    async (kind: "pdf" | "zip" | "xlsx") => {
      setBusy(kind);
      setErr(null);
      try {
        if (kind === "pdf") await downloadFile(api.reportUrl(runId), "relatorio.pdf");
        else if (kind === "zip") await downloadFile(api.packageUrl(runId), "pacote.zip");
        else await downloadFile(api.tablesXlsxUrl(runId), "tabelas.xlsx");
      } catch (e) {
        setErr(
          e instanceof ApiError ? e.message : "Falha ao baixar o arquivo. Tente novamente.",
        );
      } finally {
        setBusy(null);
      }
    },
    [runId],
  );

  return (
    <div className="flex flex-col items-end gap-1.5">
      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={disabled || busy != null}
          onClick={() => go("pdf")}
        >
          <FileText /> {busy === "pdf" ? "Baixando…" : "Relatório PDF"}
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={disabled || busy != null}
          onClick={() => go("zip")}
        >
          <Package /> {busy === "zip" ? "Baixando…" : "Pacote ZIP"}
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={disabled || busy != null}
          onClick={() => go("xlsx")}
        >
          <FileSpreadsheet /> {busy === "xlsx" ? "Baixando…" : "Tabelas (xlsx)"}
        </Button>
      </div>
      {disabled ? (
        <p className="text-xs text-muted-foreground">Disponível ao concluir a análise.</p>
      ) : null}
      {err ? <p className="text-xs text-destructive">{err}</p> : null}
    </div>
  );
}

interface StepRow {
  key: string;
  title: string;
  status: "ok" | "skipped" | "failed" | "pending" | "running";
  reason?: string | null;
}

function StepsOverview({ projectId, run }: { projectId: string; run: RunOut }) {
  const rows = useMemo<StepRow[]>(() => {
    const byKey = new Map<string, StepRow>();
    for (const s of run.steps ?? []) {
      byKey.set(s.key, {
        key: s.key,
        title: s.title || stepTitle(s.key),
        status: s.status,
        reason: s.reason,
      });
    }
    // Complementa com o resumo de métricas (caso run.steps venha vazio).
    const m = run.metrics_summary ?? {};
    for (const k of (m.steps_ok as string[] | undefined) ?? []) {
      if (!byKey.has(k)) byKey.set(k, { key: k, title: stepTitle(k), status: "ok" });
    }
    for (const s of (m.steps_skipped as { key: string; title?: string; reason?: string }[] | undefined) ??
      []) {
      if (!byKey.has(s.key))
        byKey.set(s.key, {
          key: s.key,
          title: s.title || stepTitle(s.key),
          status: "skipped",
          reason: s.reason,
        });
    }
    for (const k of (m.steps_failed as string[] | undefined) ?? []) {
      if (!byKey.has(k)) byKey.set(k, { key: k, title: stepTitle(k), status: "failed" });
    }

    const ordered: StepRow[] = [];
    for (const { key } of STEP_ORDER) {
      const r = byKey.get(key);
      if (r) {
        ordered.push(r);
        byKey.delete(key);
      }
    }
    for (const r of byKey.values()) ordered.push(r);
    return ordered;
  }, [run.steps, run.metrics_summary]);

  if (rows.length === 0) {
    return (
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Andamento das análises
        </h2>
        <p className="text-sm text-muted-foreground">Nenhum passo registrado nesta execução.</p>
      </section>
    );
  }

  const counts = {
    ok: rows.filter((r) => r.status === "ok").length,
    skipped: rows.filter((r) => r.status === "skipped").length,
    failed: rows.filter((r) => r.status === "failed").length,
  };

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Andamento das análises
        </h2>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <CheckCircle2 className="size-3.5 text-success" /> {counts.ok} concluídas
          </span>
          <span className="inline-flex items-center gap-1">
            <MinusCircle className="size-3.5 text-warning" /> {counts.skipped} não aplicáveis
          </span>
          <span className="inline-flex items-center gap-1">
            <XCircle className="size-3.5 text-destructive" /> {counts.failed} falhas
          </span>
        </div>
      </div>

      <Card>
        <ul className="divide-y divide-border/60">
          {rows.map((r) => {
            const href = SECTION_BY_STEP[r.key]
              ? `/projects/${projectId}/${SECTION_BY_STEP[r.key]}`
              : null;
            const inner = (
              <div className="flex items-start gap-3 px-4 py-3">
                <div className="min-w-0 flex-1">
                  <p
                    className={cn(
                      "truncate text-sm font-medium",
                      r.status === "pending"
                        ? "text-muted-foreground"
                        : "text-foreground",
                    )}
                  >
                    {r.title}
                  </p>
                  {(r.status === "skipped" || r.status === "failed") && r.reason ? (
                    <p className="mt-0.5 text-xs text-muted-foreground">{r.reason}</p>
                  ) : null}
                </div>
                <StepStatusBadge status={r.status} />
              </div>
            );
            return (
              <li key={r.key}>
                {href ? (
                  <Link
                    href={href}
                    className="block transition-colors hover:bg-accent/50"
                  >
                    {inner}
                  </Link>
                ) : (
                  inner
                )}
              </li>
            );
          })}
        </ul>
      </Card>
    </section>
  );
}

const SECTION_BY_STEP: Record<string, string> = {
  descriptive: "descriptive",
  esda_univariate: "esda",
  moran_scatter: "moran",
  esda_bivariate: "bivariate",
  idw: "idw",
  kriging: "kriging",
  external_drift: "external-drift",
  gwr: "gwr",
  cokriging: "cokriging",
  method_comparison: "comparison",
};
