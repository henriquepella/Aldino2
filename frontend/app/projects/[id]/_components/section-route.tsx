"use client";

import Link from "next/link";
import { FlaskConical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/results/empty-state";
import { SectionPage } from "@/components/results/section-page";
import { useResolvedRunId } from "../_lib/use-run-id";

/**
 * Casca comum das seções de resultado: resolve o runId e delega para
 * <SectionPage/>. Trata carregamento, erro e ausência de execução.
 */
export function SectionRoute({
  projectId,
  stepKey,
  title,
  description,
}: {
  projectId: string;
  stepKey: string;
  title: string;
  description?: string;
}) {
  const { runId, isLoading, isError } = useResolvedRunId(projectId);

  if (isLoading) {
    return (
      <div className="space-y-4" aria-busy>
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-2">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">{title}</h1>
        <p className="text-sm text-destructive">
          Não foi possível carregar as execuções deste projeto. Tente novamente mais tarde.
        </p>
      </div>
    );
  }

  if (!runId) {
    return (
      <div className="space-y-6">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">{title}</h1>
        <EmptyState
          icon={FlaskConical}
          title="Nenhuma análise concluída"
          description="Execute a análise completa do projeto para visualizar esta seção."
          action={
            <Button asChild>
              <Link href={`/projects/${projectId}/run`}>Executar análise</Link>
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <SectionPage
      stepKey={stepKey}
      title={title}
      runId={runId}
      description={description}
      projectId={projectId}
    />
  );
}
