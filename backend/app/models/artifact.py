from __future__ import annotations

import enum

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class ArtifactKind(str, enum.Enum):
    table = "table"
    figure = "figure"
    map = "map"
    report = "report"
    export = "export"
    package = "package"
    data = "data"


class ResultArtifact(UUIDMixin, TimestampMixin, Base):
    """Um arquivo produzido por um passo do pipeline (tabela, gráfico, mapa, PDF...)."""

    __tablename__ = "result_artifacts"

    run_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[ArtifactKind] = mapped_column(String(16), index=True)
    step_key: Mapped[str] = mapped_column(String(64), index=True, default="")
    name: Mapped[str] = mapped_column(String(255), default="")
    title: Mapped[str] = mapped_column(String(512), default="")
    caption: Mapped[str] = mapped_column(Text, default="")

    # Caminho relativo a settings.storage_dir
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    size: Mapped[int] = mapped_column(Integer, default=0)

    # Para tabelas: dados serializados (colunas + linhas) para render no frontend.
    # Para figuras/mapas: metadados (bounds, crs, unidade, método, variantes svg/pdf/tif).
    data: Mapped[dict] = mapped_column(default=dict)

    run: Mapped["AnalysisRun"] = relationship(back_populates="artifacts")  # noqa: F821
