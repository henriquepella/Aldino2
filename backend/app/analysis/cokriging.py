"""Co-Krigagem colocada — Markov Model I (seção 22).

Implementa uma aproximação prática da co-krigagem colocada sob a hipótese de
Markov Model I (a variável secundária colocada "blinda" a informação dos demais
pontos da secundária). Nessa hipótese a co-krigagem colocada é aproximadamente
equivalente a:

    1. regressão linear  z_p ~ a + b · z_s   (mínimos quadrados);
    2. krigagem ordinária do resíduo  r = z_p - (a + b · z_s);
    3. estimativa final  ẑ_p(u) = a + b · z_s(u) + OK[r](u),

com ``z_s(u)`` obtido por krigagem ordinária da secundária na grade. Esta é uma
APROXIMAÇÃO — não resolve o sistema de co-krigagem completo com o modelo linear
de corregionalização — mas reproduz o comportamento do Markov I com custo baixo
e é robusta para conjuntos pequenos.

Contrato: KEY, TITLE, applicable(ctx), run(ctx) -> StepResult.
"""
from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd

from app.analysis import interpret
from app.analysis.base import AnalysisContext, StepResult, TableResult
from app.maps import renderer

KEY = "cokriging"
TITLE = "Co-Krigagem"

_VALID_MODELS = ("linear", "power", "gaussian", "spherical", "exponential", "hole-effect")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _model(ctx: AnalysisContext) -> str:
    m = ctx.param("variogram_model_override") or "spherical"
    return m if m in _VALID_MODELS else "spherical"


def _common_mask(ctx: AnalysisContext, a: str, b: str) -> np.ndarray:
    return (
        np.isfinite(ctx.mx)
        & np.isfinite(ctx.my)
        & np.isfinite(ctx.values(a))
        & np.isfinite(ctx.values(b))
    )


def _best_secondary(ctx: AnalysisContext) -> tuple[str | None, float]:
    """Secundária (!= principal) de maior |r| de Pearson com a principal."""
    from scipy.stats import pearsonr

    best_name: str | None = None
    best_r = np.nan
    zp_all = ctx.values(ctx.primary)
    for name in ctx.secondary:
        if not name or name == ctx.primary or name not in ctx.df.columns:
            continue
        zs_all = ctx.values(name)
        m = np.isfinite(zp_all) & np.isfinite(zs_all)
        if int(m.sum()) < 5 or np.nanstd(zs_all[m]) == 0:
            continue
        r = float(pearsonr(zp_all[m], zs_all[m])[0])
        if not np.isfinite(best_r) or abs(r) > abs(best_r):
            best_name, best_r = name, r
    return best_name, best_r


