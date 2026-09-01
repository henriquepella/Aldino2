from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Dataset(UUIDMixin, TimestampMixin, Base):
    """Uma versão de dados dentro de um projeto.

    `raw_path` preserva o arquivo original enviado (seção 33). `clean_path`
    guarda o CSV limpo/derivado usado pelas análises.
    """

    __tablename__ = "datasets"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1)

    original_filename: Mapped[str] = mapped_column(String(512), default="")
    raw_path: Mapped[str] = mapped_column(String(1024), default="")
    clean_path: Mapped[str] = mapped_column(String(1024), default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str] = mapped_column(String(64), default="")

    row_count: Mapped[int] = mapped_column(Integer, default=0)
    col_count: Mapped[int] = mapped_column(Integer, default=0)

    # Estrutura detectada: [{name, dtype, n_unique, n_missing, min, max, role_guess, ...}]
    columns: Mapped[list] = mapped_column(default=list)
    # Resultado de services.detection.detect(): candidatos de coordenadas/vars/CRS
    detection: Mapped[dict] = mapped_column(default=dict)
    # Configuração confirmada pelo usuário: x_col, y_col, crs, primary, secondary[], ...
    config: Mapped[dict] = mapped_column(default=dict)
    # Diagnóstico da base (seção 5): itens + status + flags por linha
    validation: Mapped[dict] = mapped_column(default=dict)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    project: Mapped["Project"] = relationship(back_populates="datasets")  # noqa: F821
    runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="dataset")  # noqa: F821
