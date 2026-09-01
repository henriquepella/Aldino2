import { CheckCircle2, Circle, Loader2, MinusCircle, XCircle } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import type { RunOut, StepState } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Ordem canônica dos passos da análise completa. */
export const STEP_ORDER: { key: string; title: string }[] = [
  { key: "descriptive", title: "Estatística Descritiva" },
  { key: "esda_univariate", title: "ESDA Univariada" },
  { key: "moran_scatter", title: "Moran Scatter Plot" },
  { key: "esda_bivariate", title: "ESDA Bivariada" },
  { key: "idw", title: "IDW" },
  { key: "kriging", title: "Krigagem Ordinária" },
  { key: "external_drift", title: "Krigagem com Deriva Externa" },
  { key: "gwr", title: "GWR / GWM" },
  { key: "cokriging", title: "Co-Krigagem" },
  { key: "method_comparison", title: "Comparação Geral dos Métodos" },
];

const ICON: Record<string, { icon: LucideIcon; className: string }> = {
  ok: { icon: CheckCircle2, className: "text-success" },
  running: { icon: Loader2, className: "text-primary animate-spin" },
  skipped: { icon: MinusCircle, className: "text-warning" },
  failed: { icon: XCircle, className: "text-destructive" },
  pending: { icon: Circle, className: "text-muted-foreground/50" },
};

function StepRow({ step }: { step: StepState }) {
  const cfg = ICON[step.status] ?? ICON.pending;
  const Icon = cfg.icon;
  return (
    <li className="flex items-start gap-2 py-1 text-sm">
      <Icon className={cn("mt-0.5 size-4 shrink-0", cfg.className)} aria-hidden />
      <div className="min-w-0 flex-1">
        <span
          className={cn(
            "block truncate",
            step.status === "pending" ? "text-muted-foreground" : "text-foreground",
          )}
        >
          {step.title}
        </span>
        {step.status === "skipped" && step.reason ? (
          <span className="block text-xs text-muted-foreground">{step.reason}</span>
        ) : null}
      </div>
    </li>
  );
}

export function RunProgress({ run, className }: { run: RunOut; className?: string }) {
  const raw = typeof run.progress === "number" ? run.progress : 0;
  const pct = Math.max(0, Math.min(100, raw <= 1 ? raw * 100 : raw));

  const byKey = new Map<string, StepState>();
  for (const s of run.steps ?? []) byKey.set(s.key, s);

  const rows: StepState[] = [];
  const used = new Set<string>();
  for (const { key, title } of STEP_ORDER) {
    const existing = byKey.get(key);
    used.add(key);
    rows.push(
      existing ?? { key, title, status: "pending", reason: null, n_tables: 0, n_figures: 0, metrics: {} },
    );
  }
  for (const s of run.steps ?? []) {
    if (!used.has(s.key)) rows.push(s);
  }

  const currentStep =
    run.steps?.find((s) => s.key === run.current_step)?.title || run.current_step || "";
  const logLines = (run.log ?? []).slice(-12);

  return (
    <div className={cn("space-y-4", className)}>
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium text-foreground">
            {run.status === "running"
              ? "Executando análise"
              : run.status === "done"
                ? "Análise concluída"
                : run.status === "failed"
                  ? "Análise interrompida"
                  : run.status === "cancelled"
                    ? "Análise cancelada"
                    : "Aguardando início"}
          </span>
          <span className="tabular text-muted-foreground">{Math.round(pct)}%</span>
        </div>
        <Progress value={pct} />
        {currentStep && (run.status === "running" || run.status === "pending") ? (
          <p className="text-xs text-muted-foreground">Passo atual: {currentStep}</p>
        ) : null}
        {run.status === "failed" && run.error ? (
          <p className="text-xs text-destructive">{run.error}</p>
        ) : null}
      </div>

      <ul className="divide-y divide-border/60 rounded-md border p-2">
        {rows.map((s) => (
          <StepRow key={s.key} step={s} />
        ))}
      </ul>

      {logLines.length > 0 ? (
        <pre className="max-h-56 overflow-auto scrollbar-thin rounded-md border bg-muted/40 p-3 text-xs leading-relaxed text-muted-foreground">
          {logLines
            .map((l) => (l.step ? `[${l.step}] ${l.msg}` : l.msg))
            .join("\n")}
        </pre>
      ) : null}
    </div>
  );
}
