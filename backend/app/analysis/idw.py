"""IDW — Inverse Distance Weighting (seções 13-14).

Interpolação por ponderação do inverso da distância implementada com
``scipy.spatial.cKDTree``: potência ``p`` e ``k`` vizinhos mais próximos.
Quando a distância é nula (ponto coincidente com a amostra) o valor observado
é usado diretamente.

A potência e o número de vizinhos são escolhidos por validação cruzada
(leave-one-out; 10-fold quando ``n > 250``) segundo ``selection_metric``.
"""
from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd

from app.analysis import interpret
from app.analysis.base import AnalysisContext, StepResult, TableResult
from app.maps import renderer

KEY = "idw"
TITLE = "IDW — Inverse Distance Weighting"

_MIN_POINTS = 10


# --------------------------------------------------------------------------- #
# Núcleo IDW
# --------------------------------------------------------------------------- #
def _idw_predict(
    src_xy: np.ndarray,
    src_z: np.ndarray,
    dst_xy: np.ndarray,
    power: float,
    k: int,
    *,
    tree: Any = None,
    skip_first: bool = False,
) -> np.ndarray:
    """Estima valores em ``dst_xy`` a partir das amostras ``src_xy/src_z``.

    ``skip_first=True`` descarta o vizinho mais próximo de cada consulta (usado
    na validação leave-one-out, em que a consulta é a própria amostra).
    """
    from scipy.spatial import cKDTree

    if tree is None:
        tree = cKDTree(src_xy)
    n_src = len(src_z)
    want = int(k) + (1 if skip_first else 0)
    kq = max(1, min(want, n_src))
    dist, idx = tree.query(dst_xy, k=kq)
    if kq == 1:
        dist = dist[:, None]
        idx = idx[:, None]
    if skip_first and dist.shape[1] > 1:
        dist = dist[:, 1:]
        idx = idx[:, 1:]

    out = np.empty(len(dst_xy), dtype=float)
    for i in range(len(dst_xy)):
        d = np.asarray(dist[i], dtype=float)
        ii = np.asarray(idx[i], dtype=int)
        zero = d <= 1e-9
        if zero.any():
            out[i] = float(np.mean(src_z[ii[zero]]))
            continue
        w = 1.0 / np.power(d, power)
        out[i] = float(np.sum(w * src_z[ii]) / np.sum(w))
    return out


