"use client";

import { AlertTriangle, FileWarning, Loader2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useRunResults } from "@/lib/hooks";
import { ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import { DataTableView } from "./data-table-view";
import { FigureGrid } from "./figure-grid";
import { InterpretationCallout } from "./interpretation-callout";
import { StepStatusBadge } from "./step-status-badge";

function LoadingState() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-96" />
      <Skeleton className="h-40 w-full" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

function Notice({
  icon: Icon,
  title,
  children,
  runHref,
  spin,
}: {
  icon: typeof AlertTriangle;
  title: string;
  children?: React.ReactNode;
  runHref: string;
  spin?: boolean;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-start gap-3 p-6">
        <div className="flex items-center gap-2 text-foreground">
          <Icon className={cn("size-5 text-muted-foreground", spin && "animate-spin")} aria-hidden />
          <span className="font-semibold">{title}</span>
        </div>
        {children ? <p className="text-sm text-muted-foreground">{children}</p> : null}
        <Button asChild variant="outline" size="sm">
          <Link href={runHref}>Ir para a execução</Link>
        </Button>
      </CardContent>
    </Card>
  );
}

export function SectionPage({
  stepKey,
  title,
  runId,
  description,
  projectId,
  className,
}: {
  stepKey: string;
  title: string;
  runId?: string;
  description?: string;
  projectId?: string;
  className?: string;
}) {
  const { data, isLoading, isError, error } = useRunResults(runId, true);

  const pid = data?.run.project_id ?? projectId;
  const runHref = pid ? `/projects/${pid}/run` : "/projects";

  const header = (
    <div className="space-y-1">
      <h1 className="text-xl font-semibold tracking-tight text-foreground">{title}</h1>
      {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
    </div>
  );

  let body: React.ReactNode;

  if (!runId) {
    body = (
      <Notice icon={AlertTriangle} title="Nenhuma análise executada" runHref={runHref}>
        Execute a análise completa do projeto para visualizar esta seção.
      </Notice>
    );
  } else if (isLoading) {
    body = <LoadingState />;
  } else if (isError) {
    const msg =
      error instanceof ApiError
        ? error.status === 404
          ? "Execução não encontrada."
          : error.message
        : "Não foi possível carregar os resultados da análise.";
    body = (
      <Notice icon={AlertTriangle} title="Erro ao carregar resultados" runHref={runHref}>
        {msg}
      </Notice>
    );
  } else if (!data) {
    body = (
      <Notice icon={AlertTriangle} title="Resultados indisponíveis" runHref={runHref}>
        Não foi possível carregar os resultados da análise.
      </Notice>
    );
  } else if (data.run.status !== "done") {
    const st = data.run.status;
    body = (
      <Notice
        icon={st === "running" || st === "pending" ? Loader2 : AlertTriangle}
        spin={st === "running" || st === "pending"}
        title={
          st === "running" || st === "pending"
            ? "Análise em andamento"
            : st === "failed"
              ? "A análise falhou"
              : "Análise cancelada"
        }
        runHref={runHref}
      >
        {st === "running" || st === "pending"
          ? "Aguarde a conclusão da execução para visualizar esta seção."
          : "Esta seção ficará disponível quando uma execução for concluída com sucesso."}
      </Notice>
    );
  } else {
    const step = data.steps.find((s) => s.key === stepKey);

    if (!step) {
      body = (
        <Card>
          <CardContent className="flex flex-col items-start gap-3 p-6">
            <div className="flex items-center gap-2 text-foreground">
              <FileWarning className="size-5 text-muted-foreground" aria-hidden />
              <span className="font-semibold">Passo não executado</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Este passo não faz parte da execução mais recente.
            </p>
          </CardContent>
        </Card>
      );
    } else if (step.status === "skipped" || step.status === "failed") {
      body = (
        <div className="space-y-4">
          <StepStatusBadge status={step.status} />
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                {step.status === "skipped" ? "Passo não aplicável" : "O passo falhou"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {step.reason?.trim() ||
                  (step.status === "skipped"
                    ? "Este passo não se aplica à configuração ou aos dados deste projeto."
                    : "Ocorreu um erro durante a execução deste passo.")}
              </p>
            </CardContent>
          </Card>
        </div>
      );
    } else {
      body = (
        <div className="space-y-6">
          <StepStatusBadge status={step.status} />
          <InterpretationCallout text={step.interpretation} />
          {step.tables.length > 0 ? (
            <div className="space-y-4">
              {step.tables.map((t) => (
                <DataTableView key={t.id} table={t} />
              ))}
            </div>
          ) : null}
          {step.figures.length > 0 ? (
            <FigureGrid figures={step.figures} runId={runId} />
          ) : null}
          {step.tables.length === 0 && step.figures.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Este passo foi concluído sem tabelas ou figuras.
            </p>
          ) : null}
        </div>
      );
    }
  }

  return (
    <div className={cn("space-y-6", className)}>
      {header}
      {body}
    </div>
  );
}
