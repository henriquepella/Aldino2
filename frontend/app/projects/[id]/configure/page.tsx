"use client";

import { ArrowLeft, ArrowRight, Info, MapPin, UploadCloud } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { ApiError } from "@/lib/api";
import { useActiveDataset, useDataset, useRuns, useSetDatasetConfig } from "@/lib/hooks";
import type { DatasetOut, DatasetConfig, DetectionResult } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

const NONE = "__none__";

function readDatasetId(projectId: string): string | undefined {
  try {
    return sessionStorage.getItem(`ds:${projectId}`) ?? undefined;
  } catch {
    return undefined;
  }
}

function confidenceBadge(v: number): { variant: "success" | "warning" | "destructive"; label: string } {
  const pct = Math.round((Number.isFinite(v) ? v : 0) * 100);
  if (v >= 0.7) return { variant: "success", label: `Confiança alta · ${pct}%` };
  if (v >= 0.4) return { variant: "warning", label: `Confiança média · ${pct}%` };
  return { variant: "destructive", label: `Confiança baixa · ${pct}%` };
}

export default function ConfigurePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const runsQ = useRuns(id);

  const [cachedDsId, setCachedDsId] = useState<string | undefined>(undefined);
  const [checkedCache, setCheckedCache] = useState(false);
  useEffect(() => {
    setCachedDsId(readDatasetId(id));
    setCheckedCache(true);
  }, [id]);

  const activeDs = useActiveDataset(id);
  const datasetId = cachedDsId ?? activeDs.datasetId ?? runsQ.data?.[0]?.dataset_id;
  const datasetQ = useDataset(datasetId);

  const waiting =
    !checkedCache || (!datasetId && (runsQ.isLoading || activeDs.isLoading));

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Assistente · Passo 2 de 4
        </p>
        <h1 className="text-2xl font-bold tracking-tight">Confirmar colunas</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Revise o mapeamento detectado automaticamente. As sugestões vêm da análise da planilha —
          ajuste o que for necessário antes de validar a base.
        </p>
      </header>

      {waiting ? (
        <FormSkeleton />
      ) : !datasetId ? (
        <MissingDatasetNotice projectId={id} />
      ) : datasetQ.isLoading ? (
        <FormSkeleton />
      ) : datasetQ.isError ? (
        <ErrorNotice
          message={
            datasetQ.error instanceof ApiError
              ? datasetQ.error.message
              : "Não foi possível carregar a base enviada."
          }
          projectId={id}
        />
      ) : !datasetQ.data ? (
        <MissingDatasetNotice projectId={id} />
      ) : !datasetQ.data.detection ? (
        <ErrorNotice
          message="A detecção automática de colunas não está disponível para esta base. Reenvie o arquivo para gerar as sugestões."
          projectId={id}
        />
      ) : (
        <ConfigureForm
          key={datasetQ.data.id}
          projectId={id}
          dataset={datasetQ.data}
          detection={datasetQ.data.detection}
        />
      )}
    </div>
  );
}

