"""Regressão Geograficamente Ponderada / GWM (seções 20-21).

Ajusta ``mgwr.gwr.GWR`` com largura de banda selecionada por
``mgwr.sel_bw.Sel_BW`` (critério AICc). Testa banda fixa e/ou adaptativa
conforme ``ctx.param('bandwidth_kind')`` e escolhe a de menor AICc.

As variáveis explicativas e a dependente são padronizadas (escore z) antes do
ajuste; as médias e desvios são guardados para permitir a leitura dos
coeficientes. O R² é invariante à padronização; predições e resíduos são
reconvertidos à escala original para os mapas.
"""
from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd

from app.analysis.base import AnalysisContext, StepResult, TableResult
from app.analysis.interpret import interpret_gwr, num
from app.maps import renderer

KEY = "gwr"
TITLE = "GWR / GWM"

_T_CRIT = 1.96


# --------------------------------------------------------------------------- #
def applicable(ctx: AnalysisContext) -> tuple[bool, str]:
    exps = [c for c in ctx.explanatory if c and c in ctx.df.columns]
    if not exps:
        return False, "Nenhuma variável explicativa definida para o modelo GWR."
    if ctx.primary not in ctx.df.columns:
        return False, "Variável dependente ausente na base."
    cols = [ctx.primary, *exps]
    sub = ctx.df[cols].apply(pd.to_numeric, errors="coerce")
    m = np.isfinite(ctx.mx) & np.isfinite(ctx.my) & sub.notna().all(axis=1).to_numpy()
    n_ok = int(m.sum())
    if n_ok < 30:
        return False, (
            f"Amostras válidas insuficientes para GWR (n={n_ok}; mínimo 30)."
        )
    return True, ""


