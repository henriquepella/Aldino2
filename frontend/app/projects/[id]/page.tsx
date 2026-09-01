"use client";

import { useRouter } from "next/navigation";
import { use, useEffect } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { useProject } from "@/lib/hooks";

export default function ProjectIndexPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: project, isLoading, isError } = useProject(id);
  const router = useRouter();

  useEffect(() => {
    if (!project) return;
    if (project.dataset_count === 0) {
      router.replace(`/projects/${id}/upload`);
    } else if (project.run_count > 0) {
      router.replace(`/projects/${id}/dashboard`);
    } else {
      router.replace(`/projects/${id}/configure`);
    }
  }, [project, id, router]);

  if (isError) {
    return (
      <p className="text-sm text-destructive">
        Não foi possível carregar este projeto. Tente novamente mais tarde.
      </p>
    );
  }

  return (
    <div className="space-y-3" aria-busy={isLoading || !project}>
      <Skeleton className="h-7 w-56" />
      <Skeleton className="h-4 w-80" />
      <p className="text-sm text-muted-foreground">Abrindo o projeto…</p>
    </div>
  );
}
