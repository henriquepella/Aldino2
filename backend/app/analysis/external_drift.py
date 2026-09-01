"""Krigagem com Deriva Externa — regressão-krigagem (seção 19).

Estratégia (regressão-krigagem):

1. Ajusta uma regressão linear (OLS) da variável principal sobre a variável
   auxiliar (deriva externa): ``principal ~ aux`` — reporta R², coeficiente,
   p-valor e o r de Pearson.
2. A tendência é a predição do OLS; o resíduo é ``principal - tendência``.
3. Krigagem ordinária dos resíduos, com modelo de variograma ``spherical`` ou
   o melhor entre os candidatos por uma validação cruzada rápida (k-fold).
4. Na grade: a auxiliar é interpolada por IDW (potência 2, 12 vizinhos), a
   tendência da grade é reconstruída pelo OLS e somada à krigagem ordinária
   dos resíduos na grade -> estimativa final.
5. Validação cruzada leave-one-out (ou 10-fold se n > 250) da estimativa
   combinada: ME (viés), MAE, MSE, RMSE e R².

A seleção do modelo de variograma é sempre pela métrica
``ctx.param('selection_metric', 'rmse')`` na validação cruzada — nunca por
ajuste visual.
"""
from __future__ import annotations

import warnings
from typing import Any, Sequence

import numpy as np
import pandas as pd

from app.analysis import interpret
from app.analysis.base import AnalysisContext, StepResult, TableResult
from app.maps import renderer

KEY = "external_drift"
TITLE = "Krigagem com Deriva Externa"

