from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.services.detection import detect
from app.services.ingest import read_table

DEMO = Path(__file__).resolve().parents[2] / "sample_data" / "demo_soil.xlsx"


def test_detect_synthetic(synthetic_field):
    res = detect(synthetic_field)
    assert res.coord_x == "x"
    assert res.coord_y == "y"
    assert res.coord_kind == "utm"
    assert "teor" in res.numeric_variables
    assert res.primary_guess in res.numeric_variables
    assert "id" in res.id_like_columns
    # elevação deve ser sugerida como auxiliar (correlacionada com a principal)
    assert res.aux_drift_guess == "elevacao"


def test_detect_lonlat():
    df = pd.DataFrame({
        "site": [f"S{i}" for i in range(30)],
        "longitude": [-47.1 + i * 0.001 for i in range(30)],
        "latitude": [-22.8 + i * 0.001 for i in range(30)],
        "yield": [3.1 + (i % 5) * 0.2 for i in range(30)],
    })
    res = detect(df)
    assert res.coord_x == "longitude"
    assert res.coord_y == "latitude"
    assert res.coord_kind == "lonlat"
    assert res.crs_suggested == "EPSG:4326"


@pytest.mark.skipif(not DEMO.exists(), reason="rode sample_data/generate_demo.py")
def test_detect_demo_file():
    df, meta = read_table(DEMO)
    assert meta["row_count"] > 400
    res = detect(df)
    assert res.coord_x == "coord_x"
    assert res.coord_y == "coord_y"
    assert "argila_pct" in res.numeric_variables
    assert "ponto_id" in res.id_like_columns
