import { ImageOff } from "lucide-react";
import type { ArtifactOut } from "@/lib/types";
import { cn } from "@/lib/utils";
import { EmptyState } from "./empty-state";
import { FigureViewer } from "./figure-viewer";

export function FigureGrid({
  figures,
  runId,
  className,
}: {
  figures: ArtifactOut[];
  runId?: string;
  className?: string;
}) {
  void runId;
  if (!figures || figures.length === 0) {
    return (
      <EmptyState
        icon={ImageOff}
        title="Sem figuras"
        description="Este passo não gerou gráficos ou mapas."
        className={className}
      />
    );
  }
  return (
    <div className={cn("grid gap-4 sm:grid-cols-2", className)}>
      {figures.map((fig) => (
        <FigureViewer key={fig.id} fig={fig} />
      ))}
    </div>
  );
}
