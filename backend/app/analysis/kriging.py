"""Krigagem Ordinária — análise variográfica, seleção de modelo por validação
cruzada e interpolação da variável principal (seções 15-18).

O módulo ajusta vários modelos de variograma teórico ao variograma experimental,
seleciona o melhor por validação cruzada (leave-one-out, ou k-fold(10) quando
n > 250) segundo ``ctx.param('selection_metric')`` e produz a superfície estimada
e o mapa de erro-padrão da krigagem com o modelo vencedor.
"""
from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from app.analysis import interpret  # noqa: E402
from app.analysis.base import AnalysisContext, StepResult, TableResult  # noqa: E402
from app.maps import renderer  # noqa: E402

KEY = "kriging"
TITLE = "Krigagem Ordinária"

_MIN_POINTS = 20
_MODELS_3P = ("spherical", "exponential", "gaussian")


# --------------------------------------------------------------------------- #
# Aplicabilidade
# --------------------------------------------------------------------------- #
def applicable(ctx: AnalysisContext) -> tuple[bool, str]:
    if not ctx.primary or ctx.primary not in ctx.df.columns:
        return False, "Variável principal ausente na base."
    mx, my, z = ctx.clean_xyz(ctx.primary)
    if z.size < _MIN_POINTS:
        return False, (
            f"Apenas {z.size} pontos com coordenada e valor válidos "
            f"(mínimo {_MIN_POINTS}) para krigagem."
        )
    if not np.isfinite(np.nanstd(z)) or np.nanstd(z) == 0:
        return False, "Variável principal é constante — variograma indefinido."
    if np.unique(np.c_[mx, my], axis=0).shape[0] < _MIN_POINTS:
        return False, "Poucas localizações distintas para estimar o variograma."
    return True, ""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _params_dict(model: str, p: np.ndarray) -> dict[str, float]:
    """Converte ``ok.variogram_model_parameters`` para o dict aceito de volta
    pelo pykrige (``sill`` = patamar total = psill + nugget)."""
    p = [float(v) for v in np.asarray(p, float)]
    if model in _MODELS_3P:
        psill, rng, nugget = p
        return {"sill": psill + nugget, "range": rng, "nugget": nugget}
    if model == "linear":
        slope, nugget = p
        return {"slope": slope, "nugget": nugget}
    # power
    scale, exponent, nugget = p
    return {"scale": scale, "exponent": exponent, "nugget": nugget}


def _summ_params(model: str, p: np.ndarray) -> dict[str, float]:
    """Resumo interpretável: nugget, psill, sill_total, range, razão."""
    p = [float(v) for v in np.asarray(p, float)]
    if model in _MODELS_3P:
        psill, rng, nugget = p
        sill_total = psill + nugget
        ratio = nugget / sill_total if sill_total else np.nan
        return {
            "nugget": nugget,
            "psill": psill,
            "sill_total": sill_total,
            "range": rng,
            "nugget_sill": ratio,
        }
    nugget = p[-1]
    return {
        "nugget": nugget,
        "psill": np.nan,
        "sill_total": np.nan,
        "range": np.nan,
        "nugget_sill": np.nan,
    }


def _fit_full(mx, my, z, model: str, nlags: int):
    """Ajusta OrdinaryKriging no conjunto completo. Retorna o objeto ok."""
    from pykrige.ok import OrdinaryKriging

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return OrdinaryKriging(
            mx, my, z, variogram_model=model, nlags=int(nlags),
            enable_plotting=False, exact_values=True,
        )


