"""Aplicação Celery (usada quando ``JOB_BACKEND=celery``)."""
from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "geoestatistica",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    worker_max_tasks_per_child=20,
    task_time_limit=60 * 60,
    task_soft_time_limit=55 * 60,
)
