from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"
    cancelled = "cancelled"


class AnalysisRun(UUIDMixin, TimestampMixin, Base):
    """Execução do pipeline completo (seção 29). Também carrega o estado do job."""

    __tablename__ = "analysis_runs"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False
    )

    status: Mapped[RunStatus] = mapped_column(
        String(16), default=RunStatus.pending, index=True
    )
    mode: Mapped[str] = mapped_column(String(16), default="full")  # full | custom

    # Configuração efetiva da execução (colunas + parâmetros avançados resolvidos)
    config: Mapped[dict] = mapped_column(default=dict)
    # run.json — manifesto de reprodutibilidade (seção 42)
    manifest: Mapped[dict] = mapped_column(default=dict)
    # Números crus para o dashboard (seção 7) e comparação de métodos
    metrics_summary: Mapped[dict] = mapped_column(default=dict)
    # Estado por passo: [{key,title,status,reason,started_at,finished_at,n_tables,n_figures}]
    steps: Mapped[list] = mapped_column(default=list)
    lib_versions: Mapped[dict] = mapped_column(default=dict)

    # ---- Estado do job assíncrono (seção 30) ----
    progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0..100
    current_step: Mapped[str] = mapped_column(String(64), default="")
    log: Mapped[list] = mapped_column(default=list)  # linhas de log com timestamp
    cancel_requested: Mapped[bool] = mapped_column(default=False)
    error: Mapped[str] = mapped_column(Text, default="")

    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped["Project"] = relationship(back_populates="runs")  # noqa: F821
    dataset: Mapped["Dataset"] = relationship(back_populates="runs")  # noqa: F821
    artifacts: Mapped[list["ResultArtifact"]] = relationship(  # noqa: F821
        back_populates="run", cascade="all, delete-orphan"
    )
