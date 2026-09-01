"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  Ban,
  CheckCircle2,
  Clock,
  FileDown,
  LayoutDashboard,
  Loader2,
  Package,
  RefreshCw,
  Rocket,
} from "lucide-react";
import { toast } from "sonner";
import { ConfettiBurst } from "@/components/run/confetti-burst";
import { RunProgress, STEP_ORDER } from "@/components/results/run-progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { api, downloadFile } from "@/lib/api";
import { fmtDateTime } from "@/lib/format";
import {
  useActiveDataset,
  useCancelRun,
  useCreateRun,
  useProject,
  useRun,
  useRuns,
} from "@/lib/hooks";
import type { RunOut, RunStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const runKey = (pid: string) => `run:${pid}`;
const datasetKey = (pid: string) => `dataset:${pid}`;

function readSession(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.sessionStorage.getItem(key);
  } catch {
    return null;
  }
}
function writeSession(key: string, value: string | null) {
  if (typeof window === "undefined") return;
  try {
    if (value) window.sessionStorage.setItem(key, value);
    else window.sessionStorage.removeItem(key);
  } catch {
    /* ignore */
  }
}

const STEP_NOTES: Record<string, string> = {
  descriptive: "Medidas de posição, dispersão e forma; detecção de valores atípicos.",
  esda_univariate: "Autocorrelação espacial global e local (LISA) da variável principal.",
  moran_scatter: "Diagrama de dispersão de Moran e mapa de agrupamentos.",
  esda_bivariate: "Índice de Moran bivariado entre os pares de variáveis.",
  idw: "Interpolação por inverso da distância com validação cruzada.",
  kriging: "Ajuste do variograma e krigagem ordinária.",
  external_drift: "Krigagem com deriva externa a partir da variável auxiliar.",
  gwr: "Regressão geograficamente ponderada / modelos locais.",
  cokriging: "Co-krigagem com a variável secundária correlacionada.",
  method_comparison: "Comparação de RMSE, MAE e R² entre todos os métodos.",
};

const STATUS_META: Record<
  RunStatus,
  { label: string; variant: "default" | "secondary" | "success" | "warning" | "destructive" }
> = {
  pending: { label: "Na fila", variant: "secondary" },
  running: { label: "Em execução", variant: "default" },
  done: { label: "Concluída", variant: "success" },
  failed: { label: "Falhou", variant: "destructive" },
  cancelled: { label: "Cancelada", variant: "warning" },
};

const isLive = (s?: RunStatus) => s === "pending" || s === "running";

export default function RunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <RunView projectId={id} />;
}