def _cv_predict(mx, my, z, model: str, vparams: dict[str, float], seed: int):
    """Validação cruzada. LOO por padrão; k-fold(10) se n > 250.

    Reaproveita ``vparams`` (variograma ajustado no conjunto completo) em cada
    dobra, evitando reajuste instável em subconjuntos.
    """
    from pykrige.ok import OrdinaryKriging

    n = z.size
    idx = np.arange(n)
    if n > 250:
        rng = np.random.default_rng(seed)
        folds = np.array_split(rng.permutation(idx), 10)
    else:
        folds = [np.array([i]) for i in idx]

    pred = np.full(n, np.nan)
    var = np.full(n, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for test in folds:
            train = np.setdiff1d(idx, test, assume_unique=True)
            try:
                ok = OrdinaryKriging(
                    mx[train], my[train], z[train],
                    variogram_model=model, variogram_parameters=dict(vparams),
                    enable_plotting=False, exact_values=True,
                )
                zhat, ss = ok.execute("points", mx[test], my[test])
            except Exception:  # noqa: BLE001 — modelo instável nesta dobra
                continue
            pred[test] = np.asarray(zhat, float)
            var[test] = np.asarray(ss, float)
    return pred, var


def _metrics(z: np.ndarray, pred: np.ndarray, var: np.ndarray) -> dict[str, float]:
    m = np.isfinite(pred) & np.isfinite(z)
    if m.sum() < 3:
        return {k: np.nan for k in ("me", "mae", "mse", "rmse", "r2", "msdr", "n")}
    err = pred[m] - z[m]
    ss_tot = float(np.sum((z[m] - z[m].mean()) ** 2))
    r2 = 1.0 - float(np.sum(err ** 2)) / ss_tot if ss_tot > 0 else np.nan
    vm = m & np.isfinite(var) & (var > 0)
    if vm.sum() >= 3:
        e2 = (pred[vm] - z[vm]) ** 2
        msdr = float(np.mean(e2 / var[vm]))
    else:
        msdr = np.nan
    return {
        "me": float(np.mean(err)),
        "mae": float(np.mean(np.abs(err))),
        "mse": float(np.mean(err ** 2)),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "r2": r2,
        "msdr": msdr,
        "n": int(m.sum()),
    }


def _rank_key(metric: str):
    metric = (metric or "rmse").lower()
    if metric == "r2":
        return lambda d: (-(d["cv"]["r2"]) if np.isfinite(d["cv"]["r2"]) else np.inf)
    if metric == "me":
        return lambda d: (abs(d["cv"]["me"]) if np.isfinite(d["cv"]["me"]) else np.inf)
    return lambda d: (
        d["cv"][metric] if np.isfinite(d["cv"].get(metric, np.nan)) else np.inf
    )


# --------------------------------------------------------------------------- #
# run
# --------------------------------------------------------------------------- #
def run(ctx: AnalysisContext) -> StepResult:  # noqa: C901
    ok_flag, reason = applicable(ctx)
    if not ok_flag:
        return StepResult.skipped(KEY, TITLE, reason)

    name = ctx.primary
    zall = ctx.values(name)
    finite = np.isfinite(ctx.mx) & np.isfinite(ctx.my) & np.isfinite(zall)
    mx, my, z = ctx.mx[finite], ctx.my[finite], zall[finite]

    nlags = int(ctx.param("variogram_bins", 15))
    models = list(ctx.param("variogram_models",
                            ["spherical", "exponential", "gaussian", "linear", "power"]))
    metric = str(ctx.param("selection_metric", "rmse")).lower()
    override = ctx.param("variogram_model_override", None)
    seed = int(ctx.random_seed)

    params_used = {
        "variogram_bins": nlags,
        "variogram_models": models,
        "selection_metric": metric,
        "variogram_model_override": override,
        "cv": "kfold10" if z.size > 250 else "loo",
        "grid_resolution": int(ctx.param("grid_resolution", 80)),
        "n_points": int(z.size),
    }

    # ---- 1) ajuste e CV por modelo ------------------------------------- #
    fitted: list[dict[str, Any]] = []
    exp_lags = exp_semi = None
    for m in models:
        try:
            okf = _fit_full(mx, my, z, m, nlags)
        except Exception as exc:  # noqa: BLE001
            ctx.logger.warning("Krigagem: modelo %s falhou no ajuste (%s)", m, exc)
            continue
        if exp_lags is None:
            exp_lags = np.asarray(okf.lags, float)
            exp_semi = np.asarray(okf.semivariance, float)
        raw = np.asarray(okf.variogram_model_parameters, float)
        vp = _params_dict(m, raw)
        summ = _summ_params(m, raw)
        pred, var = _cv_predict(mx, my, z, m, vp, seed)
        cv = _metrics(z, pred, var)
        fitted.append({
            "model": m, "ok": okf, "vparams": vp, "summ": summ,
            "cv": cv, "pred": pred, "var": var,
        })

    if not fitted:
        return StepResult.skipped(
            KEY, TITLE, "Nenhum modelo de variograma pôde ser ajustado."
        )

    # ---- 2) seleção do melhor ---------------------------------------- #
    ranked = sorted(fitted, key=_rank_key(metric))
    best = ranked[0]
    if override and str(override).lower() in {f["model"] for f in fitted}:
        best = next(f for f in fitted if f["model"] == str(override).lower())
        params_used["override_applied"] = True

    b_model = best["model"]
    b_summ = best["summ"]
    b_cv = best["cv"]
    b_pred, b_var = best["pred"], best["var"]

    # ---- Tabela 1: análise variográfica ---------------------------- #
    t1 = pd.DataFrame([
        {
            "Modelo": f["model"],
            "Nugget": f["summ"]["nugget"],
            "Sill": f["summ"]["sill_total"],
            "Range": f["summ"]["range"],
            "Nugget/Sill(%)": f["summ"]["nugget_sill"] * 100
            if np.isfinite(f["summ"]["nugget_sill"]) else np.nan,
        }
        for f in fitted
    ])
    tbl1 = TableResult(
        name="kriging_variografia", df=t1,
        title="Krigagem — Análise Variográfica",
        caption="Parâmetros dos modelos de variograma ajustados ao variograma "
                "experimental (nlags = %d)." % nlags,
    )

    # ---- Tabela 2: CV por modelo (ordenada melhor→pior) ------------ #
    order = sorted(fitted, key=_rank_key(metric))
    t2 = pd.DataFrame([
        {
            "Modelo": f["model"],
            "Nugget": f["summ"]["nugget"],
            "Sill": f["summ"]["sill_total"],
            "Range": f["summ"]["range"],
            "ME": f["cv"]["me"],
            "MAE": f["cv"]["mae"],
            "RMSE": f["cv"]["rmse"],
            "R²": f["cv"]["r2"],
        }
        for f in order
    ])
    hl = [i for i, f in enumerate(order) if f["model"] == b_model]
    tbl2 = TableResult(
        name="kriging_cv_modelos", df=t2,
        title="Krigagem — CV por Modelo",
        caption="Validação cruzada (%s). Ordenada do melhor para o pior por %s."
                % (params_used["cv"].upper(), metric.upper()),
        highlight_rows=hl or [0],
    )

    # ---- Tabela 3: validação do melhor ---------------------------- #
    t3 = pd.DataFrame({
        "Métrica": ["ME (viés)", "MAE", "MSE", "RMSE", "R²", "MSDR"],
        "Valor": [b_cv["me"], b_cv["mae"], b_cv["mse"], b_cv["rmse"],
                  b_cv["r2"], b_cv["msdr"]],
    })
    tbl3 = TableResult(
        name="kriging_validacao", df=t3,
        title="Krigagem Ordinária — Validação",
        caption=f"Modelo selecionado: {b_model}.",
    )

    # ---- 4) superfície + variância na grade ----------------------- #
    figures = []
    gx, gy = ctx.make_grid()
    from pykrige.ok import OrdinaryKriging

    surf = err_std = None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            okg = OrdinaryKriging(
                mx, my, z, variogram_model=b_model,
                variogram_parameters=dict(best["vparams"]),
                enable_plotting=False, exact_values=True,
            )
            zg, ssg = okg.execute("grid", gx, gy)
        surf = np.ma.filled(np.asarray(zg, float), np.nan)
        err_std = np.sqrt(np.clip(np.ma.filled(np.asarray(ssg, float), np.nan), 0, None))
    except Exception as exc:  # noqa: BLE001
        ctx.logger.warning("Krigagem: falha ao interpolar a grade (%s)", exc)

    # ---- Figuras -------------------------------------------------- #
    figures.append(_fig_variogram(ctx, exp_lags, exp_semi, fitted, b_model))

    if surf is not None:
        figures.append(renderer.render_surface(
            ctx, surf, gx, gy, name="kriging_superficie",
            title=f"Krigagem ordinária de {name}",
            method=f"Krigagem ordinária — modelo {b_model}",
            cbar_label=f"{name} ({ctx.units})" if ctx.units else name,
            sample_values=z,
            caption="Superfície estimada por krigagem ordinária com o modelo "
                    f"de variograma {b_model}.",
        ))
    if err_std is not None:
        figures.append(renderer.render_surface(
            ctx, err_std, gx, gy, name="kriging_erro_padrao",
            title=f"Erro-padrão da krigagem de {name}",
            method=f"Krigagem ordinária — modelo {b_model}",
            cbar_label=f"erro-padrão ({ctx.units})" if ctx.units else "erro-padrão",
            show_points=True,
            caption="Raiz quadrada da variância de krigagem (incerteza da estimativa).",
        ))

    figures.append(renderer.render_points(
        ctx, zall, name="kriging_amostras",
        title=f"Pontos amostrais — {name}",
        method="Amostras",
        cbar_label=f"{name} ({ctx.units})" if ctx.units else name,
        caption="Valores observados nos pontos de amostragem.",
    ))

    res_full = np.full(ctx.n, np.nan)
    res_full[finite] = z - b_pred  # resíduo = observado - previsto (LOO)
    figures.append(renderer.render_points(
        ctx, res_full, name="kriging_residuos",
        title=f"Resíduos da validação cruzada — {name}",
        method=f"Krigagem ordinária — modelo {b_model}",
        cbar_label=f"resíduo obs − prev ({ctx.units})" if ctx.units else "resíduo obs − prev",
        diverging=True,
        caption="Resíduos leave-one-out (observado menos previsto).",
    ))

    figures.append(_fig_obs_pred(ctx, z, b_pred, b_cv, b_model))
    figures.append(_fig_hist_err(ctx, z - b_pred, b_model))
    figures.append(_fig_qq(ctx, z - b_pred, b_var, b_model))
    figures = [f for f in figures if f is not None][:8]

    # ---- interpretação ----------------------------------------------- #
    ranked_payload = [
        {"model": f["model"], "rmse": f["cv"]["rmse"], "mae": f["cv"]["mae"],
         "r2": f["cv"]["r2"]}
        for f in order
    ]
    interp = " ".join([
        interpret.interpret_variogram(
            b_model, b_summ["nugget"], b_summ["psill"], b_summ["range"]
        ),
        interpret.interpret_kriging_cv(b_model, b_cv),
        interpret.interpret_model_selection(
            [{"model": r["model"], **r} for r in ranked_payload], metric
        ),
    ])

    metrics = {
        "best_model": b_model,
        "params": {
            "nugget": _safe(b_summ["nugget"]),
            "sill": _safe(b_summ["sill_total"]),
            "range": _safe(b_summ["range"]),
        },
        "cv": {k: _safe(b_cv.get(k)) for k in ("me", "mae", "mse", "rmse", "r2", "msdr")},
        "ranked": [
            {"model": r["model"], "rmse": _safe(r["rmse"]), "mae": _safe(r["mae"]),
             "r2": _safe(r["r2"])}
            for r in ranked_payload
        ],
    }

    return StepResult(
        key=KEY, title=TITLE, status="ok",
        tables=[tbl1, tbl2, tbl3], figures=figures,
        metrics=metrics, interpretation=interp, params_used=params_used,
    )


def _safe(v: Any) -> float | None:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if np.isfinite(v) else None


# --------------------------------------------------------------------------- #
# Figuras auxiliares (matplotlib)
# --------------------------------------------------------------------------- #
def _fig_variogram(ctx, lags, semi, fitted, best_model):
    if lags is None:
        return None
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.scatter(lags, semi, s=32, color="#333333", zorder=5,
               label="variograma experimental")
    dmax = float(np.nanmax(lags)) * 1.05
    dd = np.linspace(1e-6, dmax, 200)
    cmap = plt.get_cmap("viridis")
    cols = [cmap(v) for v in np.linspace(0.1, 0.85, len(fitted))]
    for f, col in zip(fitted, cols):
        okf = f["ok"]
        yy = okf.variogram_function(okf.variogram_model_parameters, dd)
        is_best = f["model"] == best_model
        ax.plot(dd, yy, color=col, lw=3.0 if is_best else 1.4,
                ls="-" if is_best else "--",
                label=f["model"] + (" (selecionado)" if is_best else ""))
    ax.set_xlabel("distância (m)")
    ax.set_ylabel("semivariância")
    ax.set_title("Variograma experimental e modelos ajustados", fontsize=11,
                 fontweight="bold")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, framealpha=0.9)
    return ctx.save_fig(fig, "kriging_variograma", subdir="figures",
                        title="Variograma experimental e modelos",
                        caption="Modelo selecionado destacado em linha cheia mais grossa.",
                        kind="chart")


