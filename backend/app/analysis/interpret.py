"""Interpretação automática determinística (seção 28).

REGRA: nenhuma frase é gerada sem os números reais correspondentes. Se um
resultado não é estatisticamente significativo, isso é dito explicitamente.
Não há chamada a modelo de linguagem — apenas gabaritos parametrizados.
"""
from __future__ import annotations

import math
from typing import Any, Iterable


# --------------------------------------------------------------------------- #
# Formatação
# --------------------------------------------------------------------------- #
def num(x: Any, n: int = 3) -> str:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "—"
    if not math.isfinite(x):
        return "—"
    if x != 0 and (abs(x) >= 1e6 or abs(x) < 1e-4):
        s = f"{x:.{n}e}"
    else:
        s = f"{x:,.{n}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def pval(p: Any) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return "—"
    if not math.isfinite(p):
        return "—"
    if p < 0.001:
        return "p < 0,001"
    return f"p = {num(p, 3)}"


def is_sig(p: Any, alpha: float = 0.05) -> bool:
    try:
        return float(p) < alpha
    except (TypeError, ValueError):
        return False


def sig_clause(p: Any, alpha: float = 0.05) -> str:
    if is_sig(p, alpha):
        return f"estatisticamente significativo ao nível de {num(alpha, 2)} ({pval(p)})"
    return f"não significativo ao nível de {num(alpha, 2)} ({pval(p)})"


# --------------------------------------------------------------------------- #
# Controle de qualidade (seção 3)
# --------------------------------------------------------------------------- #
def interpret_data_quality(counts: dict[str, int]) -> str:
    n = counts.get("rows", 0)
    parts = [f"A base contém {n} registros e {counts.get('cols', 0)} colunas, "
             f"das quais {counts.get('numeric_vars', 0)} são numéricas."]
    issues = []
    if counts.get("missing_cells"):
        issues.append(f"{counts['missing_cells']} células ausentes")
    if counts.get("duplicate_rows"):
        issues.append(f"{counts['duplicate_rows']} linhas duplicadas")
    if counts.get("coincident_points"):
        issues.append(f"{counts['coincident_points']} pontos coincidentes")
    if counts.get("invalid_coords"):
        issues.append(f"{counts['invalid_coords']} coordenadas inválidas")
    if counts.get("infinite_values"):
        issues.append(f"{counts['infinite_values']} valores infinitos")
    if counts.get("outliers"):
        issues.append(f"{counts['outliers']} possíveis outliers (critério IQR)")
    if issues:
        parts.append("Foram identificados: " + "; ".join(issues) + ".")
    else:
        parts.append("Não foram identificados problemas estruturais relevantes.")
    return " ".join(parts)


# --------------------------------------------------------------------------- #
# Estatística descritiva (seção 8)
# --------------------------------------------------------------------------- #
def interpret_descriptive(name: str, s: dict[str, float], units: str = "") -> str:
    u = f" {units}" if units else ""
    cv = s.get("cv")
    txt = (
        f"A variável {name} apresenta média de {num(s.get('mean'))}{u} "
        f"(mediana {num(s.get('median'))}{u}), com desvio-padrão de {num(s.get('std'))}{u} "
        f"e amplitude de {num(s.get('min'))} a {num(s.get('max'))}{u}."
    )
    if cv is not None and math.isfinite(cv):
        if cv < 15:
            grade = "baixa dispersão relativa"
        elif cv < 35:
            grade = "dispersão relativa moderada"
        else:
            grade = "alta dispersão relativa"
        txt += f" O coeficiente de variação é {num(cv, 1)}% ({grade})."
    sk = s.get("skewness")
    if sk is not None and math.isfinite(sk):
        if abs(sk) < 0.5:
            shape = "distribuição aproximadamente simétrica"
        elif sk > 0:
            shape = "assimetria positiva (cauda à direita)"
        else:
            shape = "assimetria negativa (cauda à esquerda)"
        txt += f" A assimetria é {num(sk, 2)} — {shape}."
    return txt


