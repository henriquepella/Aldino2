"""Tarefas Celery. A lógica real vive em ``app.services.jobs.execute``."""
from __future__ import annotations

from app.core.logging import get_logger
from app.worker.celery_app import celery_app

log = get_logger("worker")


@celery_app.task(name="pipeline.run", bind=True, max_retries=0)
def run_pipeline_task(self, run_id: str) -> str:  # noqa: ANN001
    from app.services.jobs import execute

    log.info("Celery: iniciando pipeline do run %s", run_id)
    execute(run_id)
    return run_id
