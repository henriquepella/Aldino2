from __future__ import annotations

import shutil

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DbSession, OwnedProject
from app.models import AnalysisRun, Dataset, Project, RunStatus
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services import storage

router = APIRouter(prefix="/projects", tags=["projects"])


def _to_out(db: DbSession, p: Project) -> ProjectOut:
    ds = db.scalar(select(func.count(Dataset.id)).where(Dataset.project_id == p.id)) or 0
    rc = db.scalar(select(func.count(AnalysisRun.id)).where(AnalysisRun.project_id == p.id)) or 0
    latest = db.scalar(
        select(AnalysisRun.id)
        .where(AnalysisRun.project_id == p.id)
        .order_by(AnalysisRun.created_at.desc())
        .limit(1)
    )
    out = ProjectOut.model_validate(p)
    out.dataset_count = ds
    out.run_count = rc
    out.latest_run_id = latest
    return out


@router.get("", response_model=list[ProjectOut])
def list_projects(db: DbSession, user: CurrentUser):
    rows = db.scalars(
        select(Project).where(Project.owner_id == user.id).order_by(Project.updated_at.desc())
    ).all()
    return [_to_out(db, p) for p in rows]


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: DbSession, user: CurrentUser):
    p = Project(owner_id=user.id, **payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return _to_out(db, p)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project: OwnedProject, db: DbSession):
    return _to_out(db, project)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(payload: ProjectUpdate, project: OwnedProject, db: DbSession):
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(project, k, v)
    db.commit()
    db.refresh(project)
    return _to_out(db, project)


@router.delete("/{project_id}", status_code=204)
def delete_project(project: OwnedProject, db: DbSession, user: CurrentUser):
    pdir = storage.project_dir(user.id, project.id)
    db.delete(project)
    db.commit()
    shutil.rmtree(pdir, ignore_errors=True)


@router.post("/{project_id}/duplicate", response_model=ProjectOut, status_code=201)
def duplicate_project(project: OwnedProject, db: DbSession, user: CurrentUser):
    clone = Project(
        owner_id=user.id,
        name=f"{project.name} (cópia)",
        client=project.client, technical_lead=project.technical_lead,
        description=project.description, variable_units=project.variable_units,
        analysis_date=project.analysis_date, crs=project.crs, crs_label=project.crs_label,
        settings=dict(project.settings or {}),
    )
    db.add(clone)
    db.flush()

    for ds in project.datasets:
        if not ds.is_active:
            continue
        new_ds = Dataset(
            project_id=clone.id, version=ds.version,
            original_filename=ds.original_filename, file_size=ds.file_size,
            content_hash=ds.content_hash, row_count=ds.row_count, col_count=ds.col_count,
            columns=ds.columns, detection=ds.detection, config=ds.config,
            validation=ds.validation, is_active=True,
        )
        db.add(new_ds)
        db.flush()
        if ds.raw_path:
            src = storage.abspath(ds.raw_path)
            if src.exists():
                dst = storage.raw_dir(user.id, clone.id) / src.name
                shutil.copy2(src, dst)
                new_ds.raw_path = storage.rel(dst)
        if ds.clean_path:
            src = storage.abspath(ds.clean_path)
            if src.exists():
                dst = storage.dataset_dir(user.id, clone.id, new_ds.id) / "clean.csv"
                shutil.copy2(src, dst)
                new_ds.clean_path = storage.rel(dst)

    db.commit()
    db.refresh(clone)
    return _to_out(db, clone)
