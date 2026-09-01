"use client";

import { Rocket, Save } from "lucide-react";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api";
import { useProject, useUpdateProject } from "@/lib/hooks";

const VARIOGRAM_MODELS = [
  { v: "spherical", l: "Esférico" },
  { v: "exponential", l: "Exponencial" },
  { v: "gaussian", l: "Gaussiano" },
  { v: "linear", l: "Linear" },
  { v: "power", l: "Potência" },
];

const toNum = (v: string, d: number) => {
  const n = Number.parseFloat(String(v).replace(",", "."));
  return Number.isFinite(n) ? n : d;
};
const toInt = (v: string, d: number) => {
  const n = Number.parseInt(String(v), 10);
  return Number.isFinite(n) ? n : d;
};
const asStr = (v: unknown, d: string) =>
  v === undefined || v === null || v === "" ? d : String(v);

export default function SettingsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return <Settings projectId={id} />;
}

type Fields = {
  name: string;
  client: string;
  technical_lead: string;
  analysis_date: string;
  description: string;
  variable_units: string;
  crs: string;
  crs_label: string;
};

type Advanced = {
  n_permutations: string;
  alpha: string;
  knn_neighbors: string;
  idw_power: string;
  idw_neighbors: string;
  variogram_bins: string;
  grid_resolution: string;
  selection_metric: string;
  bandwidth_method: string;
  basemap: string;
};

