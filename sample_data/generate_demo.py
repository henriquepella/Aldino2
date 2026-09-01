"""Gera um conjunto de dados sintético, porém realista, de fertilidade do solo
com estrutura espacial genuína (campo aleatório gaussiano por covariância
exponencial), para demonstrar a plataforma de ponta a ponta (seções 45-47).

Saídas em ``sample_data/``:
  - demo_soil.xlsx   (aba "dados")
  - demo_soil.csv

O dataset inclui, de propósito, alguns problemas (ausentes, duplicatas, pontos
coincidentes, um outlier, uma coordenada inválida) para exercitar a tela de
Diagnóstico da Base.

CRS: SIRGAS 2000 / UTM 22S (EPSG:31982).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

OUT = Path(__file__).resolve().parent
SEED = 20260827
N = 480


def _grf(coords: np.ndarray, rng: np.random.Generator, range_m: float) -> np.ndarray:
    """Campo aleatório gaussiano ~N(0,1) com covariância exponencial."""
    d = cdist(coords, coords)
    cov = np.exp(-d / float(range_m))
    cov[np.diag_indices_from(cov)] += 1e-8
    L = np.linalg.cholesky(cov)
    field = L @ rng.standard_normal(len(coords))
    return (field - field.mean()) / field.std()


def _z(a: np.ndarray) -> np.ndarray:
    return (a - a.mean()) / a.std()


def build() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)

    # --- malha amostral irregular sobre um talhão de ~ 900 x 650 m ---
    x0, y0 = 305_000.0, 7_650_000.0
    gx = rng.uniform(0, 900, N)
    gy = rng.uniform(0, 650, N)
    # leve agrupamento (amostragem em transectos)
    gx += 25 * np.sin(gy / 90)
    coords = np.c_[gx, gy]

    g_elev = _grf(coords, rng, 380)
    g_text = _grf(coords, rng, 240)
    g_ph = _grf(coords, rng, 210)
    g_loc = _grf(coords, rng, 110)

    # Cenário realista: a textura (argila) acompanha o relevo — solos mais argilosos
    # nas cotas mais baixas (deposição). Isso dá a `elevacao` valor como deriva externa
    # e a `materia_organica` / `ctc` valor como variável secundária de co-krigagem.
    elevacao = 512 + 11.0 * g_elev + rng.normal(0, 0.5, N)

    clay = np.clip(36 + 9.0 * _z(0.45 * g_text - 0.55 * g_elev) + rng.normal(0, 1.0, N), 12, 60)
    silt = np.clip(24 + 5.0 * _z(0.6 * g_text - 0.2 * g_loc) + rng.normal(0, 1.1, N), 8, 40)
    sand = np.clip(100 - clay - silt, 5, 80)
    tot = clay + silt + sand
    clay, silt, sand = 100 * clay / tot, 100 * silt / tot, 100 * sand / tot

    ph = np.clip(5.5 + 0.42 * _z(0.6 * g_ph + 0.2 * g_elev + 0.2 * g_text)
                 + rng.normal(0, 0.12, N), 4.2, 6.9)
    materia_organica = np.clip(2.8 + 0.8 * _z(0.30 * g_text - 0.34 * g_elev + 0.36 * g_loc)
                               + rng.normal(0, 0.35, N), 0.8, 5.2)
    fosforo = np.clip(np.exp(2.5 + 0.55 * _z(0.8 * g_loc + 0.2 * g_ph)
                             + rng.normal(0, 0.25, N)), 1.5, 65)

    potassio = np.clip(0.26 + 0.11 * _z(0.5 * g_ph + 0.5 * g_loc) + rng.normal(0, 0.02, N), 0.04, 0.95)
    calcio = np.clip(3.3 + 1.3 * _z(0.45 * g_ph + 0.55 * g_text) + rng.normal(0, 0.18, N), 0.4, 8.5)
    magnesio = np.clip(1.15 + 0.5 * _z(0.6 * g_ph + 0.4 * g_loc) + rng.normal(0, 0.08, N), 0.2, 3.6)
    h_al = np.clip(3.6 - 0.9 * _z(g_ph) + rng.normal(0, 0.2, N), 0.6, 7.5)

    ctc = calcio + magnesio + potassio + h_al
    sat_bases = 100 * (calcio + magnesio + potassio) / ctc

    df = pd.DataFrame({
        "ponto_id": [f"P{i:03d}" for i in range(1, N + 1)],
        "coord_x": np.round(x0 + gx, 2),
        "coord_y": np.round(y0 + gy, 2),
        "elevacao_m": np.round(elevacao, 2),
        "argila_pct": np.round(clay, 1),
        "silte_pct": np.round(silt, 1),
        "areia_pct": np.round(sand, 1),
        "ph_h2o": np.round(ph, 2),
        "materia_organica_pct": np.round(materia_organica, 2),
        "fosforo_mg_dm3": np.round(fosforo, 1),
        "potassio_cmolc_dm3": np.round(potassio, 3),
        "calcio_cmolc_dm3": np.round(calcio, 2),
        "magnesio_cmolc_dm3": np.round(magnesio, 2),
        "ctc_cmolc_dm3": np.round(ctc, 2),
        "saturacao_bases_pct": np.round(sat_bases, 1),
    })

    # ------- problemas propositais para a tela de diagnóstico -------
    df.loc[5, "ph_h2o"] = np.nan
    df.loc[27, "fosforo_mg_dm3"] = np.nan
    df.loc[41, "materia_organica_pct"] = np.nan
    df.loc[63, "argila_pct"] = np.nan
    df.loc[88, "calcio_cmolc_dm3"] = np.nan
    df.loc[120, "ph_h2o"] = np.nan
    df.loc[200, "elevacao_m"] = np.nan

    df.loc[150, "fosforo_mg_dm3"] = 480.0          # outlier grosseiro
    df.loc[151, "potassio_cmolc_dm3"] = -0.2       # valor negativo impossível

    # ponto coincidente (mesma coordenada do vizinho)
    df.loc[300, ["coord_x", "coord_y"]] = df.loc[299, ["coord_x", "coord_y"]].to_numpy()

    # coordenada inválida
    df.loc[350, "coord_x"] = np.nan

    # duas linhas duplicadas
    df = pd.concat([df, df.iloc[[10, 60]]], ignore_index=True)

    return df


def main() -> None:
    df = build()
    xlsx = OUT / "demo_soil.xlsx"
    csv = OUT / "demo_soil.csv"
    with pd.ExcelWriter(xlsx, engine="xlsxwriter") as xw:
        df.to_excel(xw, index=False, sheet_name="dados")
    df.to_csv(csv, index=False)
    print(f"OK  {xlsx}  ({len(df)} linhas, {df.shape[1]} colunas)")
    print(f"OK  {csv}")


if __name__ == "__main__":
    main()
