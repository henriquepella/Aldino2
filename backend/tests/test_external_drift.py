from __future__ import annotations

from app.analysis import external_drift


def test_applicable(ctx):
    ok, msg = external_drift.applicable(ctx)
    assert isinstance(ok, bool)
    # elevacao é fortemente correlacionada com teor na fixture
    assert ok, msg


def test_runs(ctx):
    r = external_drift.run(ctx)
    assert r.status in ("ok", "skipped")
    if r.status == "ok":
        assert r.tables and r.tables[0].name == "external_drift"
        assert len(r.figures) >= 4
        assert r.metrics["aux"] == "elevacao"
        assert set(r.metrics["cv"]) == {"rmse", "mae", "me", "r2"}
        assert r.interpretation


def test_skips_without_aux(ctx):
    ctx.aux_drift = None
    ok, msg = external_drift.applicable(ctx)
    assert not ok
    r = external_drift.run(ctx)
    assert r.status == "skipped"
