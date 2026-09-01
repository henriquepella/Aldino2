"""Identificação automática de coordenadas, variáveis e CRS (seções 3-4-46).

A detecção **não** depende exclusivamente dos nomes das colunas: combina nome,
tipo de dado, faixa numérica, número de valores únicos, presença de casas
decimais e correlação entre colunas.
"""
from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

from app.schemas.dataset import (
    ColumnInfo,
    CoordinateCandidate,
    DetectionResult,
)

# ---- padrões de nome ------------------------------------------------------- #
_X_NAME = re.compile(
    r"^(x|lon|long|lng|longitude|easting|este|leste|utm[_\s-]?e|coord[_\s-]?x|"
    r"x[_\s-]?utm|e|pos[_\s-]?x|gps[_\s-]?x)$",
    re.I,
)
_Y_NAME = re.compile(
    r"^(y|lat|latitude|northing|norte|utm[_\s-]?n|coord[_\s-]?y|y[_\s-]?utm|n|"
    r"pos[_\s-]?y|gps[_\s-]?y)$",
    re.I,
)
_ID_NAME = re.compile(
    r"^(id|id[_\s-]?\w*|fid|objectid|oid|codigo|cod|c[oó]d[_\s-]?\w*|ponto|"
    r"pt|amostra|sample|plot|parcela|talhao|talh[aã]o|n[uú]mero|numero|num|seq)$",
    re.I,
)
_ELEV_NAME = re.compile(
    r"(elev|altitude|altura|cota|dem|mde|mdt|z[_\s-]?coord|relevo)", re.I
)
_DATE_NAME = re.compile(r"(data|date|dt|ano|year|mes|month|dia|day|timestamp|hora)", re.I)


def _has_decimals(a: np.ndarray) -> float:
    a = a[np.isfinite(a)]
    if a.size == 0:
        return 0.0
    return float(np.mean(np.abs(a - np.round(a)) > 1e-9))


def _frac_unique(s: pd.Series) -> float:
    n = s.notna().sum()
    return float(s.nunique() / n) if n else 0.0


def profile_columns(df: pd.DataFrame) -> list[ColumnInfo]:
    infos: list[ColumnInfo] = []
    for col in df.columns:
        s = df[col]
        num = pd.to_numeric(s, errors="coerce")
        is_numeric = num.notna().sum() >= max(3, 0.7 * s.notna().sum()) and s.notna().sum() > 0
        parsed_dt = None
        if not is_numeric and _DATE_NAME.search(str(col)):
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                parsed_dt = pd.to_datetime(s, errors="coerce", dayfirst=True)
            if parsed_dt.notna().sum() < 0.7 * s.notna().sum():
                parsed_dt = None

        info = ColumnInfo(
            name=str(col),
            dtype=("float" if is_numeric else ("datetime" if parsed_dt is not None else "text")),
            is_numeric=bool(is_numeric),
            n_total=int(len(s)),
            n_missing=int(s.isna().sum()),
            n_unique=int(s.nunique(dropna=True)),
            sample_values=[
                None if (isinstance(v, float) and not np.isfinite(v)) else
                (round(float(v), 4) if isinstance(v, (int, float, np.number)) else str(v))
                for v in s.dropna().head(5).tolist()
            ],
        )
        if is_numeric:
            vals = num.to_numpy(float)
            fin = vals[np.isfinite(vals)]
            if fin.size:
                info.min = float(np.min(fin))
                info.max = float(np.max(fin))
                info.mean = float(np.mean(fin))
                info.std = float(np.std(fin, ddof=1)) if fin.size > 1 else 0.0

        # palpite de papel
        name = str(col)
        if parsed_dt is not None:
            info.role_guess = "datetime"
        elif is_numeric and _ID_NAME.match(name) and _frac_unique(s) > 0.98:
            info.role_guess = "id"
        elif not is_numeric:
            info.role_guess = "text"
        else:
            info.role_guess = "variable"
        infos.append(info)
    return infos


def _coord_score(col: ColumnInfo, axis: str, s: pd.Series) -> tuple[float, list[str]]:
    if not col.is_numeric or col.min is None:
        return 0.0, []
    score = 0.0
    reasons: list[str] = []
    name = col.name
    rx = _X_NAME.match(name) if axis == "x" else _Y_NAME.match(name)
    if rx:
        score += 3.0
        reasons.append(f"nome corresponde a coordenada {axis.upper()}")
    elif (_X_NAME.match(name) if axis == "y" else _Y_NAME.match(name)):
        score -= 2.0  # nome é do outro eixo

    lo, hi = col.min, col.max
    dec = _has_decimals(pd.to_numeric(s, errors="coerce").to_numpy(float))

    if axis == "y" and -90 <= lo and hi <= 90 and dec > 0.5:
        score += 2.5
        reasons.append("faixa compatível com latitude (−90..90)")
    if axis == "x" and -180 <= lo and hi <= 180 and dec > 0.5:
        score += 2.0
        reasons.append("faixa compatível com longitude (−180..180)")
    # UTM
    if axis == "x" and 100_000 <= lo and hi <= 1_100_000:
        score += 2.0
        reasons.append("faixa compatível com easting UTM")
    if axis == "y" and 0 <= lo and hi <= 10_600_000 and (hi - lo) < 2_000_000:
        score += 1.5
        reasons.append("faixa compatível com northing UTM")

    frac_u = _frac_unique(s)
    if frac_u > 0.5:
        score += 1.0
        reasons.append(f"{frac_u*100:.0f}% de valores distintos")
    if _ID_NAME.match(name) and frac_u > 0.98 and dec < 0.05:
        score -= 3.0
        reasons.append("parece coluna de identificador")
    if col.std and lo != hi:
        score += 0.5
    if _DATE_NAME.search(name):
        score -= 2.0
    return score, reasons


