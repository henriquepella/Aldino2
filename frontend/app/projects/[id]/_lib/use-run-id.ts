"use client";

import * as React from "react";
import { useRuns } from "@/lib/hooks";

/**
 * Resolve o runId de uma seção de resultados:
 *  1. sessionStorage 'run:<projectId>' se apontar para uma execução concluída;
 *  2. senão, a execução "done" mais recente do projeto;
 *  3. senão, undefined (a página deve mostrar um estado vazio com CTA para /run).
 */
export function useResolvedRunId(projectId: string) {
  const { data: runs, isLoading, isError } = useRuns(projectId);
  const [stored, setStored] = React.useState<string | null>(null);

  React.useEffect(() => {
    try {
      setStored(window.sessionStorage.getItem(`run:${projectId}`));
    } catch {
      setStored(null);
    }
  }, [projectId]);

  const runId = React.useMemo(() => {
    if (!runs) return undefined;
    const done = runs.filter((r) => r.status === "done");
    if (stored && done.some((r) => r.id === stored)) return stored;
    const sorted = [...done].sort((a, b) =>
      a.created_at < b.created_at ? 1 : a.created_at > b.created_at ? -1 : 0,
    );
    return sorted[0]?.id;
  }, [runs, stored]);

  return {
    runId,
    isLoading,
    isError,
    hasRuns: (runs?.length ?? 0) > 0,
  };
}
