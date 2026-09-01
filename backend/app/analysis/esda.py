"""ESDA univariada — autocorrelação espacial global e local (seções 9-10).

Para cada variável de análise calcula:

* I de Moran global (com teste de permutação);
* Moran Local / LISA (quadrantes e contagem entre os significativos);
* C de Geary;
* Getis-Ord Gi* (contagem de hot spots e cold spots);
* teste de normalidade de D'Agostino-Pearson.

A seleção de vizinhança segue ``build_weights(ctx)`` (KNN row-standardized por
padrão). Todos os textos vêm de ``app.analysis.interpret``.
"""
from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd

from app.analysis.base import AnalysisContext, StepResult, TableResult
from app.analysis.interpret import (
    interpret_geary,
    interpret_getis,
    interpret_local_moran,
    interpret_moran,
)
from app.analysis.weights import build_weights
from app.maps import renderer

KEY = "esda_univariate"
TITLE = "ESDA Univariada"

# q do esda: 1=HH, 2=LH, 3=LL, 4=HL
_QUAD_KEY = {1: "HH", 2: "LH", 3: "LL", 4: "HL"}
_LISA_LABELS = {
    0: "nao sig",
    1: "Alto-Alto",
    2: "Baixo-Alto",
    3: "Baixo-Baixo",
    4: "Alto-Baixo",
}
_HOTCOLD_LABELS = {-1: "cold spot", 0: "nao sig", 1: "hot spot"}
_MIN_N = 10
_MIN_FINITE = 8


# --------------------------------------------------------------------------- #
def applicable(ctx: AnalysisContext) -> tuple[bool, str]:
    if ctx.n < _MIN_N:
        return False, f"Amostra insuficiente para ESDA (n = {ctx.n}, mínimo {_MIN_N})."
    if not ctx.analysis_variables:
        return False, "Nenhuma variável numérica disponível para análise espacial."
    for name in ctx.analysis_variables:
        z = ctx.values(name)
        if np.isfinite(z).sum() >= _MIN_FINITE and np.nanstd(z) > 0:
            return True, ""
    return False, "Nenhuma variável com dados finitos e variância suficiente."


# --------------------------------------------------------------------------- #
def _analyze_variable(
    ctx: AnalysisContext, name: str, alpha: float
) -> dict[str, Any] | None:
    """Roda todos os estimadores para uma variável; None se inviável."""
    from esda import Geary, G_Local, Moran, Moran_Local
    from scipy import stats

    z_full = ctx.values(name)
    mask = np.isfinite(ctx.mx) & np.isfinite(ctx.my) & np.isfinite(z_full)
    if int(mask.sum()) < _MIN_FINITE or float(np.nanstd(z_full[mask])) <= 0:
        return None

    z = z_full[mask].astype(float)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w, winfo = build_weights(ctx, mask=mask)

        np.random.seed(ctx.random_seed)
        mi = Moran(z, w, permutations=ctx.n_perm)

        ml = Moran_Local(z, w, permutations=ctx.n_perm, seed=ctx.random_seed, n_jobs=1)

        np.random.seed(ctx.random_seed)
        gc = Geary(z, w, permutations=ctx.n_perm)

        # n_jobs=1: o padrão -1 do G_Local abre um pool de subprocessos por CPU
        gl = G_Local(z, w, star=True, permutations=ctx.n_perm, seed=ctx.random_seed, n_jobs=1)

        dstat, dp = stats.normaltest(z)

    # LISA — quadrantes entre os significativos
    lisa_sig = np.asarray(ml.p_sim) < alpha
    quad_counts = {"HH": 0, "LH": 0, "LL": 0, "HL": 0}
    for q_val, is_sig_i in zip(np.asarray(ml.q), lisa_sig):
        if is_sig_i:
            quad_counts[_QUAD_KEY.get(int(q_val), "HH")] += 1
    n_sig = int(lisa_sig.sum())

    # Getis Gi*
    g_zs = np.asarray(gl.Zs)
    g_p = np.asarray(gl.p_sim)
    n_hot = int(np.sum((g_zs > 0) & (g_p < alpha)))
    n_cold = int(np.sum((g_zs < 0) & (g_p < alpha)))

    # vetor de quadrantes de comprimento ctx.n (0 = não significativo / fora da máscara)
    q_full = np.zeros(ctx.n, dtype=int)
    idx = np.where(mask)[0]
    q_arr = np.asarray(ml.q, dtype=int)
    q_full[idx[lisa_sig]] = q_arr[lisa_sig]

    hotcold_full = np.zeros(ctx.n, dtype=int)
    hot_local = (g_zs > 0) & (g_p < alpha)
    cold_local = (g_zs < 0) & (g_p < alpha)
    hotcold_full[idx[hot_local]] = 1
    hotcold_full[idx[cold_local]] = -1

    return {
        "name": name,
        "I": float(mi.I),
        "EI": float(mi.EI),
        "z": float(mi.z_sim),
        "p": float(mi.p_sim),
        "geary_C": float(gc.C),
        "geary_p": float(gc.p_sim),
        "quad_counts": quad_counts,
        "n_sig": n_sig,
        "n_mask": int(mask.sum()),
        "n_hot": n_hot,
        "n_cold": n_cold,
        "norm_stat": float(dstat),
        "norm_p": float(dp),
        "q_full": q_full,
        "hotcold_full": hotcold_full,
        "weights": winfo,
    }