function NumField({
  id,
  label,
  hint,
  value,
  step,
  onChange,
}: {
  id: string;
  label: string;
  hint?: string;
  value: string;
  step?: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        type="number"
        inputMode="decimal"
        step={step}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

function Settings({ projectId }: { projectId: string }) {
  const router = useRouter();
  const { data: project, isLoading, isError, error } = useProject(projectId);
  const update = useUpdateProject(projectId);

  const [f, setF] = useState<Fields>({
    name: "",
    client: "",
    technical_lead: "",
    analysis_date: "",
    description: "",
    variable_units: "",
    crs: "",
    crs_label: "",
  });
  const [adv, setAdv] = useState<Advanced>({
    n_permutations: "999",
    alpha: "0.05",
    knn_neighbors: "8",
    idw_power: "2",
    idw_neighbors: "12",
    variogram_bins: "15",
    grid_resolution: "80",
    selection_metric: "rmse",
    bandwidth_method: "fixed",
    basemap: "satellite",
  });
  const [models, setModels] = useState<string[]>([
    "spherical",
    "exponential",
    "gaussian",
  ]);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    if (!project || hydrated) return;
    setF({
      name: project.name ?? "",
      client: project.client ?? "",
      technical_lead: project.technical_lead ?? "",
      analysis_date: (project.analysis_date ?? "").slice(0, 10),
      description: project.description ?? "",
      variable_units: project.variable_units ?? "",
      crs: project.crs ?? "",
      crs_label: project.crs_label ?? "",
    });
    const s = project.settings ?? {};
    setAdv((a) => ({
      n_permutations: asStr(s.n_permutations, a.n_permutations),
      alpha: asStr(s.alpha, a.alpha),
      knn_neighbors: asStr(s.knn_neighbors, a.knn_neighbors),
      idw_power: asStr(s.idw_power, a.idw_power),
      idw_neighbors: asStr(s.idw_neighbors, a.idw_neighbors),
      variogram_bins: asStr(s.variogram_bins, a.variogram_bins),
      grid_resolution: asStr(s.grid_resolution, a.grid_resolution),
      selection_metric: asStr(s.selection_metric, a.selection_metric),
      bandwidth_method: asStr(s.bandwidth_method, a.bandwidth_method),
      basemap: asStr(s.basemap, a.basemap),
    }));
    if (Array.isArray(s.variogram_models) && s.variogram_models.length > 0) {
      setModels((s.variogram_models as unknown[]).map(String));
    }
    setHydrated(true);
  }, [project, hydrated]);

  async function save(): Promise<boolean> {
    if (!project) return false;
    if (!f.name.trim()) {
      toast.error("Informe o nome do projeto.");
      return false;
    }
    const chosen = models.length > 0 ? models : ["spherical"];
    const settings: Record<string, unknown> = {
      ...(project.settings ?? {}),
      n_permutations: toInt(adv.n_permutations, 999),
      alpha: toNum(adv.alpha, 0.05),
      knn_neighbors: toInt(adv.knn_neighbors, 8),
      idw_power: toNum(adv.idw_power, 2),
      idw_neighbors: toInt(adv.idw_neighbors, 12),
      variogram_bins: toInt(adv.variogram_bins, 15),
      variogram_models: chosen,
      grid_resolution: toInt(adv.grid_resolution, 80),
      selection_metric: adv.selection_metric,
      bandwidth_method: adv.bandwidth_method,
      basemap: adv.basemap,
    };
    try {
      await update.mutateAsync({
        name: f.name.trim(),
        client: f.client.trim(),
        technical_lead: f.technical_lead.trim(),
        analysis_date: f.analysis_date,
        description: f.description,
        variable_units: f.variable_units.trim(),
        crs: f.crs.trim(),
        crs_label: f.crs_label.trim(),
        settings,
      });
      return true;
    } catch (e) {
      toast.error(
        e instanceof ApiError
          ? e.message
          : "Não foi possível salvar as configurações.",
      );
      return false;
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-72 w-full rounded-lg" />
        <Skeleton className="h-40 w-full rounded-lg" />
      </div>
    );
  }

  if (isError || !project) {
    return (
      <p className="rounded-md bg-destructive/15 px-3 py-2 text-sm text-destructive">
        {error instanceof ApiError
          ? error.message
          : "Não foi possível carregar o projeto."}
      </p>
    );
  }

  const set = (patch: Partial<Fields>) => setF((prev) => ({ ...prev, ...patch }));
  const setAdvanced = (patch: Partial<Advanced>) =>
    setAdv((prev) => ({ ...prev, ...patch }));

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-xl font-semibold tracking-tight">Configurações</h1>
        <p className="text-sm text-muted-foreground">
          Identificação do estudo e parâmetros da análise geoestatística.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Identificação do projeto</CardTitle>
          <CardDescription>
            Estes dados aparecem no relatório técnico e nas exportações.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="name">Nome do projeto</Label>
            <Input
              id="name"
              value={f.name}
              onChange={(e) => set({ name: e.target.value })}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="client">Cliente</Label>
            <Input
              id="client"
              value={f.client}
              onChange={(e) => set({ client: e.target.value })}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="lead">Responsável técnico</Label>
            <Input
              id="lead"
              value={f.technical_lead}
              onChange={(e) => set({ technical_lead: e.target.value })}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="date">Data da análise</Label>
            <Input
              id="date"
              type="date"
              value={f.analysis_date}
              onChange={(e) => set({ analysis_date: e.target.value })}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="units">Unidade das variáveis</Label>
            <Input
              id="units"
              value={f.variable_units}
              onChange={(e) => set({ variable_units: e.target.value })}
              placeholder="Ex.: mg/dm³"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="crs">CRS (EPSG)</Label>
            <Input
              id="crs"
              value={f.crs}
              onChange={(e) => set({ crs: e.target.value })}
              placeholder="Ex.: EPSG:31982"
            />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="crs_label">Rótulo do CRS</Label>
            <Input
              id="crs_label"
              value={f.crs_label}
              onChange={(e) => set({ crs_label: e.target.value })}
              placeholder="Ex.: SIRGAS 2000 / UTM zona 22S"
            />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="description">Descrição</Label>
            <textarea
              id="description"
              rows={4}
              value={f.description}
              onChange={(e) => set({ description: e.target.value })}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="Objetivo do estudo, área, método de amostragem…"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <Accordion type="single" collapsible defaultValue="adv">
            <AccordionItem value="adv" className="border-b-0">
              <AccordionTrigger className="px-5">
                Parâmetros avançados
              </AccordionTrigger>
              <AccordionContent className="px-5">
                <p className="mb-4 text-sm text-muted-foreground">
                  Valores padrão adequados à maioria dos estudos. Ajuste apenas se
                  necessário.
                </p>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <NumField
                    id="n_permutations"
                    label="Nº de permutações"
                    hint="Testes de Moran (padrão 999)"
                    step="1"
                    value={adv.n_permutations}
                    onChange={(v) => setAdvanced({ n_permutations: v })}
                  />
                  <NumField
                    id="alpha"
                    label="Nível de significância (α)"
                    hint="Padrão 0,05"
                    step="0.01"
                    value={adv.alpha}
                    onChange={(v) => setAdvanced({ alpha: v })}
                  />
                  <NumField
                    id="knn_neighbors"
                    label="Vizinhos KNN"
                    hint="Matriz de vizinhança (padrão 8)"
                    step="1"
                    value={adv.knn_neighbors}
                    onChange={(v) => setAdvanced({ knn_neighbors: v })}
                  />
                  <NumField
                    id="idw_power"
                    label="Potência do IDW"
                    hint="Expoente da distância (padrão 2)"
                    step="0.5"
                    value={adv.idw_power}
                    onChange={(v) => setAdvanced({ idw_power: v })}
                  />
                  <NumField
                    id="idw_neighbors"
                    label="Nº de vizinhos do IDW"
                    hint="Padrão 12"
                    step="1"
                    value={adv.idw_neighbors}
                    onChange={(v) => setAdvanced({ idw_neighbors: v })}
                  />
                  <NumField
                    id="variogram_bins"
                    label="Bins do variograma"
                    hint="Padrão 15"
                    step="1"
                    value={adv.variogram_bins}
                    onChange={(v) => setAdvanced({ variogram_bins: v })}
                  />
                  <NumField
                    id="grid_resolution"
                    label="Resolução da grade"
                    hint="Células por eixo (padrão 80)"
                    step="1"
                    value={adv.grid_resolution}
                    onChange={(v) => setAdvanced({ grid_resolution: v })}
                  />
                  <div className="space-y-1.5">
                    <Label htmlFor="selection_metric">Métrica de seleção</Label>
                    <Select
                      value={adv.selection_metric}
                      onValueChange={(v) => setAdvanced({ selection_metric: v })}
                    >
                      <SelectTrigger id="selection_metric">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="rmse">RMSE</SelectItem>
                        <SelectItem value="mae">MAE</SelectItem>
                        <SelectItem value="r2">R²</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      Critério para comparar os métodos
                    </p>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="bandwidth_method">Método de bandwidth</Label>
                    <Select
                      value={adv.bandwidth_method}
                      onValueChange={(v) => setAdvanced({ bandwidth_method: v })}
                    >
                      <SelectTrigger id="bandwidth_method">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="fixed">Fixo</SelectItem>
                        <SelectItem value="adaptive">Adaptativo</SelectItem>
                        <SelectItem value="both">Ambos</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">GWR / GWM</p>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="basemap">Mapa-base</Label>
                    <Select
                      value={adv.basemap}
                      onValueChange={(v) => setAdvanced({ basemap: v })}
                    >
                      <SelectTrigger id="basemap">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="satellite">Satélite (Esri)</SelectItem>
                        <SelectItem value="streets">Ruas (Esri)</SelectItem>
                        <SelectItem value="gray">Cinza claro (Esri)</SelectItem>
                        <SelectItem value="topo">Topográfico (Esri)</SelectItem>
                        <SelectItem value="terrain">Relevo (OpenTopoMap)</SelectItem>
                        <SelectItem value="none">Sem mapa-base</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      Fundo dos mapas (requer internet ao gerar)
                    </p>
                  </div>
                </div>

                <div className="mt-5 space-y-2">
                  <Label>Modelos de variograma</Label>
                  <div className="flex flex-wrap gap-2">
                    {VARIOGRAM_MODELS.map((m) => {
                      const on = models.includes(m.v);
                      return (
                        <label
                          key={m.v}
                          className="flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm has-[:checked]:border-primary has-[:checked]:bg-primary/5"
                        >
                          <Checkbox
                            checked={on}
                            onCheckedChange={(c) =>
                              setModels((prev) =>
                                c
                                  ? [...prev, m.v]
                                  : prev.filter((x) => x !== m.v),
                              )
                            }
                          />
                          {m.l}
                        </label>
                      );
                    })}
                  </div>
                  {models.length === 0 ? (
                    <p className="text-xs text-warning">
                      Selecione ao menos um modelo — o esférico será usado por
                      padrão.
                    </p>
                  ) : null}
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </CardContent>
      </Card>

      <div className="flex flex-wrap items-center justify-end gap-3 border-t pt-4">
        <Button
          variant="outline"
          disabled={update.isPending}
          onClick={async () => {
            if (await save()) toast.success("Configurações salvas.");
          }}
        >
          <Save className="h-4 w-4" />
          {update.isPending ? "Salvando…" : "Salvar alterações"}
        </Button>
        <Button
          disabled={update.isPending}
          onClick={async () => {
            if (await save()) router.push(`/projects/${projectId}/run`);
          }}
        >
          Ir para execução
          <Rocket className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
