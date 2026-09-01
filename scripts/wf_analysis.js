export const meta = {
  name: 'analysis-modules',
  description: 'Implementa os 8 modulos cientificos de app/analysis contra a interface travada',
  phases: [
    { title: 'Modulos', detail: 'um agente por modulo de analise, escreve modulo + teste' },
  ],
}

const ROOT = 'C:/Users/henri/aldino'
const PY = ROOT + '/.venv/Scripts/python.exe'

const SPEC = `
Projeto: Plataforma de Analise Geoestatistica. Backend Python 3.12.
Use o interpretador: ${PY}
Diretorio backend: ${ROOT}/backend  (rode pytest a partir dele).

ANTES DE CODAR, LEIA (ferramenta Read) — sao a fonte da verdade:
  ${ROOT}/backend/app/analysis/base.py        interface TRAVADA (AnalysisContext, StepResult, TableResult, FigureResult)
  ${ROOT}/backend/app/analysis/weights.py     build_weights(ctx, kind=, k=, threshold=, mask=) -> (w, info); w = libpysal W row-standardized
  ${ROOT}/backend/app/analysis/interpret.py   funcoes de texto PT-BR determinístico — USE-AS, nao escreva frases proprias
  ${ROOT}/backend/app/maps/renderer.py        render_surface(ctx, Z, gx, gy, name=, title=, method=, cbar_label=, sample_values=, diverging=, caption=) ; render_points(ctx, values, name=, title=, method=, cbar_label=, categorical=, cat_labels=, diverging=, caption=)
  ${ROOT}/backend/tests/conftest.py           fixture 'ctx' (n=140; campo com autocorrelacao forte; primary='teor'; aux_drift='elevacao'; secondary=['elevacao','aleatoria']; explanatory=['elevacao'])
  ${ROOT}/backend/app/core/config.py          defaults dos parametros avancados

CONTRATO — o modulo backend/app/analysis/<ARQ>.py DEVE expor exatamente:
  KEY: str
  TITLE: str
  def applicable(ctx) -> tuple[bool, str]      # (False, "motivo PT-BR") quando nao faz sentido p/ o dataset
  def run(ctx) -> StepResult                   # trate casos previsiveis com StepResult.skipped(...), nao com excecao

StepResult(key=KEY, title=TITLE, status="ok"|"skipped"|"failed", reason=None|str,
           tables=[TableResult...], figures=[FigureResult...], metrics={json-serializavel},
           interpretation="..."|None, params_used={...})
  StepResult.skipped(KEY, TITLE, motivo)  -> atalho para status skipped
  TableResult(name, df: pandas.DataFrame, title="", caption="", highlight_rows=[i,...])
  Graficos matplotlib: fig, ax = plt.subplots(...); ...; fr = ctx.save_fig(fig, "nome_sem_ext", subdir="figures", title=, caption=, kind="chart")
  Mapas: use renderer.render_surface / render_points (salvam em subdir 'maps' com png+svg+pdf).

HELPERS ctx (ver base.py): ctx.n, ctx.df, ctx.primary, ctx.secondary, ctx.explanatory, ctx.aux_drift, ctx.id_col,
  ctx.mx / ctx.my  (METROS — use SEMPRE p/ distancia/variograma/IDW/krigagem/pesos),
  ctx.x / ctx.y (nativas, so rotulo), ctx.values(name) -> np.ndarray float,
  ctx.clean_xyz(name) -> (mx,my,z) so linhas finitas,
  ctx.make_grid(res=None) -> (gx, gy) 1D metros,
  ctx.param(k, default), ctx.alpha, ctx.n_perm, ctx.random_seed, ctx.units, ctx.project_name,
  ctx.analysis_variables -> [primary, *secondary, *explanatory, aux_drift] deduplicado e presente no df.
  Chaves de ctx.param: n_permutations, alpha, knn_k, weights_kind, idw_power, idw_neighbors, idw_power_grid,
  idw_neighbors_grid, variogram_bins, variogram_models, variogram_model_override, grid_resolution,
  bandwidth_kind, selection_metric, cmap, drift_min_corr, cok_min_corr, gwr_mc_iters, bivariate_pairs, bivariate_all_pairs.

LIBS JA INSTALADAS (nao instale nada): numpy, pandas, scipy, scikit-learn, statsmodels,
  libpysal (KNN, DistanceBand, lag_spatial), esda (Moran, Moran_Local, Moran_BV, Moran_Local_BV, Geary, G_Local),
  pykrige.ok.OrdinaryKriging, pykrige.uk.UniversalKriging, mgwr.gwr.GWR, mgwr.sel_bw.Sel_BW, matplotlib (Agg).

REGRAS CIENTIFICAS (seções 15,16,28,43):
  - CV = leave-one-out; use k-fold(10, seed=ctx.random_seed) se n>250.
  - Metricas: ME (vies), MAE, MSE, RMSE, R².
  - Selecao de modelo/parametro SEMPRE por ctx.param('selection_metric','rmse') na CV; nunca por ajuste visual.
  - Ordene tabelas de comparacao do melhor p/ pior; highlight_rows=[0]. Nao mascare modelo ruim.
  - Interpretacao usa numeros reais via app.analysis.interpret; se p >= alpha diga que NAO e significativo.
  - Determinismo: np.random.default_rng(ctx.random_seed).
  - Suprima warnings ruidosos (warnings.catch_warnings) mas nao esconda erros.

GRAFICOS (dataviz): sequencial = 1 matiz claro->escuro (viridis p/ superficie); divergente = 2 matizes + cinza no meio
  (RdBu_r p/ residuos/coeficientes/erros, vmin=-vmax); nunca arco-iris; legenda sempre p/ >=2 series;
  grade discreta ax.grid(alpha=.3); marcas finas; textos PT-BR.

TESTE — escreva backend/tests/test_<ARQ>.py (2-4 asserts com a fixture 'ctx'):
    from app.analysis import <ARQ>
    def test_runs(ctx):
        r = <ARQ>.run(ctx)
        assert r.status in ("ok", "skipped")
        ...
  Rode SO o proprio teste:
    cd ${ROOT}/backend && ${PY} -m pytest tests/test_<ARQ>.py -q
  Itere ate passar. NAO rode a suite inteira. NAO edite base.py / weights.py / interpret.py / renderer.py / conftest.py
  (se faltar helper de texto, crie funcao local _txt_*() no seu modulo).

ESTILO: PT-BR nos textos; type hints; docstring curta citando a secao; ~150-400 linhas.
`

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['module', 'test_passed', 'summary'],
  properties: {
    module: { type: 'string' },
    test_passed: { type: 'boolean' },
    lines: { type: 'integer' },
    notes: { type: 'string' },
    summary: { type: 'string' },
  },
}