# --------------------------------------------------------------------------- #
# Autocorrelação espacial global (seções 9-10)
# --------------------------------------------------------------------------- #
def interpret_moran(
    name: str, I: float, EI: float, p: float, z: float, n_perm: int, alpha: float = 0.05
) -> str:
    direction = "positiva" if I > EI else "negativa"
    if not is_sig(p, alpha):
        return (
            f"O I de Moran global de {name} é {num(I, 3)} (esperado sob aleatoriedade "
            f"E[I] = {num(EI, 3)}; z = {num(z, 2)}), {sig_clause(p, alpha)} com "
            f"{n_perm} permutações. Não há evidência de autocorrelação espacial "
            f"em {name} nesta escala."
        )
    if abs(I) < 0.2:
        strength = "fraca"
    elif abs(I) < 0.5:
        strength = "moderada"
    else:
        strength = "forte"
    meaning = (
        "valores semelhantes tendem a se agrupar espacialmente"
        if direction == "positiva"
        else "valores altos e baixos tendem a se alternar espacialmente (padrão de xadrez)"
    )
    return (
        f"A variável {name} apresenta autocorrelação espacial {direction} {strength}, "
        f"com I de Moran = {num(I, 3)} (E[I] = {num(EI, 3)}, z = {num(z, 2)}), "
        f"{sig_clause(p, alpha)} com base em {n_perm} permutações — ou seja, {meaning}."
    )


def interpret_local_moran(
    name: str, quad_counts: dict[str, int], n_sig: int, n_total: int, alpha: float = 0.05
) -> str:
    if n_sig == 0:
        return (
            f"O Moran Local (LISA) de {name} não identificou agrupamentos locais "
            f"significativos ao nível de {num(alpha, 2)}."
        )
    hh = quad_counts.get("HH", 0)
    ll = quad_counts.get("LL", 0)
    hl = quad_counts.get("HL", 0)
    lh = quad_counts.get("LH", 0)
    return (
        f"O Moran Local (LISA) de {name} identificou {n_sig} de {n_total} localizações "
        f"com associação espacial significativa: {hh} no quadrante Alto-Alto, "
        f"{ll} Baixo-Baixo, {hl} Alto-Baixo e {lh} Baixo-Alto. Os quadrantes AA e BB "
        f"indicam clusters; AB e BA indicam outliers espaciais."
    )


def interpret_geary(name: str, C: float, p: float, alpha: float = 0.05) -> str:
    if not is_sig(p, alpha):
        return (
            f"O C de Geary de {name} é {num(C, 3)}, {sig_clause(p, alpha)} — "
            f"sem evidência de estrutura espacial local."
        )
    tendency = "autocorrelação positiva (C < 1)" if C < 1 else "autocorrelação negativa (C > 1)"
    return f"O C de Geary de {name} é {num(C, 3)}, indicando {tendency}, {sig_clause(p, alpha)}."


def interpret_getis(
    name: str, n_hot: int, n_cold: int, alpha: float = 0.05
) -> str:
    if n_hot == 0 and n_cold == 0:
        return (
            f"A estatística Getis-Ord Gi* de {name} não identificou hot spots ou "
            f"cold spots significativos ao nível de {num(alpha, 2)}."
        )
    return (
        f"A estatística Getis-Ord Gi* de {name} identificou {n_hot} hot spots "
        f"(agrupamentos de valores altos) e {n_cold} cold spots (valores baixos) "
        f"significativos ao nível de {num(alpha, 2)}."
    )


# --------------------------------------------------------------------------- #
# Testes (seção 10)
# --------------------------------------------------------------------------- #
def interpret_normality(name: str, test: str, stat: float, p: float, alpha: float = 0.05) -> str:
    if is_sig(p, alpha):
        return (
            f"{test} rejeita a normalidade de {name} "
            f"(estatística = {num(stat, 3)}, {pval(p)}). Recomenda-se cautela com "
            f"métodos que assumem gaussianidade; considerar transformação."
        )
    return (
        f"{test} não rejeita a normalidade de {name} "
        f"(estatística = {num(stat, 3)}, {pval(p)})."
    )


# --------------------------------------------------------------------------- #
# Moran scatter (seção 11)
# --------------------------------------------------------------------------- #
def interpret_moran_scatter(
    name: str, I: float, p: float, quad_counts: dict[str, int], alpha: float = 0.05
) -> str:
    dominant = max(quad_counts, key=quad_counts.get) if quad_counts else "—"
    labels = {"HH": "Alto-Alto", "LL": "Baixo-Baixo", "HL": "Alto-Baixo", "LH": "Baixo-Alto"}
    base = (
        f"O gráfico de dispersão de Moran de {name} tem inclinação {num(I, 3)} "
        f"(igual ao I de Moran), {sig_clause(p, alpha)}."
    )
    if is_sig(p, alpha):
        base += (
            f" O quadrante predominante é {labels.get(dominant, dominant)} "
            f"({quad_counts.get(dominant, 0)} pontos)."
        )
    return base


