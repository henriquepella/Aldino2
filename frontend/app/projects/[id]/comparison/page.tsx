"use client";

import { Trophy } from "lucide-react";
import { use } from "react";
import { MetricCard } from "@/components/results/metric-card";
import { SectionPage } from "@/components/results/section-page";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fmtNum } from "@/lib/format";
import { useRunResults, useRuns } from "@/lib/hooks";
import type { ArtifactOut } from "@/lib/types";
import { cn } from "@/lib/utils";

const STEP_KEY = "method_comparison";
const TITLE = "Comparação Geral dos Métodos";

export default function ComparisonPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: runs } = useRuns(id);
  const done = (runs ?? []).filter((r) => r.status === "done");
  const runId = [...done].sort((a, b) => (a.created_at < b.created_at ? 1 : -1))[0]?.id;

  return (
    <div className="space-y-6">
      <WinnerHighlight runId={runId} />
      <SectionPage
        stepKey={STEP_KEY}
        title={TITLE}
        description="Validação cruzada de todos os métodos de interpolação aplicados e escolha do melhor."
        runId={runId}
        projectId={id}
      />
    </div>
  );
}

function toNumber(v: unknown): number | undefined {
  const n =
    typeof v === "number" ? v : typeof v === "string" ? Number(v.replace(",", ".")) : NaN;
  return Number.isFinite(n) ? n : undefined;
}

interface RankRow {
  method: string;
  rmse?: number;
  r2?: number;
}

function buildRanking(table: ArtifactOut | undefined): RankRow[] {
  const payload = table?.data?.payload;
  if (!payload || payload.columns.length === 0) return [];
  const cols = payload.columns;
  const key = (c: { key: string; label: string }) => `${c.key} ${c.label}`;
  const methodCol =
    cols.find((c) => /m[eé]todo|method|nome|modelo/i.test(key(c))) ?? cols[0];
  const rmseCol = cols.find((c) => /rmse/i.test(key(c)));
  const r2Col = cols.find((c) => /r²|r2|r\^2/i.test(key(c)));

  const rows: RankRow[] = payload.rows.map((r) => ({
    method: String(r[methodCol.key] ?? "—"),
    rmse: rmseCol ? toNumber(r[rmseCol.key]) : undefined,
    r2: r2Col ? toNumber(r[r2Col.key]) : undefined,
  }));

  if (rows.some((r) => r.rmse != null)) {
    rows.sort((a, b) => (a.rmse ?? Number.POSITIVE_INFINITY) - (b.rmse ?? Number.POSITIVE_INFINITY));
  }
  return rows.slice(0, 8);
}

function WinnerHighlight({ runId }: { runId?: string }) {
  const { data } = useRunResults(runId, true);

  if (!runId || !data || data.run.status !== "done") return null;

  const m = (data.run.metrics_summary ?? {}) as Record<string, unknown>;
  const best = m.best_method;
  if (best == null || best === "") return null;

  const step = data.steps.find((s) => s.key === STEP_KEY);
  const ranking = buildRanking(step?.tables?.[0]);

  return (
    <Card className="border-primary/30 bg-primary/5">
      <CardHeader className="flex-row items-center gap-3 space-y-0">
        <span className="grid size-10 shrink-0 place-items-center rounded-full bg-primary/15 text-primary">
          <Trophy className="size-5" aria-hidden />
        </span>
        <div className="space-y-0.5">
          <CardTitle className="text-base">Método vencedor</CardTitle>
          <p className="text-sm text-muted-foreground">
            Melhor desempenho na validação cruzada
          </p>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-2xl font-semibold tracking-tight text-foreground">{String(best)}</p>

        <div className="grid gap-3 sm:grid-cols-3">
          <MetricCard label="RMSE" value={fmtNum(toNumber(m.best_method_rmse))} accent="primary" />
          <MetricCard label="MAE" value={fmtNum(toNumber(m.best_method_mae))} />
          <MetricCard label="R²" value={fmtNum(toNumber(m.best_method_r2))} />
        </div>

        {ranking.length > 0 ? (
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Ranking dos métodos
            </p>
            <ol className="space-y-1.5">
              {ranking.map((r, i) => (
                <li
                  key={`${r.method}-${i}`}
                  className="flex items-center justify-between gap-3 rounded-md border bg-card px-3 py-2 text-sm"
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <span
                      className={cn(
                        "grid size-5 shrink-0 place-items-center rounded-full text-[11px] font-semibold tabular",
                        i === 0
                          ? "bg-primary/15 text-primary"
                          : "bg-muted text-muted-foreground",
                      )}
                    >
                      {i + 1}
                    </span>
                    <span className="truncate font-medium text-foreground">{r.method}</span>
                  </span>
                  <span className="shrink-0 tabular text-xs text-muted-foreground">
                    {r.rmse != null ? `RMSE ${fmtNum(r.rmse)}` : ""}
                    {r.rmse != null && r.r2 != null ? " · " : ""}
                    {r.r2 != null ? `R² ${fmtNum(r.r2)}` : ""}
                  </span>
                </li>
              ))}
            </ol>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
