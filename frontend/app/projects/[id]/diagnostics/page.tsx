"use client";

import { useMutation } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Copy,
  Database,
  Info,
  MapPinOff,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";
import { toast } from "sonner";
import { EmptyState } from "@/components/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ApiError, api } from "@/lib/api";
import { fmtInt } from "@/lib/format";
import { useActiveDataset, useCleanDataset, useDataset, useRuns } from "@/lib/hooks";
import type { DiagnosticItem, ValidationResult } from "@/lib/types";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 10;

const COUNT_LABELS: Record<string, string> = {
  rows: "Registros",
  n_rows: "Registros",
  total: "Registros",
  total_rows: "Registros",
  records: "Registros",
  n_records: "Registros",
  n_total: "Registros",
  valid: "Válidos",
  valid_rows: "Linhas válidas",
  valid_coords: "Coordenadas válidas",
  coords_valid: "Coordenadas válidas",
  coordinates_valid: "Coordenadas válidas",
  n_valid_coords: "Coordenadas válidas",
  invalid_coords: "Coordenadas inválidas",
  coords_invalid: "Coordenadas inválidas",
  missing: "Valores ausentes",
  n_missing: "Valores ausentes",
  missing_values: "Valores ausentes",
  missing_coords: "Coordenadas ausentes",
  missing_primary: "Primária ausente",
  duplicates: "Duplicidades",
  n_duplicates: "Duplicidades",
  duplicate_rows: "Duplicidades",
  duplicated: "Duplicidades",
  coincident: "Pontos coincidentes",
  coincident_points: "Pontos coincidentes",
  coincident_coords: "Coordenadas coincidentes",
  outliers: "Outliers",
  n_outliers: "Outliers",
  outlier_rows: "Outliers",
  negatives: "Valores negativos",
  n_negatives: "Valores negativos",
  negative_values: "Valores negativos",
};

const ISSUE_LABELS: Record<string, string> = {
  missing_coord: "Coordenada ausente",
  missing_coords: "Coordenada ausente",
  missing_coordinates: "Coordenada ausente",
  missing_x: "X ausente",
  missing_y: "Y ausente",
  invalid_coord: "Coordenada inválida",
  invalid_coords: "Coordenada inválida",
  invalid_coordinates: "Coordenada inválida",
  out_of_range: "Fora do intervalo",
  coord_out_of_range: "Coordenada fora do intervalo",
  duplicate: "Registro duplicado",
  duplicate_row: "Registro duplicado",
  duplicated: "Registro duplicado",
  coincident: "Ponto coincidente",
  coincident_point: "Ponto coincidente",
  coincident_coords: "Coordenadas coincidentes",
  outlier: "Outlier",
  outlier_primary: "Outlier (variável primária)",
  negative: "Valor negativo",
  negative_value: "Valor negativo",
  negative_primary: "Primária negativa",
  missing_primary: "Variável primária ausente",
  missing_value: "Valor ausente",
  non_numeric: "Valor não numérico",
};

function humanize(s: string): string {
  return s.replace(/[_-]+/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}
const countLabel = (k: string) => COUNT_LABELS[k] ?? humanize(k);
const issueLabel = (s: string) => ISSUE_LABELS[s] ?? humanize(s);
const isWarnCount = (k: string) =>
  /missing|ausen|dupl|outlier|negativ|invalid|coincid/i.test(k);

function useWizardDatasetId(projectId: string): {
  dsId: string | undefined;
  resolving: boolean;
} {
  const runsQ = useRuns(projectId);
  const activeDs = useActiveDataset(projectId);
  const [ss, setSs] = useState<string | null | undefined>(undefined);
  useEffect(() => {
    try {
      setSs(sessionStorage.getItem(`ds:${projectId}`));
    } catch {
      setSs(null);
    }
  }, [projectId]);
  const dsId =
    (ss || undefined) ?? activeDs.datasetId ?? runsQ.data?.[0]?.dataset_id ?? undefined;
  return {
    dsId,
    resolving: ss === undefined || (!dsId && (runsQ.isLoading || activeDs.isLoading)),
  };
}

export default function DiagnosticsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return <Diagnostics projectId={id} />;
}

function Header({ subtitle }: { subtitle?: string }) {
  return (
    <div className="space-y-1">
      <h1 className="text-xl font-semibold tracking-tight">Diagnóstico da base</h1>
      <p className="text-sm text-muted-foreground">
        {subtitle ??
          "Revise os problemas detectados e limpe a base antes de configurar a análise."}
      </p>
    </div>
  );
}

