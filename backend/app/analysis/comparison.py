"""Comparação geral dos métodos de interpolação/predição (seção 23).

Este módulo não segue o contrato ``applicable``/``run`` porque depende dos
resultados de vários passos anteriores. O ``PipelineRunner`` extrai as métricas
de validação cruzada de cada método e chama :func:`build_comparison`.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.analysis.base import AnalysisContext, FigureResult, StepResult, TableResult
from app.analysis.interpret import interpret_comparison, num

KEY = "method_comparison"
TITLE = "Comparação Geral dos Métodos"

_METRIC_LABEL = {"rmse": "RMSE", "mae": "MAE", "me": "Erro médio", "r2": "R²"}


def _clean_cv(d: dict[str, Any] | None) -> dict[str, float]:
    out: dict[str, float] = {}
    for k in ("rmse", "mae", "mse", "me", "r2"):
        v = (d or {}).get(k)
        try:
            v = float(v)
            if np.isfinite(v):
                out[k] = v
        except (TypeError, ValueError):
            pass
    if "rmse" not in out and "mse" in out:
        out["rmse"] = float(np.sqrt(out["mse"]))
    return out


def build_comparison(
    ctx: AnalysisContext, method_metrics: list[dict[str, Any]]
) -> StepResult:
    """``method_metrics``: [{"method": str, "cv": {...}, "note": str}]."""
    metric = str(ctx.param("selection_metric", "rmse")).lower()
    rows: list[dict[str, Any]] = []
    for m in method_metrics:
        cv = _clean_cv(m.get("cv"))
        if not cv or "rmse" not in cv:
            continue
        rows.append({
            "Método": m["method"],
            "RMSE": cv.get("rmse"),
            "MAE": cv.get("mae"),
            "R²": cv.get("r2"),
            "Erro médio": cv.get("me"),
            "_note": m.get("note", ""),
        })

    if not rows:
        return StepResult.skipped(
            KEY, TITLE,
            "Nenhum método de interpolação produziu métricas de validação cruzada comparáveis.",
        )

    ascending = metric != "r2"
    sort_col = _METRIC_LABEL.get(metric, "RMSE")
    df = pd.DataFrame(rows).sort_values(
        sort_col, ascending=ascending, na_position="last"
    ).reset_index(drop=True)
    df.insert(0, "Ranking", range(1, len(df) + 1))
    notes = df.pop("_note")

    ranked = [
        {
            "method": r["Método"], "rmse": r["RMSE"], "mae": r["MAE"],
            "r2": r["R²"], "me": r["Erro médio"],
        }
        for _, r in df.iterrows()
    ]

    table = TableResult(
        name="comparacao_geral",
        df=df,
        title="Comparação Geral dos Métodos",
        caption=(
            "Métricas de validação cruzada (leave-one-out / k-fold). "
            f"Ordenação pelo critério {sort_col}. "
            + ("; ".join(f"{m}: {n}" for m, n in zip(df['Método'], notes) if n) or "")
        ).strip(),
        highlight_rows=[0],
    )

    figures: list[FigureResult] = [_bar_chart(ctx, df, sort_col)]

    best = ranked[0]
    metrics = {
        "best_method": best["method"],
        "ranking": [r["method"] for r in ranked],
        "table": ranked,
        "selection_metric": metric,
    }
    return StepResult(
        key=KEY, title=TITLE, status="ok",
        tables=[table], figures=figures, metrics=metrics,
        interpretation=interpret_comparison(ranked, metric),
        params_used={"selection_metric": metric},
    )


def _bar_chart(ctx: AnalysisContext, df: pd.DataFrame, sort_col: str) -> FigureResult:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    vals = df[sort_col].to_numpy(float)
    y = np.arange(len(df))
    ax.barh(y, vals, color="#3b6ea5", height=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(df["Método"])
    ax.invert_yaxis()
    ax.set_xlabel(sort_col)
    ax.set_title(f"Desempenho dos métodos — {sort_col} (validação cruzada)", fontsize=11)
    for i, v in enumerate(vals):
        if np.isfinite(v):
            ax.text(v, i, f" {num(v)}", va="center", fontsize=8)
    ax.grid(axis="x", alpha=0.3)
    return ctx.save_fig(
        fig, "comparacao_metodos", subdir="figures",
        title="Comparação dos métodos", kind="chart",
        caption=f"Menor {sort_col} indica melhor desempenho preditivo.",
    )
