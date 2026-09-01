"use client";

import Link from "next/link";
import { use } from "react";
import { FlaskConical } from "lucide-react";
import { EmptyState } from "@/components/results/empty-state";
import { SectionPage } from "@/components/results/section-page";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useRuns } from "@/lib/hooks";

/**
 * Casca das páginas de seção de resultados: resolve o runId (execução "done"
 * mais recente, ou a marcada em sessionStorage) e delega ao <SectionPage>.
 */
export function SectionRoute({
  params,
  stepKey,
  title,
  description,
}: {
  params: Promise<{ id: string }>;
  stepKey: string;
  title: string;
  description?: string;
}) {
  const { id } = use(params);
  const { data: runs, isLoading, isError } = useRuns(id);

  const done = (runs ?? []).filter((r) => r.status === "done");
  let stored: string | null = null;
  try {
    stored = typeof window !== "undefined" ? window.sessionStorage.getItem(`run:${id}`) : null;
  } catch {
    stored = null;
  }
  const runId =
    (stored && done.some((r) => r.id === stored) ? stored : undefined) ??
    [...done].sort((a, b) => (a.created_at < b.created_at ? 1 : -1))[0]?.id;

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
          Não foi possível carregar as execuções deste projeto.
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
              <Link href={`/projects/${id}/run`}>Executar análise</Link>
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
      description={description}
      runId={runId}
      projectId={id}
    />
  );
}
