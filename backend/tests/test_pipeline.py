from __future__ import annotations

import pytest

from app.analysis.base import AnalysisContext
from app.reports.pdf import build_report
from app.services.packaging import build_package
from app.services.pipeline import run_pipeline


@pytest.fixture(scope="module")
def pipeline_output(synthetic_field, tmp_path_factory):
    d = tmp_path_factory.mktemp("run")
    dirs = {k: d / k for k in ("tables", "figures", "maps", "report", "exports")}
    dirs["base"] = d
    for x in dirs.values():
        x.mkdir(parents=True, exist_ok=True)
    ctx = AnalysisContext(
        df=synthetic_field.copy(),
        x_col="x", y_col="y", crs="EPSG:31982",
        primary="teor", secondary=["elevacao", "aleatoria"],
        explanatory=["elevacao"], aux_drift="elevacao", id_col="id",
        dirs=dirs,
        config={"advanced": {"n_permutations": 99, "grid_resolution": 22}},
        n_perm=99, project_name="Teste Pipeline", units="g/kg",
    )
    out = run_pipeline(ctx, lib_versions={"numpy": "x"})
    return out, dirs, ctx


def test_all_steps_ran(pipeline_output):
    out, _, _ = pipeline_output
    keys = {s.key for s in out.steps}
    assert {"descriptive", "esda_univariate", "idw", "kriging", "method_comparison"} <= keys
    # nenhum passo pode ter derrubado o pipeline
    failed = [s.key for s in out.steps if s.status == "failed"]
    assert not failed, f"passos com falha: {failed}"


def test_core_steps_ok(pipeline_output):
    out, _, _ = pipeline_output
    ok = {s.key for s in out.steps if s.status == "ok"}
    assert {"descriptive", "esda_univariate", "moran_scatter", "idw", "kriging"} <= ok


def test_summary_and_manifest(pipeline_output):
    out, _, _ = pipeline_output
    s = out.metrics_summary
    assert s["n_points"] == 140
    assert "morans_i" in s and s["morans_i"] is not None
    assert "best_method" in s
    assert out.manifest["context"]["primary"] == "teor"
    assert len(out.manifest["steps"]) == len(out.steps)
    assert out.conclusion


def test_strong_autocorrelation_detected(pipeline_output):
    """O campo sintético é fortemente autocorrelacionado -> Moran I > 0 e significativo."""
    out, _, _ = pipeline_output
    esda = next(s for s in out.steps if s.key == "esda_univariate")
    pm = esda.metrics.get("primary_moran") or esda.metrics["morans"]["teor"]
    assert pm["I"] > 0.2
    assert pm["p"] <= 0.05


def test_report_pdf(pipeline_output):
    out, dirs, ctx = pipeline_output
    pdf = build_report(
        out_path=dirs["report"] / "relatorio.pdf",
        project={"name": "Teste Pipeline", "client": "—", "technical_lead": "—",
                 "analysis_date": "2026-08-27", "description": "", "crs": "EPSG:31982",
                 "crs_label": "SIRGAS 2000 / UTM 22S", "variable_units": "g/kg"},
        dataset={"original_filename": "sintetico.csv", "row_count": 140, "col_count": 6,
                 "config": {"x_col": "x", "y_col": "y", "primary": "teor",
                            "secondary": ["elevacao"], "aux_drift": "elevacao"}},
        run_meta={"id": "testrun", "alpha": 0.05, "n_perm": 99, "lib_versions": {"numpy": "x"}},
        pipeline_output=out, validation={"summary": [], "counts": {"rows": 140}},
    )
    assert pdf.exists()
    assert pdf.stat().st_size > 50_000


def test_package_zip(pipeline_output):
    out, dirs, _ = pipeline_output
    pkg = build_package(dirs["base"], dest=dirs["exports"] / "pacote.zip",
                        config={"primary": "teor"}, manifest=out.manifest)
    import zipfile

    names = zipfile.ZipFile(pkg).namelist()
    assert any(n.startswith("tabelas/") for n in names)
    assert any(n.startswith("mapas/") for n in names)
    assert any(n.startswith("configuracoes/") for n in names)