function ConfigureForm({
  projectId,
  dataset,
  detection: det,
}: {
  projectId: string;
  dataset: DatasetOut;
  detection: DetectionResult;
}) {
  const router = useRouter();
  const setConfig = useSetDatasetConfig(dataset.id);
  const existing = dataset.config;

  const allCols = useMemo(() => dataset.columns.map((c) => c.name), [dataset.columns]);
  const numVars = det.numeric_variables;

  const [xCol, setXCol] = useState(existing?.x_col ?? det.coord_x ?? "");
  const [yCol, setYCol] = useState(existing?.y_col ?? det.coord_y ?? "");
  const [crs, setCrs] = useState(existing?.crs ?? det.crs_suggested ?? "");
  const [crsLabel, setCrsLabel] = useState(existing?.crs_label ?? det.crs_label ?? "");
  const [idCol, setIdCol] = useState(existing?.id_col ?? "");
  const [negativesAllowed, setNegativesAllowed] = useState(existing?.negatives_allowed ?? false);

  const [selected, setSelected] = useState<string[]>(() => {
    if (existing) {
      const set = new Set(
        [existing.primary, ...existing.secondary, ...existing.explanatory].filter(Boolean),
      );
      const list = numVars.filter((v) => set.has(v));
      if (list.length) return list;
    }
    return [...numVars];
  });
  const [primary, setPrimary] = useState(existing?.primary ?? det.primary_guess ?? numVars[0] ?? "");
  const [secondary, setSecondary] = useState<string[]>(
    existing?.secondary ?? det.secondary_guess ?? [],
  );
  const [explanatory, setExplanatory] = useState<string[]>(
    existing?.explanatory ?? det.explanatory_guess ?? [],
  );
  const [auxDrift, setAuxDrift] = useState(existing?.aux_drift ?? det.aux_drift_guess ?? "");

  const analyze = useMemo(
    () => numVars.filter((v) => selected.includes(v)),
    [numVars, selected],
  );

  // Mantém as listas dependentes coerentes com as variáveis escolhidas.
  useEffect(() => {
    const set = new Set(analyze);
    setSecondary((s) => s.filter((v) => set.has(v) && v !== primary));
    setExplanatory((s) => s.filter((v) => set.has(v)));
    setPrimary((p) => (set.size && !set.has(p) ? analyze[0] : p));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analyze.join("|")]);

  function toggleAnalyze(name: string) {
    setSelected((prev) =>
      prev.includes(name) ? prev.filter((v) => v !== name) : [...prev, name],
    );
  }
  function toggleList(
    list: string[],
    setList: (v: string[]) => void,
    name: string,
  ) {
    setList(list.includes(name) ? list.filter((v) => v !== name) : [...list, name]);
  }

  function applyCrs(value: string) {
    setCrs(value);
    const alt = det.crs_alternatives.find((a) => a.epsg === value || `EPSG:${a.epsg}` === value);
    setCrsLabel(alt ? alt.label : value ? (/^EPSG:/i.test(value) ? value : `EPSG:${value}`) : "");
  }

  const coordErr =
    !xCol || !yCol
      ? "Selecione as colunas de coordenada X e Y."
      : xCol === yCol
        ? "As coordenadas X e Y devem ser colunas diferentes."
        : null;
  const crsErr = !crs.trim() ? "Informe o código EPSG do sistema de referência." : null;
  const varsErr = analyze.length === 0 ? "Escolha ao menos uma variável para analisar." : null;
  const primaryErr = !primary ? "Defina a variável principal." : null;
  const formErr = coordErr ?? crsErr ?? varsErr ?? primaryErr;

  async function onSubmit() {
    if (formErr) return;
    const cfg: DatasetConfig = {
      x_col: xCol,
      y_col: yCol,
      crs: crs.trim(),
      crs_label: crsLabel.trim() || crs.trim(),
      id_col: idCol || null,
      primary,
      secondary: secondary.filter((v) => analyze.includes(v) && v !== primary),
      explanatory: explanatory.filter((v) => analyze.includes(v)),
      aux_drift: auxDrift || null,
      bivariate_pairs: existing?.bivariate_pairs ?? [],
      negatives_allowed: negativesAllowed,
      advanced: existing?.advanced ?? {},
    };
    try {
      await setConfig.mutateAsync(cfg);
      toast.success("Configuração salva. Vamos ao diagnóstico da base.");
      router.push(`/projects/${projectId}/diagnostics`);
    } catch (err) {
      toast.error(
        err instanceof ApiError
          ? err.message
          : "Não foi possível salvar a configuração. Tente novamente.",
      );
    }
  }

  const coordConf = confidenceBadge(det.coord_confidence);
  const crsConf = confidenceBadge(det.crs_confidence);

  return (
    <TooltipProvider delayDuration={150}>
      <div className="space-y-6 pb-24">
        {det.notes.length > 0 ? (
          <div className="flex gap-2 rounded-md border border-border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
            <Info className="mt-0.5 h-4 w-4 shrink-0" />
            <ul className="space-y-0.5">
              {det.notes.map((n, i) => (
                <li key={i}>{n}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Coordenadas + CRS */}
          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle className="flex items-center gap-2 text-base">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                Georreferenciamento
              </CardTitle>
              <Badge variant={coordConf.variant}>{coordConf.label}</Badge>
            </CardHeader>
            <CardContent className="space-y-5">
              <ColumnField
                label="Coordenada X (Este / Longitude)"
                value={xCol}
                onChange={setXCol}
                options={allCols}
                candidates={det.candidates_x}
                onPickCandidate={setXCol}
              />
              <ColumnField
                label="Coordenada Y (Norte / Latitude)"
                value={yCol}
                onChange={setYCol}
                options={allCols}
                candidates={det.candidates_y}
                onPickCandidate={setYCol}
              />
              {coordErr ? <FieldError>{coordErr}</FieldError> : null}

              <Separator />

              <div className="space-y-1.5">
                <Label htmlFor="crs-epsg">Sistema de referência (EPSG)</Label>
                <div className="flex flex-wrap items-center gap-2">
                  <Input
                    id="crs-epsg"
                    value={crs}
                    onChange={(e) => applyCrs(e.target.value)}
                    placeholder="Ex.: EPSG:31983"
                    className="w-44"
                  />
                  {det.crs_alternatives.length > 0 ? (
                    <Select value="" onValueChange={applyCrs}>
                      <SelectTrigger className="w-64">
                        <SelectValue placeholder="Escolher da lista sugerida" />
                      </SelectTrigger>
                      <SelectContent>
                        {det.crs_alternatives.map((a) => (
                          <SelectItem key={a.epsg} value={a.epsg}>
                            {a.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : null}
                </div>
                <p className="text-xs text-muted-foreground">
                  {crsLabel || det.crs_label || "Sistema não identificado"}
                </p>
                <div className="flex flex-wrap items-center gap-2 pt-1">
                  <Badge variant={crsConf.variant}>{crsConf.label}</Badge>
                  <span className="text-xs text-muted-foreground">
                    Detecção: {det.coord_kind}
                  </span>
                </div>
                {det.crs_reason && det.crs_confidence < 0.5 ? (
                  <div className="mt-1 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-warning">
                    {det.crs_reason}
                  </div>
                ) : det.crs_reason ? (
                  <p className="text-xs text-muted-foreground">{det.crs_reason}</p>
                ) : null}
                {crsErr ? <FieldError>{crsErr}</FieldError> : null}
              </div>

              <Separator />

              <div className="space-y-1.5">
                <Label>Coluna identificadora (opcional)</Label>
                <Select
                  value={idCol || NONE}
                  onValueChange={(v) => setIdCol(v === NONE ? "" : v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NONE}>Nenhuma</SelectItem>
                    {allCols.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
                        {det.id_like_columns.includes(c) ? "  ·  sugerida" : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Código único por amostra usado para rastrear linhas nos relatórios.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Variáveis */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Variáveis a analisar</CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              {numVars.length === 0 ? (
                <p className="text-sm text-destructive">
                  Nenhuma variável numérica foi detectada na planilha. Reenvie o arquivo com ao menos
                  uma coluna de valores.
                </p>
              ) : (
                <>
                  <div className="space-y-2">
                    <Label>Colunas numéricas ({analyze.length} selecionadas)</Label>
                    <div className="grid gap-1.5 sm:grid-cols-2">
                      {numVars.map((v) => (
                        <label
                          key={v}
                          className="flex cursor-pointer items-center gap-2 rounded-md border border-border px-2.5 py-1.5 text-sm hover:bg-accent/40"
                        >
                          <Checkbox
                            checked={selected.includes(v)}
                            onCheckedChange={() => toggleAnalyze(v)}
                          />
                          <span className="truncate">{v}</span>
                        </label>
                      ))}
                    </div>
                    {varsErr ? <FieldError>{varsErr}</FieldError> : null}
                  </div>

                  <Separator />

                  <div className="space-y-1.5">
                    <Label>Variável principal</Label>
                    <Select
                      value={primary || undefined}
                      onValueChange={setPrimary}
                      disabled={analyze.length === 0}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione a variável principal" />
                      </SelectTrigger>
                      <SelectContent>
                        {analyze.map((v) => (
                          <SelectItem key={v} value={v}>
                            {v}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      Atributo interpolado por IDW, krigagem e comparado entre métodos.
                    </p>
                    {primaryErr ? <FieldError>{primaryErr}</FieldError> : null}
                  </div>

                  <ChipMultiSelect
                    label="Variáveis secundárias"
                    hint="Entram na ESDA bivariada e no Moran bivariado com a principal."
                    options={analyze.filter((v) => v !== primary)}
                    selected={secondary}
                    onToggle={(name) => toggleList(secondary, setSecondary, name)}
                    empty="Sem outras variáveis disponíveis."
                  />

                  <ChipMultiSelect
                    label="Variáveis explicativas (GWR / GWM)"
                    hint="Preditoras da regressão geograficamente ponderada."
                    options={analyze.filter((v) => v !== primary)}
                    selected={explanatory}
                    onToggle={(name) => toggleList(explanatory, setExplanatory, name)}
                    empty="Sem outras variáveis disponíveis."
                  />

                  <div className="space-y-1.5">
                    <Label>Variável auxiliar (deriva externa / co-krigagem, opcional)</Label>
                    <Select
                      value={auxDrift || NONE}
                      onValueChange={(v) => setAuxDrift(v === NONE ? "" : v)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={NONE}>Nenhuma</SelectItem>
                        {numVars
                          .filter((v) => v !== primary)
                          .map((v) => (
                            <SelectItem key={v} value={v}>
                              {v}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      Covariável densamente amostrada usada como apoio (ex.: altitude, NDVI).
                    </p>
                  </div>

                  <Separator />

                  <label className="flex cursor-pointer items-start gap-2.5 text-sm">
                    <Checkbox
                      checked={negativesAllowed}
                      onCheckedChange={(c) => setNegativesAllowed(c === true)}
                      className="mt-0.5"
                    />
                    <span>
                      Valores negativos são válidos
                      <span className="mt-0.5 block text-xs text-muted-foreground">
                        Marque para atributos que podem ser negativos (ex.: elevação relativa, saldo).
                        Caso contrário, valores &lt; 0 serão sinalizados no diagnóstico.
                      </span>
                    </span>
                  </label>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Barra de ação fixa */}
      <div className="fixed inset-x-0 bottom-0 z-30 border-t bg-background/95 backdrop-blur md:pl-64">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-6 py-3">
          <Button asChild variant="ghost" size="sm">
            <Link href={`/projects/${projectId}/upload`}>
              <ArrowLeft className="h-4 w-4" />
              Voltar
            </Link>
          </Button>
          <div className="flex items-center gap-3">
            {formErr ? (
              <span className="hidden text-xs text-muted-foreground sm:inline">{formErr}</span>
            ) : null}
            <Button onClick={onSubmit} disabled={!!formErr || setConfig.isPending}>
              {setConfig.isPending ? "Salvando…" : "Salvar e validar"}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}

function ColumnField({
  label,
  value,
  onChange,
  options,
  candidates,
  onPickCandidate,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
  candidates: { column: string; score: number; reasons: string[] }[];
  onPickCandidate: (v: string) => void;
}) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      <Select value={value || undefined} onValueChange={onChange}>
        <SelectTrigger>
          <SelectValue placeholder="Selecione a coluna" />
        </SelectTrigger>
        <SelectContent>
          {options.map((c) => (
            <SelectItem key={c} value={c}>
              {c}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {candidates.length > 0 ? (
        <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
          <span className="text-xs text-muted-foreground">Candidatas:</span>
          {candidates.slice(0, 4).map((c) => (
            <Tooltip key={c.column}>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={() => onPickCandidate(c.column)}
                  className={cn(
                    "rounded-full border px-2 py-0.5 text-xs tabular-nums transition-colors hover:bg-accent",
                    c.column === value
                      ? "border-primary/50 bg-primary/10 text-primary"
                      : "border-border text-muted-foreground",
                  )}
                >
                  {c.column} · {Math.round((c.score || 0) * 100)}%
                </button>
              </TooltipTrigger>
              <TooltipContent>
                {c.reasons.length ? c.reasons.join(" · ") : "Sem detalhes adicionais."}
              </TooltipContent>
            </Tooltip>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function ChipMultiSelect({
  label,
  hint,
  options,
  selected,
  onToggle,
  empty,
}: {
  label: string;
  hint: string;
  options: string[];
  selected: string[];
  onToggle: (name: string) => void;
  empty: string;
}) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {options.length === 0 ? (
        <p className="text-xs text-muted-foreground">{empty}</p>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {options.map((v) => {
            const on = selected.includes(v);
            return (
              <button
                key={v}
                type="button"
                onClick={() => onToggle(v)}
                className={cn(
                  "rounded-full border px-2.5 py-1 text-xs transition-colors",
                  on
                    ? "border-primary/50 bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:bg-accent",
                )}
              >
                {v}
              </button>
            );
          })}
        </div>
      )}
      <p className="text-xs text-muted-foreground">{hint}</p>
    </div>
  );
}

function FieldError({ children }: { children: React.ReactNode }) {
  return <p className="text-xs text-destructive">{children}</p>;
}

function FormSkeleton() {
  return (
    <div className="grid gap-6 lg:grid-cols-2" aria-busy>
      {[0, 1].map((i) => (
        <div key={i} className="space-y-4 rounded-lg border p-5">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-2/3" />
          <Skeleton className="h-24 w-full" />
        </div>
      ))}
    </div>
  );
}

function MissingDatasetNotice({ projectId }: { projectId: string }) {
  return (
    <Card>
      <CardContent className="flex flex-col items-start gap-3 p-6">
        <div className="flex items-center gap-2 font-semibold">
          <UploadCloud className="h-5 w-5 text-muted-foreground" />
          Nenhuma planilha para configurar
        </div>
        <p className="text-sm text-muted-foreground">
          Não encontramos a base enviada nesta sessão. Reenvie o arquivo para continuar a
          configuração das colunas.
        </p>
        <Button asChild variant="outline" size="sm">
          <Link href={`/projects/${projectId}/upload`}>
            <ArrowLeft className="h-4 w-4" />
            Ir para o envio da planilha
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}

function ErrorNotice({ message, projectId }: { message: string; projectId: string }) {
  return (
    <Card>
      <CardContent className="flex flex-col items-start gap-3 p-6">
        <div className="font-semibold text-destructive">Não foi possível preparar a configuração</div>
        <p className="text-sm text-muted-foreground">{message}</p>
        <Button asChild variant="outline" size="sm">
          <Link href={`/projects/${projectId}/upload`}>
            <ArrowLeft className="h-4 w-4" />
            Reenviar planilha
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
