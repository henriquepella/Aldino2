"""Execução assíncrona do pipeline (seção 30).

Backend padrão local: ``ThreadPoolExecutor`` em processo, com estado persistido
na linha ``AnalysisRun`` (progresso, passo atual, log, cancelamento).
Backend de produção: Celery (``JOB_BACKEND=celery``) — ver ``app/worker``.
"""
from __future__ import annotations

import datetime as dt
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pandas as pd

from app.analysis.base import AnalysisContext
from app.api.meta import library_versions
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models import AnalysisRun, ArtifactKind, Dataset, Project, ResultArtifact, RunStatus
from app.reports.pdf import build_report
from app.services import storage
from app.services.packaging import build_package
from app.services.pipeline import STEP_TITLES, PipelineCancelled, run_pipeline

log = get_logger("jobs")

_executor = ThreadPoolExecutor(
    max_workers=max(1, settings.job_max_workers), thread_name_prefix="geo-job"
)


def submit(run_id: str) -> None:
    if settings.job_backend == "celery":  # pragma: no cover
        from app.worker.tasks import run_pipeline_task

        run_pipeline_task.delay(run_id)
        return
    _executor.submit(_guarded, run_id)


def _guarded(run_id: str) -> None:
    try:
        execute(run_id)
    except Exception:  # noqa: BLE001  (última linha de defesa)
        log.exception("Job %s morreu inesperadamente", run_id)


# --------------------------------------------------------------------------- #
def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _load_frame(dataset: Dataset) -> pd.DataFrame:
    from app.services.ingest import read_table
    from app.services.validation import apply_cleaning

    if dataset.clean_path:
        p = storage.abspath(dataset.clean_path)
        if p.exists():
            return pd.read_csv(p)
    raw = storage.abspath(dataset.raw_path)
    df, _ = read_table(raw)
    df, _ = apply_cleaning(df, dataset.config or {}, drop_missing_in_coords=True)
    return df


# Nomes amigáveis vindos do frontend -> chaves internas usadas por ctx.param()
_PARAM_ALIASES = {
    "knn_neighbors": "knn_k",
    "knn": "knn_k",
    "bandwidth_method": "bandwidth_kind",
    "bandwidth": "bandwidth_kind",
    "permutations": "n_permutations",
    "colormap": "cmap",
}


