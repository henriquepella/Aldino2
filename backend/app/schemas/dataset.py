from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Estrutura de colunas / detecção (seções 3-4)
# --------------------------------------------------------------------------- #
class ColumnInfo(BaseModel):
    name: str
    dtype: str
    is_numeric: bool
    n_total: int
    n_missing: int
    n_unique: int
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    std: float | None = None
    sample_values: list[Any] = Field(default_factory=list)
    role_guess: str = "unknown"  # coordinate_x | coordinate_y | id | variable | datetime | text | unknown


class CoordinateCandidate(BaseModel):
    column: str
    score: float
    reasons: list[str] = Field(default_factory=list)


class DetectionResult(BaseModel):
    columns: list[ColumnInfo]
    coord_x: str | None = None
    coord_y: str | None = None
    coord_kind: Literal["lonlat", "utm", "planar", "unknown"] = "unknown"
    coord_confidence: float = 0.0
    candidates_x: list[CoordinateCandidate] = Field(default_factory=list)
    candidates_y: list[CoordinateCandidate] = Field(default_factory=list)
    crs_suggested: str | None = None
    crs_label: str = ""
    crs_confidence: float = 0.0
    crs_reason: str = ""
    crs_alternatives: list[dict] = Field(default_factory=list)
    numeric_variables: list[str] = Field(default_factory=list)
    id_like_columns: list[str] = Field(default_factory=list)
    primary_guess: str | None = None
    secondary_guess: list[str] = Field(default_factory=list)
    explanatory_guess: list[str] = Field(default_factory=list)
    aux_drift_guess: str | None = None
    notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Configuração confirmada pelo usuário (seções 3-4-6-36)
# --------------------------------------------------------------------------- #
class DatasetConfig(BaseModel):
    x_col: str
    y_col: str
    crs: str = "EPSG:4326"
    crs_label: str = ""
    id_col: str | None = None
    primary: str
    secondary: list[str] = Field(default_factory=list)
    explanatory: list[str] = Field(default_factory=list)
    aux_drift: str | None = None
    bivariate_pairs: list[tuple[str, str]] = Field(default_factory=list)
    negatives_allowed: bool = True
    advanced: dict = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Diagnóstico da base (seção 5)
# --------------------------------------------------------------------------- #
class DiagnosticItem(BaseModel):
    item: str
    value: str
    status: Literal["ok", "warn", "error"]
    detail: str = ""


class RowFlag(BaseModel):
    row_index: int
    issues: list[str]
    severity: Literal["warn", "error"]


class ValidationResult(BaseModel):
    summary: list[DiagnosticItem]
    counts: dict[str, int]
    column_missing: dict[str, int] = Field(default_factory=dict)
    row_flags: list[RowFlag] = Field(default_factory=list)
    crs_ok: bool = True
    can_proceed: bool = True
    notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Requests / responses
# --------------------------------------------------------------------------- #
class DatasetConfigUpdate(BaseModel):
    config: DatasetConfig


class CleanRequest(BaseModel):
    drop_row_indices: list[int] = Field(default_factory=list)
    drop_duplicates: bool = False
    drop_missing_in_coords: bool = True
    drop_missing_in_primary: bool = False


class DatasetOut(BaseModel):
    id: str
    project_id: str
    version: int
    original_filename: str
    file_size: int
    row_count: int
    col_count: int
    columns: list[ColumnInfo]
    detection: DetectionResult | None = None
    config: DatasetConfig | None = None
    validation: ValidationResult | None = None
    is_active: bool
    created_at: dt.datetime

    model_config = {"from_attributes": True}
