from __future__ import annotations

import io

import pandas as pd

from app.services.ingest import _coerce_numeric, read_table


def test_international_decimals_preserved(tmp_path):
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "x": ["300123.45", "300500.1", "300999.99", "300250.0"],
        "teor": ["25.34", "25.3", "26.0", "24.87"],
    })
    out = _coerce_numeric(df.astype(object))
    assert out["teor"].tolist() == [25.34, 25.3, 26.0, 24.87]
    assert abs(out["x"].iloc[0] - 300123.45) < 1e-6


def test_brazilian_decimals_detected():
    df = pd.DataFrame({
        "valor": ["1.234,56", "2.000,10", "987,65", "12,00"],
    }).astype(object)
    out = _coerce_numeric(df)
    assert out["valor"].tolist() == [1234.56, 2000.10, 987.65, 12.00]


def test_read_csv_semicolon_br(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text(
        "id;x;y;teor\n1;300000,5;7500000,2;25,3\n2;300100,0;7500100,9;26,1\n3;300200,4;7500200,1;24,8\n",
        encoding="utf-8",
    )
    df, meta = read_table(p)
    assert meta["sep"] == ";"
    assert df["teor"].tolist() == [25.3, 26.1, 24.8]


def test_read_xlsx_typed(tmp_path):
    p = tmp_path / "d.xlsx"
    src = pd.DataFrame({"id": [1, 2, 3], "x": [1.5, 2.25, 3.75], "y": [10.1, 20.2, 30.3],
                        "v": [100.0, 200.5, 300.25]})
    with pd.ExcelWriter(p, engine="xlsxwriter") as xw:
        src.to_excel(xw, index=False)
    df, _ = read_table(p)
    assert df["v"].tolist() == [100.0, 200.5, 300.25]
    assert df["x"].iloc[1] == 2.25