def _normalize_advanced(raw: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in (raw or {}).items():
        out[_PARAM_ALIASES.get(k, k)] = v
    return out


def _build_context(run: AnalysisRun, project: Project, dataset: Dataset) -> AnalysisContext:
    df = _load_frame(dataset)
    cfg = dict(dataset.config or {})
    advanced = _normalize_advanced({
        **(project.settings or {}),
        **(cfg.get("advanced") or {}),
        **(run.config.get("advanced") or {}),
    })

    dirs = storage.run_subdirs(project.owner_id, project.id, run.id)
    n_perm = int(advanced.get("n_permutations", settings.default_n_permutations))
    alpha = float(advanced.get("alpha", settings.default_alpha))

    merged_cfg: dict[str, Any] = {
        "advanced": {
            "knn_k": settings.default_knn_k,
            "idw_power": settings.default_idw_power,
            "idw_neighbors": settings.default_idw_neighbors,
            "variogram_bins": settings.default_variogram_bins,
            "grid_resolution": settings.default_grid_resolution,
            "map_dpi": settings.default_map_dpi,
            "report_map_dpi": settings.report_map_dpi,
            "selection_metric": "rmse",
            "basemap": settings.default_basemap,
            **advanced,
        },
        "bivariate_pairs": cfg.get("bivariate_pairs", []),
    }

    return AnalysisContext(
        df=df,
        x_col=cfg["x_col"], y_col=cfg["y_col"], crs=cfg.get("crs") or project.crs or "EPSG:4326",
        primary=cfg["primary"],
        secondary=list(cfg.get("secondary") or []),
        explanatory=list(cfg.get("explanatory") or []),
        aux_drift=cfg.get("aux_drift"),
        id_col=cfg.get("id_col"),
        dirs=dirs, config=merged_cfg,
        alpha=alpha, n_perm=n_perm,
        random_seed=int(advanced.get("random_seed", 42)),
        project_name=project.name, client=project.client,
        units=project.variable_units,
        data_source=dataset.original_filename or "arquivo enviado pelo usuário",
    )


def _register_artifacts(db, run: AnalysisRun, output, project: Project) -> None:
    base = storage.abspath(storage.rel(storage.run_dir(project.owner_id, project.id, run.id)))
    for step in output.steps:
        for t in step.tables:
            csv_path = (t.meta or {}).get("csv_path")
            if not csv_path or not Path(csv_path).exists():
                continue
            db.add(ResultArtifact(
                run_id=run.id, kind=ArtifactKind.table, step_key=step.key,
                name=t.name, title=t.title or t.name, caption=t.caption,
                path=storage.rel(csv_path), mime="text/csv",
                size=Path(csv_path).stat().st_size,
                data={"payload": t.to_payload(), "highlight_rows": t.highlight_rows},
            ))
        for f in step.figures:
            png = f.paths.get("png")
            if not png or not Path(png).exists():
                continue
            variants = {k: storage.rel(v) for k, v in f.paths.items() if Path(v).exists()}
            db.add(ResultArtifact(
                run_id=run.id,
                kind=ArtifactKind.map if f.kind == "map" else ArtifactKind.figure,
                step_key=step.key, name=f.name, title=f.title or f.name, caption=f.caption,
                path=storage.rel(png), mime="image/png",
                size=Path(png).stat().st_size,
                data={"variants": variants, "meta": f.meta, "kind": f.kind},
            ))
    db.flush()


def _step_states(output) -> list[dict[str, Any]]:
    return [
        {
            "key": s.key, "title": s.title, "status": s.status, "reason": s.reason,
            "n_tables": len(s.tables), "n_figures": len(s.figures),
            "metrics": s.metrics,
        }
        for s in output.steps
    ]


def execute(run_id: str) -> None:
    db = SessionLocal()
    try:
        run = db.get(AnalysisRun, run_id)
        if run is None:
            log.error("Run %s inexistente", run_id)
            return
        project = db.get(Project, run.project_id)
        dataset = db.get(Dataset, run.dataset_id)

        run.status = RunStatus.running
        run.started_at = _now()
        run.progress = 1.0
        run.error = ""
        run.log = [{"t": _now().isoformat(), "step": "start", "msg": "Iniciando análise…"}]
        db.commit()

        ctx = _build_context(run, project, dataset)

        def progress(step_key: str, status: str, pct: float, msg: str) -> None:
            run.current_step = step_key
            run.progress = max(run.progress, pct)
            states = {s["key"]: s for s in (run.steps or [])}
            st = states.setdefault(step_key, {"key": step_key})
            st["title"] = STEP_TITLES.get(step_key, step_key)
            st["status"] = status
            run.steps = list(states.values())
            if msg:
                run.log = (run.log or []) + [
                    {"t": _now().isoformat(), "step": step_key, "msg": msg}
                ]
            db.commit()

        def should_cancel() -> bool:
            db.expire(run, ["cancel_requested"])
            return bool(run.cancel_requested)

        selected = run.config.get("steps") if run.mode == "custom" else None
        output = run_pipeline(
            ctx, selected=selected, progress=progress,
            should_cancel=should_cancel, lib_versions=library_versions(),
        )

        _register_artifacts(db, run, output, project)

        dirs = storage.run_subdirs(project.owner_id, project.id, run.id)
        report_path = dirs["report"] / "relatorio.pdf"
        try:
            build_report(
                out_path=report_path,
                project={
                    "name": project.name, "client": project.client,
                    "technical_lead": project.technical_lead,
                    "analysis_date": project.analysis_date,
                    "description": project.description,
                    "crs": project.crs, "crs_label": project.crs_label,
                    "variable_units": project.variable_units,
                },
                dataset={
                    "original_filename": dataset.original_filename,
                    "row_count": dataset.row_count, "col_count": dataset.col_count,
                    "config": dataset.config or {},
                },
                run_meta={
                    "id": run.id, "created_at": str(run.created_at),
                    "alpha": ctx.alpha, "n_perm": ctx.n_perm,
                    "lib_versions": library_versions(),
                },
                pipeline_output=output,
                validation=dataset.validation or {},
            )
            db.add(ResultArtifact(
                run_id=run.id, kind=ArtifactKind.report, step_key="report",
                name="relatorio", title="Relatório Técnico (PDF)",
                path=storage.rel(report_path), mime="application/pdf",
                size=report_path.stat().st_size,
            ))
        except Exception as exc:  # noqa: BLE001
            log.exception("Falha ao gerar PDF")
            run.log = (run.log or []) + [
                {"t": _now().isoformat(), "step": "report", "msg": f"Falha no PDF: {exc}"}
            ]

        try:
            pkg_path = dirs["exports"] / "Projeto_Geoestatistico.zip"
            build_package(
                dirs["base"], dest=pkg_path,
                original_file=storage.abspath(dataset.raw_path) if dataset.raw_path else None,
                clean_file=storage.abspath(dataset.clean_path) if dataset.clean_path else None,
                config=dataset.config or {}, manifest=output.manifest,
            )
            db.add(ResultArtifact(
                run_id=run.id, kind=ArtifactKind.package, step_key="package",
                name="pacote", title="Pacote Completo (ZIP)",
                path=storage.rel(pkg_path), mime="application/zip",
                size=pkg_path.stat().st_size,
            ))
        except Exception:  # noqa: BLE001
            log.exception("Falha ao gerar pacote ZIP")

        run.status = RunStatus.done
        run.progress = 100.0
        run.current_step = "done"
        run.finished_at = _now()
        run.metrics_summary = output.metrics_summary
        run.manifest = output.manifest
        run.lib_versions = library_versions()
        run.steps = _step_states(output)
        run.log = (run.log or []) + [{"t": _now().isoformat(), "step": "done", "msg": "Análise concluída."}]
        db.commit()
        log.info("Run %s concluído", run_id)

    except PipelineCancelled:
        db.rollback()
        run = db.get(AnalysisRun, run_id)
        if run:
            run.status = RunStatus.cancelled
            run.finished_at = _now()
            run.log = (run.log or []) + [{"t": _now().isoformat(), "step": "cancel", "msg": "Análise cancelada pelo usuário."}]
            db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        run = db.get(AnalysisRun, run_id)
        if run:
            run.status = RunStatus.failed
            run.error = f"{exc}\n{traceback.format_exc(limit=8)}"
            run.finished_at = _now()
            db.commit()
        log.exception("Run %s falhou", run_id)
    finally:
        db.close()
