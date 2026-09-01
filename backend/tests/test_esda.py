from __future__ import annotations

from app.analysis import esda


def test_runs(ctx):
    r = esda.run(ctx)
    assert r.status in ("ok", "skipped")
    if r.status == "skipped":
        return
    # duas tabelas no contrato
    names = {t.name for t in r.tables}
    assert {"esda_univariada", "esda_univariada_testes"} <= names
    # métricas da variável principal
    assert "primary_moran" in r.metrics
    assert set(r.metrics["primary_moran"]) == {"I", "p", "z", "EI"}
    assert ctx.primary in r.metrics["morans"]


def test_primary_has_spatial_autocorrelation(ctx):
    r = esda.run(ctx)
    assert r.status == "ok"
    pm = r.metrics["primary_moran"]
    # campo sintético tem autocorrelação forte e positiva
    assert pm["I"] > pm["EI"]
    assert pm["p"] < ctx.alpha
    assert r.interpretation and "Moran" in r.interpretation


def test_tables_and_figures_shape(ctx):
    r = esda.run(ctx)
    assert r.status == "ok"
    t2 = next(t for t in r.tables if t.name == "esda_univariada_testes")
    tests_per_var = set(t2.df["Teste"])
    assert {"Moran I (permutacao)", "Geary C", "Normalidade (D'Agostino)"} <= tests_per_var
    assert len(r.figures) >= 2
