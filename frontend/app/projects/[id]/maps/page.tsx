"use client";

import { Map as MapIcon } from "lucide-react";
import { use } from "react";
import { DownloadButton } from "@/components/download-button";
import { EmptyState } from "@/components/results/empty-state";
import { FigureGrid } from "@/components/results/figure-grid";
import { RunNotice } from "@/components/run-notice";
import { Skeleton } from "@/components/ui/skeleton";
import { api, ApiError } from "@/lib/api";
import { useProject, useRunResults } from "@/lib/hooks";
import type { ArtifactOut } from "@/lib/types";

export default function MapsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: project } = useProject(id);
  const runId = project?.latest_run_id ?? undefined;
  const runHref = `/projects/${id}/run`;

  const { data, isLoading, isError, error } = useRunResults(runId, true);

  const header = (
    <div className="space-y-1">
      <h1 className="text-xl font-semibold tracking-tight text-foreground">Mapas</h1>
      <p className="text-sm text-muted-foreground">
        Todos os mapas gerados pela análise, reunidos por etapa.
      </p>
    </div>
  );

  let body: React.ReactNode;

  if (!runId) {
    body = (
      <RunNotice title="Nenhuma análise executada" runHref={runHref}>
        Execute a análise completa do projeto para visualizar os mapas.
      </RunNotice>
    );
  } else if (isLoading) {
    body = (
      <div className="space-y-4">
        <Skeleton className="h-6 w-48" />
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  } else if (isError) {
    body = (
      <RunNotice title="Erro ao carregar resultados" runHref={runHref}>
        {error instanceof ApiError
          ? error.status === 404
            ? "Execução não encontrada."
            : error.message
          : "Não foi possível carregar os resultados da análise."}
      </RunNotice>
    );
  } else if (!data) {
    body = (
      <RunNotice title="Resultados indisponíveis" runHref={runHref}>
        Não foi possível carregar os resultados da análise.
      </RunNotice>
    );
  } else if (data.run.status !== "done") {
    const st = data.run.status;
    const live = st === "running" || st === "pending";
    body = (
      <RunNotice
        title={live ? "Análise em andamento" : st === "failed" ? "A análise falhou" : "Análise cancelada"}
        spin={live}
        runHref={runHref}
      >
        {live
          ? "Aguarde a conclusão da execução para visualizar os mapas."
          : "Os mapas ficam disponíveis quando uma execução é concluída com sucesso."}
      </RunNotice>
    );
  } else {
    const groups = data.steps
      .map((s) => ({
        key: s.key,
        title: s.title,
        maps: s.figures.filter((f) => f.kind === "map") as ArtifactOut[],
      }))
      .filter((g) => g.maps.length > 0);

    const total = groups.reduce((n, g) => n + g.maps.length, 0);

    if (total === 0) {
      body = (
        <EmptyState
          icon={MapIcon}
          title="Nenhum mapa gerado"
          description="A execução mais recente não produziu mapas. Métodos de interpolação como krigagem e IDW geram mapas quando aplicáveis."
        />
      );
    } else {
      body = (
        <div className="space-y-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-muted-foreground">
              {total} {total === 1 ? "mapa" : "mapas"} em {groups.length}{" "}
              {groups.length === 1 ? "etapa" : "etapas"}.
            </p>
            <DownloadButton
              url={api.packageUrl(runId)}
              filename="pacote.zip"
              variant="outline"
              size="sm"
            >
              Baixar todos (pacote ZIP)
            </DownloadButton>
          </div>

          {groups.map((g) => (
            <section key={g.key} className="space-y-3">
              <h2 className="text-sm font-semibold text-foreground">{g.title}</h2>
              <FigureGrid figures={g.maps} runId={runId} />
            </section>
          ))}
        </div>
      );
    }
  }

  return (
    <div className="space-y-6">
      {header}
      {body}
    </div>
  );
}
