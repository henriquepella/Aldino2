from app.analysis import moran


def test_runs(ctx):
    r = moran.run(ctx)
    assert r.status in ("ok", "skipped")
    if r.status == "ok":
        assert r.tables and r.tables[0].name == "moran_scatter_resumo"
        assert len(r.figures) >= 1
        assert ctx.primary in r.metrics
        m = r.metrics[ctx.primary]
        assert abs(m["I"] - m["slope"]) < 1e-6
        assert set(m["quadrants"]) == {"HH", "LH", "HL", "LL"}
        assert sum(m["quadrants"].values()) == ctx.n
        assert r.interpretation


def test_applicable(ctx):
    ok, reason = moran.applicable(ctx)
    assert ok and reason == ""
