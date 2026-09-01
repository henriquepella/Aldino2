"""Módulo de análise ESDA Bivariada (seção 12).

Calcula o I de Moran bivariado global e o LISA bivariado (Moran Local BV) para
pares de variáveis numéricas, medindo a associação espacial cruzada entre uma
variável e a defasagem espacial da outra. Textos em PT-BR via ``app.analysis.interpret``.
"""
from __future__ import annotations

import warnings
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd

from app.analysis import interpret
from app.analysis.base import AnalysisContext, StepResult, TableResult
from app.analysis.weights import build_weights
from app.maps import renderer

KEY = "esda_bivariate"
TITLE = "ESDA Bivariada"

# quadrantes do Moran Local (libpysal/esda): 1=AA, 2=BA, 3=BB, 4=AB
_QUAD_CODE = {1: "AA", 2: "BA", 3: "BB", 4: "AB"}
_QUAD_LABEL = {
    "AA": "Alto-Alto",
    "BB": "Baixo-Baixo",
    "AB": "Alto-Baixo",
    "BA": "Baixo-Alto",
    "ns": "Não significativo",
    "nd": "Sem dado",
}
_MIN_N = 10
_MAX_FIG_PAIRS = 4


# --------------------------------------------------------------------------- #
# Seleção de variáveis / pares
# --------------------------------------------------------------------------- #
def _numeric_cols(ctx: AnalysisContext) -> list[str]:
    """Colunas numéricas úteis (exclui coordenadas e identificador)."""
    skip = {ctx.x_col, ctx.y_col, ctx.id_col}
    out: list[str] = []
    for c in ctx.df.columns:
        if c in skip or not pd.api.types.is_numeric_dtype(ctx.df[c]):
            continue
        v = ctx.values(c)
        fin = v[np.isfinite(v)]
        if fin.size >= _MIN_N and np.unique(fin).size > 2:
            out.append(str(c))
    return out