def _fig_obs_pred(ctx, z, pred, cv, model):
    m = np.isfinite(pred) & np.isfinite(z)
    if m.sum() < 3:
        return None
    fig, ax = plt.subplots(figsize=(5.6, 5.4))
    ax.scatter(z[m], pred[m], s=26, color="#2c7fb8", alpha=0.8, edgecolors="white",
               linewidths=0.4)
    lo = float(min(z[m].min(), pred[m].min()))
    hi = float(max(z[m].max(), pred[m].max()))
    ax.plot([lo, hi], [lo, hi], color="#888888", ls="--", lw=1.2, label="reta 1:1")
    ax.set_xlabel(f"observado ({ctx.units})" if ctx.units else "observado")
    ax.set_ylabel(f"previsto ({ctx.units})" if ctx.units else "previsto")
    ax.set_title(f"Observado vs. previsto — modelo {model}", fontsize=11,
                 fontweight="bold")
    ax.text(0.05, 0.92, f"R² = {interpret.num(cv['r2'], 3)}\nRMSE = {interpret.num(cv['rmse'])}",
            transform=ax.transAxes, fontsize=9, va="top",
            bbox=dict(boxstyle="round", fc="white", ec="#cccccc"))
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_aspect("equal", adjustable="datalim")
    return ctx.save_fig(fig, "kriging_obs_prev", subdir="figures",
                        title="Observado vs. previsto (validação cruzada)",
                        caption="Quanto mais próximos da reta 1:1, melhor a predição.",
                        kind="chart")


