from app.analysis import bivariate


def test_runs(ctx):
    r = bivariate.run(ctx)
    assert r.status in ("ok", "skipped")
    if r.status == "ok":
        assert len(r.tables) == 2
        assert r.tables[0].title == "ESDA Bivariada"
        assert r.metrics["pairs"]
        assert r.interpretation


def test_applicable(ctx):
    ok, reason = bivariate.applicable(ctx)
    assert ok is True
    assert reason == ""


def test_all_pairs_heatmap(ctx):
    ctx.config["advanced"]["bivariate_all_pairs"] = True
    r = bivariate.run(ctx)
    assert r.status == "ok"
    pairs = {(p["a"], p["b"]) for p in r.metrics["pairs"]}
    assert len(pairs) >= 2
    assert any(f.name == "bivariate_matriz_I" for f in r.figures)


def test_metrics_shape(ctx):
    r = bivariate.run(ctx)
    if r.status == "ok":
        for p in r.metrics["pairs"]:
            assert set(p) == {"a", "b", "I", "p", "z", "n_sig"}
