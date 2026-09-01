"""Popula o banco com o usuário e o projeto de demonstração (seções 45, 47).

Uso:
    python scripts/seed_demo.py            # cria usuário + projeto + dataset configurado
    python scripts/seed_demo.py --run      # ...e dispara a análise completa
    python scripts/seed_demo.py --run --wait

Requer que ``sample_data/demo_soil.xlsx`` exista (rode ``sample_data/generate_demo.py``).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.config import settings  # noqa: E402
from app.db.init_db import ensure_demo_user, init_db  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import Dataset, Project, RunStatus  # noqa: E402
from app.schemas.dataset import DatasetConfig  # noqa: E402
from app.services import storage  # noqa: E402
from app.services.detection import detect  # noqa: E402
from app.services.ingest import read_table  # noqa: E402
from app.services.validation import apply_cleaning, validate  # noqa: E402

DEMO_FILE = Path(__file__).resolve().parents[1] / "sample_data" / "demo_soil.xlsx"
PROJECT_NAME = "Análise de Solo 2026"

CONFIG = dict(
    primary="argila_pct",
    secondary=["materia_organica_pct", "calcio_cmolc_dm3", "ph_h2o"],
    explanatory=["elevacao_m", "materia_organica_pct", "areia_pct"],
    aux_drift="elevacao_m",
)


def seed(run: bool = False, wait: bool = False) -> str:
    if not DEMO_FILE.exists():
        raise SystemExit(f"Arquivo demo ausente: {DEMO_FILE}\nRode: python sample_data/generate_demo.py")

    init_db()
    db = SessionLocal()
    try:
        user = ensure_demo_user(db)

        project = (
            db.query(Project)
            .filter(Project.owner_id == user.id, Project.name == PROJECT_NAME)
            .one_or_none()
        )
        if project is None:
            project = Project(
                owner_id=user.id, name=PROJECT_NAME, client="Fazenda Modelo",
                technical_lead="Eng. Agrônomo Responsável", analysis_date="2026-08-27",
                description="Caracterização geoestatística da fertilidade do solo em talhão "
                            "experimental, com base em amostragem em grade irregular.",
                variable_units="% / cmolc dm⁻³ / mg dm⁻³",
                crs="EPSG:31982", crs_label="SIRGAS 2000 / UTM 22S",
            )
            db.add(project)
            db.flush()

        ds = (
            db.query(Dataset)
            .filter(Dataset.project_id == project.id)
            .order_by(Dataset.version.desc())
            .first()
        )
        if ds is None:
            data = DEMO_FILE.read_bytes()
            ds = Dataset(project_id=project.id, version=1,
                         original_filename=DEMO_FILE.name, file_size=len(data))
            db.add(ds)
            db.flush()
            raw = storage.raw_dir(user.id, project.id) / f"v1_{DEMO_FILE.name}"
            raw.write_bytes(data)
            ds.raw_path = storage.rel(raw)

            df, _ = read_table(raw)
            det = detect(df)
            ds.row_count, ds.col_count = df.shape
            ds.columns = [c.model_dump() for c in det.columns]
            ds.detection = det.model_dump()

            cfg = DatasetConfig(
                x_col=det.coord_x or "coord_x", y_col=det.coord_y or "coord_y",
                crs="EPSG:31982", crs_label="SIRGAS 2000 / UTM 22S",
                id_col="ponto_id", negatives_allowed=False, **CONFIG,
            )
            ds.config = cfg.model_dump()
            ds.validation = validate(df, ds.config).model_dump()

            clean, _ = apply_cleaning(df, ds.config, drop_duplicates=True, drop_missing_in_coords=True)
            cp = storage.dataset_dir(user.id, project.id, ds.id) / "clean.csv"
            clean.to_csv(cp, index=False, encoding="utf-8-sig")
            ds.clean_path = storage.rel(cp)
            ds.row_count = len(clean)

        db.commit()
        print(f"Usuário demo : {settings.demo_email} / {settings.demo_password}")
        print(f"Projeto      : {project.name}  ({project.id})")
        print(f"Dataset      : {ds.id}  v{ds.version}  ({ds.row_count} linhas)")

        run_id = ""
        if run:
            from app.models import AnalysisRun
            from app.services import jobs

            r = AnalysisRun(project_id=project.id, dataset_id=ds.id, mode="full",
                            status=RunStatus.pending, config={"advanced": {}}, steps=[], log=[])
            db.add(r)
            db.commit()
            run_id = r.id
            print(f"Execução     : {run_id}  (disparada)")
            jobs.submit(run_id)

            if wait:
                print("Aguardando conclusão…")
                while True:
                    time.sleep(3)
                    db.expire_all()
                    r = db.get(AnalysisRun, run_id)
                    print(f"  {r.progress:5.1f}%  {r.current_step}")
                    if r.status in (RunStatus.done, RunStatus.failed, RunStatus.cancelled):
                        print(f"  -> {r.status.value if hasattr(r.status,'value') else r.status}")
                        if r.error:
                            print(r.error[:1000])
                        break
        return run_id
    finally:
        db.close()


if __name__ == "__main__":
    seed(run="--run" in sys.argv, wait="--wait" in sys.argv)
