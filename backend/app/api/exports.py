from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select

from app.core.deps import DbSession, OwnedRun
from app.models import ArtifactKind, ResultArtifact
from app.services import storage

router = APIRouter(tags=["exports"])


@router.get("/runs/{run_id}/package.zip")
def get_package(run: OwnedRun, db: DbSession):
    art = db.scalar(
        select(ResultArtifact).where(
            ResultArtifact.run_id == run.id, ResultArtifact.kind == ArtifactKind.package
        )
    )
    if art is None:
        raise HTTPException(404, "Pacote ainda não disponível.")
    path = storage.abspath(art.path)
    if not path.exists():
        raise HTTPException(404, "Arquivo do pacote ausente.")
    return FileResponse(path, media_type="application/zip", filename="Projeto_Geoestatistico.zip")


@router.get("/runs/{run_id}/tables.xlsx")
def export_tables_xlsx(run: OwnedRun, db: DbSession):
    """Consolida todas as tabelas do relatório em uma única planilha Excel (seção 35)."""
    import pandas as pd

    arts = db.scalars(
        select(ResultArtifact).where(
            ResultArtifact.run_id == run.id, ResultArtifact.kind == ArtifactKind.table
        )
    ).all()
    if not arts:
        raise HTTPException(404, "Nenhuma tabela disponível.")

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        used: set[str] = set()
        for a in arts:
            payload = (a.data or {}).get("payload", {})
            cols = [c["key"] for c in payload.get("columns", [])]
            rows = payload.get("rows", [])
            df = pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame()
            sheet = (a.name or a.step_key or "tabela")[:28]
            i = 1
            base = sheet
            while sheet in used:
                sheet = f"{base[:25]}_{i}"
                i += 1
            used.add(sheet)
            df.to_excel(xw, sheet_name=sheet, index=False)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="tabelas.xlsx"'},
    )


@router.get("/runs/{run_id}/artifacts")
def list_artifacts(run: OwnedRun, db: DbSession, kind: str | None = Query(default=None)):
    q = select(ResultArtifact).where(ResultArtifact.run_id == run.id)
    if kind:
        q = q.where(ResultArtifact.kind == kind)
    arts = db.scalars(q.order_by(ResultArtifact.step_key)).all()
    return [
        {
            "id": a.id, "kind": a.kind.value if hasattr(a.kind, "value") else str(a.kind),
            "step_key": a.step_key, "name": a.name, "title": a.title,
            "mime": a.mime, "size": a.size,
            "url": f"/api/runs/{run.id}/artifacts/{a.id}",
            "variants": (a.data or {}).get("variants", {}),
        }
        for a in arts
    ]
