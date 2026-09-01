from __future__ import annotations

from pathlib import Path

import pytest

from app.services.detection import detect
from app.services.ingest import read_table
from app.services.validation import apply_cleaning, validate

DEMO = Path(__file__).resolve().parents[2] / "sample_data" / "demo_soil.xlsx"


@pytest.mark.skipif(not DEMO.exists(), reason="rode sample_data/generate_demo.py")
def test_validate_demo_finds_injected_issues():
    df, _ = read_table(DEMO)
    det = detect(df)
    config = {
        "x_col": det.coord_x, "y_col": det.coord_y, "crs": "EPSG:31982",
        "primary": det.primary_guess, "secondary": det.secondary_guess,
        "explanatory": det.explanatory_guess, "aux_drift": det.aux_drift_guess,
        "negatives_allowed": False,
    }
    res = validate(df, config)
    c = res.counts
    assert c["duplicate_rows"] >= 2
    assert c["coincident_points"] >= 2
    assert c["invalid_coords"] >= 1
    assert c["missing_cells"] >= 5
    assert c["outliers"] >= 1
    assert c["negative_values"] >= 1
    assert res.can_proceed is True
    assert len(res.row_flags) > 0


@pytest.mark.skipif(not DEMO.exists(), reason="rode sample_data/generate_demo.py")
def test_cleaning_removes_rows():
    df, _ = read_table(DEMO)
    det = detect(df)
    config = {"x_col": det.coord_x, "y_col": det.coord_y, "primary": det.primary_guess}
    clean, report = apply_cleaning(
        df, config, drop_duplicates=True, drop_missing_in_coords=True
    )
    assert report["removed_total"] >= 3
    assert len(clean) < len(df)
    assert clean[config["x_col"]].notna().all()
