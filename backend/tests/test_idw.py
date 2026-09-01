from __future__ import annotations

from app.analysis import idw


def test_runs(ctx):
    r = idw.run(ctx)
    assert r.status in ("ok", "skipped")
    if r.status == "skipped":
        return
    assert r.key == "idw"
    # 4 figuras: superfície, pontos, erro LOO, observado x previsto
    assert len(r.figures) == 4
    # 1 tabela de validação cruzada, ordenada por RMSE, com destaque
    assert len(r.tables) == 1
    tbl = r.tables[0]
    assert list(tbl.df.columns) == ["Power", "Vizinhos", "ME", "MAE", "RMSE", "R²"]
    assert list(tbl.df["RMSE"]) == sorted(tbl.df["RMSE"])
    assert tbl.highlight_rows and tbl.highlight_rows[0] < len(tbl.df)


def test_best_metrics(ctx):
    r = idw.run(ctx)
    if r.status == "skipped":
        return
    best = r.metrics["best"]
    for key in ("power", "neighbors", "rmse", "mae", "me", "r2"):
        assert key in best
    assert best["rmse"] >= 0
    assert len(r.metrics["grid_search"]) == 5 * len(r.params_used["idw_neighbors_grid"])
    assert r.interpretation and "IDW" in r.interpretation


def test_applicable_constant(ctx):
    ctx.df["teor"] = 7.0
    ok, reason = idw.applicable(ctx)
    assert ok is False
    assert reason
