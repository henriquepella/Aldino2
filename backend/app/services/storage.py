"""Layout de armazenamento em disco (seção 33/35).

    storage/
      users/<user_id>/
        projects/<project_id>/
          raw/                 arquivos originais enviados (preservados)
          datasets/<dataset_id>/clean.csv
          runs/<run_id>/
            tables/  figures/  maps/  report/  exports/
            run.json
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from app.core.config import settings

STORAGE = settings.storage_dir


def _safe(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-")
    return name or "arquivo"


def sanitize_filename(name: str) -> str:
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    return f"{_safe(stem)}{suffix}"


def project_dir(user_id: str, project_id: str) -> Path:
    p = STORAGE / "users" / user_id / "projects" / project_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def raw_dir(user_id: str, project_id: str) -> Path:
    p = project_dir(user_id, project_id) / "raw"
    p.mkdir(parents=True, exist_ok=True)
    return p


def dataset_dir(user_id: str, project_id: str, dataset_id: str) -> Path:
    p = project_dir(user_id, project_id) / "datasets" / dataset_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def run_dir(user_id: str, project_id: str, run_id: str) -> Path:
    p = project_dir(user_id, project_id) / "runs" / run_id
    for sub in ("tables", "figures", "maps", "report", "exports"):
        (p / sub).mkdir(parents=True, exist_ok=True)
    return p


def run_subdirs(user_id: str, project_id: str, run_id: str) -> dict[str, Path]:
    base = run_dir(user_id, project_id, run_id)
    return {
        "base": base,
        "tables": base / "tables",
        "figures": base / "figures",
        "maps": base / "maps",
        "report": base / "report",
        "exports": base / "exports",
    }


def rel(path: Path | str) -> str:
    """Caminho relativo a STORAGE, com barras normais (para guardar no banco)."""
    return Path(path).resolve().relative_to(STORAGE.resolve()).as_posix()


def abspath(relpath: str) -> Path:
    return (STORAGE / relpath).resolve()