const MODS = [
  {
    arq: 'descriptive', effort: 'medium',
    brief: `KEY="descriptive"  TITLE="Estatistica Descritiva"  (Secao 8).
Para CADA variavel de ctx.analysis_variables: n, media, mediana, moda, min, max, amplitude, variancia,
desvio-padrao, CV(%), Q1, Q3, IQR, assimetria, curtose, percentis 5/10/25/50/75/90/95.
Tabela unica "Estatistica Descritiva" (linha por variavel).
Figuras: por variavel (ate 6 variaveis), painel com histograma+KDE (scipy.stats.gaussian_kde), boxplot e ECDF.
interpretation: junte interpret.interpret_descriptive(nome, stats, ctx.units) das 3 primeiras variaveis.
metrics: {"variables": {nome: {mean, median, std, cv, skewness, kurtosis, min, max, n}}}.
applicable: sempre True se ha >=1 variavel numerica.`,
  },
  {
    arq: 'esda', effort: 'high',
    brief: `KEY="esda_univariate"  TITLE="ESDA Univariada"  (Secoes 9-10).
w,_ = build_weights(ctx). Para CADA variavel (mask das linhas finitas):
  Moran global (esda.Moran, permutations=ctx.n_perm): I, EI, p_sim, z_sim.
  Moran Local/LISA (esda.Moran_Local): q (1HH 2LH 3LL 4HD->4HL), p_sim; contagem por quadrante entre os significativos; n_sig.
  Geary (esda.Geary): C, p_sim.  Getis Gi* (esda.G_Local star=True): n hot (Zs>0 & p<alpha), n cold (Zs<0 & p<alpha).
Tabelas:
  1 "ESDA Univariada": Variavel | Moran I | E[I] | z | p-value | Geary C | p (Geary) | LISA sig | Hot | Cold
  2 "ESDA Univariada — Testes": Variavel | Teste | Estatistica | p-value | Significativo
     (linhas: "Moran I (permutacao)", "Geary C", "Normalidade (D'Agostino)" por variavel)
Figuras: mapa LISA por variavel (render_points categorical=True, cat_labels={0:'nao sig',1:'Alto-Alto',2:'Baixo-Alto',3:'Baixo-Baixo',4:'Alto-Baixo'}) p/ ate 4 variaveis; mapa hot/cold (Getis) da principal.
interpretation: interpret_moran + interpret_local_moran + interpret_geary + interpret_getis da principal.
metrics: {"morans": {nome: {"I","EI","z","p"}}, "primary_moran": {"I","p","z","EI"}, "weights": info}.`,
  },
  {
    arq: 'moran', effort: 'medium',
    brief: `KEY="moran_scatter"  TITLE="Moran Scatter Plot"  (Secao 11).
w,_ = build_weights(ctx). Para CADA variavel: z padronizado; lag = libpysal.weights.lag_spatial(w, z);
slope OLS (== Moran I); contagem HH/LH/HL/LL; p (esda.Moran).
Figura Moran scatter por variavel (ate 6): x=z, y=lag(z), retas em 0, reta de regressao, pontos coloridos por quadrante
(categorico ordem fixa), caixa de texto com I, slope, p.
Tabela "Moran Scatter — Resumo": Variavel | Moran I | slope | p-value | HH | LH | HL | LL | Quadrante dominante.
interpretation: interpret_moran_scatter(principal, I, p, quad_counts, ctx.alpha).
metrics: {nome: {"I","slope","p","quadrants"}}.`,
  },
  {
    arq: 'bivariate', effort: 'high',
    brief: `KEY="esda_bivariate"  TITLE="ESDA Bivariada"  (Secao 12).
applicable: False se < 2 variaveis numericas.
Pares: ctx.param('bivariate_pairs') se dado; senao se ctx.param('bivariate_all_pairs',False) todos os pares (limite 8);
senao (primary, s) p/ s em secondary+explanatory (limite 6).
Cada par (a,b): esda.Moran_BV(x=a, y=b, w, permutations=ctx.n_perm) -> I, p_sim, z_sim; esda.Moran_Local_BV -> quadrantes, n_sig.
Tabelas:
  1 "ESDA Bivariada": Par | I bivariado | z | p-value | Significativo | LISA sig
  2 "ESDA Bivariada — Testes": mesma info formatada (Estatistica, p-value, Significativo)
Figuras: ate 4 pares -> mapa LISA bivariado (render_points categorical) + scatter (a vs lag(b)).
Se all_pairs: heatmap divergente da matriz de I bivariado.
interpretation: interpret_bivariate_moran do 1o par significativo (ou 1o par).
metrics: {"pairs": [{"a","b","I","p","z","n_sig"}]}.`,
  },
  {
    arq: 'idw', effort: 'high',
    brief: `KEY="idw"  TITLE="IDW — Inverse Distance Weighting"  (Secoes 13-14).
IDW proprio com scipy.spatial.cKDTree: potencia p, k vizinhos; se dist==0 -> valor do ponto.
Superficie na grade ctx.make_grid() p/ a principal com p=ctx.param('idw_power',2.0), k=ctx.param('idw_neighbors',12).
CV LOO sobre grade: powers=ctx.param('idw_power_grid',[1,1.5,2,2.5,3]), neighbors=ctx.param('idw_neighbors_grid',[6,12,18]).
Cada combinacao: ME, MAE, MSE, RMSE, R². Melhor por selection_metric. Re-render superficie na melhor config.
Tabela 1 "IDW — Validacao Cruzada": Power | Vizinhos | ME | MAE | RMSE | R²  (ordenada por RMSE, highlight_rows=[0]).
Figuras (4): (1) superficie interpolada melhor config (sample_values=principal), (2) pontos amostrais (render_points),
  (3) erro absoluto LOO por ponto (render_points), (4) observado x previsto LOO (matplotlib, reta 1:1, R²).
interpretation: interpret_idw_cv(best, metric).
metrics: {"best": {"power","neighbors","rmse","mae","me","r2"}, "grid_search": [...]}.`,
  },
  {
    arq: 'kriging', effort: 'high',
    brief: `KEY="kriging"  TITLE="Krigagem Ordinaria"  (Secoes 15-18). Variavel principal. pykrige.ok.OrdinaryKriging.
1) Para cada modelo em ctx.param('variogram_models',['spherical','exponential','gaussian','linear','power']):
   OrdinaryKriging(mx,my,z, variogram_model=m, nlags=ctx.param('variogram_bins',15)). Extraia lags e semivariancia
   experimental (ok.lags, ok.semivariance) e parametros (ok.variogram_model_parameters -> p/ spherical/exp/gauss = [psill, range, nugget]).
   Calcule nugget, sill_total=psill+nugget, range, razao nugget/sill.
2) Selecao por CV: p/ cada modelo, LOO (k-fold 10 se n>250) reaproveitando variogram_parameters ajustados no conjunto completo
   (OrdinaryKriging(..., variogram_model=m, variogram_parameters=params) sem o ponto/fold i; execute 'points').
   Metricas ME/MAE/MSE/RMSE/R² + MSDR (media de (erro^2 / var_krig)).
3) Melhor por selection_metric; override por ctx.param('variogram_model_override').
4) Superficie + variancia (sigma) na grade com o melhor modelo.
Tabelas:
  1 "Krigagem — Analise Variografica": Modelo | Nugget | Sill | Range | Nugget/Sill(%)
  2 "Krigagem — CV por Modelo": Modelo | Nugget | Sill | Range | ME | MAE | RMSE | R²   (ordenada, highlight_rows=[0])
  3 "Krigagem Ordinaria — Validacao": Metrica | Valor  (do melhor)
Figuras (ate 8): variograma exp+modelos (melhor destacado); superficie estimada; mapa de erro-padrao (sqrt var);
  pontos amostrais; residuos LOO (render_points diverging=True); obs x prev (reta 1:1, R²); histograma dos erros;
  QQ-plot dos erros padronizados.
interpretation: interpret_variogram + interpret_kriging_cv + interpret_model_selection.
metrics: {"best_model": str, "params": {"nugget","sill","range"}, "cv": {"me","mae","mse","rmse","r2","msdr"}, "ranked": [{"model","rmse","mae","r2"}]}.`,
  },
  {
    arq: 'external_drift', effort: 'high',
    brief: `KEY="external_drift"  TITLE="Krigagem com Deriva Externa"  (Secao 19).
applicable: exige ctx.aux_drift numerico, |r| com a principal >= ctx.param('drift_min_corr',0.3), poucos NaN.
Senao StepResult.skipped(KEY, TITLE, "nenhuma variavel auxiliar adequada: ...").
Metodo REGRESSAO-KRIGAGEM (documente na docstring):
  1 OLS principal ~ aux (statsmodels.api.OLS): R², coef, p, r de Pearson.
  2 tendencia = predicao OLS; residuo = principal - tendencia.
  3 Krigagem ordinaria dos residuos (variogram_model spherical ou o melhor por CV rapida).
  4 grade: aux interpolado p/ a grade (IDW p=2 k=12) -> tendencia_grade + OK(residuos) na grade -> estimativa final.
  5 CV LOO da estimativa combinada: ME/MAE/MSE/RMSE/R².
Tabela "Krigagem com Deriva Externa": R² regressao | r | nugget | sill | range (residuos) | ME | MAE | RMSE | R² (CV).
Figuras: (1) tendencia, (2) estimativa final, (3) erro-padrao, (4) residuos (diverging), (5) obs x prev.
interpretation: interpret_external_drift(primary, aux, r_corr, r2_reg, cv).
metrics: {"aux": nome, "r_corr":.., "r2_reg":.., "cv": {"rmse","mae","me","r2"}}.`,
  },
  {
    arq: 'gwr', effort: 'high',
    brief: `KEY="gwr"  TITLE="GWR / GWM"  (Secoes 20-21).
applicable: exige >=1 variavel em ctx.explanatory. dependente = ctx.primary. Remova NaN.
mgwr.sel_bw.Sel_BW + mgwr.gwr.GWR. Padronize X e y (documente; guarde media/sd p/ interpretar coef).
  bandwidth: ctx.param('bandwidth_kind','both') -> testa 'fixed' (Sel_BW(..., fixed=True)) e 'adaptive' (fixed=False),
  escolhe menor AICc. Ajusta GWR(bw).
Extraia: results.R2 (global), results.aicc, results.aic, results.RSS, bw, results.params, results.tvalues,
  results.localR2, results.resid_response, results.predy.
Se ctx.param('gwr_mc_iters',0) > 0: results.spatial_variability(selector, n_iters=iters) -> variaveis com p<alpha.
Tabelas:
  1 "GWR/GWM — Metricas": Metrica | Valor  (bw, tipo, R² global, AICc, AIC, RSS, n, k)
  2 "GWR/GWM — Coeficientes Locais": Variavel | Media | Min | Max | % |t|>1,96
Figuras (por explicativa, ate 3): coef local (render_points diverging=True) + significancia (categorical sig/nao sig);
  + R² local (render_points), residuos (render_points diverging=True), obs x prev.
interpretation: interpret_gwr(dep, bw, kind, r2_global, r2_local_min, r2_local_max, aicc, mc_significant_vars).
metrics: {"bw":.., "bw_kind":.., "r2_global":.., "aicc":.., "rss":.., "r2_local":[min,max]}.
Suprima warnings do mgwr.`,
  },
  {
    arq: 'cokriging', effort: 'high',
    brief: `KEY="cokriging"  TITLE="Co-Krigagem"  (Secao 22).
applicable: exige >=1 secundaria numerica com |r| com a principal >= ctx.param('cok_min_corr',0.4). Senao skipped com motivo (inclua o r).
secundaria = maior |r| entre ctx.secondary (!= principal).
Implemente CO-KRIGAGEM COLOCADA (Markov Model I) e DOCUMENTE que e aproximacao:
  - variograma da primaria e da secundaria (OrdinaryKriging p/ ajuste); r de Pearson.
  - abordagem pratica equivalente sob Markov I: regressao z_p ~ z_s + krigagem ordinaria do residuo; estimativa = a+b*z_s(grade) + OK(residuo)(grade),
    com z_s na grade por OK/IDW. (deixe claro na docstring).
  - CV LOO co-krigagem: ME/MAE/MSE/RMSE/R². Rode OK puro nas MESMAS particoes p/ comparar.
Tabela "Co-Krigagem": Item | Co-Krigagem | Krigagem Ordinaria  (linhas: RMSE, MAE, ME, R²) + linha r e sills.
Figuras: (1) predicao co-krigagem, (2) incerteza, (3) scatter primaria x secundaria (reta), (4) obs x prev CV.
interpretation: interpret_cokriging(primary, secondary, r, cv_ck, cv_ok).
metrics: {"secondary": nome, "r":.., "cv_ck": {"rmse","mae","me","r2"}, "cv_ok": {"rmse","mae","me","r2"}}.`,
  },
]

phase('Modulos')

const results = await parallel(
  MODS.map((m) => () =>
    agent(
      `Implemente o modulo de analise "${m.arq}".\n\n${SPEC}\n\n=== ESPEC. DESTE MODULO ===\n${m.brief}\n\n` +
      `Escreva 2 arquivos:\n  ${ROOT}/backend/app/analysis/${m.arq}.py\n  ${ROOT}/backend/tests/test_${m.arq}.py\n` +
      `Rode APENAS tests/test_${m.arq}.py ate passar. Reporte test_passed honestamente.`,
      { label: `mod:${m.arq}`, phase: 'Modulos', effort: m.effort, schema: SCHEMA },
    ),
  ),
)

log('Resultado: ' + results.filter(Boolean).map((r) => `${r.module}=${r.test_passed ? 'ok' : 'FALHOU'}`).join('  '))
return { modules: results.filter(Boolean) }
