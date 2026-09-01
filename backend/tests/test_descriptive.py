from app.analysis import descriptive


def test_runs(ctx):
    r = descriptive.run(ctx)
    assert r.status in ("ok", "skipped")
    assert descriptive.applicable(ctx)[0] is True


def test_content(ctx):
    r = descriptive.run(ctx)
    assert r.status == "ok"
    assert len(r.tables) == 1
    df = r.tables[0].df
    assert len(df) == len(ctx.analysis_variables)
    assert {"media", "mediana", "desvio_padrao", "cv_pct", "P95"}.issubset(df.columns)
    assert "teor" in r.metrics["variables"]
    assert set(r.metrics["variables"]["teor"]) >= {
        "mean", "median", "std", "cv", "skewness", "kurtosis", "min", "max", "n"
    }
    assert 1 <= len(r.figures) <= 6
    assert r.interpretation and "teor" in r.interpretation
