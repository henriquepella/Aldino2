"use client";

import { use } from "react";
import { DownloadButton } from "@/components/download-button";
import { RunNotice } from "@/components/run-notice";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, ApiError, authedAssetUrl } from "@/lib/api";
import { useProject, useRun } from "@/lib/hooks";

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: project } = useProject(id);
  const runId = project?.latest_run_id ?? undefined;
  const runHref = `/projects/${id}/run`;

  const { data: run, isLoading, isError, error } = useRun(runId);

  const live = run?.status === "running" || run?.status === "pending";

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">Relatório PDF</h1>
        <p className="text-sm text-muted-foreground">
          Documento técnico completo com metodologia, resultados e interpretações.
        </p>
      </div>

      {!runId ? (
        <RunNotice title="Nenhuma análise executada" runHref={runHref}>
          Execute a análise completa do projeto para gerar o relatório.
        </RunNotice>
      ) : isLoading ? (
        <Skeleton className="h-[80vh] w-full" />
      ) : isError ? (
        <RunNotice title="Erro ao carregar" runHref={runHref}>
          {error instanceof ApiError ? error.message : "Não foi possível carregar a execução."}
        </RunNotice>
      ) : !run ? (
        <RunNotice title="Execução indisponível" runHref={runHref} />
      ) : run.status !== "done" ? (
        <RunNotice
          title={live ? "Análise em andamento" : "Relatório indisponível"}
          spin={live}
          runHref={runHref}
        >
          {live
            ? "O relatório ficará disponível assim que a execução for concluída."
            : "O relatório só é gerado para execuções concluídas com sucesso."}
        </RunNotice>
      ) : (
        <>
          <div className="flex flex-wrap gap-2">
            <DownloadButton url={api.reportUrl(runId)} filename="relatorio.pdf">
              Baixar PDF
            </DownloadButton>
            <DownloadButton
              url={api.packageUrl(runId)}
              filename="pacote.zip"
              variant="outline"
            >
              Baixar pacote (ZIP)
            </DownloadButton>
          </div>

          <Card className="overflow-hidden">
            <CardContent className="p-0">
              <iframe
                title="Pré-visualização do relatório PDF"
                src={authedAssetUrl(api.reportUrl(runId))}
                className="h-[80vh] w-full border-0 bg-muted/30"
              />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