def _guess_crs(kind: str, x: ColumnInfo | None, y: ColumnInfo | None) -> dict[str, Any]:
    if kind == "lonlat":
        return {
            "suggested": "EPSG:4326",
            "label": "WGS 84 (graus decimais)",
            "confidence": 0.85,
            "reason": "coordenadas em graus decimais dentro de −180..180 / −90..90",
            "alternatives": [
                {"epsg": "EPSG:4674", "label": "SIRGAS 2000 (geográfico)"},
                {"epsg": "EPSG:4618", "label": "SAD 69 (geográfico)"},
            ],
        }
    if kind == "utm":
        return {
            "suggested": "EPSG:31982",
            "label": "SIRGAS 2000 / UTM 22S (verifique a zona)",
            "confidence": 0.3,
            "reason": "coordenadas métricas com magnitude de easting/northing UTM; "
            "a zona não pode ser inferida sem a longitude — confirme manualmente",
            "alternatives": [
                {"epsg": f"EPSG:319{z}", "label": f"SIRGAS 2000 / UTM {z-60}S"}
                for z in range(77, 86)
            ]
            + [{"epsg": "EPSG:32722", "label": "WGS 84 / UTM 22S"}],
        }
    return {
        "suggested": None,
        "label": "",
        "confidence": 0.0,
        "reason": "não foi possível inferir o sistema de coordenadas — informe o CRS/EPSG",
        "alternatives": [],
    }


def detect(df: pd.DataFrame) -> DetectionResult:
    columns = profile_columns(df)
    by_name = {c.name: c for c in columns}

    cand_x, cand_y = [], []
    for c in columns:
        sx, rx = _coord_score(c, "x", df[c.name])
        sy, ry = _coord_score(c, "y", df[c.name])
        if sx > 0:
            cand_x.append(CoordinateCandidate(column=c.name, score=round(sx, 2), reasons=rx))
        if sy > 0:
            cand_y.append(CoordinateCandidate(column=c.name, score=round(sy, 2), reasons=ry))
    cand_x.sort(key=lambda c: -c.score)
    cand_y.sort(key=lambda c: -c.score)

    coord_x = cand_x[0].column if cand_x else None
    coord_y = cand_y[0].column if cand_y else None
    # evita mesma coluna para os dois eixos
    if coord_x and coord_y and coord_x == coord_y:
        if len(cand_y) > 1:
            coord_y = cand_y[1].column
        elif len(cand_x) > 1:
            coord_x = cand_x[1].column

    kind = "unknown"
    conf = 0.0
    if coord_x and coord_y:
        cx, cy = by_name[coord_x], by_name[coord_y]
        if (
            cx.min is not None and cy.min is not None
            and -180 <= cx.min and cx.max <= 180
            and -90 <= cy.min and cy.max <= 90
        ):
            kind = "lonlat"
        elif (cx.max or 0) > 100_000 and (cy.max or 0) > 100_000:
            kind = "utm"
        else:
            kind = "planar"
        top = (cand_x[0].score + cand_y[0].score)
        conf = float(min(0.98, max(0.2, top / 12.0)))

    crs = _guess_crs(kind, by_name.get(coord_x or ""), by_name.get(coord_y or ""))

    used = {coord_x, coord_y}
    numeric_vars = [
        c.name for c in columns
        if c.is_numeric and c.name not in used and c.role_guess == "variable"
    ]
    id_like = [c.name for c in columns if c.role_guess in ("id", "text", "datetime") and c.name not in used]

    # primária: variável numérica com mais dados e maior CV (mais informativa)
    def _cv(name: str) -> float:
        c = by_name[name]
        return abs(c.std / c.mean) if (c.std and c.mean) else 0.0

    primary = None
    if numeric_vars:
        primary = sorted(
            numeric_vars,
            key=lambda n: (by_name[n].n_total - by_name[n].n_missing, _cv(n)),
            reverse=True,
        )[0]

    secondary = [v for v in numeric_vars if v != primary]
    explanatory = list(secondary)

    aux = None
    if primary and secondary:
        base = pd.to_numeric(df[primary], errors="coerce")
        best_r = 0.0
        for v in secondary:
            other = pd.to_numeric(df[v], errors="coerce")
            r = base.corr(other)
            score = abs(r) if pd.notna(r) else 0.0
            if _ELEV_NAME.search(v):
                score += 0.15
            if score > best_r:
                best_r, aux = score, v
        if best_r < 0.35:
            aux = next((v for v in secondary if _ELEV_NAME.search(v)), None)

    notes: list[str] = []
    if not coord_x or not coord_y:
        notes.append("Não foi possível identificar automaticamente as duas coordenadas — selecione manualmente.")
    if kind == "utm":
        notes.append("Coordenadas UTM detectadas: confirme a zona/EPSG na tela de configuração.")
    if not numeric_vars:
        notes.append("Nenhuma variável numérica de análise foi detectada além das coordenadas.")

    return DetectionResult(
        columns=columns,
        coord_x=coord_x,
        coord_y=coord_y,
        coord_kind=kind,  # type: ignore[arg-type]
        coord_confidence=round(conf, 2),
        candidates_x=cand_x[:5],
        candidates_y=cand_y[:5],
        crs_suggested=crs["suggested"],
        crs_label=crs["label"],
        crs_confidence=crs["confidence"],
        crs_reason=crs["reason"],
        crs_alternatives=crs["alternatives"],
        numeric_variables=numeric_vars,
        id_like_columns=id_like,
        primary_guess=primary,
        secondary_guess=secondary,
        explanatory_guess=explanatory,
        aux_drift_guess=aux,
        notes=notes,
    )