function RunView({ projectId }: { projectId: string }) {
  const projectQ = useProject(projectId);
  const runsQ = useRuns(projectId);
  const createRun = useCreateRun(projectId);
  const cancelRun = useCancelRun();

  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<"pdf" | "zip" | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const celebratedRef = useRef<string | null>(null);

  // Restaura a execução ativa da sessão (compartilhada com o painel/seções).
  useEffect(() => {
    const stored = readSession(runKey(projectId));
    if (stored) setActiveRunId(stored);
  }, [projectId]);

  // Se não há execução ativa mas existe uma rodando, adota-a.
  useEffect(() => {
    if (activeRunId) return;
    const live = runsQ.data?.find((r) => isLive(r.status));
    if (live) setActiveRunId(live.id);
  }, [activeRunId, runsQ.data]);

  useEffect(() => {
    if (activeRunId) writeSession(runKey(projectId), activeRunId);
  }, [activeRunId, projectId]);

  const runQ = useRun(activeRunId ?? undefined);
  const activeRun = runQ.data;

  const activeDs = useActiveDataset(projectId);
  const datasetId = useMemo(() => {
    const fromSession =
      readSession(datasetKey(projectId)) || readSession(`ds:${projectId}`);
    if (fromSession) return fromSession;
    return activeDs.datasetId ?? runsQ.data?.[0]?.dataset_id ?? null;
  }, [projectId, runsQ.data, activeDs.datasetId]);

  const advanced = useMemo<Record<string, unknown>>(() => {
    const s = projectQ.data?.settings as Record<string, unknown> | undefined;
    const a = s?.advanced;
    return a && typeof a === "object" ? (a as Record<string, unknown>) : {};
  }, [projectQ.data?.settings]);

  const startRun = useCallback(async () => {
    if (!datasetId) {
      toast.error("Nenhuma base pronta. Confirme as colunas e faça o diagnóstico primeiro.");
      return;
    }
    try {
      const run = await createRun.mutateAsync({
        dataset_id: datasetId,
        mode: "full",
        advanced,
      });
      writeSession(datasetKey(projectId), run.dataset_id);
      celebratedRef.current = null;
      setActiveRunId(run.id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Não foi possível iniciar a execução.");
    }
  }, [advanced, createRun, datasetId, projectId]);

  const cancel = useCallback(async () => {
    if (!activeRunId) return;
    try {
      await cancelRun.mutateAsync(activeRunId);
      toast.success("Execução cancelada.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Não foi possível cancelar a execução.");
    }
  }, [activeRunId, cancelRun]);

  const clearActive = useCallback(() => {
    setActiveRunId(null);
    writeSession(runKey(projectId), null);
    celebratedRef.current = null;
    setShowConfetti(false);
    runsQ.refetch();
  }, [projectId, runsQ]);

  const download = useCallback(
    async (kind: "pdf" | "zip") => {
      if (!activeRunId) return;
      setDownloading(kind);
      try {
        if (kind === "pdf") {
          await downloadFile(api.reportUrl(activeRunId), "relatorio.pdf");
        } else {
          await downloadFile(api.packageUrl(activeRunId), "pacote-analise.zip");
        }
      } catch {
        toast.error("Falha no download. Tente novamente.");
      } finally {
        setDownloading(null);
      }
    },
    [activeRunId],
  );

  // Confete + toast uma única vez quando a execução conclui.
  useEffect(() => {
    if (activeRun?.status === "done" && celebratedRef.current !== activeRun.id) {
      celebratedRef.current = activeRun.id;
      setShowConfetti(true);
      toast.success("Análise concluída com sucesso.");
      const t = setTimeout(() => setShowConfetti(false), 3200);
      return () => clearTimeout(t);
    }
  }, [activeRun?.status, activeRun?.id]);

  const header = (
    <div className="space-y-1">
      <h1 className="text-xl font-semibold tracking-tight text-foreground">Executar análise</h1>
      <p className="text-sm text-muted-foreground">
        A execução completa roda toda a análise geoestatística em sequência a partir da base já
        validada.
      </p>
    </div>
  );

  if (projectQ.isError) {
    return (
      <div className="space-y-6">
        {header}
        <Card>
          <CardContent className="flex items-center gap-2 p-6 text-sm text-destructive">
            <AlertTriangle className="size-4 shrink-0" aria-hidden />
            Não foi possível carregar o projeto. Tente novamente mais tarde.
          </CardContent>
        </Card>
      </div>
    );
  }

  if (projectQ.isLoading || runsQ.isLoading) {
    return (
      <div className="space-y-6">
        {header}
        <Skeleton className="h-44 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  // ---------- Estado B: execução ativa (rodando ou concluída) ----------
  if (activeRunId && (runQ.isLoading || activeRun || runQ.isError)) {
    return (
      <div className="space-y-6">
        {header}
        {runQ.isLoading && !activeRun ? (
          <Skeleton className="h-72 w-full" />
        ) : activeRun ? (
          <ActiveRunPanel
            projectId={projectId}
            run={activeRun}
            showConfetti={showConfetti}
            onCancel={cancel}
            cancelling={cancelRun.isPending}
            onRetry={startRun}
            retrying={createRun.isPending}
            onNewRun={clearActive}
            onDownload={download}
            downloading={downloading}
          />
        ) : null}
        {runQ.isError ? (
          <Card>
            <CardContent className="flex flex-col items-start gap-3 p-6">
              <div className="flex items-center gap-2 text-sm text-destructive">
                <AlertTriangle className="size-4 shrink-0" aria-hidden />
                Não foi possível carregar esta execução.
              </div>
              <Button variant="outline" size="sm" onClick={clearActive}>
                Voltar
              </Button>
            </CardContent>
          </Card>
        ) : null}
      </div>
    );
  }

  // ---------- Estado A: nenhuma execução ativa ----------
  const runs = runsQ.data ?? [];
  const canRun = !!datasetId;

  return (
    <div className="space-y-8">
      {header}

      <Card className="relative overflow-hidden border-primary/30">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-primary/5"
        />
        <CardContent className="relative flex flex-col items-center gap-5 px-6 py-10 text-center">
          <span className="grid size-14 place-items-center rounded-2xl bg-primary/15 text-primary">
            <Rocket className="size-7" aria-hidden />
          </span>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold tracking-tight">Executar análise completa</h2>
            <p className="mx-auto max-w-xl text-sm text-muted-foreground">
              Cerca de 17 passos de processamento rodam automaticamente: estatística descritiva,
              ESDA, índice de Moran, IDW, krigagem ordinária, krigagem com deriva externa, GWR e
              co-krigagem, encerrando com a comparação geral dos métodos.
            </p>
          </div>

          <Button
            onClick={startRun}
            disabled={!canRun || createRun.isPending}
            className={cn(
              "h-16 gap-3 rounded-xl px-10 text-lg font-semibold shadow-lg",
              "bg-gradient-to-r from-primary to-primary/80 hover:from-primary/95 hover:to-primary/75",
            )}
          >
            {createRun.isPending ? (
              <Loader2 className="size-6 animate-spin" aria-hidden />
            ) : (
              <Rocket className="size-6" aria-hidden />
            )}
            {createRun.isPending ? "Iniciando execução…" : "EXECUTAR ANÁLISE COMPLETA"}
          </Button>

          {canRun ? (
            <p className="text-xs text-muted-foreground">
              17 etapas de processamento &middot; painel interativo &middot; relatório PDF &middot;
              pacote ZIP
            </p>
          ) : (
            <div className="flex flex-col items-center gap-2 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1.5 text-warning">
                <AlertTriangle className="size-3.5" aria-hidden />
                Nenhuma base pronta para execução.
              </span>
              <Button asChild variant="outline" size="sm">
                <Link href={`/projects/${projectId}/diagnostics`}>
                  Confirmar colunas e diagnóstico da base
                </Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">O que será calculado</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
            {STEP_ORDER.map((s, i) => (
              <li key={s.key} className="flex gap-3">
                <span className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-primary/10 text-[11px] font-semibold tabular text-primary">
                  {i + 1}
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground">{s.title}</p>
                  <p className="text-xs text-muted-foreground">{STEP_NOTES[s.key]}</p>
                </div>
              </li>
            ))}
          </ol>
          <Separator className="my-4" />
          <p className="text-xs text-muted-foreground">
            Passos sem dados suficientes (por exemplo, co-krigagem sem variável secundária) são
            marcados como não aplicáveis, sem interromper a análise.
          </p>
        </CardContent>
      </Card>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Execuções anteriores
        </h2>
        {runs.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-sm text-muted-foreground">
              Nenhuma execução ainda. Ao rodar a análise, o histórico aparece aqui.
            </CardContent>
          </Card>
        ) : (
          <Card className="divide-y divide-border">
            {runs.map((r) => (
              <PreviousRunRow
                key={r.id}
                projectId={projectId}
                run={r}
                onOpen={() => {
                  celebratedRef.current = r.id;
                  setActiveRunId(r.id);
                }}
              />
            ))}
          </Card>
        )}
      </section>
    </div>
  );
}

function ActiveRunPanel({
  projectId,
  run,
  showConfetti,
  onCancel,
  cancelling,
  onRetry,
  retrying,
  onNewRun,
  onDownload,
  downloading,
}: {
  projectId: string;
  run: RunOut;
  showConfetti: boolean;
  onCancel: () => void;
  cancelling: boolean;
  onRetry: () => void;
  retrying: boolean;
  onNewRun: () => void;
  onDownload: (kind: "pdf" | "zip") => void;
  downloading: "pdf" | "zip" | null;
}) {
  const meta = STATUS_META[run.status] ?? STATUS_META.pending;
  const live = isLive(run.status);

  return (
    <div className="space-y-5">
      <Card className="relative overflow-hidden">
        {showConfetti ? <ConfettiBurst /> : null}
        <CardContent className="relative space-y-5 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              {run.status === "done" ? (
                <CheckCircle2 className="size-5 text-success" aria-hidden />
              ) : run.status === "failed" ? (
                <AlertTriangle className="size-5 text-destructive" aria-hidden />
              ) : run.status === "cancelled" ? (
                <Ban className="size-5 text-warning" aria-hidden />
              ) : (
                <Loader2 className="size-5 animate-spin text-primary" aria-hidden />
              )}
              <div>
                <p className="text-sm font-semibold text-foreground">
                  {run.status === "done"
                    ? "Análise concluída"
                    : run.status === "failed"
                      ? "A análise falhou"
                      : run.status === "cancelled"
                        ? "Execução cancelada"
                        : "Executando análise"}
                </p>
                <p className="text-xs text-muted-foreground">
                  Iniciada em {fmtDateTime(run.started_at ?? run.created_at)}
                </p>
              </div>
            </div>
            <Badge variant={meta.variant}>{meta.label}</Badge>
          </div>

          <RunProgress run={run} />

          <div className="flex flex-wrap gap-2 pt-1">
            {live ? (
              <Button variant="outline" onClick={onCancel} disabled={cancelling}>
                {cancelling ? (
                  <Loader2 className="size-4 animate-spin" aria-hidden />
                ) : (
                  <Ban className="size-4" aria-hidden />
                )}
                Cancelar execução
              </Button>
            ) : null}

            {run.status === "done" ? (
              <>
                <Button asChild>
                  <Link href={`/projects/${projectId}/dashboard`}>
                    <LayoutDashboard className="size-4" aria-hidden />
                    Ver painel
                    <ArrowRight className="size-4" aria-hidden />
                  </Link>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => onDownload("pdf")}
                  disabled={downloading !== null}
                >
                  {downloading === "pdf" ? (
                    <Loader2 className="size-4 animate-spin" aria-hidden />
                  ) : (
                    <FileDown className="size-4" aria-hidden />
                  )}
                  Baixar relatório PDF
                </Button>
                <Button
                  variant="outline"
                  onClick={() => onDownload("zip")}
                  disabled={downloading !== null}
                >
                  {downloading === "zip" ? (
                    <Loader2 className="size-4 animate-spin" aria-hidden />
                  ) : (
                    <Package className="size-4" aria-hidden />
                  )}
                  Baixar pacote
                </Button>
              </>
            ) : null}

            {run.status === "failed" ? (
              <Button onClick={onRetry} disabled={retrying}>
                {retrying ? (
                  <Loader2 className="size-4 animate-spin" aria-hidden />
                ) : (
                  <RefreshCw className="size-4" aria-hidden />
                )}
                Tentar novamente
              </Button>
            ) : null}

            {run.status === "cancelled" ? (
              <Button onClick={onRetry} disabled={retrying}>
                {retrying ? (
                  <Loader2 className="size-4 animate-spin" aria-hidden />
                ) : (
                  <Rocket className="size-4" aria-hidden />
                )}
                Nova execução
              </Button>
            ) : null}

            {!live ? (
              <Button variant="ghost" onClick={onNewRun}>
                Voltar
              </Button>
            ) : null}
          </div>
        </CardContent>
      </Card>

      {run.status === "failed" && run.error ? (
        <Card className="border-destructive/40 bg-destructive/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm text-destructive">
              <AlertTriangle className="size-4" aria-hidden />
              Detalhe do erro
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="max-h-56 overflow-auto scrollbar-thin whitespace-pre-wrap text-xs leading-relaxed text-destructive">
              {run.error}
            </pre>
          </CardContent>
        </Card>
      ) : null}

      {run.status === "cancelled" ? (
        <Card className="border-warning/40 bg-warning/10">
          <CardContent className="flex items-center gap-2 p-4 text-sm text-warning">
            <Ban className="size-4 shrink-0" aria-hidden />
            Esta execução foi cancelada antes de concluir. Inicie uma nova execução quando quiser.
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function PreviousRunRow({
  projectId,
  run,
  onOpen,
}: {
  projectId: string;
  run: RunOut;
  onOpen: () => void;
}) {
  const meta = STATUS_META[run.status] ?? STATUS_META.pending;
  const live = isLive(run.status);

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 p-4">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Badge variant={meta.variant}>{meta.label}</Badge>
          <span className="text-sm font-medium text-foreground">Análise completa</span>
        </div>
        <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground tabular">
          <Clock className="size-3.5" aria-hidden />
          {fmtDateTime(run.created_at)}
        </p>
      </div>
      {run.status === "done" ? (
        <Button asChild variant="outline" size="sm">
          <Link href={`/projects/${projectId}/dashboard`} onClick={onOpen}>
            <LayoutDashboard className="size-4" aria-hidden />
            Ver painel
          </Link>
        </Button>
      ) : (
        <Button variant="outline" size="sm" onClick={onOpen}>
          {live ? "Acompanhar" : "Ver detalhes"}
        </Button>
      )}
    </div>
  );
}
