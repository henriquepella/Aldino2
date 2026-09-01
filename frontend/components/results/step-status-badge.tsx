import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type StepStatus = "pending" | "running" | "ok" | "skipped" | "failed";

const MAP: Record<
  StepStatus,
  { label: string; variant: "default" | "secondary" | "success" | "warning" | "destructive" }
> = {
  ok: { label: "Concluída", variant: "success" },
  skipped: { label: "Não aplicável", variant: "warning" },
  failed: { label: "Falhou", variant: "destructive" },
  running: { label: "Em execução", variant: "default" },
  pending: { label: "Na fila", variant: "secondary" },
};

export function StepStatusBadge({
  status,
  className,
}: {
  status: string;
  className?: string;
}) {
  const cfg = MAP[(status as StepStatus)] ?? MAP.pending;
  return (
    <Badge
      variant={cfg.variant}
      className={cn(status === "running" && "animate-pulse", className)}
    >
      {cfg.label}
    </Badge>
  );
}
