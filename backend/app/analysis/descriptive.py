"""Estatística descritiva das variáveis de análise (seção 8).

Para cada variável em ``ctx.analysis_variables`` calcula medidas de posição,
dispersão e forma, monta uma tabela única e painéis gráficos (histograma+KDE,
boxplot e ECDF). A interpretação textual vem de ``app.analysis.interpret``.
"""
from __future__ import annotations

import warnings
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from app.analysis import interpret
from app.analysis.base import AnalysisContext, StepResult, TableResult

KEY = "descriptive"
TITLE = "Estatística Descritiva"

_PERCENTIS = [5, 10, 25, 50, 75, 90, 95]
_MAX_FIGS = 6


def applicable(ctx: AnalysisContext) -> tuple[bool, str]:
    """Aplicável sempre que houver ao menos uma variável numérica."""
    for name in ctx.analysis_variables:
        v = ctx.values(name)
        if np.isfinite(v).sum() >= 1:
            return True, ""
    return False, "Nenhuma variável numérica disponível para descrição."


def _stats(v: np.ndarray) -> dict[str, float]:
    z = v[np.isfinite(v)]
    n = int(z.size)
    out: dict[str, float] = {"n": n}
    if n == 0:
        return out
    mean = float(np.mean(z))
    std = float(np.std(z, ddof=1)) if n > 1 else float("nan")
    var = float(np.var(z, ddof=1)) if n > 1 else float("nan")
    vmin, vmax = float(np.min(z)), float(np.max(z))
    try:
        moda = float(stats.mode(z, keepdims=False).mode)
    except Exception:  # noqa: BLE001
        moda = float("nan")
    q1, med, q3 = (float(x) for x in np.percentile(z, [25, 50, 75]))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        skew = float(stats.skew(z, bias=False)) if n > 2 else float("nan")
        kurt = float(stats.kurtosis(z, fisher=True, bias=False)) if n > 3 else float("nan")
    cv = float(std / mean * 100.0) if mean not in (0.0,) and np.isfinite(std) else float("nan")
    out.update(
        {
            "media": mean,
            "mediana": med,
            "moda": moda,
            "min": vmin,
            "max": vmax,
            "amplitude": vmax - vmin,
            "variancia": var,
            "desvio_padrao": std,
            "cv_pct": cv,
            "Q1": q1,
            "Q3": q3,
            "IQR": q3 - q1,
            "assimetria": skew,
            "curtose": kurt,
        }
    )
    for p in _PERCENTIS:
        out[f"P{p}"] = float(np.percentile(z, p))
    return out


def _row(name: str, s: dict[str, float]) -> dict[str, Any]:
    return {
        "variavel": name,
        "n": s.get("n", 0),
        "media": s.get("media"),
        "mediana": s.get("mediana"),
        "moda": s.get("moda"),
        "min": s.get("min"),
        "max": s.get("max"),
        "amplitude": s.get("amplitude"),
        "variancia": s.get("variancia"),
        "desvio_padrao": s.get("desvio_padrao"),
        "cv_pct": s.get("cv_pct"),
        "Q1": s.get("Q1"),
        "Q3": s.get("Q3"),
        "IQR": s.get("IQR"),
        "assimetria": s.get("assimetria"),
        "curtose": s.get("curtose"),
        **{f"P{p}": s.get(f"P{p}") for p in _PERCENTIS},
    }


def _interpret_stats(s: dict[str, float]) -> dict[str, float]:
    """Chaves esperadas por interpret.interpret_descriptive."""
    return {
        "mean": s.get("media"),
        "median": s.get("mediana"),
        "std": s.get("desvio_padrao"),
        "cv": s.get("cv_pct"),
        "skewness": s.get("assimetria"),
        "kurtosis": s.get("curtose"),
        "min": s.get("min"),
        "max": s.get("max"),
        "n": s.get("n"),
    }