# --------------------------------------------------------------------------- #
def run(ctx: AnalysisContext) -> StepResult:
    ok, reason = applicable(ctx)
    if not ok:
        return StepResult.skipped(KEY, TITLE, reason)

    alpha = ctx.alpha
    results: list[dict[str, Any]] = []
    for name in ctx.analysis_variables:
        try:
            res = _analyze_variable(ctx, name, alpha)
        except Exception as exc:  # noqa: BLE001
            ctx.logger.warning("ESDA falhou para %s: %s", name, exc)
            res = None
        if res is not None:
            results.append(res)

    if not results:
        return StepResult.skipped(
            KEY, TITLE, "Não foi possível calcular estatísticas espaciais para nenhuma variável."
        )

    by_name = {r["name"]: r for r in results}

    # ---- Tabela 1: resumo ------------------------------------------------- #
    rows1 = [
        {
            "Variavel": r["name"],
            "Moran I": round(r["I"], 4),
            "E[I]": round(r["EI"], 4),
            "z": round(r["z"], 3),
            "p-value": round(r["p"], 4),
            "Geary C": round(r["geary_C"], 4),
            "p (Geary)": round(r["geary_p"], 4),
            "LISA sig": r["n_sig"],
            "Hot": r["n_hot"],
            "Cold": r["n_cold"],
        }
        for r in results
    ]
    df1 = pd.DataFrame(rows1)
    highlight1 = (
        [df1.index[df1["Variavel"] == ctx.primary][0]]
        if (df1["Variavel"] == ctx.primary).any()
        else []
    )
    table1 = TableResult(
        name="esda_univariada",
        df=df1,
        title="ESDA Univariada",
        caption=(
            "I de Moran e C de Geary por variável, com teste de permutação "
            f"({ctx.n_perm} simulações). LISA sig = localizações com associação "
            f"local significativa (α = {alpha}); Hot/Cold = Getis-Ord Gi*."
        ),
        highlight_rows=[int(h) for h in highlight1],
    )

    # ---- Tabela 2: testes ---------------------------------------------- #
    rows2: list[dict[str, Any]] = []
    for r in results:
        rows2.append({
            "Variavel": r["name"],
            "Teste": "Moran I (permutacao)",
            "Estatistica": round(r["I"], 4),
            "p-value": round(r["p"], 4),
            "Significativo": "Sim" if r["p"] < alpha else "Nao",
        })
        rows2.append({
            "Variavel": r["name"],
            "Teste": "Geary C",
            "Estatistica": round(r["geary_C"], 4),
            "p-value": round(r["geary_p"], 4),
            "Significativo": "Sim" if r["geary_p"] < alpha else "Nao",
        })
        rows2.append({
            "Variavel": r["name"],
            "Teste": "Normalidade (D'Agostino)",
            "Estatistica": round(r["norm_stat"], 4),
            "p-value": round(r["norm_p"], 4),
            "Significativo": "Sim" if r["norm_p"] < alpha else "Nao",
        })
    table2 = TableResult(
        name="esda_univariada_testes",
        df=pd.DataFrame(rows2),
        title="ESDA Univariada — Testes",
        caption=(
            "Significativo = p < α. Para a normalidade, 'Sim' indica rejeição da "
            "hipótese de distribuição gaussiana."
        ),
    )

    # ---- Figuras ------------------------------------------------------- #
    figures = []
    for r in results[:4]:
        try:
            fig = renderer.render_points(
                ctx,
                r["q_full"].astype(float),
                name=f"lisa_{r['name']}",
                title=f"Moran Local (LISA) — {r['name']}",
                method="Moran Local (LISA)",
                categorical=True,
                cat_labels={float(k): v for k, v in _LISA_LABELS.items()},
                caption=(
                    f"Quadrantes LISA significativos (α = {alpha}); "
                    "'nao sig' = sem associação local significativa."
                ),
            )
            figures.append(fig)
        except Exception as exc:  # noqa: BLE001
            ctx.logger.warning("Mapa LISA falhou para %s: %s", r["name"], exc)

    pr = by_name.get(ctx.primary)
    if pr is not None:
        try:
            fig = renderer.render_points(
                ctx,
                pr["hotcold_full"].astype(float),
                name=f"getis_{ctx.primary}",
                title=f"Hot spots / Cold spots (Getis-Ord Gi*) — {ctx.primary}",
                method="Getis-Ord Gi*",
                categorical=True,
                cat_labels={float(k): v for k, v in _HOTCOLD_LABELS.items()},
                caption=f"Gi* com vizinho próprio incluído; significância α = {alpha}.",
            )
            figures.append(fig)
        except Exception as exc:  # noqa: BLE001
            ctx.logger.warning("Mapa Getis falhou: %s", exc)

    # ---- Interpretação (variável principal) --------------------------- #
    interp_target = pr if pr is not None else results[0]
    parts = [
        interpret_moran(
            interp_target["name"],
            interp_target["I"],
            interp_target["EI"],
            interp_target["p"],
            interp_target["z"],
            ctx.n_perm,
            alpha,
        ),
        interpret_local_moran(
            interp_target["name"],
            interp_target["quad_counts"],
            interp_target["n_sig"],
            interp_target["n_mask"],
            alpha,
        ),
        interpret_geary(
            interp_target["name"],
            interp_target["geary_C"],
            interp_target["geary_p"],
            alpha,
        ),
        interpret_getis(
            interp_target["name"],
            interp_target["n_hot"],
            interp_target["n_cold"],
            alpha,
        ),
    ]
    interpretation = " ".join(parts)

    # ---- Métricas ---------------------------------------------------- #
    morans = {
        r["name"]: {"I": r["I"], "EI": r["EI"], "z": r["z"], "p": r["p"]}
        for r in results
    }
    metrics = {
        "morans": morans,
        "primary_moran": {
            "I": interp_target["I"],
            "p": interp_target["p"],
            "z": interp_target["z"],
            "EI": interp_target["EI"],
        },
        "weights": interp_target["weights"],
    }

    params_used = {
        "n_permutations": ctx.n_perm,
        "alpha": alpha,
        "weights_kind": ctx.param("weights_kind", "knn"),
        "knn_k": ctx.param("knn_k", 8),
        "random_seed": ctx.random_seed,
        "variables": [r["name"] for r in results],
    }

    return StepResult(
        key=KEY,
        title=TITLE,
        status="ok",
        tables=[table1, table2],
        figures=figures,
        metrics=metrics,
        interpretation=interpretation,
        params_used=params_used,
    )