def _metrics(obs: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    obs = np.asarray(obs, float)
    pred = np.asarray(pred, float)
    m = np.isfinite(obs) & np.isfinite(pred)
    obs, pred = obs[m], pred[m]
    if len(obs) < 3:
        return {k: float("nan") for k in ("me", "mae", "mse", "rmse", "r2")}
    err = pred - obs
    mse = float(np.mean(err ** 2))
    ss_tot = float(np.sum((obs - obs.mean()) ** 2))
    return {
        "me": float(np.mean(err)),
        "mae": float(np.mean(np.abs(err))),
        "mse": mse,
        "rmse": float(np.sqrt(mse)),
        "r2": float(1.0 - np.sum(err ** 2) / ss_tot) if ss_tot > 0 else float("nan"),
    }


def _cv_splits(n: int, seed: int):
    """LOO por padrão; k-fold(10) determinístico se n > 250 (seção 15)."""
    if n > 250:
        rng = np.random.default_rng(seed)
        for fold in np.array_split(rng.permutation(n), 10):
            te = np.zeros(n, bool)
            te[fold] = True
            yield ~te, te
    else:
        for i in range(n):
            te = np.zeros(n, bool)
            te[i] = True
            yield ~te, te


def _ok(mx, my, z, model: str, nlags: int):
    from pykrige.ok import OrdinaryKriging

    return OrdinaryKriging(
        mx, my, z, variogram_model=model, nlags=nlags,
        enable_plotting=False, coordinates_type="euclidean",
    )


def _sill(ok) -> float:
    """Patamar total (psill + nugget) do modelo ajustado."""
    p = list(ok.variogram_model_parameters)
    try:
        if ok.variogram_model in ("linear", "power"):
            return float("nan")
        return float(p[0] + p[2])
    except Exception:  # noqa: BLE001
        return float("nan")


# --------------------------------------------------------------------------- #
# Contrato
# --------------------------------------------------------------------------- #
def applicable(ctx: AnalysisContext) -> tuple[bool, str]:
    thr = float(ctx.param("cok_min_corr", 0.4))
    name, r = _best_secondary(ctx)
    if name is None:
        return False, "Nenhuma variável secundária numérica com variância disponível."
    if not np.isfinite(r) or abs(r) < thr:
        return False, (
            f"A secundária de maior correlação ({name}) tem |r| = "
            f"{interpret.num(abs(r), 3)} com {ctx.primary} (r = {interpret.num(r, 3)}), "
            f"abaixo do mínimo exigido de {interpret.num(thr, 2)}."
        )
    return True, ""


def run(ctx: AnalysisContext) -> StepResult:
    ok_flag, reason = applicable(ctx)
    if not ok_flag:
        return StepResult.skipped(KEY, TITLE, reason)

    from scipy.stats import pearsonr

    primary = ctx.primary
    secondary, _ = _best_secondary(ctx)
    assert secondary is not None
    model = _model(ctx)
    nlags = int(ctx.param("variogram_bins", 15))
    sel_metric = str(ctx.param("selection_metric", "rmse"))

    mask = _common_mask(ctx, primary, secondary)
    mx, my = ctx.mx[mask], ctx.my[mask]
    zp, zs = ctx.values(primary)[mask], ctx.values(secondary)[mask]
    n = len(zp)
    if n < 15:
        return StepResult.skipped(
            KEY, TITLE, f"Apenas {n} pares completos ({primary}, {secondary}) — insuficiente."
        )

    r_corr = float(pearsonr(zp, zs)[0])

    params_used = {
        "secondary": secondary,
        "variogram_model": model,
        "variogram_bins": nlags,
        "cok_min_corr": float(ctx.param("cok_min_corr", 0.4)),
        "selection_metric": sel_metric,
        "cv": "kfold10" if n > 250 else "loo",
        "grid_resolution": int(ctx.param("grid_resolution", 80)),
        "approach": "colocada / Markov Model I (aproximação por regressão + OK do resíduo)",
    }

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # ---- variogramas de referência (ajuste global) ------------------- #
        try:
            ok_p = _ok(mx, my, zp, model, nlags)
            ok_s = _ok(mx, my, zs, model, nlags)
            sill_p, sill_s = _sill(ok_p), _sill(ok_s)
        except Exception as exc:  # noqa: BLE001
            return StepResult.skipped(KEY, TITLE, f"Falha no ajuste do variograma: {exc}")

        # ---- validação cruzada ----------------------------------------- #
        pred_ck = np.full(n, np.nan)
        pred_ok = np.full(n, np.nan)
        for tr, te in _cv_splits(n, ctx.random_seed):
            xi, yi = mx[te], my[te]
            try:
                b, a = np.polyfit(zs[tr], zp[tr], 1)
                resid = zp[tr] - (a + b * zs[tr])
                okr = _ok(mx[tr], my[tr], resid, model, nlags)
                rk, _ = okr.execute("points", xi, yi)
                pred_ck[te] = a + b * zs[te] + np.asarray(rk, float)
            except Exception:  # noqa: BLE001
                pass
            try:
                okp = _ok(mx[tr], my[tr], zp[tr], model, nlags)
                pk, _ = okp.execute("points", xi, yi)
                pred_ok[te] = np.asarray(pk, float)
            except Exception:  # noqa: BLE001
                pass

        cv_ck = _metrics(zp, pred_ck)
        cv_ok = _metrics(zp, pred_ok)
        if not np.isfinite(cv_ck["rmse"]):
            return StepResult.skipped(
                KEY, TITLE, "A validação cruzada da co-krigagem não convergiu."
            )

        # ---- superfície completa -------------------------------------- #
        gx, gy = ctx.make_grid()
        Z_ck = SD = None
        try:
            b, a = np.polyfit(zs, zp, 1)
            resid_full = zp - (a + b * zs)
            ok_sg = _ok(mx, my, zs, model, nlags)
            Zs, _ = ok_sg.execute("grid", gx, gy)
            ok_rg = _ok(mx, my, resid_full, model, nlags)
            Zr, SSr = ok_rg.execute("grid", gx, gy)
            Z_ck = a + b * np.ma.filled(Zs, np.nan) + np.ma.filled(Zr, np.nan)
            SD = np.sqrt(np.clip(np.ma.filled(SSr, np.nan), 0, None))
        except Exception:  # noqa: BLE001
            Z_ck = SD = None

    # ---- tabela ------------------------------------------------------- #
    rows: list[tuple[str, float, float]] = [
        ("RMSE", cv_ck["rmse"], cv_ok["rmse"]),
        ("MAE", cv_ck["mae"], cv_ok["mae"]),
        ("ME (viés)", cv_ck["me"], cv_ok["me"]),
        ("R²", cv_ck["r2"], cv_ok["r2"]),
        (f"Correlação r ({primary} × {secondary})", r_corr, np.nan),
        (f"Patamar variograma — {primary}", sill_p, np.nan),
        (f"Patamar variograma — {secondary}", sill_s, np.nan),
    ]
    df = pd.DataFrame(rows, columns=["Item", "Co-Krigagem", "Krigagem Ordinária"])
    better = np.isfinite(cv_ck["rmse"]) and np.isfinite(cv_ok["rmse"]) and cv_ck["rmse"] < cv_ok["rmse"]
    table = TableResult(
        name="cokriging_comparacao",
        df=df,
        title="Co-Krigagem × Krigagem Ordinária (validação cruzada)",
        caption=(
            "Métricas de validação cruzada nas mesmas partições. "
            "Co-krigagem colocada sob Markov Model I (aproximação). "
            + ("Co-krigagem com menor RMSE." if better else "Krigagem ordinária com RMSE menor ou igual.")
        ),
        highlight_rows=[0],
    )

    # ---- figuras ---------------------------------------------------------- #
    figures = []
    zp_all = ctx.values(primary)
    if Z_ck is not None and np.isfinite(Z_ck).any():
        figures.append(renderer.render_surface(
            ctx, Z_ck, gx, gy,
            name="cokriging_predicao",
            title=f"Co-Krigagem colocada — {primary}",
            method="Co-krigagem colocada (Markov Model I, aproximação)",
            cbar_label=f"{primary} ({ctx.units})" if ctx.units else primary,
            sample_values=zp_all,
            caption=f"Estimativa a + b·{secondary}(u) + OK do resíduo.",
        ))
    if SD is not None and np.isfinite(SD).any():
        figures.append(renderer.render_surface(
            ctx, SD, gx, gy,
            name="cokriging_incerteza",
            title=f"Incerteza da co-krigagem — {primary}",
            method="Desvio-padrão de krigagem do resíduo (aproximação)",
            cbar_label="desvio-padrão",
            caption="Aproximação da incerteza pela variância de krigagem do resíduo.",
        ))
    figures.append(_fig_scatter(ctx, zs, zp, secondary, primary, r_corr))
    figures.append(_fig_cv(ctx, zp, pred_ck, pred_ok))

    metrics: dict[str, Any] = {
        "secondary": secondary,
        "r": r_corr,
        "sill_primary": sill_p,
        "sill_secondary": sill_s,
        "cv_ck": {k: cv_ck[k] for k in ("rmse", "mae", "me", "r2")},
        "cv_ok": {k: cv_ok[k] for k in ("rmse", "mae", "me", "r2")},
        "n_pairs": int(n),
    }

    interpretation = interpret.interpret_cokriging(primary, secondary, r_corr, cv_ck, cv_ok)
    interpretation += (
        " Observação metodológica: trata-se de uma aproximação da co-krigagem "
        "colocada sob Markov Model I (regressão linear com a secundária + krigagem "
        "ordinária do resíduo), não da solução do sistema de co-krigagem completo."
    )

    return StepResult(
        key=KEY, title=TITLE, status="ok",
        tables=[table], figures=figures, metrics=metrics,
        interpretation=interpretation, params_used=params_used,
    )


# --------------------------------------------------------------------------- #
# Figuras auxiliares
# --------------------------------------------------------------------------- #
def _fig_scatter(ctx, zs, zp, s_name, p_name, r_corr):
    import matplotlib.pyplot as plt

    b, a = np.polyfit(zs, zp, 1)
    xs = np.linspace(float(np.min(zs)), float(np.max(zs)), 100)
    fig, ax = plt.subplots(figsize=(6.4, 5.0))
    ax.scatter(zs, zp, s=24, color="#3b6ea5", edgecolors="white", linewidths=0.4,
               alpha=0.85, label="Amostras")
    ax.plot(xs, a + b * xs, color="#b2182b", lw=1.8,
            label=f"Reta: {interpret.num(a, 2)} + {interpret.num(b, 3)}·{s_name}")
    ax.set_xlabel(f"{s_name} ({ctx.units})" if ctx.units else s_name)
    ax.set_ylabel(f"{p_name} ({ctx.units})" if ctx.units else p_name)
    ax.set_title(f"{p_name} × {s_name}  (r = {interpret.num(r_corr, 3)})",
                 fontsize=11, fontweight="bold")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    return ctx.save_fig(
        fig, "cokriging_scatter",
        title=f"Dispersão {p_name} × {s_name}",
        caption="Regressão linear usada na etapa de deriva da co-krigagem colocada.",
        kind="chart",
    )


def _fig_cv(ctx, obs, pred_ck, pred_ok):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 5.0))
    finite = np.isfinite(obs)
    lo = float(np.nanmin(obs[finite]))
    hi = float(np.nanmax(obs[finite]))
    ax.plot([lo, hi], [lo, hi], color="#666666", lw=1.2, ls="--", label="1:1")
    ax.scatter(obs, pred_ok, s=22, color="#9970ab", edgecolors="white",
               linewidths=0.3, alpha=0.8, label="Krigagem ordinária")
    ax.scatter(obs, pred_ck, s=22, color="#1b7837", edgecolors="white",
               linewidths=0.3, alpha=0.8, label="Co-krigagem")
    ax.set_xlabel(f"Observado ({ctx.units})" if ctx.units else "Observado")
    ax.set_ylabel(f"Previsto ({ctx.units})" if ctx.units else "Previsto")
    ax.set_title("Validação cruzada: observado × previsto", fontsize=11, fontweight="bold")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    return ctx.save_fig(
        fig, "cokriging_cv_obs_prev",
        title="Validação cruzada — observado × previsto",
        caption="Pontos mais próximos da reta 1:1 indicam melhor desempenho.",
        kind="chart",
    )
