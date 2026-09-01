from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.core.deps import DbSession, OwnedRun
from app.models import ArtifactKind, ResultArtifact
from app.services import storage

router = APIRouter(tags=["reports"])


@router.get("/runs/{run_id}/report.pdf")
def get_report(run: OwnedRun, db: DbSession):
    art = db.scalar(
        select(ResultArtifact).where(
            ResultArtifact.run_id == run.id, ResultArtifact.kind == ArtifactKind.report
        )
    )
    if art is None:
        raise HTTPException(404, "Relatório ainda não disponível.")
    path = storage.abspath(art.path)
    if not path.exists():
        raise HTTPException(404, "Arquivo do relatório ausente.")
    return FileResponse(
        path, media_type="application/pdf",
        filename=f"relatorio_{run.project_id[:8]}.pdf",
    )
