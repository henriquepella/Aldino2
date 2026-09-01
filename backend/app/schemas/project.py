from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    client: str = Field(default="", max_length=255)
    technical_lead: str = Field(default="", max_length=255)
    description: str = ""
    variable_units: str = Field(default="", max_length=255)
    analysis_date: str = Field(default="", max_length=32)
    crs: str = Field(default="", max_length=64)
    crs_label: str = Field(default="", max_length=128)
    settings: dict = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    client: str | None = None
    technical_lead: str | None = None
    description: str | None = None
    variable_units: str | None = None
    analysis_date: str | None = None
    crs: str | None = None
    crs_label: str | None = None
    settings: dict | None = None


class ProjectOut(ProjectBase):
    id: str
    owner_id: str
    created_at: dt.datetime
    updated_at: dt.datetime
    dataset_count: int = 0
    run_count: int = 0
    latest_run_id: str | None = None

    model_config = {"from_attributes": True}
