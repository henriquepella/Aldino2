from __future__ import annotations

from app.analysis import cokriging


def test_runs(ctx):
    r = cokriging.run(ctx)
    assert r.status in ("ok", "skipped")
    if r.status == "ok":
        assert r.metrics["secondary"] == "elevacao"
        assert set(r.metrics["cv_ck"]) == {"rmse", "mae", "me", "r2"}
        assert set(r.metrics["cv_ok"]) == {"rmse", "mae", "me", "r2"}
        assert len(r.figures) >= 3
        assert r.tables and list(r.tables[0].df.columns) == [
            "Item", "Co-Krigagem", "Krigagem Ordinária"
        ]
        assert r.interpretation and "co-krigagem" in r.interpretation.lower()


def test_applicable(ctx):
    ok, reason = cokriging.applicable(ctx)
    assert ok is True
    assert reason == ""
