"""Configuração central da aplicação (12-factor, via variáveis de ambiente).

Todos os parâmetros têm valores padrão sensatos para desenvolvimento local
(SQLite + fila de jobs em processo). Produção sobrescreve via `.env` /
variáveis de ambiente (PostgreSQL/PostGIS + Celery/Redis).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Raiz do backend (…/backend)
BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Identidade ----
    app_name: str = "Plataforma de Análise Geoestatística"
    app_env: str = Field(default="development")  # development | production | test
    api_v1_prefix: str = "/api"
    debug: bool = True

    # ---- Segurança / Auth ----
    secret_key: str = Field(
        default="dev-insecure-change-me-please-0123456789abcdef",
        description="Chave para assinatura JWT. OBRIGATÓRIO definir em produção.",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 dias
    allow_registration: bool = True

    # ---- Banco de dados ----
    database_url: str = Field(
        default="sqlite:///./storage/app.db",
        description="SQLAlchemy URL. Ex.: postgresql+psycopg2://user:pass@db:5432/geo",
    )
    sql_echo: bool = False

    # ---- Armazenamento de arquivos ----
    storage_dir: Path = Field(default=BACKEND_ROOT / "storage")

    # ---- Upload ----
    max_upload_mb: int = 50
    allowed_upload_extensions: Annotated[set[str], NoDecode] = {".xlsx", ".xls", ".csv"}

    # ---- Jobs assíncronos ----
    job_backend: str = Field(default="thread")  # thread | celery
    job_max_workers: int = 2
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ---- Padrões científicos (seções 10, 15, 28, 36) ----
    default_n_permutations: int = 999
    default_alpha: float = 0.05
    default_knn_k: int = 8
    default_idw_power: float = 2.0
    default_idw_neighbors: int = 12
    default_variogram_bins: int = 15
    default_grid_resolution: int = 80  # células por eixo na grade de interpolação
    default_map_dpi: int = 120  # gráficos (histogramas, scatter…)
    report_map_dpi: int = 150  # mapas cartográficos (rasterizados p/ SVG/PDF compactos)
    default_basemap: str = "satellite"  # satellite | gray | streets | topo | terrain | osm | none
    max_points_for_full_analysis: int = 5000

    # ---- CORS ----
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # ---- Conta demo (seed) ----
    demo_email: str = "demo@demo.local"
    demo_password: str = "demo12345"
    demo_full_name: str = "Usuário Demonstração"

    @field_validator("storage_dir", mode="before")
    @classmethod
    def _resolve_storage(cls, v: str | Path) -> Path:
        p = Path(v)
        if not p.is_absolute():
            p = (BACKEND_ROOT / p).resolve()
        return p

    @field_validator("cors_origins", "allowed_upload_extensions", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    # Resolve caminho de SQLite relativo para dentro de storage_dir (independe do CWD)
    if settings.database_url.startswith("sqlite:///") and "./storage/" in settings.database_url:
        name = settings.database_url.rsplit("/", 1)[-1]
        settings.database_url = f"sqlite:///{(settings.storage_dir / name).as_posix()}"
    return settings


settings = get_settings()
