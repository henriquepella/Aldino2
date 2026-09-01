from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import func, select

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession, OwnedDataset, OwnedProject
from app.core.logging import get_logger
from app.models import Dataset
from app.schemas.dataset import (
    CleanRequest,
    DatasetConfig,
    DatasetConfigUpdate,
    DatasetOut,
    ValidationResult,
)
from app.services import storage
from app.services.detection import detect
from app.services.ingest import IngestError, file_hash, read_table
from app.services.validation import apply_cleaning, validate

log = get_logger("api.datasets")
router = APIRouter(tags=["datasets"])


def _to_out(ds: Dataset) -> DatasetOut:
    return DatasetOut(
        id=ds.id, project_id=ds.project_id, version=ds.version,
        original_filename=ds.original_filename, file_size=ds.file_size,
        row_count=ds.row_count, col_count=ds.col_count,
        columns=ds.columns or [],
        detection=ds.detection or None,
        config=ds.config or None,
        validation=ds.validation or None,
        is_active=ds.is_active, created_at=ds.created_at,
    )


@router.post("/projects/{project_id}/datasets", response_model=DatasetOut, status_code=201)
async def upload_dataset(
    project: OwnedProject, db: DbSession, user: CurrentUser,
    file: UploadFile = File(...),
):
    name = storage.sanitize_filename(file.filename or "dados.xlsx")
    ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in settings.allowed_upload_extensions:
        raise HTTPException(400, f"Formato não suportado. Use: {', '.join(sorted(settings.allowed_upload_extensions))}")

    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, f"Arquivo excede {settings.max_upload_mb} MB.")
    if not data:
        raise HTTPException(400, "Arquivo vazio.")

    version = (db.scalar(
        select(func.max(Dataset.version)).where(Dataset.project_id == project.id)
    ) or 0) + 1

    ds = Dataset(project_id=project.id, version=version, original_filename=name,
                 file_size=len(data), content_hash=file_hash(data))
    db.add(ds)
    db.flush()

    raw_path = storage.raw_dir(user.id, project.id) / f"v{version}_{name}"
    raw_path.write_bytes(data)
    ds.raw_path = storage.rel(raw_path)

    try:
        df, meta = read_table(raw_path)
    except IngestError as exc:
        db.rollback()
        raise HTTPException(422, str(exc))

    det = detect(df)
    ds.row_count = int(df.shape[0])
    ds.col_count = int(df.shape[1])
    ds.columns = [c.model_dump() for c in det.columns]
    ds.detection = det.model_dump()

    # configuração inicial sugerida (o usuário confirma/ajusta depois)
    if det.coord_x and det.coord_y and det.primary_guess:
        ds.config = DatasetConfig(
            x_col=det.coord_x, y_col=det.coord_y,
            crs=det.crs_suggested or project.crs or "EPSG:4326",
            crs_label=det.crs_label,
            id_col=(det.id_like_columns[0] if det.id_like_columns else None),
            primary=det.primary_guess,
            secondary=det.secondary_guess,
            explanatory=det.explanatory_guess,
            aux_drift=det.aux_drift_guess,
        ).model_dump()

    db.commit()
    db.refresh(ds)
    log.info("Dataset %s (v%d) enviado: %d linhas x %d colunas", ds.id, version, ds.row_count, ds.col_count)
    return _to_out(ds)


@router.get("/projects/{project_id}/datasets", response_model=list[DatasetOut])
def list_datasets(project: OwnedProject, db: DbSession):
    rows = db.scalars(
        select(Dataset)
        .where(Dataset.project_id == project.id)
        .order_by(Dataset.version.desc())
    ).all()
    return [_to_out(d) for d in rows]


@router.get("/datasets/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset: OwnedDataset):
    return _to_out(dataset)


@router.patch("/datasets/{dataset_id}/config", response_model=DatasetOut)
def set_config(payload: DatasetConfigUpdate, dataset: OwnedDataset, db: DbSession, user: CurrentUser):
    cfg = payload.config
    cols = {c["name"] for c in (dataset.columns or [])}
    for field in ("x_col", "y_col", "primary"):
        if getattr(cfg, field) not in cols:
            raise HTTPException(422, f"Coluna '{getattr(cfg, field)}' não existe no conjunto de dados.")
    dataset.config = cfg.model_dump()

    # valida + gera versão limpa
    df, _ = read_table(storage.abspath(dataset.raw_path))
    val = validate(df, dataset.config)
    dataset.validation = val.model_dump()

    clean, _ = apply_cleaning(df, dataset.config, drop_missing_in_coords=True)
    clean_path = storage.dataset_dir(user.id, dataset.project_id, dataset.id) / "clean.csv"
    clean.to_csv(clean_path, index=False, encoding="utf-8-sig")
    dataset.clean_path = storage.rel(clean_path)

    db.commit()
    db.refresh(dataset)
    return _to_out(dataset)


@router.post("/datasets/{dataset_id}/validate", response_model=ValidationResult)
def revalidate(dataset: OwnedDataset, db: DbSession):
    if not dataset.config:
        raise HTTPException(400, "Configure as colunas antes de validar.")
    df, _ = read_table(storage.abspath(dataset.raw_path))
    val = validate(df, dataset.config)
    dataset.validation = val.model_dump()
    db.commit()
    return val


@router.post("/datasets/{dataset_id}/clean", response_model=DatasetOut)
def clean_dataset(payload: CleanRequest, dataset: OwnedDataset, db: DbSession, user: CurrentUser):
    if not dataset.config:
        raise HTTPException(400, "Configure as colunas antes de limpar.")
    df, _ = read_table(storage.abspath(dataset.raw_path))
    clean, report = apply_cleaning(
        df, dataset.config,
        drop_row_indices=payload.drop_row_indices,
        drop_duplicates=payload.drop_duplicates,
        drop_missing_in_coords=payload.drop_missing_in_coords,
        drop_missing_in_primary=payload.drop_missing_in_primary,
    )
    clean_path = storage.dataset_dir(user.id, dataset.project_id, dataset.id) / "clean.csv"
    clean.to_csv(clean_path, index=False, encoding="utf-8-sig")
    dataset.clean_path = storage.rel(clean_path)
    dataset.row_count = len(clean)

    val = validate(clean, dataset.config)
    dataset.validation = val.model_dump()
    dataset.validation["cleaning_report"] = report
    db.commit()
    db.refresh(dataset)
    return _to_out(dataset)