# --------------------------------------------------------------------------- #
# ESDA bivariada (seção 12)
# --------------------------------------------------------------------------- #
def interpret_bivariate_moran(a: str, b: str, I: float, p: float, alpha: float = 0.05) -> str:
    if not is_sig(p, alpha):
        return (
            f"O I de Moran bivariado entre {a} e a defasagem espacial de {b} é "
            f"{num(I, 3)}, {sig_clause(p, alpha)} — sem associação espacial cruzada."
        )
    direction = "positiva" if I > 0 else "negativa"
    return (
        f"Há associação espacial cruzada {direction} entre {a} e a vizinhança de {b} "
        f"(I bivariado = {num(I, 3)}, {sig_clause(p, alpha)}): valores de {a} estão "
        f"espacialmente relacionados aos valores de {b} nas localizações vizinhas."
    )


# --------------------------------------------------------------------------- #
# IDW (seções 13-14)
# --------------------------------------------------------------------------- #
def interpret_idw_cv(best: dict[str, Any], metric: str = "rmse") -> str:
    return (
        f"A validação cruzada leave-one-out do IDW indica melhor desempenho com "
        f"potência = {num(best.get('power'), 2)} e {int(best.get('neighbors', 0))} vizinhos "
        f"(RMSE = {num(best.get('rmse'))}, MAE = {num(best.get('mae'))}, "
        f"R² = {num(best.get('r2'), 3)}). Seleção pelo critério {metric.upper()}."
    )


# --------------------------------------------------------------------------- #
# Variograma / Krigagem (seções 15-18)
# --------------------------------------------------------------------------- #
def interpret_variogram(model: str, nugget: float, sill: float, rng: float) -> str:
    total = nugget + sill if (nugget is not None and sill is not None) else None
    ratio = (nugget / total) if total else None
    txt = (
        f"O variograma experimental foi ajustado pelo modelo {model} com efeito "
        f"pepita (nugget) = {num(nugget)}, patamar (sill) = {num(total if total else sill)} "
        f"e alcance (range) = {num(rng)} m."
    )
    if ratio is not None and math.isfinite(ratio):
        if ratio < 0.25:
            dep = "forte dependência espacial"
        elif ratio < 0.75:
            dep = "dependência espacial moderada"
        else:
            dep = "fraca dependência espacial"
        txt += f" A razão pepita/patamar é {num(ratio * 100, 1)}% — {dep}."
    return txt


def interpret_kriging_cv(model: str, m: dict[str, Any]) -> str:
    txt = (
        f"A validação cruzada da krigagem ordinária (modelo {model}) resulta em "
        f"RMSE = {num(m.get('rmse'))}, MAE = {num(m.get('mae'))}, "
        f"erro médio (viés) = {num(m.get('me'))} e R² = {num(m.get('r2'), 3)}."
    )
    mse_std = m.get("msdr") or m.get("mean_std_error")
    if mse_std is not None and math.isfinite(mse_std):
        ok = 0.8 <= mse_std <= 1.2
        txt += (
            f" A média do erro quadrático padronizado é {num(mse_std, 3)} "
            f"({'próxima de 1 — variâncias de krigagem bem calibradas' if ok else 'afastada de 1 — variâncias possivelmente mal calibradas'})."
        )
    return txt


def interpret_model_selection(ranked: Iterable[dict[str, Any]], metric: str = "rmse") -> str:
    ranked = list(ranked)
    if not ranked:
        return "Não foi possível ajustar modelos de variograma."
    best = ranked[0]
    worst = ranked[-1]
    txt = (
        f"Entre os {len(ranked)} modelos de variograma testados, o {best.get('model')} "
        f"apresentou o menor {metric.upper()} na validação cruzada "
        f"({num(best.get(metric))}), sendo selecionado automaticamente."
    )
    if len(ranked) > 1:
        txt += (
            f" O pior desempenho foi do modelo {worst.get('model')} "
            f"({metric.upper()} = {num(worst.get(metric))})."
        )
    return txt


# --------------------------------------------------------------------------- #
# Deriva externa (seção 19)
# --------------------------------------------------------------------------- #
def interpret_external_drift(
    primary: str, aux: str, r_corr: float, r2_reg: float, cv: dict[str, Any]
) -> str:
    return (
        f"A krigagem com deriva externa usa {aux} como covariável de {primary} "
        f"(correlação r = {num(r_corr, 3)}; R² da regressão = {num(r2_reg, 3)}). "
        f"A validação cruzada resulta em RMSE = {num(cv.get('rmse'))}, "
        f"MAE = {num(cv.get('mae'))} e R² = {num(cv.get('r2'), 3)}."
    )