_MODELS_DEFAULT = ["spherical", "exponential", "gaussian"]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _metrics(obs: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    """ME (viés), MAE, MSE, RMSE, R² (seções 15/16/28/43)."""
    obs = np.asarray(obs, float)
    pred = np.asarray(pred, float)
    e = pred - obs
    ss_res = float(np.sum((obs - pred) ** 2))
    ss_tot = float(np.sum((obs - obs.mean()) ** 2))
    return {
        "me": float(np.mean(e)),
        "mae": float(np.mean(np.abs(e))),
        "mse": float(np.mean(e ** 2)),
        "rmse": float(np.sqrt(np.mean(e ** 2))),
        "r2": float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan"),
    }


def _rank_value(m: dict[str, float], metric: str) -> float:
    if metric == "r2":
        v = m.get("r2", float("nan"))
        return -v if np.isfinite(v) else np.inf
    if metric == "me":
        return abs(m.get("me", np.inf))
    return m.get(metric, m.get("rmse", np.inf))


def _kfold(n: int, k: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    return [np.sort(idx[i::k]) for i in range(min(k, n))]


def _idw_grid(
    mx: np.ndarray, my: np.ndarray, z: np.ndarray,
    gx: np.ndarray, gy: np.ndarray, *, power: float = 2.0, k: int = 12,
) -> np.ndarray:
    """Interpola ``z`` para a grade (IDW potência ``power``, ``k`` vizinhos)."""
    from scipy.spatial import cKDTree

    GX, GY = np.meshgrid(gx, gy)
    pts = np.c_[GX.ravel(), GY.ravel()]
    tree = cKDTree(np.c_[mx, my])
    k = int(min(k, len(mx)))
    dist, idx = tree.query(pts, k=k)
    if k == 1:
        dist = dist[:, None]
        idx = idx[:, None]
    dist = np.maximum(dist, 1e-12)
    w = 1.0 / dist ** power
    vals = np.sum(w * z[idx], axis=1) / np.sum(w, axis=1)
    exact = dist[:, 0] <= 1e-9
    vals[exact] = z[idx[exact, 0]]
    return vals.reshape(GX.shape)


def _ols_beta(aux: np.ndarray, z: np.ndarray) -> np.ndarray:
    X = np.c_[np.ones(len(aux)), aux]
    return np.linalg.lstsq(X, z, rcond=None)[0]


def _combined_cv(
    mx: np.ndarray, my: np.ndarray, z: np.ndarray, aux: np.ndarray,
    model: str, folds: Sequence[np.ndarray],
) -> np.ndarray:
    """Predições de VC da estimativa combinada (tendência OLS + OK dos resíduos)."""
    from pykrige.ok import OrdinaryKriging

    pred = np.full(len(z), np.nan)
    for test_idx in folds:
        test_idx = np.asarray(test_idx, int)
        if len(test_idx) == 0:
            continue
        train = np.ones(len(z), bool)
        train[test_idx] = False
        if train.sum() < 10:
            continue
        beta = _ols_beta(aux[train], z[train])
        resid_tr = z[train] - (beta[0] + beta[1] * aux[train])
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                okr = OrdinaryKriging(
                    mx[train], my[train], resid_tr,
                    variogram_model=model, enable_plotting=False,
                )
                rk, _ = okr.execute("points", mx[test_idx], my[test_idx])
        except Exception:  # noqa: BLE001 — ponto degenerado: fica como NaN
            continue
        trend_te = beta[0] + beta[1] * aux[test_idx]
        pred[test_idx] = np.asarray(trend_te, float) + np.asarray(rk, float)
    return pred


# --------------------------------------------------------------------------- #
# Contrato
# --------------------------------------------------------------------------- #
def applicable(ctx: AnalysisContext) -> tuple[bool, str]:
    aux = ctx.aux_drift
    min_corr = float(ctx.param("drift_min_corr", 0.3))
    if not aux or aux not in ctx.df.columns:
        return False, "nenhuma variavel auxiliar adequada: aux_drift não definida"
    prim = ctx.values(ctx.primary)
    a = ctx.values(aux)
    m = np.isfinite(prim) & np.isfinite(a) & np.isfinite(ctx.mx) & np.isfinite(ctx.my)
    if int(m.sum()) < 15:
        return False, (
            f"nenhuma variavel auxiliar adequada: apenas {int(m.sum())} pares "
            f"válidos entre {aux} e {ctx.primary}"
        )
    nan_frac = 1.0 - m.sum() / len(prim)
    if nan_frac > 0.2:
        return False, (
            f"nenhuma variavel auxiliar adequada: {aux} tem "
            f"{nan_frac:.0%} de valores ausentes"
        )
    r = float(np.corrcoef(prim[m], a[m])[0, 1])
    if not np.isfinite(r) or abs(r) < min_corr:
        return False, (
            f"nenhuma variavel auxiliar adequada: correlação |r| = {abs(r):.2f} "
            f"entre {aux} e {ctx.primary} abaixo do mínimo ({min_corr:.2f})"
        )
    return True, ""


def run(ctx: AnalysisContext) -> StepResult:
    ok, why = applicable(ctx)
    if not ok:
        return StepResult.skipped(KEY, TITLE, why)

    import statsmodels.api as sm

    primary = ctx.primary
    aux = ctx.aux_drift  # type: ignore[assignment]
    units = ctx.units or "valor"
    seed = int(ctx.random_seed)
    sel_metric = str(ctx.param("selection_metric", "rmse")).lower()
    idw_power = float(ctx.param("idw_power_grid", ctx.param("idw_power", 2.0)))
    idw_neigh = int(ctx.param("idw_neighbors_grid", ctx.param("idw_neighbors", 12)))

    # ---- dados válidos ------------------------------------------------- #
    prim = ctx.values(primary)
    a_all = ctx.values(aux)
    mask = np.isfinite(prim) & np.isfinite(a_all) & np.isfinite(ctx.mx) & np.isfinite(ctx.my)
    mx = ctx.mx[mask]
    my = ctx.my[mask]
    z = prim[mask]
    av = a_all[mask]
    n_obs = int(len(z))
    if n_obs < 15:
        return StepResult.skipped(KEY, TITLE, "nenhuma variavel auxiliar adequada: dados insuficientes após limpeza")

    r_corr = float(np.corrcoef(av, z)[0, 1])

    # ---- 1. regressão OLS ------------------------------------------------ #
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ols = sm.OLS(z, sm.add_constant(av)).fit()
    intercept = float(ols.params[0])
    coef = float(ols.params[1])
    r2_reg = float(ols.rsquared)
    p_slope = float(ols.pvalues[1])

    # ---- 2. tendência + resíduos -------------------------------------- #
    trend = intercept + coef * av
    resid = z - trend

    # ---- 3. seleção do modelo de variograma (CV rápida) -------------- #
    override = ctx.param("variogram_model_override", None)
    if override:
        candidates = [str(override)]
    else:
        candidates = [str(c) for c in ctx.param("variogram_models", _MODELS_DEFAULT)]
        candidates = [c for c in candidates if c in ("spherical", "exponential", "gaussian", "linear", "power")]
        if not candidates:
            candidates = list(_MODELS_DEFAULT)

    folds_sel = _kfold(n_obs, min(5, n_obs), seed)
    sel_rows: list[dict[str, Any]] = []
    for model in candidates:
        pred = _combined_cv(mx, my, z, av, model, folds_sel)
        ok_m = np.isfinite(pred)
        if ok_m.sum() < n_obs * 0.6:
            continue
        m = _metrics(z[ok_m], pred[ok_m])
        m["model"] = model
        sel_rows.append(m)

    if not sel_rows:
        return StepResult.skipped(
            KEY, TITLE,
            "nenhuma variavel auxiliar adequada: krigagem dos resíduos não convergiu",
        )

    sel_rows.sort(key=lambda mm: _rank_value(mm, sel_metric if sel_metric in mm else "rmse"))
    best_model = str(sel_rows[0]["model"])

    # ---- 4/5. VC combinada leave-one-out da estimativa final --------- #
    if n_obs > 250:
        folds_final = _kfold(n_obs, 10, seed)
        cv_kind = "10-fold"
    else:
        folds_final = [np.array([i]) for i in range(n_obs)]
        cv_kind = "leave-one-out"
    pred_cv = _combined_cv(mx, my, z, av, best_model, folds_final)
    cv_ok = np.isfinite(pred_cv)
    if cv_ok.sum() < n_obs * 0.6:
        return StepResult.skipped(
            KEY, TITLE,
            "nenhuma variavel auxiliar adequada: validação cruzada não convergiu",
        )
    cv = _metrics(z[cv_ok], pred_cv[cv_ok])

    # ---- krigagem ordinária dos resíduos (ajuste completo) ---------- #
    from pykrige.ok import OrdinaryKriging

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        okr_full = OrdinaryKriging(
            mx, my, resid, variogram_model=best_model, enable_plotting=False,
        )
        gx, gy = ctx.make_grid()
        rgrid, vgrid = okr_full.execute("grid", gx, gy)

    # pykrige: [psill, range, nugget] para spherical/exponential/gaussian
    vp = list(np.asarray(okr_full.variogram_model_parameters, float).ravel())
    if len(vp) >= 3:
        psill, vrange, nugget = vp[0], vp[1], vp[2]
    elif len(vp) == 2:
        psill, vrange, nugget = vp[0], vp[1], 0.0
    else:
        psill, vrange, nugget = float("nan"), float("nan"), float("nan")
    sill_total = psill + nugget if np.isfinite(psill) and np.isfinite(nugget) else float("nan")

    # ---- grade: tendência + resíduo krigado -> estimativa final ----- #
    aux_grid = _idw_grid(mx, my, av, gx, gy, power=idw_power, k=idw_neigh)
    trend_grid = intercept + coef * aux_grid
    resid_grid = np.asarray(rgrid, float)
    se_grid = np.sqrt(np.maximum(np.asarray(vgrid, float), 0.0))
    final_grid = trend_grid + resid_grid

    # ---- tabela ----------------------------------------------------------- #
    tbl = pd.DataFrame([{
        "R² regressão": round(r2_reg, 4),
        "r": round(r_corr, 4),
        "nugget": round(float(nugget), 4),
        "sill": round(float(sill_total), 4),
        "range (resíduos)": round(float(vrange), 2),
        "ME": round(cv["me"], 4),
        "MAE": round(cv["mae"], 4),
        "RMSE": round(cv["rmse"], 4),
        "R² (CV)": round(cv["r2"], 4),
    }])
    tables = [TableResult(
        name="external_drift",
        df=tbl,
        title=TITLE,
        caption=(
            f"Regressão-krigagem de {primary} sobre {aux}. Modelo de variograma "
            f"dos resíduos: {best_model}. Validação cruzada {cv_kind} "
            f"(n = {int(cv_ok.sum())})."
        ),
        highlight_rows=[0],
    )]

    if len(sel_rows) > 1:
        sel_df = pd.DataFrame([{
            "modelo": r["model"],
            "ME": round(r["me"], 4),
            "MAE": round(r["mae"], 4),
            "RMSE": round(r["rmse"], 4),
            "R²": round(r["r2"], 4),
        } for r in sel_rows])
        tables.append(TableResult(
            name="external_drift_modelos",
            df=sel_df,
            title="Seleção do modelo de variograma (resíduos)",
            caption=(
                f"Validação cruzada 5-fold da estimativa combinada. Seleção pelo "
                f"critério {sel_metric.upper()}; melhor modelo em destaque."
            ),
            highlight_rows=[0],
        ))

    # ---- figuras -------------------------------------------------------- #
    figures = []
    sv = ctx.values(primary)
    figures.append(renderer.render_surface(
        ctx, trend_grid, gx, gy,
        name="external_drift_tendencia",
        title=f"Tendência da regressão — {primary} ~ {aux}",
        method=f"Regressão OLS sobre {aux}",
        cbar_label=f"{primary} ({units})",
        sample_values=sv,
        caption=(
            f"Componente determinística: {intercept:.3g} + {coef:.3g}·{aux} "
            f"(R² = {r2_reg:.3f})."
        ),
    ))
    figures.append(renderer.render_surface(
        ctx, final_grid, gx, gy,
        name="external_drift_estimativa",
        title=f"Estimativa final — krigagem com deriva externa ({primary})",
        method=f"Regressão-krigagem (variograma {best_model})",
        cbar_label=f"{primary} ({units})",
        sample_values=sv,
        caption="Tendência da regressão somada à krigagem ordinária dos resíduos.",
    ))
    figures.append(renderer.render_surface(
        ctx, se_grid, gx, gy,
        name="external_drift_erro_padrao",
        title="Erro-padrão da krigagem dos resíduos",
        method=f"Desvio-padrão da krigagem ordinária (variograma {best_model})",
        cbar_label=f"desvio-padrão ({units})",
        caption="Incerteza do componente estocástico (resíduos); maior longe das amostras.",
    ))
    figures.append(renderer.render_surface(
        ctx, resid_grid, gx, gy,
        name="external_drift_residuos",
        title="Resíduos da regressão (krigados)",
        method=f"Krigagem ordinária dos resíduos (variograma {best_model})",
        cbar_label=f"resíduo ({units})",
        diverging=True,
        caption="Estrutura espacial não explicada pela variável auxiliar.",
    ))

    import matplotlib.pyplot as plt

    obs = z[cv_ok]
    prd = pred_cv[cv_ok]
    fig, ax = plt.subplots(figsize=(6.2, 6.0))
    lo = float(min(obs.min(), prd.min()))
    hi = float(max(obs.max(), prd.max()))
    ax.plot([lo, hi], [lo, hi], color="#888888", ls="--", lw=1.0, label="1:1")
    ax.scatter(obs, prd, s=20, alpha=0.75, color="#2c7fb8",
               edgecolors="black", linewidths=0.3, label="pontos")
    ax.set_xlabel(f"{primary} observado ({units})")
    ax.set_ylabel(f"{primary} previsto — VC ({units})")
    ax.set_title("Observado vs. previsto — deriva externa")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)
    ax.text(0.97, 0.03, f"RMSE = {cv['rmse']:.3g}\nR² = {cv['r2']:.3f}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
            bbox={"boxstyle": "round", "fc": "white", "ec": "#cccccc"})
    figures.append(ctx.save_fig(
        fig, "external_drift_obs_prev", subdir="figures",
        title="Observado vs. previsto (validação cruzada)",
        caption=f"Validação cruzada {cv_kind} da estimativa combinada.",
        kind="chart",
    ))

    # ---- interpretação + metrics -------------------------------------- #
    interpretation = interpret.interpret_external_drift(
        primary, aux, r_corr, r2_reg,
        {"rmse": cv["rmse"], "mae": cv["mae"], "r2": cv["r2"]},
    )
    if not interpret.is_sig(p_slope, ctx.alpha):
        interpretation += (
            f" Observação: o coeficiente de {aux} {interpret.sig_clause(p_slope, ctx.alpha)}."
        )

    metrics = {
        "aux": aux,
        "r_corr": round(r_corr, 4),
        "r2_reg": round(r2_reg, 4),
        "cv": {
            "rmse": round(cv["rmse"], 4),
            "mae": round(cv["mae"], 4),
            "me": round(cv["me"], 4),
            "r2": round(cv["r2"], 4),
        },
        "variogram_model": best_model,
        "variogram": {
            "nugget": round(float(nugget), 4),
            "sill": round(float(sill_total), 4),
            "range": round(float(vrange), 2),
        },
        "regression": {
            "intercept": round(intercept, 4),
            "slope": round(coef, 4),
            "p_slope": p_slope,
        },
        "n_obs": n_obs,
        "cv_kind": cv_kind,
    }

    params_used = {
        "aux_drift": aux,
        "drift_min_corr": float(ctx.param("drift_min_corr", 0.3)),
        "variogram_model": best_model,
        "variogram_candidates": candidates,
        "selection_metric": sel_metric,
        "idw_power_grid": idw_power,
        "idw_neighbors_grid": idw_neigh,
        "grid_resolution": int(ctx.param("grid_resolution", 80)),
        "random_seed": seed,
    }

    return StepResult(
        key=KEY, title=TITLE, status="ok",
        tables=tables, figures=figures, metrics=metrics,
        interpretation=interpretation, params_used=params_used,
    )