# --------------------------------------------------------------------------- #
def _standardize(a: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = np.asarray(a, float)
    mean = a.mean(axis=0)
    sd = a.std(axis=0)
    sd_safe = np.where(sd == 0, 1.0, sd)
    return (a - mean) / sd_safe, mean, sd


def _fit_bw(coords: np.ndarray, y: np.ndarray, X: np.ndarray, *, fixed: bool):
    """Retorna ``(selector, results)`` para uma configuração de banda."""
    from mgwr.gwr import GWR
    from mgwr.sel_bw import Sel_BW

    sel = Sel_BW(coords, y, X, fixed=fixed, kernel="bisquare", n_jobs=1)
    bw = sel.search(criterion="AICc")
    res = GWR(coords, y, X, bw, fixed=fixed, kernel="bisquare", n_jobs=1).fit()
    return sel, res, float(bw)


# --------------------------------------------------------------------------- #
def run(ctx: AnalysisContext) -> StepResult:
    ok, reason = applicable(ctx)
    if not ok:
        return StepResult.skipped(KEY, TITLE, reason)

    dep = ctx.primary
    exps = [c for c in ctx.explanatory if c and c in ctx.df.columns]
    alpha = float(ctx.alpha)
    mc_iters = int(ctx.param("gwr_mc_iters", 0) or 0)
    bw_kind_param = str(ctx.param("bandwidth_kind", "both")).lower()

    raw = ctx.df[[dep, *exps]].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    finite = np.isfinite(ctx.mx) & np.isfinite(ctx.my) & np.isfinite(raw).all(axis=1)
    idx = np.where(finite)[0]
    coords = np.c_[ctx.mx[idx], ctx.my[idx]]
    y_raw = raw[idx, 0]
    X_raw = raw[idx, 1:]

    ys, y_mean, y_sd = _standardize(y_raw)
    Xs, X_mean, X_sd = _standardize(X_raw)
    ys = ys.reshape(-1, 1)

    if bw_kind_param == "fixed":
        candidates = [("fixa", True)]
    elif bw_kind_param == "adaptive":
        candidates = [("adaptativa", False)]
    else:
        candidates = [("fixa", True), ("adaptativa", False)]

    fits: list[tuple[str, Any, Any, float]] = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        np.seterr(all="ignore")
        for label, fixed in candidates:
            try:
                sel, res, bw = _fit_bw(coords, ys, Xs, fixed=fixed)
                fits.append((label, sel, res, bw))
            except Exception as exc:  # noqa: BLE001
                ctx.logger.warning("GWR banda %s falhou: %s", label, exc)

    if not fits:
        return StepResult.skipped(
            KEY, TITLE, "Não foi possível selecionar a largura de banda do GWR."
        )

    fits.sort(key=lambda t: float(t[2].aicc))
    bw_kind, selector, results, bw = fits[0]

    params = np.asarray(results.params, float)          # (n, k)  col 0 = intercepto
    tvals = np.asarray(results.tvalues, float)
    local_r2 = np.asarray(results.localR2, float).ravel()
    resid_std = np.asarray(results.resid_response, float).ravel()
    predy_std = np.asarray(results.predy, float).ravel()

    predy = predy_std * y_sd + y_mean
    resid = resid_std * y_sd
    r2_global = float(results.R2)
    aicc = float(results.aicc)
    aic = float(results.aic)
    rss = float(getattr(results, "resid_ss", np.nan))
    r2_local_min = float(np.nanmin(local_r2))
    r2_local_max = float(np.nanmax(local_r2))

    var_names = ["Intercepto", *exps]

    # ---- Monte Carlo (variabilidade espacial dos coeficientes) ----------- #
    mc_significant: list[str] | None = None
    mc_pvals: np.ndarray | None = None
    if mc_iters > 0:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mc_pvals = np.asarray(
                    results.spatial_variability(selector, n_iters=mc_iters), float
                ).ravel()
            mc_significant = [
                var_names[i]
                for i in range(min(len(var_names), len(mc_pvals)))
                if np.isfinite(mc_pvals[i]) and mc_pvals[i] < alpha
            ]
        except Exception as exc:  # noqa: BLE001
            ctx.logger.warning("spatial_variability falhou: %s", exc)
            mc_significant = None

    # ---- Tabela 1: métricas -------------------------------------------- #
    t1 = pd.DataFrame(
        {
            "Métrica": [
                "Largura de banda",
                "Tipo de banda",
                "R² global",
                "AICc",
                "AIC",
                "RSS (padronizado)",
                "n",
                "k (preditores)",
            ],
            "Valor": [
                num(bw, 2),
                bw_kind,
                num(r2_global, 3),
                num(aicc, 1),
                num(aic, 1),
                num(rss, 3),
                str(len(idx)),
                str(len(exps)),
            ],
        }
    )
    tables = [
        TableResult(
            name="gwr_metricas",
            df=t1,
            title="GWR/GWM — Métricas",
            caption=(
                "Banda selecionada por AICc entre as configurações testadas. "
                "Variáveis padronizadas (escore z) antes do ajuste."
            ),
        )
    ]

    # ---- Tabela 2: coeficientes locais -------------------------------- #
    rows = []
    for j, name in enumerate(var_names):
        col = params[:, j]
        tc = np.abs(tvals[:, j])
        rows.append(
            {
                "Variável": name,
                "Média": round(float(np.nanmean(col)), 4),
                "Mín": round(float(np.nanmin(col)), 4),
                "Máx": round(float(np.nanmax(col)), 4),
                "% |t|>1,96": round(float(np.nanmean(tc > _T_CRIT) * 100.0), 1),
            }
        )
    t2 = pd.DataFrame(rows)
    tables.append(
        TableResult(
            name="gwr_coeficientes_locais",
            df=t2,
            title="GWR/GWM — Coeficientes Locais",
            caption=(
                "Coeficientes em unidades padronizadas (variação em desvios-padrão "
                "de "
                + dep
                + " por 1 desvio-padrão do preditor). A última coluna indica a "
                "fração de localizações com coeficiente significativo (|t| > 1,96)."
            ),
        )
    )

    # ---- Figuras ------------------------------------------------------- #
    figures = []
    n_full = ctx.n

    def _full(vec: np.ndarray) -> np.ndarray:
        out = np.full(n_full, np.nan, float)
        out[idx] = vec
        return out

    for j, name in enumerate(exps, start=1):
        coef_full = _full(params[:, j])
        try:
            figures.append(
                renderer.render_points(
                    ctx,
                    coef_full,
                    name=f"gwr_coef_{name}",
                    title=f"GWR — coeficiente local de {name}",
                    method="GWR (coeficiente local, unidades padronizadas)",
                    cbar_label=f"β local ({name})",
                    diverging=True,
                    caption=(
                        "Coeficiente local de "
                        + name
                        + " sobre "
                        + dep
                        + ". Escala divergente centrada em zero."
                    ),
                )
            )
        except Exception as exc:  # noqa: BLE001
            ctx.logger.warning("mapa coef %s falhou: %s", name, exc)

        sig_code = _full((np.abs(tvals[:, j]) > _T_CRIT).astype(float))
        try:
            figures.append(
                renderer.render_points(
                    ctx,
                    sig_code,
                    name=f"gwr_sig_{name}",
                    title=f"GWR — significância local de {name}",
                    method="GWR (|t| > 1,96)",
                    categorical=True,
                    cat_labels={0.0: "não significativo", 1.0: "significativo"},
                    caption=(
                        "Localizações onde o coeficiente de "
                        + name
                        + " é significativo (|t| > 1,96)."
                    ),
                )
            )
        except Exception as exc:  # noqa: BLE001
            ctx.logger.warning("mapa significância %s falhou: %s", name, exc)

    try:
        figures.append(
            renderer.render_points(
                ctx,
                _full(local_r2),
                name="gwr_r2_local",
                title="GWR — R² local",
                method="GWR (R² local)",
                cbar_label="R² local",
                caption="Qualidade de ajuste local do modelo GWR.",
            )
        )
    except Exception as exc:  # noqa: BLE001
        ctx.logger.warning("mapa R² local falhou: %s", exc)

    try:
        figures.append(
            renderer.render_points(
                ctx,
                _full(resid),
                name="gwr_residuos",
                title="GWR — resíduos",
                method="GWR (resíduo = observado - previsto)",
                cbar_label=f"resíduo ({ctx.units or 'valor'})",
                diverging=True,
                caption="Resíduos do GWR na escala original da variável dependente.",
            )
        )
    except Exception as exc:  # noqa: BLE001
        ctx.logger.warning("mapa resíduos falhou: %s", exc)

    figures.append(_scatter_obs_pred(ctx, y_raw, predy, dep))

    # ---- Interpretação ---------------------------------------------- #
    interpretation = interpret_gwr(
        dep=dep,
        bw=bw,
        bw_kind=bw_kind,
        r2_global=r2_global,
        r2_local_min=r2_local_min,
        r2_local_max=r2_local_max,
        aicc=aicc,
        mc_significant_vars=mc_significant,
    )

    metrics: dict[str, Any] = {
        "bw": bw,
        "bw_kind": bw_kind,
        "r2_global": r2_global,
        "aicc": aicc,
        "rss": rss,
        "r2_local": [r2_local_min, r2_local_max],
    }
    if mc_pvals is not None:
        metrics["mc_pvalues"] = {
            var_names[i]: float(mc_pvals[i])
            for i in range(min(len(var_names), len(mc_pvals)))
        }

    params_used = {
        "bandwidth_kind": bw_kind_param,
        "bw_selecionada": bw,
        "bw_tipo": bw_kind,
        "kernel": "bisquare",
        "criterio_selecao": "AICc",
        "padronizacao": "escore z (X e y)",
        "gwr_mc_iters": mc_iters,
        "alpha": alpha,
        "aicc_por_configuracao": {lbl: float(r.aicc) for lbl, _, r, _ in fits},
    }

    return StepResult(
        key=KEY,
        title=TITLE,
        status="ok",
        tables=tables,
        figures=figures,
        metrics=metrics,
        interpretation=interpretation,
        params_used=params_used,
    )


# --------------------------------------------------------------------------- #
def _scatter_obs_pred(ctx: AnalysisContext, obs: np.ndarray, pred: np.ndarray, dep: str):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.0, 6.0))
    ax.scatter(obs, pred, s=18, color="#3b6", edgecolors="black", linewidths=0.3,
               alpha=0.8, label="amostras")
    lo = float(min(np.nanmin(obs), np.nanmin(pred)))
    hi = float(max(np.nanmax(obs), np.nanmax(pred)))
    ax.plot([lo, hi], [lo, hi], color="#444", lw=1.0, ls="--", label="y = x")
    ax.set_xlabel(f"{dep} observado ({ctx.units or 'valor'})")
    ax.set_ylabel(f"{dep} previsto (GWR)")
    ax.set_title("GWR — observado vs. previsto", fontsize=12, fontweight="bold")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_aspect("equal", adjustable="box")
    return ctx.save_fig(
        fig,
        "gwr_obs_vs_prev",
        subdir="figures",
        title="GWR — observado vs. previsto",
        caption="Valores previstos pelo GWR contra os observados; a linha tracejada é y = x.",
        kind="chart",
    )