# --------------------------------------------------------------------------- #
# GWR / GWM (seções 20-21)
# --------------------------------------------------------------------------- #
def interpret_gwr(
    dep: str,
    bw: float,
    bw_kind: str,
    r2_global: float,
    r2_local_min: float,
    r2_local_max: float,
    aicc: float,
    mc_significant_vars: list[str] | None = None,
) -> str:
    txt = (
        f"A Regressão Geograficamente Ponderada (GWR) para {dep} usa largura de banda "
        f"{bw_kind} = {num(bw, 2)} (selecionada por AICc = {num(aicc, 1)}). "
        f"O R² global é {num(r2_global, 3)}; o R² local varia de {num(r2_local_min, 3)} "
        f"a {num(r2_local_max, 3)}, evidenciando heterogeneidade espacial na relação."
    )
    if mc_significant_vars:
        txt += (
            " O teste de Monte Carlo indica variação espacial significativa dos "
            f"coeficientes de: {', '.join(mc_significant_vars)}."
        )
    elif mc_significant_vars is not None:
        txt += (
            " O teste de Monte Carlo não indica variação espacial significativa "
            "dos coeficientes."
        )
    return txt


# --------------------------------------------------------------------------- #
# Co-krigagem (seção 22)
# --------------------------------------------------------------------------- #
def interpret_cokriging(
    primary: str, secondary: str, r_corr: float, cv_ck: dict[str, Any], cv_ok: dict[str, Any]
) -> str:
    rmse_ck = cv_ck.get("rmse")
    rmse_ok = cv_ok.get("rmse")
    better = (
        rmse_ck is not None and rmse_ok is not None and rmse_ck < rmse_ok
    )
    cmp = (
        f"A co-krigagem melhora a predição em relação à krigagem ordinária "
        f"(RMSE {num(rmse_ck)} vs {num(rmse_ok)})."
        if better
        else f"A co-krigagem não supera a krigagem ordinária neste conjunto "
        f"(RMSE {num(rmse_ck)} vs {num(rmse_ok)})."
    )
    return (
        f"A co-krigagem colocada usa {secondary} como variável secundária de "
        f"{primary} (correlação r = {num(r_corr, 3)}). {cmp}"
    )


# --------------------------------------------------------------------------- #
# Comparação geral (seção 23)
# --------------------------------------------------------------------------- #
def interpret_comparison(ranked: Iterable[dict[str, Any]], metric: str = "rmse") -> str:
    ranked = list(ranked)
    if not ranked:
        return "Nenhum método de interpolação pôde ser comparado."
    best = ranked[0]
    lines = [
        f"Comparando {len(ranked)} métodos pelo {metric.upper()} na validação cruzada, "
        f"o melhor desempenho é de {best.get('method')} "
        f"({metric.upper()} = {num(best.get(metric))}, R² = {num(best.get('r2'), 3)})."
    ]
    if len(ranked) > 1:
        others = ", ".join(
            f"{r.get('method')} ({num(r.get(metric))})" for r in ranked[1:]
        )
        lines.append(f"Demais métodos, em ordem: {others}.")
    lines.append(
        "O ranking reflete exclusivamente as métricas de validação cruzada, sem "
        "ajuste subjetivo."
    )
    return " ".join(lines)


# --------------------------------------------------------------------------- #
# Conclusão do relatório (seção 26.15)
# --------------------------------------------------------------------------- #
def build_conclusion(findings: dict[str, Any]) -> str:
    """Monta a conclusão a partir de achados já calculados (sem inventar)."""
    parts: list[str] = []
    mo = findings.get("moran_primary")
    if mo:
        parts.append(
            f"A variável principal ({findings.get('primary')}) "
            + (
                f"apresenta autocorrelação espacial significativa (I = {num(mo.get('I'), 3)}, "
                f"{pval(mo.get('p'))}), justificando o uso de métodos geoestatísticos."
                if is_sig(mo.get("p"), findings.get("alpha", 0.05))
                else f"não apresenta autocorrelação espacial significativa "
                f"(I = {num(mo.get('I'), 3)}, {pval(mo.get('p'))}); os resultados "
                f"geoestatísticos devem ser interpretados com cautela."
            )
        )
    best = findings.get("best_method")
    if best:
        parts.append(
            f"Entre os métodos de interpolação avaliados, {best.get('method')} obteve "
            f"o melhor desempenho (RMSE = {num(best.get('rmse'))}, "
            f"R² = {num(best.get('r2'), 3)}) na validação cruzada."
        )
    skipped = findings.get("skipped") or []
    if skipped:
        parts.append(
            "Não foram executadas as seguintes análises, por inadequação dos dados: "
            + "; ".join(f"{s['title']} ({s['reason']})" for s in skipped)
            + "."
        )
    if not parts:
        parts.append(
            "As análises foram concluídas. Consulte as seções anteriores para os "
            "resultados detalhados."
        )
    return " ".join(parts)
