from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.gettempdir()}/geo_test.db")
os.environ.setdefault("STORAGE_DIR", str(Path(tempfile.gettempdir()) / "geo_test_storage"))
os.environ.setdefault("SECRET_KEY", "test-secret-key-000000000000000000")
os.environ.setdefault("DEFAULT_N_PERMUTATIONS", "199")
os.environ.setdefault("DEFAULT_BASEMAP", "none")  # testes não acessam a rede

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from scipy.spatial.distance import cdist  # noqa: E402


@pytest.fixture(scope="session")
def synthetic_field() -> pd.DataFrame:
    """Campo espacial pequeno (n=140) com autocorrelação forte e uma covariável."""
    rng = np.random.default_rng(123)
    n = 140
    x = rng.uniform(0, 500, n)
    y = rng.uniform(0, 400, n)
    coords = np.c_[x, y]
    cov = np.exp(-cdist(coords, coords) / 120.0)
    cov[np.diag_indices_from(cov)] += 1e-8
    L = np.linalg.cholesky(cov)
    base = L @ rng.standard_normal(n)
    base = (base - base.mean()) / base.std()

    elev = 500 + 10 * base + rng.normal(0, 0.5, n)
    primary = 30 + 8 * base + rng.normal(0, 1.0, n)
    noise_only = rng.normal(50, 10, n)

    return pd.DataFrame({
        "id": range(1, n + 1),
        "x": np.round(300000 + x, 2),
        "y": np.round(7500000 + y, 2),
        "teor": np.round(primary, 3),
        "elevacao": np.round(elev, 2),
        "aleatoria": np.round(noise_only, 3),
    })


@pytest.fixture(scope="session")
def demo_config() -> dict:
    return {
        "x_col": "x",
        "y_col": "y",
        "crs": "EPSG:31982",
        "primary": "teor",
        "secondary": ["elevacao", "aleatoria"],
        "explanatory": ["elevacao"],
        "aux_drift": "elevacao",
        "id_col": "id",
        "negatives_allowed": True,
        "advanced": {"n_permutations": 199, "grid_resolution": 30},
    }


@pytest.fixture()
def ctx(synthetic_field, demo_config, tmp_path):
    from app.analysis.base import AnalysisContext

    dirs = {k: tmp_path / k for k in ("tables", "figures", "maps", "report", "exports")}
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return AnalysisContext(
        df=synthetic_field.copy(),
        x_col="x", y_col="y", crs="EPSG:31982",
        primary="teor", secondary=["elevacao", "aleatoria"],
        explanatory=["elevacao"], aux_drift="elevacao", id_col="id",
        dirs=dirs, config=demo_config, alpha=0.05, n_perm=199,
        project_name="Teste", units="g/kg",
    )