def _fig_hist_err(ctx, err, model):
    err = err[np.isfinite(err)]
    if err.size < 3:
        return None
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.hist(err, bins=min(25, max(8, err.size // 6)), color="#2c7fb8",
            edgecolor="white")
    ax.axvline(0.0, color="#c0392b", lw=1.4, ls="--", label="erro zero")
    ax.axvline(float(np.mean(err)), color="#2c3e50", lw=1.4,
               label=f"média = {interpret.num(np.mean(err))}")
    ax.set_xlabel(f"erro obs − prev ({ctx.units})" if ctx.units else "erro obs − prev")
    ax.set_ylabel("frequência")
    ax.set_title(f"Distribuição dos erros de validação — modelo {model}",
                 fontsize=11, fontweight="bold")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    return ctx.save_fig(fig, "kriging_hist_erros", subdir="figures",
                        title="Histograma dos erros de validação cruzada",
                        caption="Idealmente centrado em zero e aproximadamente simétrico.",
                        kind="chart")


def _fig_qq(ctx, err, var, model):
    from scipy import stats

    m = np.isfinite(err) & np.isfinite(var) & (var > 0)
    if m.sum() < 3:
        return None
    std_err = err[m] / np.sqrt(var[m])
    fig, ax = plt.subplots(figsize=(5.6, 5.2))
    stats.probplot(std_err, dist="norm", plot=ax)
    ax.get_lines()[0].set_marker("o")
    ax.get_lines()[0].set_markerfacecolor("#2c7fb8")
    ax.get_lines()[0].set_markeredgecolor("white")
    ax.get_lines()[0].set_markersize(5)
    ax.get_lines()[1].set_color("#c0392b")
    ax.set_title(f"QQ-plot dos erros padronizados — modelo {model}", fontsize=11,
                 fontweight="bold")
    ax.set_xlabel("quantis teóricos (normal)")
    ax.set_ylabel("quantis dos erros padronizados")
    ax.grid(alpha=0.3)
    return ctx.save_fig(fig, "kriging_qqplot", subdir="figures",
                        title="QQ-plot dos erros padronizados",
                        caption="Erro dividido pelo desvio-padrão de krigagem; "
                                "alinhamento à reta indica boa calibração.",
                        kind="chart")
