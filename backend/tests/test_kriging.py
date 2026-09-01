from app.analysis import kriging


def test_runs(ctx):
    r = kriging.run(ctx)
    assert r.status in ("ok", "skipped")
    if r.status == "skipped":
        return
    assert len(r.tables) == 3
    assert 1 <= len(r.figures) <= 8
    assert r.metrics["best_model"] in (
        "spherical", "exponential", "gaussian", "linear", "power"
    )


def test_cv_metrics_and_ranking(ctx):
    r = kriging.run(ctx)
    assert r.status == "ok"
    cv = r.metrics["cv"]
    for k in ("me", "mae", "mse", "rmse", "r2", "msdr"):
        assert k in cv
    assert cv["rmse"] is not None and cv["rmse"] >= 0
    ranked = r.metrics["ranked"]
    metric = r.params_used["selection_metric"]
    if metric == "rmse" and all(x["rmse"] is not None for x in ranked):
        assert ranked == sorted(ranked, key=lambda d: d["rmse"])
    # tabela de CV destacando o melhor modelo
    tbl = r.tables[1]
    assert tbl.highlight_rows == [0]


def test_applicable_rejects_constant(ctx):
    ctx.df[ctx.primary] = 5.0
    ok, reason = kriging.applicable(ctx)
    assert ok is False and reason
