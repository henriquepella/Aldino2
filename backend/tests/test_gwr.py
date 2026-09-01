from app.analysis import gwr


def test_runs(ctx):
    r = gwr.run(ctx)
    assert r.status in ("ok", "skipped")
    if r.status == "skipped":
        return
    assert r.interpretation and "teor" in r.interpretation
    assert {"bw", "bw_kind", "r2_global", "aicc", "rss", "r2_local"} <= set(r.metrics)
    assert len(r.metrics["r2_local"]) == 2
    assert r.metrics["r2_local"][0] <= r.metrics["r2_local"][1]


def test_tables_and_figures(ctx):
    r = gwr.run(ctx)
    if r.status == "skipped":
        return
    names = {t.name for t in r.tables}
    assert {"gwr_metricas", "gwr_coeficientes_locais"} <= names
    coef = next(t for t in r.tables if t.name == "gwr_coeficientes_locais")
    assert "Intercepto" in set(coef.df["Variável"])
    assert len(r.figures) >= 3


def test_applicable_without_explanatory(ctx):
    ctx.explanatory = []
    ok, reason = gwr.applicable(ctx)
    assert ok is False and reason


def test_mc_iters(ctx):
    ctx.config["advanced"]["gwr_mc_iters"] = 20
    r = gwr.run(ctx)
    assert r.status in ("ok", "skipped")
    if r.status == "ok":
        assert r.params_used["gwr_mc_iters"] == 20
