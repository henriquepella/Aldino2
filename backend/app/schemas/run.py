from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, Field


class RunCreate(BaseModel):
    dataset_id: str
    mode: Literal["full", "custom"] = "full"
    # Sobrescreve parâmetros avançados (seção 36). Vazio => usa defaults do projeto/sistema.
    advanced: dict = Field(default_factory=dict)
    # Para mode="custom": lista de chaves de passo a executar.
    steps: list[str] | None = None


class StepState(BaseModel):
    key: str
    title: str = ""
    status: str = "pending"  # pending | running | ok | skipped | failed
    reason: str | None = None
    started_at: dt.datetime | None = None
    finished_at: dt.datetime | None = None
    n_tables: int = 0
    n_figures: int = 0
    metrics: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "ignore"}


class RunOut(BaseModel):
    id: str
    project_id: str
    dataset_id: str
    status: str
    mode: str
    progress: float
    current_step: str
    steps: list[StepState] = Field(default_factory=list)
    log: list[dict] = Field(default_factory=list)
    metrics_summary: dict = Field(default_factory=dict)
    manifest: dict = Field(default_factory=dict)
    lib_versions: dict = Field(default_factory=dict)
    error: str = ""
    started_at: dt.datetime | None = None
    finished_at: dt.datetime | None = None
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class ArtifactOut(BaseModel):
    id: str
    run_id: str
    kind: str
    step_key: str
    name: str
    title: str
    caption: str
    mime: str
    size: int
    url: str
    data: dict = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class StepResultOut(BaseModel):
    key: str
    title: str
    status: str
    reason: str | None = None
    interpretation: str | None = None
    metrics: dict = Field(default_factory=dict)
    params_used: dict = Field(default_factory=dict)
    tables: list[ArtifactOut] = Field(default_factory=list)
    figures: list[ArtifactOut] = Field(default_factory=list)


class RunResultsOut(BaseModel):
    run: RunOut
    steps: list[StepResultOut]
    report_url: str | None = None
    package_url: str | None = None
