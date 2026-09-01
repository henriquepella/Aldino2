"use client";

import { use } from "react";
import Link from "next/link";
import { AlertTriangle, FlaskConical, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { DataTableView } from "@/components/results/data-table-view";
import { EmptyState } from "@/components/results/empty-state";
import { ApiError } from "@/lib/api";
import { fmtInt, fmtNum } from "@/lib/format";
import { useRunResults } from "@/lib/hooks";
import type { ArtifactOut, StepResultOut } from "@/lib/types";
import { useResolvedRunId } from "../_lib/use-run-id";

const SOURCE_KEYS = ["esda_univariate", "esda_bivariate"];
const TEST_RE = /test|teste/i;

function isTestTable(t: ArtifactOut): boolean {
  return TEST_RE.test(t.name ?? "") || TEST_RE.test(t.title ?? "") || TEST_RE.test(t.data?.payload?.title ?? "");
}

function pick(obj: Record<string, unknown> | undefined, keys: string[]): unknown {
  if (!obj) return undefined;
  for (const k of keys) {
    if (obj[k] != null) return obj[k];
  }
  return undefined;
}

function Header() {
  return (
    <div className="space-y-1">
      <h1 className="text-xl font-semibold tracking-tight text-foreground">Testes Estatísticos</h1>
      <p className="text-sm text-muted-foreground">
        Testes de hipótese das análises exploratórias univariada e bivariada.
      </p>
    </div>
  );
}

function Notice({
  icon: Icon,
  title,
  children,
  spin,
}: {
  icon: typeof AlertTriangle;
  title: string;
  children?: React.ReactNode;
  spin?: boolean;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-start gap-2 p-6">
        <div className="flex items-center gap-2 text-foreground">
          <Icon className={spin ? "size-5 animate-spin text-muted-foreground" : "size-5 text-muted-foreground"} aria-hidden />
          <span className="font-semibold">{title}</span>
        </div>
        {children ? <p className="text-sm text-muted-foreground">{children}</p> : null}
      </CardContent>
    </Card>
  );
}

export default function TestsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { runId, isLoading: runsLoading, isError: runsError } = useResolvedRunId(id);
  const { data, isLoading, isError, error } = useRunResults(runId, true);

  if (runsLoading || (runId && isLoading)) {
    return (
      <div className="space-y-6">
        <Header />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (runsError) {
    return (
      <div className="space-y-6">
        <Header />
        <p className="text-sm text-destructive">
          Não foi possível carregar as execuções deste projeto.
        </p>
      </div>
    );
  }

  if (!runId) {
    return (
      <div className="space-y-6">
        <Header />
        <EmptyState
          icon={FlaskConical}
          title="Nenhuma análise concluída"
          description="Execute a análise completa do projeto para visualizar os testes estatísticos."
          action={
            <Button asChild>
              <Link href={`/projects/${id}/run`}>Executar análise</Link>
            </Button>
          }
        />
      </div>
    );
  }

  if (isError) {
    const msg =
      error instanceof ApiError
        ? error.status === 404
          ? "Execução não encontrada."
          : error.message
        : "Não foi possível carregar os resultados da análise.";
    return (
      <div className="space-y-6">
        <Header />
        <Notice icon={AlertTriangle} title="Erro ao carregar resultados">
          {msg}
        </Notice>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <Header />
        <Notice icon={AlertTriangle} title="Resultados indisponíveis">
          Não foi possível carregar os resultados da análise.
        </Notice>
      </div>
    );
  }

  if (data.run.status !== "done") {
    const st = data.run.status;
    const live = st === "running" || st === "pending";
    return (
      <div className="space-y-6">
        <Header />
        <Notice
          icon={live ? Loader2 : AlertTriangle}
          spin={live}
          title={
            live
              ? "Análise em andamento"
              : st === "failed"
                ? "A análise falhou"
                : "Análise cancelada"
          }
        >
          {live
            ? "Aguarde a conclusão da execução para visualizar esta seção."
            : "Esta seção ficará disponível quando uma execução for concluída com sucesso."}
        </Notice>
      </div>
    );
  }

  const steps: StepResultOut[] = data.steps.filter((s) => SOURCE_KEYS.includes(s.key));
  const tables: ArtifactOut[] = steps
    .filter((s) => s.status === "ok")
    .flatMap((s) => s.tables)
    .filter(isTestTable);

  // Nota sobre alpha / permutações (manifest do run + params dos passos).
  const manifest = (data.run.manifest ?? {}) as Record<string, unknown>;
  const manifestParams = (manifest.context ??
    manifest.params ??
    manifest.settings ??
    {}) as Record<string, unknown>;
  const stepParams = Object.assign(
    {},
    ...steps.map((s) => s.params_used as Record<string, unknown>),
  ) as Record<string, unknown>;

  const alphaRaw =
    pick(manifest, ["alpha", "alpha_level", "significance", "significance_level"]) ??
    pick(manifestParams, ["alpha", "alpha_level", "significance"]) ??
    pick(stepParams, ["alpha", "alpha_level", "significance"]);
  const permsRaw =
    pick(manifest, ["permutations", "n_permutations", "n_perm", "perms"]) ??
    pick(manifestParams, ["permutations", "n_permutations", "n_perm"]) ??
    pick(stepParams, ["permutations", "n_permutations", "n_perm"]);

  const alpha = typeof alphaRaw === "number" ? alphaRaw : undefined;
  const perms = typeof permsRaw === "number" ? permsRaw : undefined;
  const hasNote = alpha != null || perms != null;

  return (
    <div className="space-y-6">
      <Header />

      {hasNote ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Parâmetros de inferência</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
            {alpha != null ? (
              <div>
                <span className="text-muted-foreground">Nível de significância (α): </span>
                <span className="font-medium tabular-nums text-foreground">{fmtNum(alpha)}</span>
              </div>
            ) : null}
            {perms != null ? (
              <div>
                <span className="text-muted-foreground">Permutações: </span>
                <span className="font-medium tabular-nums text-foreground">{fmtInt(perms)}</span>
              </div>
            ) : null}
          </CardContent>
        </Card>
      ) : null}

      {steps.length === 0 ? (
        <Notice icon={FlaskConical} title="Passos não executados">
          As análises ESDA univariada e bivariada não fazem parte da execução mais recente.
        </Notice>
      ) : tables.length === 0 ? (
        <EmptyState
          icon={FlaskConical}
          title="Nenhum teste estatístico disponível"
          description="A execução mais recente não gerou tabelas de testes de hipótese nas análises exploratórias."
        />
      ) : (
        <div className="space-y-4">
          {tables.map((t) => (
            <DataTableView key={t.id} table={t} />
          ))}
        </div>
      )}
    </div>
  );
}
