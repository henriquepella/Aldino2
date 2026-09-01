"""Leitura robusta e segura de planilhas Excel/CSV (seções 2, 40, 46).

- valida extensão
- detecta separador / separador decimal (inclui padrão brasileiro `;` + `,`)
- normaliza nomes de colunas e remove colunas/linhas totalmente vazias
- tenta converter colunas de texto que são, na verdade, numéricas
- nunca executa fórmulas/macros (pandas lê apenas valores)
"""
from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.core.config import settings

EXCEL_EXT = {".xlsx", ".xls"}
CSV_EXT = {".csv", ".txt", ".tsv"}


class IngestError(ValueError):
    """Arquivo inválido / não legível."""


def file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dedupe_columns(cols: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    for c in cols:
        c = (str(c).strip() or "coluna")
        if c in seen:
            seen[c] += 1
            out.append(f"{c}.{seen[c]}")
        else:
            seen[c] = 0
            out.append(c)
    return out


def _sniff_csv(sample: str) -> tuple[str, str]:
    """Retorna (sep, decimal)."""
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        sep = dialect.delimiter
    except csv.Error:
        counts = {d: sample.count(d) for d in [",", ";", "\t", "|"]}
        sep = max(counts, key=counts.get) or ","
    # separador decimal: se sep é ';' e há muitos '0,0', decimal é ','
    decimal = "."
    if sep == ";" and sample.count(",") > sample.count("."):
        decimal = ","
    return sep, decimal


def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        s = df[col]
        if s.dtype != object:
            continue
        cleaned = (
            s.astype(str)
            .str.strip()
            .str.replace(" ", "", regex=False)
        )
        non_empty = cleaned.replace(
            {"": np.nan, "nan": np.nan, "None": np.nan, "NaN": np.nan, "-": np.nan}
        ).notna()
        n = int(non_empty.sum())
        if n == 0:
            continue

        # Prioriza o formato internacional ('.' decimal). Só interpreta como
        # formato brasileiro ('.' milhar + ',' decimal) quando há vírgula e
        # essa leitura recupera claramente mais valores.
        intl = pd.to_numeric(cleaned, errors="coerce")
        has_comma = bool(cleaned.str.contains(",", regex=False).any())

        if not has_comma:
            if intl.notna().sum() >= 0.85 * n:
                df[col] = intl
            continue

        br = pd.to_numeric(
            cleaned.str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
            errors="coerce",
        )
        if br.notna().sum() >= 0.85 * n and br.notna().sum() >= intl.notna().sum():
            df[col] = br
        elif intl.notna().sum() >= 0.85 * n:
            df[col] = intl
    return df


def read_table(
    path: str | Path,
    *,
    sheet: str | int | None = None,
    max_bytes: int | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    path = Path(path)
    ext = path.suffix.lower()
    if ext not in settings.allowed_upload_extensions and ext not in (EXCEL_EXT | CSV_EXT):
        raise IngestError(f"Extensão não suportada: {ext}")

    size = path.stat().st_size
    limit = max_bytes or settings.max_upload_bytes
    if size > limit:
        raise IngestError(
            f"Arquivo excede o limite de {limit / 1024 / 1024:.0f} MB."
        )

    meta: dict[str, Any] = {"filename": path.name, "size": size, "ext": ext}

    if ext in EXCEL_EXT:
        engine = "openpyxl" if ext == ".xlsx" else "xlrd"
        try:
            xls = pd.ExcelFile(path, engine=engine)
        except Exception as exc:  # noqa: BLE001
            raise IngestError(f"Não foi possível abrir o Excel: {exc}") from exc
        meta["sheets"] = xls.sheet_names
        target = sheet if sheet is not None else xls.sheet_names[0]
        meta["sheet"] = target
        # deixa o pandas inferir os tipos das células do Excel (já são tipadas);
        # _coerce_numeric cuida apenas das colunas que sobrarem como texto.
        df = xls.parse(target)
    elif ext in CSV_EXT:
        raw = path.read_bytes()
        encoding = "utf-8"
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            encoding = "latin-1"
            text = raw.decode("latin-1")
        sep, decimal = _sniff_csv(text[:16384])
        meta.update(encoding=encoding, sep=sep, decimal=decimal)
        try:
            df = pd.read_csv(
                io.StringIO(text),
                sep=sep,
                decimal=decimal,
                dtype=object,
                skip_blank_lines=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise IngestError(f"Não foi possível ler o CSV: {exc}") from exc
    else:  # pragma: no cover
        raise IngestError(f"Extensão não suportada: {ext}")

    if df.empty or df.shape[1] == 0:
        raise IngestError("A planilha não contém dados.")

    df.columns = _dedupe_columns([str(c) for c in df.columns])
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
    df = df.reset_index(drop=True)
    df = _coerce_numeric(df)

    if df.shape[0] < 3:
        raise IngestError("São necessárias ao menos 3 linhas de dados.")

    meta["row_count"] = int(df.shape[0])
    meta["col_count"] = int(df.shape[1])
    return df, meta
