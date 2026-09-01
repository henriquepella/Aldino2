"use client";

import { ArrowRight, FileSpreadsheet, RefreshCw, Table2, UploadCloud } from "lucide-react";
import { useRouter } from "next/navigation";
import { use, useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { fmtBytes, fmtInt } from "@/lib/format";
import { useDataset, useProject, useRuns, useUploadDataset } from "@/lib/hooks";
import type { DatasetOut } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

const ACCEPT = ".xlsx,.xls,.csv";
const EXT_RE = /\.(xlsx|xls|csv)$/i;

function dsKey(projectId: string) {
  return `ds:${projectId}`;
}

function storeDatasetId(projectId: string, datasetId: string) {
  try {
    sessionStorage.setItem(dsKey(projectId), datasetId);
    sessionStorage.setItem(`dataset:${projectId}`, datasetId); // chave usada pela página de execução
  } catch {
    /* sessionStorage indisponível — segue sem cache */
  }
}

function readDatasetId(projectId: string): string | undefined {
  try {
    return sessionStorage.getItem(dsKey(projectId)) ?? undefined;
  } catch {
    return undefined;
  }
}

export default function UploadPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();

  const projectQ = useProject(id);
  const runsQ = useRuns(id);

  const [cachedDsId, setCachedDsId] = useState<string | undefined>(undefined);
  useEffect(() => {
    setCachedDsId(readDatasetId(id));
  }, [id]);

  const activeDsId = cachedDsId ?? runsQ.data?.[0]?.dataset_id;
  const datasetQ = useDataset(activeDsId);
  const dataset = datasetQ.data;

  const upload = useUploadDataset(id);
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [pct, setPct] = useState(0);

  useEffect(() => {
    if (!upload.isPending) return;
    setPct(10);
    const t = setInterval(() => {
      setPct((p) => (p >= 92 ? p : Math.min(92, p + Math.random() * 11)));
    }, 420);
    return () => clearInterval(t);
  }, [upload.isPending]);

  const handleFile = useCallback(
    (file: File | undefined | null) => {
      if (!file) return;
      if (!EXT_RE.test(file.name)) {
        setLocalError("Formato não suportado. Envie um arquivo .xlsx, .xls ou .csv.");
        return;
      }
      setLocalError(null);
      upload.mutate(file, {
        onSuccess: (ds) => {
          setPct(100);
          storeDatasetId(id, ds.id);
          setCachedDsId(ds.id);
        },
        onError: () => setPct(0),
      });
    },
    [id, upload],
  );

  const errorMsg =
    localError ??
    (upload.isError
      ? upload.error instanceof ApiError
        ? upload.error.message
        : "Não foi possível enviar a planilha. Verifique o arquivo e tente novamente."
      : null);

  const busy = upload.isPending;

  if (projectQ.isLoading) {
    return (
      <div className="space-y-6" aria-busy>
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (projectQ.isError) {
    return (
      <p className="text-sm text-destructive">
        Não foi possível carregar este projeto. Recarregue a página e tente novamente.
      </p>
    );
  }

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Assistente · Passo 1 de 4
        </p>
        <h1 className="text-2xl font-bold tracking-tight">Enviar planilha</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Envie a planilha com as amostras georreferenciadas. Detectamos automaticamente as colunas
          de coordenadas, o sistema de referência e as variáveis numéricas — você confirma tudo no
          próximo passo.
        </p>
      </header>

      {dataset ? (
        <ExistingDatasetCard
          dataset={dataset}
          onContinue={() => router.push(`/projects/${id}/configure`)}
        />
      ) : null}

      {/* Área de envio */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-foreground">
          {dataset ? "Substituir planilha" : "Arquivo da base"}
        </h2>

        <div
          role="button"
          tabIndex={0}
          aria-disabled={busy}
          onClick={() => !busy && inputRef.current?.click()}
          onKeyDown={(e) => {
            if ((e.key === "Enter" || e.key === " ") && !busy) {
              e.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={(e) => {
            e.preventDefault();
            if (!busy) setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            if (busy) return;
            handleFile(e.dataTransfer.files?.[0]);
          }}
          className={cn(
            "flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-14 text-center transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            busy
              ? "cursor-progress border-border bg-muted/40"
              : "cursor-pointer hover:border-primary/50 hover:bg-accent/40",
            dragActive && "border-primary bg-primary/5",
          )}
        >
          <span
            className={cn(
              "grid h-12 w-12 place-items-center rounded-full bg-primary/10 text-primary",
              dragActive && "bg-primary/20",
            )}
          >
            <UploadCloud className="h-6 w-6" />
          </span>
          <p className="mt-4 text-sm font-medium text-foreground">
            Arraste seu arquivo Excel ou CSV aqui
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            ou clique para procurar no computador · .xlsx, .xls ou .csv
          </p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="mt-5"
            disabled={busy}
            onClick={(e) => {
              e.stopPropagation();
              inputRef.current?.click();
            }}
          >
            {dataset ? (
              <>
                <RefreshCw className="h-4 w-4" />
                Selecionar outro arquivo
              </>
            ) : (
              <>
                <FileSpreadsheet className="h-4 w-4" />
                Selecionar arquivo
              </>
            )}
          </Button>

          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            className="hidden"
            onChange={(e) => {
              handleFile(e.target.files?.[0]);
              e.target.value = "";
            }}
          />
        </div>

        {busy ? (
          <div className="space-y-1.5" aria-live="polite">
            <Progress value={pct} />
            <p className="text-xs text-muted-foreground">
              Enviando e analisando a planilha… {Math.round(pct)}%
            </p>
          </div>
        ) : null}

        {errorMsg ? (
          <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {errorMsg}
          </div>
        ) : null}

        <div className="pt-1">
          <a
            href={api.templateUrl()}
            className="inline-flex items-center gap-1.5 text-sm text-primary underline-offset-4 hover:underline"
          >
            <FileSpreadsheet className="h-4 w-4" />
            Baixar modelo Excel
          </a>
        </div>
      </section>

      <RequiredDataCard />
    </div>
  );
}

function ExistingDatasetCard({
  dataset,
  onContinue,
}: {
  dataset: DatasetOut;
  onContinue: () => void;
}) {
  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
        <div className="min-w-0">
          <CardTitle className="flex items-center gap-2 text-base">
            <Table2 className="h-4 w-4 shrink-0 text-muted-foreground" />
            <span className="truncate">{dataset.original_filename}</span>
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            Versão {fmtInt(dataset.version)} · {fmtBytes(dataset.file_size)}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap justify-end gap-1.5">
          <Badge variant={dataset.is_active ? "success" : "secondary"}>
            {dataset.is_active ? "Base ativa" : "Inativa"}
          </Badge>
          {dataset.config ? <Badge variant="outline">Colunas confirmadas</Badge> : null}
          {dataset.validation ? <Badge variant="outline">Base diagnosticada</Badge> : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
          <div>
            <dt className="text-xs text-muted-foreground">Linhas</dt>
            <dd className="text-lg font-semibold tabular-nums">{fmtInt(dataset.row_count)}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Colunas</dt>
            <dd className="text-lg font-semibold tabular-nums">{fmtInt(dataset.col_count)}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Tamanho</dt>
            <dd className="text-lg font-semibold tabular-nums">{fmtBytes(dataset.file_size)}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Variáveis numéricas</dt>
            <dd className="text-lg font-semibold tabular-nums">
              {fmtInt(dataset.detection?.numeric_variables.length ?? 0)}
            </dd>
          </div>
        </dl>
        <Separator />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-muted-foreground">
            Planilha recebida. Avance para confirmar o mapeamento das colunas.
          </p>
          <Button onClick={onContinue}>
            Avançar: confirmar colunas
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function RequiredDataCard() {
  return (
    <Card className="bg-card/60">
      <CardHeader>
        <CardTitle className="text-base">Dados necessários</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <Item title="Coordenadas X e Y (obrigatório)">
          Duas colunas numéricas com a posição de cada amostra — longitude/latitude (graus) ou
          Este/Norte (metros, UTM). Uma linha por ponto amostrado.
        </Item>
        <Item title="Variáveis numéricas (obrigatório)">
          Ao menos uma coluna com o atributo a ser interpolado (teor, concentração, pH, produtividade
          etc.). Colunas adicionais podem entrar como variáveis secundárias.
        </Item>
        <Item title="Coluna auxiliar (opcional)">
          Uma variável de apoio para krigagem com deriva externa ou co-krigagem (ex.: altitude,
          índice de vegetação, condutividade elétrica).
        </Item>
        <Item title="Identificador (opcional)">
          Um código único por amostra (ponto, furo, talhão) para rastrear as linhas nos relatórios.
        </Item>
        <p className="flex items-center gap-1.5 pt-1 text-xs text-muted-foreground">
          <FileSpreadsheet className="h-3.5 w-3.5" />
          Sem uma planilha pronta? Baixe o modelo Excel acima e preencha com as suas amostras.
        </p>
      </CardContent>
    </Card>
  );
}

function Item({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-l-2 border-border pl-3">
      <p className="font-medium text-foreground">{title}</p>
      <p className="mt-0.5 text-muted-foreground">{children}</p>
    </div>
  );
}
