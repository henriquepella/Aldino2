from __future__ import annotations

import importlib.metadata as im
import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/meta", tags=["meta"])

_TRACKED = [
    "numpy", "pandas", "scipy", "scikit-learn", "statsmodels",
    "geopandas", "shapely", "pyproj", "libpysal", "esda",
    "PyKrige", "mgwr", "matplotlib", "reportlab", "fastapi",
]


def library_versions() -> dict[str, str]:
    out: dict[str, str] = {}
    for pkg in _TRACKED:
        try:
            out[pkg] = im.version(pkg)
        except im.PackageNotFoundError:
            out[pkg] = "n/d"
    return out


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/versions")
def versions() -> dict:
    return {"libraries": library_versions()}


@router.get("/template.xlsx")
def template() -> StreamingResponse:
    """Modelo de planilha para o usuário (seção 2)."""
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(7)
    n = 25
    df = pd.DataFrame({
        "id": range(1, n + 1),
        "x": np.round(rng.uniform(300000, 301000, n), 2),      # easting (m)
        "y": np.round(rng.uniform(7500000, 7501000, n), 2),    # northing (m)
        "argila": np.round(rng.uniform(15, 55, n), 1),
        "ph": np.round(rng.uniform(4.5, 6.8, n), 2),
        "materia_organica": np.round(rng.uniform(1.0, 4.5, n), 2),
        "fosforo": np.round(rng.uniform(2, 40, n), 1),
        "elevacao": np.round(rng.uniform(480, 540, n), 1),
    })
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        df.to_excel(xw, index=False, sheet_name="dados")
        info = pd.DataFrame({
            "coluna": ["id", "x", "y", "<variáveis>", "elevacao"],
            "descrição": [
                "identificador do ponto (opcional)",
                "coordenada X / Longitude / Easting",
                "coordenada Y / Latitude / Northing",
                "uma coluna numérica por variável analisada",
                "exemplo de variável auxiliar (co-krigagem / deriva externa)",
            ],
        })
        info.to_excel(xw, index=False, sheet_name="instruções")
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="modelo_geoestatistica.xlsx"'},
    )
