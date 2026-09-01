"use client";

import { use, useState } from "react";
import Link from "next/link";
import { Database, Download, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/results/empty-state";
import { api, downloadFile } from "@/lib/api";
import { fmtBytes, fmtInt, fmtNum } from "@/lib/format";
import { useActiveDataset, useDataset, useRun, useRuns } from "@/lib/hooks";
import type { ColumnInfo, DatasetConfig } from "@/lib/types";
import { useResolvedRunId } from "../_lib/use-run-id";

function Header() {
  return (
    <div className="space-y-1">
      <h1 className="text-xl font-semibold tracking-tight text-foreground">Dados</h1>
      <p className="text-sm text-muted-foreground">
        Configuração de colunas, papéis e sistema de coordenadas do conjunto de dados analisado.
      </p>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className="text-sm text-foreground">{children}</dd>
    </div>
  );
}

function RoleList({ items }: { items: string[] }) {
  if (!items || items.length === 0) return <span className="text-muted-foreground">—</span>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((it) => (
        <Badge key={it} variant="secondary">
          {it}
        </Badge>
      ))}
    </div>
  );
}

function ConfigCard({ config }: { config: DatasetConfig }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Configuração do conjunto de dados</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Coordenada X">{config.x_col || "—"}</Field>
          <Field label="Coordenada Y">{config.y_col || "—"}</Field>
          <Field label="Sistema de coordenadas (CRS)">
            {config.crs_label ? `${config.crs_label} (${config.crs})` : config.crs || "—"}
          </Field>
          <Field label="Identificador">{config.id_col || "—"}</Field>
          <Field label="Variável primária">{config.primary || "—"}</Field>
          <Field label="Valores negativos">
            {config.negatives_allowed ? "Permitidos" : "Não permitidos"}
          </Field>
          <Field label="Variáveis secundárias">
            <RoleList items={config.secondary} />
          </Field>
          <Field label="Variáveis explicativas">
            <RoleList items={config.explanatory} />
          </Field>
          <Field label="Deriva externa (auxiliar)">{config.aux_drift || "—"}</Field>
          {config.bivariate_pairs?.length ? (
            <Field label="Pares bivariados">
              <RoleList items={config.bivariate_pairs.map(([a, b]) => `${a} × ${b}`)} />
            </Field>
          ) : null}
        </dl>
      </CardContent>
    </Card>
  );
}

function ColumnsTable({ columns }: { columns: ColumnInfo[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Colunas ({columns.length})</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="max-w-full overflow-x-auto scrollbar-thin">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Coluna</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Papel sugerido</TableHead>
                <TableHead className="text-right">Únicos</TableHead>
                <TableHead className="text-right">Ausentes</TableHead>
                <TableHead className="text-right">Mín.</TableHead>
                <TableHead className="text-right">Máx.</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {columns.map((c) => (
                <TableRow key={c.name}>
                  <TableCell className="whitespace-nowrap font-medium text-foreground">
                    {c.name}
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-muted-foreground">
                    {c.dtype}
                  </TableCell>
                  <TableCell className="whitespace-nowrap">
                    {c.role_guess ? (
                      <Badge variant="outline">{c.role_guess}</Badge>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-right tabular-nums">
                    {fmtInt(c.n_unique)}
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-right tabular-nums">
                    {c.n_missing > 0 ? (
                      <span className="text-warning">{fmtInt(c.n_missing)}</span>
                    ) : (
                      fmtInt(c.n_missing)
                    )}
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-right tabular-nums">
                    {c.is_numeric ? fmtNum(c.min ?? null) : "—"}
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-right tabular-nums">
                    {c.is_numeric ? fmtNum(c.max ?? null) : "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DataPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { runId, isLoading: runsLoading } = useResolvedRunId(id);
  const { data: run } = useRun(runId);
  const { data: runs, isLoading: runsListLoading } = useRuns(id);
  const activeDs = useActiveDataset(id);
  const datasetId = run?.dataset_id ?? activeDs.datasetId ?? runs?.[0]?.dataset_id;
  const { data: dataset, isLoading: dsLoading, isError: dsError } = useDataset(datasetId);
  const [busy, setBusy] = useState(false);

  async function handleDownload() {
    if (!runId) return;
    setBusy(true);
    try {
      await downloadFile(api.packageUrl(runId), `pacote-${runId}.zip`);
    } catch {
      /* silencioso */
    } finally {
      setBusy(false);
    }
  }

  const loading =
    runsLoading || runsListLoading || activeDs.isLoading || (!!datasetId && dsLoading);

  if (loading) {
    return (
      <div className="space-y-6">
        <Header />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!datasetId) {
    return (
      <div className="space-y-6">
        <Header />
        <EmptyState
          icon={Upload}
          title="Nenhum conjunto de dados"
          description="Envie uma planilha para este projeto para visualizar seus dados."
          action={
            <Button asChild>
              <Link href={`/projects/${id}/upload`}>Enviar planilha</Link>
            </Button>
          }
        />
      </div>
    );
  }

  if (dsError || !dataset) {
    return (
      <div className="space-y-6">
        <Header />
        <p className="text-sm text-destructive">
          Não foi possível carregar o conjunto de dados. Tente novamente mais tarde.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <Header />
        {runId ? (
          <Button variant="outline" size="sm" onClick={handleDownload} disabled={busy}>
            <Download />
            Pacote (ZIP)
          </Button>
        ) : null}
      </div>

      <Card>
        <CardContent className="flex flex-wrap items-center gap-x-8 gap-y-2 p-4 text-sm">
          <div className="flex items-center gap-2 font-medium text-foreground">
            <Database className="size-4 text-muted-foreground" aria-hidden />
            {dataset.original_filename}
          </div>
          <div>
            <span className="text-muted-foreground">Linhas: </span>
            <span className="tabular-nums">{fmtInt(dataset.row_count)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Colunas: </span>
            <span className="tabular-nums">{fmtInt(dataset.col_count)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Tamanho: </span>
            <span className="tabular-nums">{fmtBytes(dataset.file_size)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Versão: </span>
            <span className="tabular-nums">{dataset.version}</span>
          </div>
        </CardContent>
      </Card>

      {dataset.config ? (
        <ConfigCard config={dataset.config} />
      ) : (
        <EmptyState
          icon={Database}
          title="Colunas ainda não confirmadas"
          description="Confirme os papéis das colunas no assistente para configurar a análise."
          action={
            <Button asChild variant="outline">
              <Link href={`/projects/${id}/configure`}>Confirmar colunas</Link>
            </Button>
          }
        />
      )}

      <ColumnsTable columns={dataset.columns} />

      {runId ? (
        <p className="text-xs text-muted-foreground">
          O pacote ZIP da execução inclui o conjunto de dados limpo utilizado na análise.
        </p>
      ) : null}
    </div>
  );
}
