// Navegação do "shell" do projeto: assistente (wizard) + seções de análise.
// Ordem EXATA conforme o spec da plataforma.

import {
  Activity,
  BarChart3,
  Boxes,
  Database,
  Download,
  FileText,
  FlaskConical,
  GitCompare,
  Globe,
  Grid3x3,
  Layers,
  LayoutDashboard,
  Map,
  Mountain,
  ScatterChart,
  Settings,
  Sigma,
  type LucideIcon,
} from "lucide-react";

export interface WizardStep {
  /** segmento de rota sob /projects/[id]/ */
  slug: string;
  label: string;
}

/** Bloco "Assistente" — passos guiados da planilha até a execução. */
export const WIZARD_STEPS: WizardStep[] = [
  { slug: "upload", label: "Enviar planilha" },
  { slug: "configure", label: "Confirmar colunas" },
  { slug: "diagnostics", label: "Diagnóstico da base" },
  { slug: "run", label: "Executar análise" },
];

export interface Section {
  /** segmento de rota sob /projects/[id]/ */
  slug: string;
  label: string;
  icon: LucideIcon;
}

/** Menu lateral "Análise" — na ordem exata do spec. */
export const SECTIONS: Section[] = [
  { slug: "dashboard", label: "Painel", icon: LayoutDashboard },
  { slug: "data", label: "Dados", icon: Database },
  { slug: "descriptive", label: "Estatística Descritiva", icon: Sigma },
  { slug: "esda", label: "ESDA Univariada", icon: Activity },
  { slug: "tests", label: "Testes Estatísticos", icon: FlaskConical },
  { slug: "moran", label: "Moran Scatter", icon: ScatterChart },
  { slug: "bivariate", label: "ESDA Bivariada", icon: GitCompare },
  { slug: "idw", label: "IDW", icon: Grid3x3 },
  { slug: "kriging", label: "Krigagem", icon: Layers },
  { slug: "external-drift", label: "Deriva Externa", icon: Mountain },
  { slug: "gwr", label: "GWR / GWM", icon: Globe },
  { slug: "cokriging", label: "Co-Krigagem", icon: Boxes },
  { slug: "comparison", label: "Comparação", icon: BarChart3 },
  { slug: "maps", label: "Mapas", icon: Map },
  { slug: "report", label: "Relatório PDF", icon: FileText },
  { slug: "exports", label: "Exportações", icon: Download },
  { slug: "settings", label: "Configurações", icon: Settings },
];

/** Href de uma seção de análise. */
export function sectionHref(projectId: string, slug: string): string {
  return `/projects/${projectId}/${slug}`;
}

/** Href de um passo do assistente. */
export function wizardHref(projectId: string, slug: string): string {
  return `/projects/${projectId}/${slug}`;
}
