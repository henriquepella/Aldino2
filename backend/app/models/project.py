from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Project(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # ---- Informações do projeto (seção 6) ----
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client: Mapped[str] = mapped_column(String(255), default="")
    technical_lead: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    variable_units: Mapped[str] = mapped_column(String(255), default="")
    analysis_date: Mapped[str] = mapped_column(String(32), default="")  # ISO date string

    # ---- Sistema de coordenadas ----
    crs: Mapped[str] = mapped_column(String(64), default="")  # ex.: "EPSG:31982"
    crs_label: Mapped[str] = mapped_column(String(128), default="")  # ex.: "SIRGAS 2000 / UTM 22S"

    # ---- Parâmetros avançados default do projeto (seção 36) ----
    settings: Mapped[dict] = mapped_column(default=dict)
    meta: Mapped[dict] = mapped_column(default=dict)

    owner: Mapped["User"] = relationship(back_populates="projects")  # noqa: F821
    datasets: Mapped[list["Dataset"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan", order_by="Dataset.version"
    )
    runs: Mapped[list["AnalysisRun"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )
