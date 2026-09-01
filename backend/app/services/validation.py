"""Diagnóstico da base e limpeza de registros (seção 5).

Produz a tabela "Diagnóstico da Base", os contadores para o dashboard e uma
lista de linhas problemáticas que o usuário pode excluir antes de continuar.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.schemas.dataset import (
    DiagnosticItem,
    RowFlag,
    ValidationResult,
)

COORD_TOL = 1e-6  # tolerância para pontos "coincidentes" em coordenadas nativas


def _status(ok: bool, warn: bool = False) -> str:
    if ok:
        return "ok"
    return "warn" if warn else "error"


def _iqr_outliers(v: np.ndarray, k: float = 3.0) -> np.ndarray:
    fin = np.isfinite(v)
    if fin.sum() < 8:
        return np.zeros_like(v, dtype=bool)
    q1, q3 = np.nanpercentile(v[fin], [25, 75])
    iqr = q3 - q1
    if iqr == 0:
        return np.zeros_like(v, dtype=bool)
    lo, hi = q1 - k * iqr, q3 + k * iqr
    out = np.zeros_like(v, dtype=bool)
    out[fin] = (v[fin] < lo) | (v[fin] > hi)
    return out


def validate(df: pd.DataFrame, config: dict[str, Any]) -> ValidationResult:
    n_rows, n_cols = df.shape
    x_col = config.get("x_col")
    y_col = config.get("y_col")
    primary = config.get("primary")
    crs = config.get("crs", "")
    negatives_allowed = bool(config.get("negatives_allowed", True))

    analysis_vars = [
        v for v in [
            primary,
            *(config.get("secondary") or []),
            *(config.get("explanatory") or []),
            config.get("aux_drift"),
        ] if v and v in df.columns
    ]
    analysis_vars = list(dict.fromkeys(analysis_vars))

    issues: dict[int, list[str]] = {}

    def flag(idx, msg):
        issues.setdefault(int(idx), []).append(msg)

    # ---- coordenadas ----
    x = pd.to_numeric(df[x_col], errors="coerce") if x_col in df else pd.Series([np.nan] * n_rows)
    y = pd.to_numeric(df[y_col], errors="coerce") if y_col in df else pd.Series([np.nan] * n_rows)
    bad_coord = ~np.isfinite(x) | ~np.isfinite(y)
    if crs and "4326" in str(crs):
        bad_coord |= (x.abs() > 180) | (y.abs() > 90)
    for i in np.where(bad_coord.to_numpy())[0]:
        flag(i, "coordenada inválida")
    n_invalid_coords = int(bad_coord.sum())

    valid_xy = ~bad_coord
    n_valid_coords = int(valid_xy.sum())

    # ---- pontos coincidentes ----
    coincident = np.zeros(n_rows, dtype=bool)
    if n_valid_coords > 1:
        key = (
            np.round(x.to_numpy() / max(COORD_TOL, 1e-9)).astype("float64"),
            np.round(y.to_numpy() / max(COORD_TOL, 1e-9)).astype("float64"),
        )
        pairs = pd.DataFrame({"x": key[0], "y": key[1]})
        dup_mask = pairs.duplicated(keep=False) & valid_xy.to_numpy()
        coincident = dup_mask.to_numpy()
        for i in np.where(coincident)[0]:
            flag(i, "ponto coincidente")
    n_coincident = int(coincident.sum())

    # ---- linhas duplicadas ----
    dup_rows = df.duplicated(keep="first")
    for i in np.where(dup_rows.to_numpy())[0]:
        flag(i, "linha duplicada")
    n_dup = int(dup_rows.sum())

    # ---- ausentes ----
    col_missing = {c: int(df[c].isna().sum()) for c in df.columns if df[c].isna().any()}
    n_missing_cells = int(df.isna().sum().sum())
    for v in analysis_vars:
        for i in np.where(df[v].isna().to_numpy())[0]:
            flag(i, f"ausente: {v}")

    # ---- infinitos / negativos / outliers ----
    n_inf = 0
    n_neg = 0
    n_out = 0
    for v in analysis_vars:
        col = pd.to_numeric(df[v], errors="coerce").to_numpy(float)
        inf_mask = np.isinf(col)
        n_inf += int(inf_mask.sum())
        for i in np.where(inf_mask)[0]:
            flag(i, f"infinito: {v}")
        neg_mask = np.isfinite(col) & (col < 0)
        if neg_mask.any():
            n_neg += int(neg_mask.sum())
            if not negatives_allowed:
                for i in np.where(neg_mask)[0]:
                    flag(i, f"negativo: {v}")
        out_mask = _iqr_outliers(col)
        n_out += int(out_mask.sum())
        for i in np.where(out_mask)[0]:
            flag(i, f"outlier: {v}")

    # ---- tipos ----
    dtype_problem = []
    for v in [x_col, y_col, primary, *analysis_vars]:
        if v and v in df.columns:
            raw_non_na = df[v].notna().sum()
            num_ok = pd.to_numeric(df[v], errors="coerce").notna().sum()
            if raw_non_na and num_ok < raw_non_na:
                dtype_problem.append(f"{v} ({raw_non_na - num_ok} não numéricos)")

    # ---- CRS ----
    crs_ok = True
    crs_note = ""
    if not crs:
        crs_ok = False
        crs_note = "CRS não definido"
    else:
        try:
            from pyproj import CRS as _CRS

            _CRS.from_user_input(crs)
        except Exception:  # noqa: BLE001
            crs_ok = False
            crs_note = f"CRS '{crs}' não reconhecido"

    n_numeric_vars = int(sum(1 for c in df.columns if pd.to_numeric(df[c], errors="coerce").notna().sum() >= 0.7 * df[c].notna().sum() and df[c].notna().any()))

    summary = [
        DiagnosticItem(item="Registros", value=f"{n_rows}", status="ok"),
        DiagnosticItem(
            item="Coordenadas válidas", value=f"{n_valid_coords}",
            status=_status(n_invalid_coords == 0, warn=True),
            detail=f"{n_invalid_coords} inválidas" if n_invalid_coords else "",
        ),
        DiagnosticItem(
            item="Valores ausentes", value=f"{n_missing_cells}",
            status=_status(n_missing_cells == 0, warn=True),
            detail=f"em {len(col_missing)} colunas" if col_missing else "",
        ),
        DiagnosticItem(
            item="Linhas duplicadas", value=f"{n_dup}",
            status=_status(n_dup == 0, warn=True),
        ),
        DiagnosticItem(
            item="Pontos coincidentes", value=f"{n_coincident}",
            status=_status(n_coincident == 0, warn=True),
            detail="podem exigir tratamento na krigagem" if n_coincident else "",
        ),
        DiagnosticItem(item="Variáveis numéricas", value=f"{n_numeric_vars}", status="ok"),
        DiagnosticItem(
            item="Valores infinitos", value=f"{n_inf}",
            status=_status(n_inf == 0, warn=False if n_inf else True),
        ),
        DiagnosticItem(
            item="Valores negativos", value=f"{n_neg}",
            status=_status(n_neg == 0 or negatives_allowed, warn=True),
            detail="permitidos pela configuração" if (n_neg and negatives_allowed) else "",
        ),
        DiagnosticItem(
            item="Possíveis outliers", value=f"{n_out}",
            status=_status(n_out == 0, warn=True),
            detail="critério IQR (k=3) nas variáveis de análise" if n_out else "",
        ),
        DiagnosticItem(
            item="Tipos de dados", value="OK" if not dtype_problem else "Atenção",
            status=_status(not dtype_problem, warn=True),
            detail="; ".join(dtype_problem),
        ),
        DiagnosticItem(
            item="Sistema de coordenadas", value=crs or "—",
            status=_status(crs_ok, warn=True), detail=crs_note,
        ),
    ]

    row_flags = [
        RowFlag(
            row_index=idx,
            issues=sorted(set(msgs)),
            severity="error" if any(
                m.startswith(("coordenada", "infinito")) for m in msgs
            ) else "warn",
        )
        for idx, msgs in sorted(issues.items())
    ]

    can_proceed = n_valid_coords >= 3 and (primary in df.columns if primary else True)
    notes = []
    if not can_proceed:
        notes.append("São necessárias ao menos 3 coordenadas válidas e a variável principal definida.")
    if n_coincident:
        notes.append("Pontos coincidentes serão tratados com um pequeno jitter na krigagem, se necessário.")

    counts = {
        "rows": n_rows, "cols": n_cols, "numeric_vars": n_numeric_vars,
        "missing_cells": n_missing_cells, "duplicate_rows": n_dup,
        "coincident_points": n_coincident, "invalid_coords": n_invalid_coords,
        "valid_coords": n_valid_coords, "infinite_values": n_inf,
        "negative_values": n_neg, "outliers": n_out,
        "flagged_rows": len(row_flags),
    }

    return ValidationResult(
        summary=summary,
        counts=counts,
        column_missing=col_missing,
        row_flags=row_flags,
        crs_ok=crs_ok,
        can_proceed=can_proceed,
        notes=notes,
    )


def apply_cleaning(
    df: pd.DataFrame, config: dict[str, Any], *,
    drop_row_indices: list[int] | None = None,
    drop_duplicates: bool = False,
    drop_missing_in_coords: bool = True,
    drop_missing_in_primary: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    original_n = len(df)
    out = df.copy()
    report: dict[str, Any] = {}

    if drop_row_indices:
        out = out.drop(index=[i for i in drop_row_indices if i in out.index])
        report["dropped_selected"] = original_n - len(out)

    if drop_duplicates:
        before = len(out)
        out = out.drop_duplicates(keep="first")
        report["dropped_duplicates"] = before - len(out)

    x_col, y_col, primary = config.get("x_col"), config.get("y_col"), config.get("primary")
    if drop_missing_in_coords and x_col in out and y_col in out:
        before = len(out)
        xok = pd.to_numeric(out[x_col], errors="coerce").notna()
        yok = pd.to_numeric(out[y_col], errors="coerce").notna()
        out = out[xok & yok]
        report["dropped_bad_coords"] = before - len(out)

    if drop_missing_in_primary and primary in out:
        before = len(out)
        out = out[pd.to_numeric(out[primary], errors="coerce").notna()]
        report["dropped_missing_primary"] = before - len(out)

    out = out.reset_index(drop=True)
    report["final_n"] = len(out)
    report["removed_total"] = original_n - len(out)
    return out, report