function LoadingBlocks() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-lg" />
        ))}
      </div>
      <Skeleton className="h-48 w-full rounded-lg" />
      <Skeleton className="h-64 w-full rounded-lg" />
    </div>
  );
}

function StatusBadge({ status }: { status: DiagnosticItem["status"] }) {
  if (status === "ok") return <Badge variant="success">OK</Badge>;
  if (status === "warn") return <Badge variant="warning">Atenção</Badge>;
  return <Badge variant="destructive">Erro</Badge>;
}

function Diagnostics({ projectId }: { projectId: string }) {
  const router = useRouter();
  const { dsId, resolving } = useWizardDatasetId(projectId);
  const dsQ = useDataset(dsId);
  const ds = dsQ.data;
  const clean = useCleanDataset(dsId ?? "");

  const validateMut = useMutation({
    mutationFn: () => api.validateDataset(dsId!),
  });

  const needValidate = !!ds && !ds.validation;
  useEffect(() => {
    if (
      needValidate &&
      dsId &&
      !validateMut.isPending &&
      !validateMut.data &&
      !validateMut.isError
    ) {
      validateMut.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [needValidate, dsId]);

  const validation: ValidationResult | null =
    ds?.validation ?? validateMut.data ?? null;

  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [page, setPage] = useState(0);

  async function runClean(body: Parameters<typeof api.cleanDataset>[1]) {
    try {
      await clean.mutateAsync(body);
      setSelected(new Set());
      setPage(0);
      validateMut.reset();
      toast.success("Base atualizada.");
    } catch (e) {
      toast.error(
        e instanceof ApiError ? e.message : "Não foi possível atualizar a base.",
      );
    }
  }

  // ---- loading / empty / error gates ----
  if (resolving || (dsId && dsQ.isLoading)) {
    return (
      <div className="space-y-6">
        <Header />
        <LoadingBlocks />
      </div>
    );
  }

  if (!dsId) {
    return (
      <div className="space-y-6">
        <Header />
        <EmptyState
          icon={<Database />}
          title="Nenhuma base enviada"
          description="Envie a planilha de amostras para diagnosticar a base do projeto."
          action={
            <Button asChild>
              <Link href={`/projects/${projectId}/upload`}>Enviar planilha</Link>
            </Button>
          }
        />
      </div>
    );
  }

  if (dsQ.isError) {
    const msg =
      dsQ.error instanceof ApiError
        ? dsQ.error.status === 404
          ? "Base não encontrada. Envie a planilha novamente."
          : dsQ.error.message
        : "Não foi possível carregar a base.";
    return (
      <div className="space-y-6">
        <Header />
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {msg}
        </div>
        <Button asChild variant="outline">
          <Link href={`/projects/${projectId}/upload`}>Voltar ao envio</Link>
        </Button>
      </div>
    );
  }

  const subtitle = ds
    ? `${ds.original_filename} · ${fmtInt(ds.row_count)} registros · ${fmtInt(ds.col_count)} colunas`
    : undefined;

  if (!validation) {
    return (
      <div className="space-y-6">
        <Header subtitle={subtitle} />
        {validateMut.isError ? (
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
            {validateMut.error instanceof ApiError
              ? validateMut.error.message
              : "Não foi possível validar a base."}
            <div className="mt-3">
              <Button
                size="sm"
                variant="outline"
                onClick={() => validateMut.mutate()}
                disabled={validateMut.isPending}
              >
                Tentar novamente
              </Button>
            </div>
          </div>
        ) : (
          <LoadingBlocks />
        )}
      </div>
    );
  }

  const counts = Object.entries(validation.counts ?? {});
  const flags = validation.row_flags ?? [];
  const totalPages = Math.max(1, Math.ceil(flags.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages - 1);
  const pageRows = flags.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE);
  const allSelected = flags.length > 0 && selected.size === flags.length;
  const busy = clean.isPending;

  return (
    <div className="space-y-6">
      <Header subtitle={subtitle} />

      {/* Contadores */}
      {counts.length > 0 ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {counts.map(([k, v]) => {
            const warn = isWarnCount(k) && Number(v) > 0;
            return (
              <Card key={k} className="p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  {countLabel(k)}
                </p>
                <p
                  className={cn(
                    "mt-1 text-2xl font-semibold tabular leading-tight",
                    warn ? "text-warning" : "text-foreground",
                  )}
                >
                  {fmtInt(Number(v))}
                </p>
              </Card>
            );
          })}
        </div>
      ) : null}

      {/* Tabela de diagnóstico */}
      {validation.summary.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Diagnóstico da base</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Item</TableHead>
                  <TableHead>Resultado</TableHead>
                  <TableHead className="w-28">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {validation.summary.map((it, i) => (
                  <TableRow key={`${it.item}-${i}`}>
                    <TableCell className="align-top">
                      <span className="font-medium text-foreground">{it.item}</span>
                      {it.detail ? (
                        <span className="mt-0.5 block text-xs font-normal text-muted-foreground">
                          {it.detail}
                        </span>
                      ) : null}
                    </TableCell>
                    <TableCell className="align-top">{it.value || "—"}</TableCell>
                    <TableCell className="align-top">
                      <StatusBadge status={it.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}

      {/* Aviso can_proceed */}
      {!validation.can_proceed ? (
        <div className="flex gap-3 rounded-lg border border-warning/40 bg-warning/10 p-4 text-sm">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
          <div className="space-y-1">
            <p className="font-medium text-foreground">
              A base ainda não está pronta para a análise
            </p>
            {validation.notes.length > 0 ? (
              <ul className="list-disc space-y-0.5 pl-4 text-muted-foreground">
                {validation.notes.map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            ) : (
              <p className="text-muted-foreground">
                Remova as linhas problemáticas destacadas abaixo para prosseguir.
              </p>
            )}
          </div>
        </div>
      ) : validation.notes.length > 0 ? (
        <div className="flex gap-3 rounded-lg border bg-muted/40 p-4 text-sm">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
          <ul className="list-disc space-y-0.5 pl-4 text-muted-foreground">
            {validation.notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {/* Linhas problemáticas */}
      {flags.length === 0 ? (
        <Card>
          <CardContent className="flex items-center gap-2 p-6 text-sm text-muted-foreground">
            <CheckCircle2 className="h-4 w-4 text-success" />
            Nenhuma linha problemática encontrada.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <CardTitle className="text-base">
                Linhas problemáticas{" "}
                <span className="font-normal text-muted-foreground">
                  ({fmtInt(flags.length)})
                </span>
              </CardTitle>
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busy || selected.size === 0}
                  onClick={() => runClean({ drop_row_indices: [...selected] })}
                >
                  <Trash2 className="h-4 w-4" />
                  Excluir selecionadas
                  {selected.size > 0 ? ` (${selected.size})` : ""}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busy}
                  onClick={() => runClean({ drop_duplicates: true })}
                >
                  <Copy className="h-4 w-4" />
                  Remover duplicatas
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busy}
                  onClick={() => runClean({ drop_missing_in_coords: true })}
                >
                  <MapPinOff className="h-4 w-4" />
                  Remover coordenadas inválidas
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <Checkbox
                      checked={allSelected}
                      onCheckedChange={(c) =>
                        setSelected(
                          c ? new Set(flags.map((f) => f.row_index)) : new Set(),
                        )
                      }
                      aria-label="Selecionar todas as linhas"
                    />
                  </TableHead>
                  <TableHead className="w-24">Linha</TableHead>
                  <TableHead>Problemas</TableHead>
                  <TableHead className="w-28">Severidade</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pageRows.map((fl) => {
                  const checked = selected.has(fl.row_index);
                  return (
                    <TableRow
                      key={fl.row_index}
                      data-state={checked ? "selected" : undefined}
                    >
                      <TableCell>
                        <Checkbox
                          checked={checked}
                          onCheckedChange={(c) =>
                            setSelected((prev) => {
                              const next = new Set(prev);
                              if (c) next.add(fl.row_index);
                              else next.delete(fl.row_index);
                              return next;
                            })
                          }
                          aria-label={`Selecionar linha ${fl.row_index}`}
                        />
                      </TableCell>
                      <TableCell>{fmtInt(fl.row_index)}</TableCell>
                      <TableCell className="whitespace-normal">
                        <div className="flex flex-wrap gap-1">
                          {fl.issues.map((is, i) => (
                            <Badge key={i} variant="secondary">
                              {issueLabel(is)}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            fl.severity === "error" ? "destructive" : "warning"
                          }
                        >
                          {fl.severity === "error" ? "Erro" : "Atenção"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
            {totalPages > 1 ? (
              <div className="flex items-center justify-between border-t p-3 text-sm">
                <span className="text-muted-foreground">
                  Página {safePage + 1} de {totalPages}
                </span>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={safePage === 0}
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                  >
                    Anterior
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={safePage >= totalPages - 1}
                    onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  >
                    Próxima
                  </Button>
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}

      {/* Avançar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-4">
        <p className="text-sm text-muted-foreground">
          {validation.can_proceed
            ? "A base está pronta para a análise."
            : "Resolva os itens pendentes para continuar."}
        </p>
        <Button
          disabled={!validation.can_proceed}
          onClick={() => router.push(`/projects/${projectId}/settings`)}
        >
          Avançar
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
