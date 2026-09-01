"use client";

import { Database, FileSpreadsheet, FileText, Package } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { use } from "react";
import { DownloadButton } from "@/components/download-button";
import { RunNotice } from "@/components/run-notice";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, ApiError } from "@/lib/api";
import { useProject, useRun } from "@/lib/hooks";

interface ExportItem {
  icon: LucideIcon;
  title: string;
  desc: string;
  url: string;
  filename: string;
}

const ZIP_STRUCTURE: { path: string; desc: string }[] = [
  { path: "relatorio.pdf", desc: "Relatório técnico completo." },
  { path: "tabelas/", desc: "Tabelas de resultados em .xlsx e .csv, uma por seção." },
  { path: "figuras/", desc: "Gráficos de cada etapa em PNG e SVG." },
  { path: "mapas/", desc: "Mapas de estimativa, erro e clusters em PNG." },
  { path: "dados/", desc: "Base de dados processada (após diagnóstico e limpeza)." },
  { path: "metadados/", desc: "Manifesto da execução, parâmetros usados e versões das bibliotecas." },
];

export default function ExportsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: project } = useProject(id);
  const runId = project?.latest_run_id ?? undefined;
  const runHref = `/projects/${id}/run`;

  const { data: run, isLoading, isError, error } = useRun(runId);
  const live = run?.status === "running" || run?.status === "pending";

  const header = (
    <div className="space-y-1">
      <h1 className="text-xl font-semibold tracking-tight text-foreground">Exportações</h1>
      <p className="text-sm text-muted-foreground">
        Baixe os resultados da análise em diferentes formatos.
      </p>
    </div>
  );

  let body: React.ReactNode;

  if (!runId) {
    body = (
      <RunNotice title="Nenhuma análise executada" runHref={runHref}>
        Execute a análise completa do projeto para liberar as exportações.
      </RunNotice>
    );
  } else if (isLoading) {
    body = (
      <div className="space-y-3">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  } else if (isError) {
    body = (
      <RunNotice title="Erro ao carregar" runHref={runHref}>
        {error instanceof ApiError ? error.message : "Não foi possível carregar a execução."}
      </RunNotice>
    );
  } else if (!run) {
    body = <RunNotice title="Execução indisponível" runHref={runHref} />;
  } else if (run.status !== "done") {
    body = (
      <RunNotice
        title={live ? "Análise em andamento" : "Exportações indisponíveis"}
        spin={live}
        runHref={runHref}
      >
        {live
          ? "Os arquivos ficam disponíveis assim que a execução for concluída."
          : "As exportações só são geradas para execuções concluídas com sucesso."}
      </RunNotice>
    );
  } else {
    const items: ExportItem[] = [
      {
        icon: FileText,
        title: "Relatório PDF",
        desc: "Documento técnico completo com metodologia, resultados e interpretações.",
        url: api.reportUrl(runId),
        filename: "relatorio.pdf",
      },
      {
        icon: Package,
        title: "Pacote ZIP completo",
        desc: "Todos os artefatos da análise: relatório, tabelas, figuras, mapas e base tratada.",
        url: api.packageUrl(runId),
        filename: "pacote.zip",
      },
      {
        icon: FileSpreadsheet,
        title: "Tabelas (.xlsx)",
        desc: "Planilha única com todas as tabelas de resultados, uma aba por seção.",
        url: api.tablesXlsxUrl(runId),
        filename: "tabelas.xlsx",
      },
      {
        icon: Database,
        title: "Base de dados processada",
        desc: "A base após o diagnóstico e a limpeza acompanha o Pacote ZIP, na pasta dados/.",
        url: api.packageUrl(runId),
        filename: "pacote.zip",
      },
    ];

    body = (
      <div className="space-y-6">
        <div className="space-y-3">
          {items.map((it) => {
            const Icon = it.icon;
            return (
              <Card key={it.title}>
                <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex min-w-0 items-start gap-3">
                    <span className="grid size-9 shrink-0 place-items-center rounded-md bg-muted text-muted-foreground">
                      <Icon className="size-4" aria-hidden />
                    </span>
                    <div className="min-w-0 space-y-0.5">
                      <p className="text-sm font-medium text-foreground">{it.title}</p>
                      <p className="text-xs text-muted-foreground">{it.desc}</p>
                    </div>
                  </div>
                  <DownloadButton
                    url={it.url}
                    filename={it.filename}
                    variant="outline"
                    size="sm"
                    className="shrink-0 self-start sm:self-auto"
                  >
                    Baixar
                  </DownloadButton>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Estrutura do pacote ZIP</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="divide-y divide-border text-sm">
              {ZIP_STRUCTURE.map((row) => (
                <div key={row.path} className="flex flex-col gap-1 py-2 sm:flex-row sm:gap-4">
                  <dt className="shrink-0 font-mono text-xs text-foreground sm:w-40">{row.path}</dt>
                  <dd className="text-xs text-muted-foreground">{row.desc}</dd>
                </div>
              ))}
            </dl>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {header}
      {body}
    </div>
  );
}