def _panel(ctx: AnalysisContext, name: str, v: np.ndarray, idx: int):
    z = v[np.isfinite(v)]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    fig.suptitle(f"Distribuição — {name}", fontsize=12)

    ax = axes[0]
    ax.hist(z, bins="auto", density=True, color="#4c72b0", alpha=0.65, edgecolor="white")
    if z.size > 1 and np.ptp(z) > 0:
        try:
            kde = stats.gaussian_kde(z)
            xs = np.linspace(z.min(), z.max(), 200)
            ax.plot(xs, kde(xs), color="#1a1a1a", lw=1.5, label="KDE")
            ax.legend(frameon=False, fontsize=8)
        except Exception:  # noqa: BLE001
            pass
    ax.set_title("Histograma + KDE", fontsize=10)
    ax.set_xlabel(ctx.units or "valor")
    ax.set_ylabel("densidade")
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.boxplot(z, vert=True, widths=0.5, patch_artist=True,
               boxprops=dict(facecolor="#dce6f2", edgecolor="#4c72b0"),
               medianprops=dict(color="#c44e52"))
    ax.set_title("Boxplot", fontsize=10)
    ax.set_ylabel(ctx.units or "valor")
    ax.set_xticks([])
    ax.grid(alpha=0.3)

    ax = axes[2]
    xs = np.sort(z)
    ys = np.arange(1, xs.size + 1) / xs.size
    ax.step(xs, ys, where="post", color="#4c72b0", lw=1.5)
    ax.set_title("ECDF", fontsize=10)
    ax.set_xlabel(ctx.units or "valor")
    ax.set_ylabel("proporção acumulada")
    ax.grid(alpha=0.3)

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return ctx.save_fig(
        fig,
        f"descriptive_{idx:02d}_{name}",
        subdir="figures",
        title=f"Distribuição de {name}",
        caption="Histograma com KDE, boxplot e função de distribuição acumulada empírica.",
        kind="chart",
    )


def run(ctx: AnalysisContext) -> StepResult:
    """Executa a estatística descritiva (seção 8)."""
    variables = ctx.analysis_variables
    if not variables:
        return StepResult.skipped(KEY, TITLE, "Nenhuma variável de análise definida.")

    rows: list[dict[str, Any]] = []
    metrics_vars: dict[str, dict[str, Any]] = {}
    interp_cache: dict[str, dict[str, float]] = {}
    valid: list[str] = []

    for name in variables:
        v = ctx.values(name)
        s = _stats(v)
        if s.get("n", 0) == 0:
            continue
        valid.append(name)
        rows.append(_row(name, s))
        interp_cache[name] = _interpret_stats(s)
        metrics_vars[name] = {
            "mean": s.get("media"),
            "median": s.get("mediana"),
            "std": s.get("desvio_padrao"),
            "cv": s.get("cv_pct"),
            "skewness": s.get("assimetria"),
            "kurtosis": s.get("curtose"),
            "min": s.get("min"),
            "max": s.get("max"),
            "n": s.get("n"),
        }

    if not rows:
        return StepResult.skipped(KEY, TITLE, "Nenhuma variável com dados finitos.")

    df = pd.DataFrame(rows)
    table = TableResult(
        name="estatistica_descritiva",
        df=df,
        title="Estatística Descritiva",
        caption="Uma linha por variável de análise. CV em %; percentis Pk.",
    )

    figures = []
    for i, name in enumerate(valid[:_MAX_FIGS]):
        try:
            figures.append(_panel(ctx, name, ctx.values(name), i + 1))
        except Exception as exc:  # noqa: BLE001
            ctx.logger.warning("Falha ao gerar painel de %s: %s", name, exc)

    parts = [
        interpret.interpret_descriptive(name, interp_cache[name], ctx.units)
        for name in valid[:3]
    ]
    interpretation = " ".join(parts) if parts else None

    return StepResult(
        key=KEY,
        title=TITLE,
        status="ok",
        tables=[table],
        figures=figures,
        metrics={"variables": metrics_vars},
        interpretation=interpretation,
        params_used={"percentis": _PERCENTIS, "max_figuras": _MAX_FIGS},
    )
