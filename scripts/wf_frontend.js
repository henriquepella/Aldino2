export const meta = {
  name: 'frontend-pages',
  description: 'Constroi as paginas e componentes do frontend Next.js contra o contrato de API travado',
  phases: [
    { title: 'Base', detail: 'componentes compartilhados, auth, shell, lista de projetos' },
    { title: 'Paginas', detail: 'wizard, dashboard e paginas de secao de resultados' },
  ],
}

const ROOT = 'C:/Users/henri/aldino/frontend'

const SPEC = `
Projeto: frontend da Plataforma de Analise Geoestatistica. Next.js 15 (app router) + React 19 + TypeScript
+ Tailwind + Radix. Diretorio: ${ROOT}. Rode checagem: cd ${ROOT} && npx tsc --noEmit
(ignore erros em arquivos que NAO sao seus / ainda nao criados por outros agentes).

LEIA ANTES (Read):
  ${ROOT}/lib/types.ts       (todos os tipos que espelham o backend: ProjectOut, DatasetOut, DatasetConfig,
                              DetectionResult, ValidationResult, RunOut, RunResultsOut, StepResultOut, ArtifactOut, TablePayload, StepState)
  ${ROOT}/lib/api.ts         (cliente 'api.*', downloadFile, authedAssetUrl, API_BASE, ApiError)
  ${ROOT}/lib/hooks.ts       (react-query: useProjects, useProject, useCreateProject, useUpdateProject, useDeleteProject,
                              useDuplicateProject, useDataset, useUploadDataset, useSetDatasetConfig, useCleanDataset,
                              useRuns, useRun, useRunResults, useCreateRun, useCancelRun, useLibraryVersions)
  ${ROOT}/lib/auth.tsx       (useAuth -> { user, loading, login, register, loginDemo, logout })
  ${ROOT}/lib/format.ts      (fmtNum, fmtInt, fmtPct, fmtPValue, fmtDate, fmtDateTime, fmtBytes)
  ${ROOT}/lib/utils.ts       (cn, CHART_COLORS, SCATTER_COLORS)
  ${ROOT}/app/globals.css    (tokens de tema; cores de grafico --chart-1..6)
  ${ROOT}/components/ui/      (primitivos ja prontos: button, card, input, label, badge, progress, separator,
                              skeleton, tabs, select, dialog, dropdown-menu, accordion, table, tooltip, checkbox, scroll-area)
  ${ROOT}/components/theme-toggle.tsx

CONTRATO DA API (todos os endpoints ja existem em lib/api.ts). Fluxo do usuario:
  login/registro -> lista de projetos -> novo projeto -> upload de planilha -> confirmar colunas (deteccao pre-preenchida)
  -> diagnostico da base (excluir linhas problematicas) -> configuracoes do projeto + parametros avancados
  -> botao "EXECUTAR ANALISE COMPLETA" -> acompanhar progresso -> dashboard -> navegar secoes -> baixar PDF / ZIP.

CHAVES DE PASSO (StepResultOut.key) e titulos:
  descriptive="Estatistica Descritiva", esda_univariate="ESDA Univariada", moran_scatter="Moran Scatter Plot",
  esda_bivariate="ESDA Bivariada", idw="IDW", kriging="Krigagem Ordinaria", external_drift="Krigagem com Deriva Externa",
  gwr="GWR / GWM", cokriging="Co-Krigagem", method_comparison="Comparacao Geral dos Metodos".
RunOut.metrics_summary tem: n_points, n_variables, extent_width_m, extent_height_m, primary, units, mean, median, std, min, max,
  morans_i, morans_p, best_variogram_model, kriging_rmse, kriging_mae, kriging_r2, best_method, best_method_rmse,
  best_method_mae, best_method_r2, steps_ok[], steps_skipped[{key,title,reason}], steps_failed[].

MENU LATERAL (ordem exata) — rotas sob /projects/[id]/:
  dashboard, data(Dados), descriptive(Estatistica Descritiva), esda(ESDA Univariada), tests(Testes Estatisticos),
  moran(Moran Scatter), bivariate(ESDA Bivariada), idw(IDW), kriging(Krigagem), external-drift(Deriva Externa),
  gwr(GWR / GWM), cokriging(Co-Krigagem), comparison(Comparacao), maps(Mapas), report(Relatorio PDF),
  exports(Exportacoes), settings(Configuracoes).
  Acima do menu, um bloco "Assistente" com: upload, configure, diagnostics, run.

DESIGN: aparencia de software cientifico profissional (NAO CRUD generico). Sidebar fixa a esquerda (colapsavel no mobile),
  topbar com nome do projeto + ThemeToggle + menu do usuario. Cards, tabelas paginadas, badges de status, tooltips.
  Modo claro/escuro (classes tailwind ja configuradas). Use os tokens (bg-background, text-foreground, bg-card, border,
  text-muted-foreground, bg-primary, text-primary, bg-success/15 text-success, bg-warning/15 text-warning, bg-destructive/15).
  Animacoes discretas. Tudo em PT-BR. Componentes de pagina que usam hooks/estado -> "use client".

GRAFICOS (Recharts, skill dataviz): use CHART_COLORS na ordem fixa (nunca cicle); para dispersao/ scatter use no maximo
  as 3 primeiras (SCATTER_COLORS); sequencial = 1 matiz; divergente = 2 matizes + cinza; legenda sempre p/ >=2 series;
  eixos discretos; tabular-nums nos numeros; tooltip sempre. Muitos "graficos" ja vem prontos como PNG/SVG do backend
  (ArtifactOut kind 'figure'/'map') — basta exibir via <img src={authedAssetUrl(fig.url)}>. Recharts so para dados
  que chegam como tabela (ex.: dispersao de Moran a partir de metrics, cards do dashboard).

REGRAS: nao invente endpoints; trate loading (Skeleton) e erro (mensagem PT-BR) em toda query; estados vazios com CTA claro;
  toda pagina de resultado deve funcionar quando o passo veio "skipped"/"failed" (mostrar o motivo, sem quebrar).
  Nao edite arquivos de outro agente. Nao edite lib/*.ts(x) nem components/ui/* (se faltar helper, crie em components/ do seu escopo).
`

const SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['area', 'files_written', 'tsc_clean', 'summary'],
  properties: {
    area: { type: 'string' },
    files_written: { type: 'array', items: { type: 'string' } },
    tsc_clean: { type: 'boolean' },
    notes: { type: 'string' },
    summary: { type: 'string' },
  },
}

// ----------------------------------------------------------------------------
phase('Base')

const base = await parallel([
  () => agent(
    `AREA: componentes compartilhados de RESULTADO.\n\n${SPEC}\n\n` +
    `Crie em ${ROOT}/components/results/ :\n` +
    `- section-page.tsx  -> <SectionPage stepKey title runId description?/> : usa useRunResults(runId), acha o step por key,\n` +
    `  renderiza: StepStatusBadge; se skipped/failed mostra Card com o motivo (reason) e retorna; senao InterpretationCallout(step.interpretation)\n` +
    `  + para cada table em step.tables => <DataTableView table/> + para step.figures => <FigureGrid figures runId/>. Trata loading (Skeleton) e run inexistente/nao concluido (aviso + link p/ /projects/[id]/run).\n` +
    `- data-table-view.tsx -> <DataTableView table: ArtifactOut/> : renderiza table.data.payload (columns/rows/highlight_rows) com <Table> ;\n` +
    `  destaca linhas em highlight_rows (bg-success/10 fonte-semibold); paginacao client-side se > 25 linhas; titulo (table.title) e legenda (table.caption); botao "CSV" que baixa via downloadFile(table.url, nome).\n` +
    `- figure-grid.tsx + figure-viewer.tsx -> grid responsivo (2 col desktop) de <img src={authedAssetUrl(fig.url)} loading="lazy">, moldura Card, caption; clique abre <Dialog> com a imagem grande e botoes de download das variantes em fig.data.variants (png/svg/pdf/tif) e do proprio fig.url.\n` +
    `- interpretation-callout.tsx -> bloco destacado (borda-l-4 border-primary bg-accent/40) com icone e o texto; nada se vazio.\n` +
    `- metric-card.tsx -> <MetricCard label value hint? accent?/> Card compacto com valor grande (tabular-nums).\n` +
    `- step-status-badge.tsx -> <StepStatusBadge status/> Badge: ok=success "Concluida", skipped=warning "Nao aplicavel", failed=destructive "Falhou", running=default, pending=secondary.\n` +
    `- run-progress.tsx -> <RunProgress run: RunOut/> : Progress(run.progress) + % + passo atual + lista (STEP order) com icone por status (CheckCircle2/Loader2 animate-spin/MinusCircle/XCircle/Circle) a partir de run.steps; e um <pre> com as ultimas ~12 linhas de run.log.\n` +
    `- empty-state.tsx -> <EmptyState icon title description action?/>.\n` +
    `Exporte tudo por named export. tsc --noEmit deve passar nesses arquivos.`,
    { label: 'fe:results-components', phase: 'Base', effort: 'high', schema: SCHEMA },
  ),
  () => agent(
    `AREA: autenticacao + shell do app.\n\n${SPEC}\n\n` +
    `Crie:\n` +
    `- ${ROOT}/app/(auth)/layout.tsx : centralizado, card, logo textual "Analise Geoestatistica", ThemeToggle no canto.\n` +
    `- ${ROOT}/app/(auth)/login/page.tsx : form email/senha (useAuth().login), link p/ registro, botao "Entrar com conta demo" (useAuth().loginDemo) em destaque; ao logar -> router.push('/projects'). Erros via toast (sonner) e mensagem inline.\n` +
    `- ${ROOT}/app/(auth)/register/page.tsx : nome/email/senha (min 8), useAuth().register -> /projects.\n` +
    `- ${ROOT}/components/require-auth.tsx : <RequireAuth> client wrapper: useAuth(); se loading -> tela de carregando; se !user -> router.replace('/login') + null; senao children.\n` +
    `- ${ROOT}/components/app-shell.tsx : <AppShell right?> topbar reutilizavel (altura h-14, borda-b) com slot esquerdo (titulo/breadcrumb via children) + ThemeToggle + <UserMenu> (DropdownMenu com email e "Sair" -> logout).\n` +
    `- ${ROOT}/components/user-menu.tsx.\n` +
    `tsc --noEmit deve passar nesses arquivos.`,
    { label: 'fe:auth-shell', phase: 'Base', effort: 'medium', schema: SCHEMA },
  ),
  () => agent(
    `AREA: landing + lista de projetos.\n\n${SPEC}\n\n` +
    `Crie:\n` +
    `- ${ROOT}/app/page.tsx : redireciona ('/projects') via redirect() do next/navigation (server) OU client. Simples.\n` +
    `- ${ROOT}/app/projects/page.tsx : "use client" + <RequireAuth>. Cabecalho grande "Analise Geoestatistica" com subtitulo do spec (secao 45). <AppShell>. Botao destacado "+ Novo Projeto" abre <Dialog> (nome, cliente, responsavel tecnico) -> useCreateProject -> router.push('/projects/'+id+'/upload'). Grid de cards (useProjects): nome, cliente, nº datasets, nº execucoes, data (fmtDate), status da ultima execucao (badge). Card clicavel -> /projects/[id]. DropdownMenu no card: Abrir, Duplicar (useDuplicateProject), Excluir (useDeleteProject com confirmacao). Skeleton no loading; EmptyState se vazio ("Crie seu primeiro projeto"). Link "Baixar modelo Excel" -> api.templateUrl().\n` +
    `tsc --noEmit deve passar.`,
    { label: 'fe:projects-list', phase: 'Base', effort: 'medium', schema: SCHEMA },
  ),
  () => agent(
    `AREA: shell do projeto (layout + sidebar + navegacao do assistente).\n\n${SPEC}\n\n` +
    `Crie:\n` +
    `- ${ROOT}/lib/nav.ts : arrays exportados WIZARD_STEPS (upload/configure/diagnostics/run com label+slug) e SECTIONS (dashboard..settings com slug+label+ícone lucide) na ORDEM do spec. Helper sectionHref(projectId, slug).\n` +
    `- ${ROOT}/app/projects/[id]/layout.tsx : "use client" + <RequireAuth>. useProject(id). Grid: <aside> fixa (w-64, borda-r, scroll) com: header (nome do projeto -> link /projects), bloco "Assistente" (WIZARD_STEPS como lista numerada com estado: feito/atual/pendente derivado de useDataset+useRuns — ex.: upload feito se project.dataset_count>0), separador, "Analise" (SECTIONS como NavLink ativo por usePathname). Mobile: sidebar em <Dialog>/drawer com botao no topbar. <main> com <AppShell> (titulo = nome do projeto) + {children} num container p-6 max-w-6xl.\n` +
    `- ${ROOT}/app/projects/[id]/page.tsx : redireciona: se dataset_count===0 -> upload; senao se run_count>0 -> dashboard; senao -> configure. (client, usa useProject).\n` +
    `- ${ROOT}/components/nav-link.tsx : <NavLink href exact?> com aria-current e classe ativa (bg-accent text-accent-foreground).\n` +
    `tsc --noEmit deve passar.`,
    { label: 'fe:project-shell', phase: 'Base', effort: 'high', schema: SCHEMA },
  ),
])

