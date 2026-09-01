"""Moran Scatter Plot (seção 11).

Para cada variável de análise: padroniza os valores, calcula a defasagem
espacial (lag) com a matriz de pesos row-standardized, ajusta a reta OLS
(cuja inclinação é igual ao I de Moran), classifica os pontos em quadrantes
(HH/LH/HL/LL) e testa a significância via permutações (``esda.Moran``).
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from app.analysis.base import AnalysisContext, StepResult, TableResult
from app.analysis.interpret import interpret_moran_scatter, num, pval
from app.analysis.weights import build_weights

KEY = "moran_scatter"
TITLE = "Moran Scatter Plot"

_MAX_VARS = 6
# ordem fixa dos quadrantes e cores (categórico)
_QUAD_ORDER = ["HH", "LH", "HL", "LL"]
_QUAD_LABELS = {
    "HH": "Alto-Alto",
    "LH": "Baixo-Alto",
    "HL": "Alto-Baixo",
    "LL": "Baixo-Baixo",
}
_QUAD_COLORS = {
    "HH": "#b2182b",
    "LH": "#92c5de",
    "HL": "#f4a582",
    "LL": "#2166ac",
}


def applicable(ctx: AnalysisContext) -> tuple[bool, str]:
    if ctx.n < 10:
        return False, f"Amostra insuficiente para autocorrelação espacial (n = {ctx.n} < 10)."
    if not ctx.analysis_variables:
        return False, "Nenhuma variável numérica disponível para análise."
    return True, ""


def _classify(z: np.ndarray, lag: np.ndarray) -> tuple[np.ndarray, dict[str, int]]:
    """Rótulo de quadrante por ponto e contagem por quadrante."""
    labels = np.empty(len(z), dtype=object)
    hi_z, hi_l = z >= 0, lag >= 0
    labels[hi_z & hi_l] = "HH"
    labels[~hi_z & hi_l] = "LH"
    labels[hi_z & ~hi_l] = "HL"
    labels[~hi_z & ~hi_l] = "LL"
    counts = {q: int(np.sum(labels == q)) for q in _QUAD_ORDER}
    return labels, counts


def _analyse_var(ctx: AnalysisContext, name: str) -> dict | None:
    v = ctx.values(name)
    m = np.isfinite(ctx.mx) & np.isfinite(ctx.my) & np.isfinite(v)
    if int(m.sum()) < 10:
        return None
    vv = v[m]
    if not np.isfinite(np.std(vv)) or np.std(vv) == 0:
        return None

    if bool(m.all()):
        w, _info = build_weights(ctx)
    else:
        w, _info = build_weights(ctx, mask=m)

    z = (vv - np.mean(vv)) / np.std(vv)

    from libpysal.weights import lag_spatial
    from esda.moran import Moran

    lag = np.asarray(lag_spatial(w, z), dtype=float)
    slope = float(np.polyfit(z, lag, 1)[0])
    labels, counts = _classify(z, lag)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mo = Moran(vv, w, permutations=ctx.n_perm)

    return {
        "name": name,
        "I": float(mo.I),
        "EI": float(mo.EI),
        "z_score": float(mo.z_sim),
        "slope": slope,
        "p": float(mo.p_sim),
        "quadrants": counts,
        "z": z,
        "lag": lag,
        "point_labels": labels,
    }


def _make_figure(ctx: AnalysisContext, res: dict):
    import matplotlib.pyplot as plt

    name = res["name"]
    z, lag, labels = res["z"], res["lag"], res["point_labels"]

    fig, ax = plt.subplots(figsize=(6.0, 5.4))
    for q in _QUAD_ORDER:
        sel = labels == q
        if not np.any(sel):
            continue
        ax.scatter(
            z[sel], lag[sel], s=26, alpha=0.8,
            color=_QUAD_COLORS[q], edgecolor="white", linewidth=0.4,
            label=f"{q} — {_QUAD_LABELS[q]} ({int(sel.sum())})",
        )

    ax.axhline(0.0, color="0.4", linewidth=0.9)
    ax.axvline(0.0, color="0.4", linewidth=0.9)

    xr = np.array([z.min(), z.max()])
    intercept = float(np.polyfit(z, lag, 1)[1])
    ax.plot(xr, res["slope"] * xr + intercept, color="0.15", linewidth=1.6,
            label=f"reta OLS (inclinação = {num(res['slope'], 3)})")

    txt = (
        f"I de Moran = {num(res['I'], 3)}\n"
        f"inclinação = {num(res['slope'], 3)}\n"
        f"{pval(res['p'])}"
    )
    ax.text(
        0.03, 0.97, txt, transform=ax.transAxes, va="top", ha="left",
        fontsize=9, bbox=dict(boxstyle="round", facecolor="white", alpha=0.85, edgecolor="0.7"),
    )

    ax.set_xlabel(f"{name} padronizado (z)")
    ax.set_ylabel(f"defasagem espacial de {name} (W·z)")
    ax.set_title(f"Moran Scatter Plot — {name}")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7.5, loc="lower right", framealpha=0.9)

    return ctx.save_fig(
        fig, f"moran_scatter_{name}", subdir="figures", kind="chart",
        title=f"Moran Scatter Plot — {name}",
        caption=(
            f"Dispersão de {name} padronizado contra sua defasagem espacial. "
            f"A inclinação da reta OLS equivale ao I de Moran ({num(res['I'], 3)})."
        ),
    )


def run(ctx: AnalysisContext) -> StepResult:
    ok, reason = applicable(ctx)
    if not ok:
        return StepResult.skipped(KEY, TITLE, reason)

    variables = ctx.analysis_variables[:_MAX_VARS]
    results: list[dict] = []
    for name in variables:
        try:
            r = _analyse_var(ctx, name)
        except Exception as exc:  # noqa: BLE001
            ctx.logger.warning("moran_scatter falhou para %s: %s", name, exc)
            r = None
        if r is not None:
            results.append(r)

    if not results:
        return StepResult.skipped(
            KEY, TITLE, "Nenhuma variável com dados suficientes e variância não nula."
        )

    figures = [_make_figure(ctx, r) for r in results]

    rows = []
    for r in results:
        q = r["quadrants"]
        dominant = max(q, key=q.get)
        rows.append({
            "Variável": r["name"],
            "Moran I": r["I"],
            "slope": r["slope"],
            "p-value": r["p"],
            "HH": q["HH"],
            "LH": q["LH"],
            "HL": q["HL"],
            "LL": q["LL"],
            "Quadrante dominante": f"{dominant} ({_QUAD_LABELS[dominant]})",
        })
    df = pd.DataFrame(rows).sort_values("Moran I", ascending=False).reset_index(drop=True)

    table = TableResult(
        name="moran_scatter_resumo",
        df=df,
        title="Moran Scatter — Resumo",
        caption=(
            "Inclinação da reta (= I de Moran), significância por permutações e "
            "distribuição dos pontos pelos quadrantes do gráfico de Moran."
        ),
    )

    principal = next((r for r in results if r["name"] == ctx.primary), results[0])
    interpretation = interpret_moran_scatter(
        principal["name"], principal["I"], principal["p"],
        principal["quadrants"], ctx.alpha,
    )

    metrics = {
        r["name"]: {
            "I": r["I"],
            "slope": r["slope"],
            "p": r["p"],
            "quadrants": r["quadrants"],
        }
        for r in results
    }

    _, winfo = build_weights(ctx)
    return StepResult(
        key=KEY,
        title=TITLE,
        status="ok",
        tables=[table],
        figures=figures,
        metrics=metrics,
        interpretation=interpretation,
        params_used={
            "n_permutations": ctx.n_perm,
            "alpha": ctx.alpha,
            "weights": winfo,
            "variables": [r["name"] for r in results],
        },
    )