def _parse_pairs(raw: Any, valid: set[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    if not raw or not isinstance(raw, (list, tuple)):
        return pairs
    for item in raw:
        a = b = None
        if isinstance(item, dict):
            a, b = item.get("a"), item.get("b")
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            a, b = item[0], item[1]
        elif isinstance(item, str):
            for sep in (",", ";", "|"):
                if sep in item:
                    parts = [p.strip() for p in item.split(sep)]
                    if len(parts) >= 2:
                        a, b = parts[0], parts[1]
                    break
        if a in valid and b in valid and a != b and (a, b) not in pairs:
            pairs.append((str(a), str(b)))
    return pairs


def _select_pairs(ctx: AnalysisContext, valid: list[str]) -> tuple[list[tuple[str, str]], str]:
    vset = set(valid)
    explicit = _parse_pairs(ctx.param("bivariate_pairs"), vset)
    if explicit:
        return explicit[:8], "pares informados"

    if bool(ctx.param("bivariate_all_pairs", False)):
        allp = [(a, b) for a, b in combinations(valid, 2)]
        return allp[:8], "todos os pares"

    seen: list[tuple[str, str]] = []
    cands = [s for s in (list(ctx.secondary) + list(ctx.explanatory)) if s != ctx.primary]
    for s in cands:
        if ctx.primary in vset and s in vset and (ctx.primary, s) not in seen:
            seen.append((ctx.primary, s))
    return seen[:6], "principal vs. secundárias/explicativas"


# --------------------------------------------------------------------------- #
# Cálculo de um par
# --------------------------------------------------------------------------- #
def _run_pair(ctx: AnalysisContext, a: str, b: str) -> dict[str, Any] | None:
    import esda
    from libpysal.weights import lag_spatial

    va, vb = ctx.values(a), ctx.values(b)
    mask = np.isfinite(ctx.mx) & np.isfinite(ctx.my) & np.isfinite(va) & np.isfinite(vb)
    if int(mask.sum()) < _MIN_N:
        return None
    za, zb = va[mask], vb[mask]
    if za.std() == 0 or zb.std() == 0:
        return None

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w, winfo = build_weights(ctx, mask=mask)
        mbv = esda.Moran_BV(za, zb, w, permutations=int(ctx.n_perm))
        lbv = esda.Moran_Local_BV(
            za, zb, w, permutations=int(ctx.n_perm), seed=int(ctx.random_seed)
        )
        # dispersão: a padronizada vs. defasagem espacial de b padronizada
        zas = (za - za.mean()) / za.std()
        zbs = (zb - zb.mean()) / zb.std()
        lag_zb = np.asarray(lag_spatial(w, zbs), float)

    p_local = np.asarray(lbv.p_sim, float)
    q_local = np.asarray(lbv.q, int)
    sig = p_local < float(ctx.alpha)
    n_sig = int(sig.sum())

    quad_counts = {c: 0 for c in ("AA", "BB", "AB", "BA")}
    for qi, s in zip(q_local, sig):
        if s:
            quad_counts[_QUAD_CODE.get(int(qi), "AA")] += 1

    # arrays de tamanho ctx.n para o mapa de pontos
    cat_full = np.full(ctx.n, "nd", dtype=object)
    idx = np.where(mask)[0]
    for j, gi in enumerate(idx):
        cat_full[gi] = _QUAD_CODE.get(int(q_local[j]), "AA") if sig[j] else "ns"

    return {
        "a": a,
        "b": b,
        "I": float(mbv.I),
        "p": float(mbv.p_sim),
        "z": float(mbv.z_sim),
        "n_sig": n_sig,
        "n": int(mask.sum()),
        "quad_counts": quad_counts,
        "weights": winfo,
        "cat_full": cat_full,
        "scatter_x": zas,
        "scatter_y": lag_zb,
        "scatter_q": q_local,
    }


# --------------------------------------------------------------------------- #
# Figuras
# --------------------------------------------------------------------------- #
def _scatter_fig(ctx: AnalysisContext, pr: dict[str, Any]):
    import matplotlib.pyplot as plt

    a, b, I = pr["a"], pr["b"], pr["I"]
    x, y, q = pr["scatter_x"], pr["scatter_y"], pr["scatter_q"]
    colors = {1: "#b2182b", 2: "#2166ac", 3: "#2166ac", 4: "#b2182b"}

    fig, ax = plt.subplots(figsize=(6.2, 5.6))
    for code, lbl in ((1, "Alto-Alto"), (4, "Alto-Baixo"), (3, "Baixo-Baixo"), (2, "Baixo-Alto")):
        m = q == code
        if m.any():
            ax.scatter(x[m], y[m], s=26, c=colors[code], alpha=0.75,
                       edgecolors="black", linewidths=0.3, label=lbl)
    ax.axhline(0, color="#888888", lw=0.8)
    ax.axvline(0, color="#888888", lw=0.8)
    xs = np.array([x.min(), x.max()])
    ax.plot(xs, I * xs, color="black", lw=1.4, label=f"I bivariado = {interpret.num(I, 3)}")
    ax.set_xlabel(f"{a} (padronizado)")
    ax.set_ylabel(f"Defasagem espacial de {b} (padronizada)")
    ax.set_title(f"Dispersão de Moran bivariada — {a} × {b}", fontsize=11)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, framealpha=0.9)
    fig.tight_layout()
    return ctx.save_fig(
        fig, f"bivariate_scatter_{a}_{b}", subdir="figures",
        title=f"Dispersão de Moran bivariada — {a} × {b}",
        caption=(f"{a} padronizado no eixo X; defasagem espacial de {b} no eixo Y. "
                 f"Inclinação da reta = I de Moran bivariado ({interpret.num(I, 3)})."),
        kind="chart",
    )


def _lisa_map(ctx: AnalysisContext, pr: dict[str, Any]):
    a, b = pr["a"], pr["b"]
    present = sorted(set(pr["cat_full"].tolist()))
    cat_labels = {c: _QUAD_LABEL.get(c, str(c)) for c in present}
    return renderer.render_points(
        ctx, pr["cat_full"], name=f"bivariate_lisa_{a}_{b}",
        title=f"LISA bivariado — {a} × defasagem de {b}",
        method="Moran Local bivariado (LISA BV)",
        categorical=True, cat_labels=cat_labels,
        caption=(f"Agrupamentos locais significativos (alpha = {interpret.num(ctx.alpha, 2)}, "
                 f"{ctx.n_perm} permutações) da associação entre {a} e a vizinhança de {b}."),
    )


def _heatmap_fig(ctx: AnalysisContext, results: list[dict[str, Any]], labels: list[str]):
    import matplotlib.pyplot as plt

    idx = {name: i for i, name in enumerate(labels)}
    M = np.full((len(labels), len(labels)), np.nan)
    for pr in results:
        i, j = idx[pr["a"]], idx[pr["b"]]
        M[i, j] = pr["I"]
        M[j, i] = pr["I"]
    vmax = float(np.nanmax(np.abs(M))) if np.isfinite(M).any() else 1.0

    fig, ax = plt.subplots(figsize=(1.4 + 0.7 * len(labels), 1.2 + 0.7 * len(labels)))
    im = ax.imshow(M, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(labels, fontsize=8)
    for i in range(len(labels)):
        for j in range(len(labels)):
            if np.isfinite(M[i, j]):
                ax.text(j, i, interpret.num(M[i, j], 2), ha="center", va="center",
                        fontsize=7, color="black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="I de Moran bivariado")
    ax.set_title("Matriz de I de Moran bivariado", fontsize=11)
    fig.tight_layout()
    return ctx.save_fig(
        fig, "bivariate_matriz_I", subdir="figures",
        title="Matriz de I de Moran bivariado",
        caption="Valores simetrizados; célula (i, j) = associação entre a variável i e a defasagem de j.",
        kind="chart",
    )


# --------------------------------------------------------------------------- #
# Contrato
# --------------------------------------------------------------------------- #
def applicable(ctx: AnalysisContext) -> tuple[bool, str]:
    if len(_numeric_cols(ctx)) < 2:
        return False, "São necessárias ao menos duas variáveis numéricas para a ESDA bivariada."
    return True, ""


def run(ctx: AnalysisContext) -> StepResult:
    """Executa o I de Moran bivariado global e o LISA bivariado (seção 12)."""
    valid = _numeric_cols(ctx)
    if len(valid) < 2:
        return StepResult.skipped(KEY, TITLE, "Menos de duas variáveis numéricas disponíveis.")

    pairs, mode = _select_pairs(ctx, valid)
    if not pairs:
        return StepResult.skipped(KEY, TITLE, "Nenhum par de variáveis pôde ser formado.")

    all_pairs = bool(ctx.param("bivariate_all_pairs", False)) and mode == "todos os pares"

    results: list[dict[str, Any]] = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for a, b in pairs:
            pr = _run_pair(ctx, a, b)
            if pr is not None:
                results.append(pr)

    if not results:
        return StepResult.skipped(
            KEY, TITLE, "Dados insuficientes para calcular o I de Moran bivariado nos pares selecionados."
        )

    results.sort(key=lambda r: (r["p"], -abs(r["I"])))

    # --- tabela 1 -------------------------------------------------------- #
    rows1 = [{
        "Par": f"{r['a']} × {r['b']}",
        "I bivariado": round(r["I"], 4),
        "z": round(r["z"], 3),
        "p-value": round(r["p"], 4),
        "Significativo": "Sim" if interpret.is_sig(r["p"], ctx.alpha) else "Não",
        "LISA sig": r["n_sig"],
    } for r in results]
    tbl1 = TableResult(
        name="esda_bivariada", df=pd.DataFrame(rows1), title="ESDA Bivariada",
        caption=(f"I de Moran bivariado (par × defasagem espacial) com {ctx.n_perm} permutações; "
                 f"LISA sig = nº de localizações com associação local significativa "
                 f"(alpha = {interpret.num(ctx.alpha, 2)})."),
        highlight_rows=[0],
    )

    # --- tabela 2 ------------------------------------------------------- #
    rows2 = [{
        "Estatística": f"I de Moran bivariado — {r['a']} × {r['b']}",
        "Valor": round(r["I"], 4),
        "p-value": round(r["p"], 4),
        "Significativo": "Sim" if interpret.is_sig(r["p"], ctx.alpha) else "Não",
    } for r in results]
    tbl2 = TableResult(
        name="esda_bivariada_testes", df=pd.DataFrame(rows2),
        title="ESDA Bivariada — Testes",
        caption="Teste de pseudo-significância por permutações do I de Moran bivariado global.",
        highlight_rows=[0],
    )

    tables = [tbl1, tbl2]

    # --- figuras ------------------------------------------------------- #
    figures = []
    for pr in results[:_MAX_FIG_PAIRS]:
        try:
            figures.append(_lisa_map(ctx, pr))
        except Exception as exc:  # noqa: BLE001
            ctx.logger.warning("Falha no mapa LISA bivariado %s×%s: %s", pr["a"], pr["b"], exc)
        try:
            figures.append(_scatter_fig(ctx, pr))
        except Exception as exc:  # noqa: BLE001
            ctx.logger.warning("Falha na dispersão bivariada %s×%s: %s", pr["a"], pr["b"], exc)

    if all_pairs and len(results) >= 2:
        labels = sorted({r["a"] for r in results} | {r["b"] for r in results})
        try:
            figures.append(_heatmap_fig(ctx, results, labels))
        except Exception as exc:  # noqa: BLE001
            ctx.logger.warning("Falha no heatmap de I bivariado: %s", exc)

    # --- interpretação ----------------------------------------------- #
    chosen = next((r for r in results if interpret.is_sig(r["p"], ctx.alpha)), results[0])
    interpretation = interpret.interpret_bivariate_moran(
        chosen["a"], chosen["b"], chosen["I"], chosen["p"], ctx.alpha
    )

    # --- metrics ----------------------------------------------------- #
    metrics = {"pairs": [
        {"a": r["a"], "b": r["b"], "I": round(r["I"], 6), "p": round(r["p"], 6),
         "z": round(r["z"], 6), "n_sig": r["n_sig"]}
        for r in results
    ]}

    params_used = {
        "n_permutations": int(ctx.n_perm),
        "alpha": float(ctx.alpha),
        "weights_kind": ctx.param("weights_kind", "knn"),
        "knn_k": int(ctx.param("knn_k", 8)),
        "pair_selection": mode,
        "n_pairs": len(results),
        "random_seed": int(ctx.random_seed),
    }

    return StepResult(
        key=KEY, title=TITLE, status="ok",
        tables=tables, figures=figures, metrics=metrics,
        interpretation=interpretation, params_used=params_used,
    )