log('Base: ' + base.filter(Boolean).map((r) => `${r.area}=${r.tsc_clean ? 'ok' : 'tsc?'}`).join('  '))

// ----------------------------------------------------------------------------
phase('Paginas')

const pages = await parallel([
  () => agent(
    `AREA: assistente — paginas de UPLOAD e CONFIGURAR COLUNAS.\n\n${SPEC}\n\n` +
    `- ${ROOT}/app/projects/[id]/upload/page.tsx : "use client". Area grande de drag-and-drop ("Arraste seu arquivo Excel ou CSV aqui") + botao "Selecionar arquivo" (accept .xlsx,.xls,.csv) + "Baixar modelo Excel" (api.templateUrl()) + card "Dados necessarios" (coordenadas X/Y + variaveis numericas + opcional auxiliar). useUploadDataset(id). Ao concluir: mostra nome/tamanho (fmtBytes)/linhas/colunas/status e botao "Avancar: confirmar colunas" -> /configure. Mostra dataset existente se ja houver (useProject.latest dataset via useRuns? use api). Barra de progresso durante upload. Erros (ApiError) em PT-BR.\n` +
    `- ${ROOT}/app/projects/[id]/configure/page.tsx : "use client". Carrega o dataset ativo (adicione em lib/api? NAO — use: busca projeto, pega ultimo dataset; se precisar de id do dataset, o backend nao lista datasets — entao guarde o dataset id no sessionStorage no upload OU adicione endpoint? NAO adicione endpoint. Solucao: no upload salve last dataset id em sessionStorage 'ds:'+projectId; configure le dela; se ausente, mostre aviso "reenvie o arquivo").\n` +
    `  Form de mapeamento usando dataset.detection: selects para Coordenada X, Coordenada Y (opcoes = todas colunas; default = detection.coord_x/y; badge de confianca detection.coord_confidence e candidatos com motivos em tooltip), CRS (input EPSG + select com detection.crs_alternatives; default detection.crs_suggested; badge/aviso detection.crs_reason quando confidence<0.5), coluna ID (opcional).\n` +
    `  Variaveis: lista de checkboxes (detection.numeric_variables) para escolher quais analisar; radio/select "variavel principal"; multiselect "secundarias", "explicativas (GWR)", "auxiliar (deriva/co-krigagem)". Pre-preenche com os *_guess. Checkbox "valores negativos sao validos".\n` +
    `  Botao "Salvar e validar" -> useSetDatasetConfig -> vai p/ /diagnostics.\n` +
    `tsc --noEmit deve passar.`,
    { label: 'fe:wizard-upload-config', phase: 'Paginas', effort: 'high', schema: SCHEMA },
  ),
  () => agent(
    `AREA: assistente — DIAGNOSTICO e CONFIGURACOES.\n\n${SPEC}\n\n` +
    `Reutilize o padrao do sessionStorage 'ds:'+projectId para achar o dataset id (definido na pagina de upload).\n` +
    `- ${ROOT}/app/projects/[id]/diagnostics/page.tsx : "use client". useDataset(dsId). Tabela "Diagnostico da Base" (validation.summary: Item | Resultado | Status[badge ok/warn/error]). Cards com counts (registros, coordenadas validas, ausentes, duplicidades, coincidentes, outliers, negativos). Tabela paginada de linhas problematicas (validation.row_flags: indice + issues como badges + severidade); checkbox por linha; acoes "Excluir selecionadas", "Remover duplicatas", "Remover coordenadas invalidas" -> useCleanDataset. Aviso se !validation.can_proceed. Botao "Avancar" -> /settings (habilitado so se can_proceed).\n` +
    `- ${ROOT}/app/projects/[id]/settings/page.tsx : "use client". useProject + useUpdateProject. Form (secao 6): nome, cliente, responsavel tecnico, data, descricao, unidade das variaveis, CRS/rotulo. Accordion "Parametros avancados" (secao 36): nº permutacoes (default 999), alpha (0.05), vizinhos KNN (8), potencia IDW (2), nº vizinhos IDW (12), bins do variograma (15), modelos de variograma (multiselect: spherical/exponential/gaussian/linear/power), resolucao da grade (80), metrica de selecao (rmse/mae/r2), metodo de bandwidth (fixed/adaptive/both). Salva em project.settings. Botao "Ir para execucao" -> /run.\n` +
    `tsc --noEmit deve passar.`,
    { label: 'fe:wizard-diag-settings', phase: 'Paginas', effort: 'high', schema: SCHEMA },
  ),
  () => agent(
    `AREA: pagina de EXECUCAO (o coracao do fluxo).\n\n${SPEC}\n\n` +
    `- ${ROOT}/app/projects/[id]/run/page.tsx : "use client". Usa dataset id do sessionStorage.\n` +
    `  Estado A (sem execucao ativa): botao GIGANTE e destacado "EXECUTAR ANALISE COMPLETA" (h-16, text-lg, gradiente/primary, icone Rocket). Texto explicando os 17 passos (secao 37 resumida). Lista de execucoes anteriores (useRuns) com status/data/link p/ dashboard. Ao clicar -> useCreateRun({dataset_id, mode:'full', advanced: project.settings?.advanced||{}}) -> seta runId ativo.\n` +
    `  Estado B (execucao rodando/concluida): <RunProgress run/> (useRun com polling). Botao "Cancelar" (useCancelRun) enquanto pending/running. Quando status==='done': confetti discreto/toast + botoes "Ver Dashboard" e "Baixar Relatorio PDF" (downloadFile(api.reportUrl(runId),'relatorio.pdf')) e "Baixar Pacote" (api.packageUrl). Quando 'failed': mostra run.error num Card destrutivo + botao "Tentar novamente". Quando 'cancelled': aviso + "Nova execucao".\n` +
    `  Guarde o runId ativo em sessionStorage 'run:'+projectId para o dashboard/secoes usarem por padrao.\n` +
    `tsc --noEmit deve passar.`,
    { label: 'fe:run-page', phase: 'Paginas', effort: 'high', schema: SCHEMA },
  ),
  () => agent(
    `AREA: DASHBOARD.\n\n${SPEC}\n\n` +
    `- ${ROOT}/app/projects/[id]/dashboard/page.tsx : "use client". Resolve runId: sessionStorage 'run:'+projectId senao a execucao mais recente 'done' de useRuns. Se nenhuma -> EmptyState com CTA "Executar analise" -> /run.\n` +
    `  useRun(runId) + useRunResults(runId). Cards (MetricCard) em grid: Nº de pontos, Nº de variaveis, Extensao espacial (width x height m), Media, Mediana, Desvio padrao, Minimo, Maximo (da principal), Moran's I (+ badge signif. por morans_p), Melhor modelo geoestatistico (best_variogram_model), RMSE, MAE, R² (best_method_*).\n` +
    `  Secao "Melhor metodo": nome + metricas. Secao "Andamento das analises": grid dos passos (steps_ok / steps_skipped[com motivo] / steps_failed) com StepStatusBadge. Barra de progresso se ainda rodando (RunProgress). Botoes topo: "Relatorio PDF", "Pacote ZIP", "Tabelas (xlsx)". Se run rodando, faz polling e vai preenchendo.\n` +
    `tsc --noEmit deve passar.`,
    { label: 'fe:dashboard', phase: 'Paginas', effort: 'medium', schema: SCHEMA },
  ),
  () => agent(
    `AREA: paginas de secao de resultados — GRUPO 1.\n\n${SPEC}\n\n` +
    `Cada pagina resolve runId (sessionStorage 'run:'+projectId senao ultima execucao done de useRuns; se nenhuma -> EmptyState -> /run) e renderiza <SectionPage stepKey title runId .../> de components/results/section-page.\n` +
    `Crie (todas "use client", sob ${ROOT}/app/projects/[id]/):\n` +
    `- data/page.tsx        -> Dados: mostra a config do dataset (colunas, papeis, CRS) + link download do dataset limpo? (use o pacote). Tabela de colunas (dataset.columns: nome, tipo, nº unicos, ausentes, min, max). Nao tem step; monte manualmente com useDataset.\n` +
    `- descriptive/page.tsx -> <SectionPage stepKey="descriptive" title="Estatistica Descritiva">\n` +
    `- esda/page.tsx        -> stepKey="esda_univariate" title="ESDA Univariada"\n` +
    `- tests/page.tsx       -> "Testes Estatisticos": pega os steps 'esda_univariate' e 'esda_bivariate', filtra as tables cujo name/titulo contem "test"/"Teste" e renderiza via <DataTableView>; + nota do alpha/permutacoes do manifest.\n` +
    `- moran/page.tsx       -> stepKey="moran_scatter" title="Moran Scatter Plot"\n` +
    `tsc --noEmit deve passar nesses arquivos.`,
    { label: 'fe:sections-1', phase: 'Paginas', effort: 'medium', schema: SCHEMA },
  ),
  () => agent(
    `AREA: paginas de secao de resultados — GRUPO 2.\n\n${SPEC}\n\n` +
    `Mesmo padrao do grupo 1 (resolve runId; usa <SectionPage> de components/results/section-page). Crie sob ${ROOT}/app/projects/[id]/ (todas "use client"):\n` +
    `- bivariate/page.tsx      -> stepKey="esda_bivariate" title="ESDA Bivariada"\n` +
    `- idw/page.tsx            -> stepKey="idw" title="IDW — Inverse Distance Weighting"\n` +
    `- kriging/page.tsx        -> stepKey="kriging" title="Krigagem Ordinaria"\n` +
    `- external-drift/page.tsx -> stepKey="external_drift" title="Krigagem com Deriva Externa"\n` +
    `- gwr/page.tsx            -> stepKey="gwr" title="GWR / GWM"\n` +
    `- cokriging/page.tsx      -> stepKey="cokriging" title="Co-Krigagem"\n` +
    `- comparison/page.tsx     -> stepKey="method_comparison" title="Comparacao Geral dos Metodos" — alem do SectionPage, um destaque do metodo vencedor (metrics.best_method) e ranking.\n` +
    `- maps/page.tsx           -> "Mapas": junta TODAS as figuras kind 'map' de TODOS os steps de useRunResults e mostra num <FigureGrid> unico, agrupadas por step (titulo do grupo). Botao "baixar todos" -> api.packageUrl.\n` +
    `- report/page.tsx         -> "Relatorio PDF": card com preview (iframe src={authedAssetUrl(api.reportUrl(runId))} class h-[80vh]) + botoes baixar PDF e Pacote. Se run nao concluida, aviso.\n` +
    `- exports/page.tsx        -> "Exportacoes": lista de downloads (Relatorio PDF, Pacote ZIP completo, Tabelas .xlsx, dataset) + explica a estrutura do zip (secao 35).\n` +
    `tsc --noEmit deve passar nesses arquivos.`,
    { label: 'fe:sections-2', phase: 'Paginas', effort: 'high', schema: SCHEMA },
  ),
])

log('Paginas: ' + pages.filter(Boolean).map((r) => `${r.area}=${r.tsc_clean ? 'ok' : 'tsc?'}`).join('  '))
return { base: base.filter(Boolean), pages: pages.filter(Boolean) }