def _metrics(obs: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    err = pred - obs
    mse = float(np.mean(err ** 2))
    ss_tot = float(np.sum((obs - obs.mean()) ** 2))
    ss_res = float(np.sum(err ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {
        "me": float(np.mean(err)),
        "mae": float(np.mean(np.abs(err))),
        "mse": mse,
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2),
    }


def _cv_predict(
    xy: np.ndarray, z: np.ndarray, power: float, k: int, seed: int
) -> np.ndarray:
    """Predição fora-da-amostra alinhada a ``z`` (LOO ou 10-fold se n>250)."""
    from scipy.spatial import cKDTree

    n = len(z)
    k = max(1, min(int(k), n - 1))
    if n > 250:
        rng = np.random.default_rng(seed)
        folds = np.array_split(rng.permutation(n), 10)
        pred = np.empty(n, dtype=float)
        for f in folds:
            train = np.ones(n, dtype=bool)
            train[f] = False
            pred[f] = _idw_predict(xy[train], z[train], xy[f], power, k)
        return pred
    tree = cKDTree(xy)
    return _idw_predict(xy, z, xy, power, k, tree=tree, skip_first=True)


# --------------------------------------------------------------------------- #
# Parâmetros
# --------------------------------------------------------------------------- #
def _as_float_list(v: Any, fallback: list[float]) -> list[float]:
    try:
        out = [float(x) for x in v]
        return out or fallback
    except (TypeError, ValueError):
        return fallback


def _as_int_list(v: Any, fallback: list[int]) -> list[int]:
    try:
        out = [int(x) for x in v]
        return out or fallback
    except (TypeError, ValueError):
        return fallback


def _lower_is_better(metric: str) -> bool:
    return metric.lower() not in ("r2", "r²")


def _score(m: dict[str, float], metric: str) -> float:
    key = "r2" if metric.lower() in ("r2", "r²") else metric.lower()
    val = m.get(key, m.get("rmse"))
    if val is None or not np.isfinite(val):
        return np.inf
    return -val if not _lower_is_better(metric) else float(val)


# --------------------------------------------------------------------------- #
# Contrato
# --------------------------------------------------------------------------- #
def applicable(ctx: AnalysisContext) -> tuple[bool, str]:
    if not ctx.primary or ctx.primary not in ctx.df.columns:
        return False, "Variável principal não definida."
    _, _, z = ctx.clean_xyz(ctx.primary)
    if z.size < _MIN_POINTS:
        return False, (
            f"Apenas {z.size} amostras válidas de {ctx.primary}; "
            f"são necessárias pelo menos {_MIN_POINTS} para o IDW."
        )
    if float(np.nanstd(z)) == 0.0:
        return False, f"A variável {ctx.primary} é constante — interpolação não informativa."
    return True, ""


def run(ctx: AnalysisContext) -> StepResult:
    ok, reason = applicable(ctx)
    if not ok:
        return StepResult.skipped(KEY, TITLE, reason)

    mx, my, z = ctx.clean_xyz(ctx.primary)
    xy = np.c_[mx, my]
    n = len(z)
    seed = ctx.random_seed
    metric = str(ctx.param("selection_metric", "rmse")).lower()

    powers = _as_float_list(ctx.param("idw_power_grid", [1, 1.5, 2, 2.5, 3]),
                            [1.0, 1.5, 2.0, 2.5, 3.0])
    neighbors = _as_int_list(ctx.param("idw_neighbors_grid", [6, 12, 18]), [6, 12, 18])
    neighbors = sorted({max(1, min(k, n - 1)) for k in neighbors})

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        grid: list[dict[str, Any]] = []
        for p in powers:
            for k in neighbors:
                pred = _cv_predict(xy, z, p, k, seed)
                m = _metrics(z, pred)
                grid.append({"power": float(p), "neighbors": int(k), **m})

    if not grid:
        return StepResult.skipped(KEY, TITLE, "Não foi possível avaliar combinações de IDW.")

    best = min(grid, key=lambda r: _score(r, metric))
    best_out = {
        "power": best["power"], "neighbors": best["neighbors"],
        "rmse": best["rmse"], "mae": best["mae"],
        "me": best["me"], "r2": best["r2"],
    }

    # ---- Tabela 1: validação cruzada (ordenada por RMSE) -------------------- #
    df_cv = pd.DataFrame(grid).sort_values("rmse", kind="stable").reset_index(drop=True)
    tbl = pd.DataFrame({
        "Power": df_cv["power"],
        "Vizinhos": df_cv["neighbors"].astype(int),
        "ME": df_cv["me"],
        "MAE": df_cv["mae"],
        "RMSE": df_cv["rmse"],
        "R²": df_cv["r2"],
    })
    hi = int(
        df_cv.index[
            (df_cv["power"] == best["power"]) & (df_cv["neighbors"] == best["neighbors"])
        ][0]
    )
    table1 = TableResult(
        name="idw_validacao_cruzada",
        df=tbl,
        title="IDW — Validação Cruzada",
        caption=(
            "Métricas de validação cruzada "
            + ("leave-one-out" if n <= 250 else "10-fold")
            + f" por combinação de potência e vizinhos. Seleção pelo critério {metric.upper()}."
        ),
        highlight_rows=[hi],
    )

    # ---- Superfície interpolada (melhor config) --------------------------- #
    bp, bk = best["power"], int(best["neighbors"])
    gx, gy = ctx.make_grid()
    GX, GY = np.meshgrid(gx, gy)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        Zsurf = _idw_predict(xy, z, np.c_[GX.ravel(), GY.ravel()], bp, bk).reshape(GX.shape)

    unit = ctx.units or "valor"
    method = f"IDW (p = {interpret.num(bp, 2)}, k = {bk})"
    primary_full = ctx.values(ctx.primary)

    fig_surface = renderer.render_surface(
        ctx, Zsurf, gx, gy,
        name="idw_superficie",
        title=f"IDW — {ctx.primary}",
        method=method,
        cbar_label=f"{ctx.primary} ({unit})",
        sample_values=primary_full,
        caption=(
            f"Superfície interpolada por IDW na melhor configuração "
            f"(potência {interpret.num(bp, 2)}, {bk} vizinhos)."
        ),
    )

    fig_points = renderer.render_points(
        ctx, primary_full,
        name="idw_pontos_amostrais",
        title=f"Pontos amostrais — {ctx.primary}",
        method="Pontos amostrais",
        cbar_label=f"{ctx.primary} ({unit})",
        caption="Distribuição espacial e valores observados das amostras.",
    )

    # ---- Erro absoluto LOO por ponto ------------------------------------- #
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pred_best = _cv_predict(xy, z, bp, bk, seed)
    abs_err = np.abs(pred_best - z)

    finite_mask = (
        np.isfinite(ctx.mx) & np.isfinite(ctx.my) & np.isfinite(primary_full)
    )
    err_full = np.full(ctx.n, np.nan, dtype=float)
    err_full[finite_mask] = abs_err

    fig_error = renderer.render_points(
        ctx, err_full,
        name="idw_erro_absoluto_loo",
        title="Erro absoluto da validação cruzada (IDW)",
        method="Validação cruzada leave-one-out",
        cbar_label=f"|previsto − observado| ({unit})",
        caption="Erro absoluto de predição por ponto na validação cruzada.",
    )

    # ---- Observado x previsto (LOO) ------------------------------------- #
    import matplotlib.pyplot as plt

    r2_best = float(best["r2"])
    fig, ax = plt.subplots(figsize=(6.2, 6.0))
    lo = float(min(z.min(), pred_best.min()))
    hi_v = float(max(z.max(), pred_best.max()))
    pad = 0.05 * (hi_v - lo or 1.0)
    lims = (lo - pad, hi_v + pad)
    ax.plot(lims, lims, color="#666666", lw=1.2, ls="--", label="Reta 1:1", zorder=2)
    ax.scatter(z, pred_best, s=26, color="#3b6fb0", edgecolors="black",
               linewidths=0.3, alpha=0.85, zorder=3, label="Amostras")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(f"{ctx.primary} observado ({unit})")
    ax.set_ylabel(f"{ctx.primary} previsto — LOO ({unit})")
    ax.set_title("Observado × Previsto (IDW, validação cruzada)", fontsize=11, fontweight="bold")
    ax.grid(alpha=0.3)
    ax.text(0.04, 0.94, f"R² = {interpret.num(r2_best, 3)}\nRMSE = {interpret.num(best['rmse'])}",
            transform=ax.transAxes, va="top", ha="left", fontsize=9,
            bbox=dict(boxstyle="round", fc="white", ec="#999999", alpha=0.9))
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    fig_scatter = ctx.save_fig(
        fig, "idw_observado_previsto", subdir="figures", kind="chart",
        title="Observado × Previsto (IDW)",
        caption="Dispersão entre valores observados e previstos na validação cruzada leave-one-out.",
    )

    metrics = {
        "best": best_out,
        "grid_search": grid,
        "n_samples": int(n),
        "cv": "loo" if n <= 250 else "kfold10",
    }
    params_used = {
        "idw_power": ctx.param("idw_power", 2.0),
        "idw_neighbors": ctx.param("idw_neighbors", 12),
        "idw_power_grid": powers,
        "idw_neighbors_grid": neighbors,
        "selection_metric": metric,
        "grid_resolution": int(ctx.param("grid_resolution", 80)),
    }

    return StepResult(
        key=KEY,
        title=TITLE,
        status="ok",
        tables=[table1],
        figures=[fig_surface, fig_points, fig_error, fig_scatter],
        metrics=metrics,
        interpretation=interpret.interpret_idw_cv(best_out, metric),
        params_used=params_used,
    )
