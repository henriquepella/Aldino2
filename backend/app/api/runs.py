from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.core.deps import DbSession, OwnedProject, OwnedRun
from app.models import AnalysisRun, ArtifactKind, Dataset, ResultArtifact, RunStatus
from app.schemas.run import (
    ArtifactOut,
    RunCreate,
    RunOut,
    RunResultsOut,
    StepResultOut,
)
from app.services import jobs, storage

router = APIRouter(tags=["runs"])

API = "/api"


def _run_out(run: AnalysisRun) -> RunOut:
    return RunOut(
        id=run.id, project_id=run.project_id, dataset_id=run.dataset_id,
        status=run.status.value if hasattr(run.status, "value") else str(run.status),
        mode=run.mode, progress=run.progress, current_step=run.current_step,
        steps=run.steps or [], log=run.log or [],
        metrics_summary=run.metrics_summary or {}, manifest=run.manifest or {},
        lib_versions=run.lib_versions or {}, error=run.error or "",
        started_at=run.started_at, finished_at=run.finished_at, created_at=run.created_at,
    )


def _artifact_out(a: ResultArtifact) -> ArtifactOut:
    base = f"{API}/runs/{a.run_id}/artifacts/{a.id}"
    data = dict(a.data or {})
    raw_variants = data.get("variants") or {}
    if raw_variants:
        # expõe URLs baixáveis (não os caminhos internos de armazenamento)
        data["variants"] = {
            fmt: (base if fmt == "png" else f"{base}?variant={fmt}") for fmt in raw_variants
        }
    return ArtifactOut(
        id=a.id, run_id=a.run_id, kind=a.kind.value if hasattr(a.kind, "value") else str(a.kind),
        step_key=a.step_key, name=a.name, title=a.title, caption=a.caption,
        mime=a.mime, size=a.size,
        url=base,
        data=data,
    )


@router.post("/projects/{project_id}/runs", response_model=RunOut, status_code=201)
def create_run(payload: RunCreate, project: OwnedProject, db: DbSession):
    dataset = db.get(Dataset, payload.dataset_id)
    if dataset is None or dataset.project_id != project.id:
        raise HTTPException(404, "Conjunto de dados não encontrado neste projeto.")
    if not dataset.config:
        raise HTTPException(400, "Configure e valide o conjunto de dados antes de executar a análise.")
    if dataset.validation and not dataset.validation.get("can_proceed", True):
        raise HTTPException(400, "O diagnóstico da base impede a execução. Corrija os registros problemáticos.")

    run = AnalysisRun(
        project_id=project.id, dataset_id=dataset.id, mode=payload.mode,
        status=RunStatus.pending,
        config={"advanced": payload.advanced or {}, "steps": payload.steps},
        steps=[], log=[],
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    jobs.submit(run.id)
    return _run_out(run)


@router.get("/projects/{project_id}/runs", response_model=list[RunOut])
def list_runs(project: OwnedProject, db: DbSession):
    rows = db.scalars(
        select(AnalysisRun).where(AnalysisRun.project_id == project.id)
        .order_by(AnalysisRun.created_at.desc())
    ).all()
    return [_run_out(r) for r in rows]


@router.get("/runs/{run_id}", response_model=RunOut)
def get_run(run: OwnedRun) -> RunOut:
    return _run_out(run)


@router.post("/runs/{run_id}/cancel", response_model=RunOut)
def cancel_run(run: OwnedRun, db: DbSession):
    if run.status in (RunStatus.done, RunStatus.failed, RunStatus.cancelled):
        raise HTTPException(409, "A execução já foi finalizada.")
    run.cancel_requested = True
    db.commit()
    db.refresh(run)
    return _run_out(run)


@router.get("/runs/{run_id}/results", response_model=RunResultsOut)
def get_results(run: OwnedRun, db: DbSession):
    arts = db.scalars(
        select(ResultArtifact).where(ResultArtifact.run_id == run.id)
        .order_by(ResultArtifact.step_key, ResultArtifact.created_at)
    ).all()

    by_step: dict[str, list[ResultArtifact]] = {}
    for a in arts:
        by_step.setdefault(a.step_key, []).append(a)

    manifest_steps = {s["key"]: s for s in (run.manifest or {}).get("steps", [])}
    step_keys = list(manifest_steps) or list(by_step)

    steps_out: list[StepResultOut] = []
    for key in step_keys:
        m = manifest_steps.get(key, {})
        arts_s = by_step.get(key, [])
        steps_out.append(StepResultOut(
            key=key,
            title=m.get("title", key),
            status=m.get("status", "ok"),
            reason=m.get("reason"),
            interpretation=m.get("interpretation"),
            metrics=m.get("metrics", {}),
            params_used=m.get("params_used", {}),
            tables=[_artifact_out(a) for a in arts_s if a.kind == ArtifactKind.table],
            figures=[_artifact_out(a) for a in arts_s
                     if a.kind in (ArtifactKind.figure, ArtifactKind.map)],
        ))

    report = next((a for a in arts if a.kind == ArtifactKind.report), None)
    package = next((a for a in arts if a.kind == ArtifactKind.package), None)
    return RunResultsOut(
        run=_run_out(run),
        steps=steps_out,
        report_url=f"{API}/runs/{run.id}/report.pdf" if report else None,
        package_url=f"{API}/runs/{run.id}/package.zip" if package else None,
    )


_VARIANT_MIME = {
    "png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf",
    "tif": "image/tiff", "csv": "text/csv",
}


@router.get("/runs/{run_id}/artifacts/{artifact_id}")
def download_artifact(
    run: OwnedRun,
    artifact_id: str,
    db: DbSession,
    variant: str | None = Query(default=None, description="png|svg|pdf|tif"),
):
    a = db.get(ResultArtifact, artifact_id)
    if a is None or a.run_id != run.id:
        raise HTTPException(404, "Artefato não encontrado.")

    rel = a.path
    mime = a.mime
    if variant:
        variants = (a.data or {}).get("variants", {})
        if variant not in variants:
            raise HTTPException(404, f"Variante '{variant}' indisponível para este artefato.")
        rel = variants[variant]
        mime = _VARIANT_MIME.get(variant, "application/octet-stream")

    path = storage.abspath(rel)
    if not path.exists():
        raise HTTPException(404, "Arquivo ausente no armazenamento.")
    return FileResponse(path, media_type=mime, filename=path.name)
