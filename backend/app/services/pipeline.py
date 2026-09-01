"""Orquestração do pipeline completo (seções 29, 37, 38).

Regras:
- cada passo é isolado: se ``applicable`` retorna ``False`` -> ``skipped`` (com motivo);
  se ``run`` lança exceção -> ``failed`` (com motivo). O pipeline NUNCA aborta.
- o progresso é reportado por callback (ponderado por passo).
- ao final, monta a comparação de métodos, o resumo de métricas (dashboard) e o
  manifesto de reprodutibilidade (``run.json``).
"""
from __future__ import annotations

import datetime as dt
import importlib
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import pandas as pd

from app.analysis.base import AnalysisContext, StepResult
from app.analysis.comparison import build_comparison
from app.analysis.interpret import build_conclusion
from app.core.logging import get_logger

log = get_logger("pipeline")

ProgressFn = Callable[[str, str, float, str], None]  # (step_key, status, pct, message)
CancelFn = Callable[[], bool]


class PipelineCancelled(RuntimeError):
    pass


@dataclass
class StepSpec:
    key: str
    module: str
    weight: float = 1.0


STEPS: list[StepSpec] = [
    StepSpec("descriptive", "app.analysis.descriptive", 1.0),
    StepSpec("esda_univariate", "app.analysis.esda", 2.0),
    StepSpec("moran_scatter", "app.analysis.moran", 1.0),
    StepSpec("esda_bivariate", "app.analysis.bivariate", 1.5),
    StepSpec("idw", "app.analysis.idw", 2.0),
    StepSpec("kriging", "app.analysis.kriging", 3.5),
    StepSpec("external_drift", "app.analysis.external_drift", 2.0),
    StepSpec("gwr", "app.analysis.gwr", 2.5),
    StepSpec("cokriging", "app.analysis.cokriging", 2.0),
]
# passos finais (peso fixo): method_comparison, report, package -> tratados fora da lista

STEP_TITLES: dict[str, str] = {
    "descriptive": "Estatística Descritiva",
    "esda_univariate": "ESDA Univariada",
    "moran_scatter": "Moran Scatter Plot",
    "esda_bivariate": "ESDA Bivariada",
    "idw": "IDW — Inverse Distance Weighting",
    "kriging": "Krigagem Ordinária",
    "external_drift": "Krigagem com Deriva Externa",
    "gwr": "GWR / GWM",
    "cokriging": "Co-Krigagem",
    "method_comparison": "Comparação Geral dos Métodos",
    "report": "Relatório PDF",
    "package": "Pacote de Exportação",
}


@dataclass
class PipelineOutput:
    steps: list[StepResult] = field(default_factory=list)
    metrics_summary: dict[str, Any] = field(default_factory=dict)
    manifest: dict[str, Any] = field(default_factory=dict)
    conclusion: str = ""


def _safe_metrics(m: dict[str, Any]) -> dict[str, Any]:
    """Torna o dicionário de métricas serializável em JSON."""
    def conv(v):
        if isinstance(v, (np.floating,)):
            return float(v)
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, np.ndarray):
            return v.tolist()
        if isinstance(v, dict):
            return {str(k): conv(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [conv(x) for x in v]
        if isinstance(v, float) and not np.isfinite(v):
            return None
        return v
    return {str(k): conv(v) for k, v in (m or {}).items()}


def _persist_tables(result: StepResult, ctx: AnalysisContext) -> None:
    for t in result.tables:
        try:
            path = ctx.table_path(f"{result.key}__{t.name}")
            t.df.to_csv(path, index=False, encoding="utf-8-sig")
            t.meta.setdefault("csv_path", str(path))
        except Exception as exc:  # noqa: BLE001
            log.warning("Falha ao salvar tabela %s: %s", t.name, exc)


def run_pipeline(
    ctx: AnalysisContext,
    *,
    selected: list[str] | None = None,
    progress: ProgressFn | None = None,
    should_cancel: CancelFn | None = None,
    lib_versions: dict[str, str] | None = None,
) -> PipelineOutput:
    progress = progress or (lambda *a: None)
    should_cancel = should_cancel or (lambda: False)

    active = [s for s in STEPS if (selected is None or s.key in selected)]
    total_weight = sum(s.weight for s in active) + 3.0  # +comparison +report +package
    done_weight = 0.0
    results: list[StepResult] = []

    def emit(key: str, status: str, msg: str = "") -> None:
        pct = round(100.0 * done_weight / total_weight, 1)
        progress(key, status, min(pct, 99.0), msg)

    for spec in active:
        if should_cancel():
            raise PipelineCancelled()
        emit(spec.key, "running", f"Executando {spec.key}…")
        try:
            mod = importlib.import_module(spec.module)
            ok, reason = mod.applicable(ctx)
            if not ok:
                res = StepResult.skipped(spec.key, getattr(mod, "TITLE", spec.key), reason)
                log.info("Passo %s ignorado: %s", spec.key, reason)
            else:
                res = mod.run(ctx)
        except PipelineCancelled:
            raise
        except Exception as exc:  # noqa: BLE001
            tb = traceback.format_exc(limit=6)
            log.error("Passo %s falhou: %s\n%s", spec.key, exc, tb)
            res = StepResult.failed(
                spec.key, spec.key,
                f"{type(exc).__name__}: {exc}",
            )
            res.params_used["traceback"] = tb

        res.metrics = _safe_metrics(res.metrics)
        _persist_tables(res, ctx)
        results.append(res)
        done_weight += spec.weight
        emit(spec.key, res.status, res.reason or "")

    # ---- comparação de métodos (seção 23) ----
    if should_cancel():
        raise PipelineCancelled()
    emit("method_comparison", "running", "Comparando métodos…")
    method_metrics = _collect_method_metrics(results)
    try:
        comp = build_comparison(ctx, method_metrics)
    except Exception as exc:  # noqa: BLE001
        comp = StepResult.failed("method_comparison", "Comparação Geral dos Métodos", str(exc))
    comp.metrics = _safe_metrics(comp.metrics)
    _persist_tables(comp, ctx)
    results.append(comp)
    done_weight += 1.0
    emit("method_comparison", comp.status, "")

    out = PipelineOutput(steps=results)
    out.metrics_summary = _build_summary(ctx, results, comp)
    out.conclusion = build_conclusion(_findings(ctx, results, comp))
    out.manifest = _build_manifest(ctx, results, lib_versions or {})
    return out


# --------------------------------------------------------------------------- #
def _get(results: list[StepResult], key: str) -> StepResult | None:
    return next((r for r in results if r.key == key), None)


def _collect_method_metrics(results: list[StepResult]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    idw = _get(results, "idw")
    if idw and idw.status == "ok":
        out.append({"method": "IDW", "cv": (idw.metrics or {}).get("best", {}), "note": ""})
    ok = _get(results, "kriging")
    if ok and ok.status == "ok":
        out.append({"method": "Krigagem Ordinária", "cv": (ok.metrics or {}).get("cv", {}), "note": ""})
    ked = _get(results, "external_drift")
    if ked and ked.status == "ok":
        out.append({"method": "Krigagem c/ Deriva Externa", "cv": (ked.metrics or {}).get("cv", {}), "note": ""})
    gwr = _get(results, "gwr")
    if gwr and gwr.status == "ok":
        m = gwr.metrics or {}
        cv = m.get("cv")
        note = ""
        if not cv and m.get("rss") and m.get("n"):
            cv = {"rmse": float(np.sqrt(m["rss"] / m["n"])), "r2": m.get("r2_global")}
            note = "ajuste do modelo (não validação cruzada)"
        out.append({"method": "GWR/GWM", "cv": cv or {}, "note": note})
    cok = _get(results, "cokriging")
    if cok and cok.status == "ok":
        out.append({"method": "Co-Krigagem", "cv": (cok.metrics or {}).get("cv_ck", {}), "note": ""})
    return out


def _build_summary(ctx: AnalysisContext, results: list[StepResult], comp: StepResult) -> dict[str, Any]:
    xmin, ymin, xmax, ymax = ctx.extent_metric
    z = ctx.values(ctx.primary)
    z = z[np.isfinite(z)]
    summary: dict[str, Any] = {
        "n_points": ctx.n,
        "n_variables": len(ctx.analysis_variables),
        "extent_width_m": round(xmax - xmin, 1),
        "extent_height_m": round(ymax - ymin, 1),
        "primary": ctx.primary,
        "units": ctx.units,
    }
    if z.size:
        summary.update(
            mean=float(np.mean(z)), median=float(np.median(z)),
            std=float(np.std(z, ddof=1)) if z.size > 1 else 0.0,
            min=float(np.min(z)), max=float(np.max(z)),
        )

    esda = _get(results, "esda_univariate")
    if esda and esda.status == "ok":
        pm = (esda.metrics or {}).get("primary_moran") or (esda.metrics or {}).get("morans", {}).get(ctx.primary)
        if pm:
            summary["morans_i"] = pm.get("I")
            summary["morans_p"] = pm.get("p")

    krig = _get(results, "kriging")
    if krig and krig.status == "ok":
        summary["best_variogram_model"] = (krig.metrics or {}).get("best_model")
        cv = (krig.metrics or {}).get("cv", {})
        summary["kriging_rmse"] = cv.get("rmse")
        summary["kriging_mae"] = cv.get("mae")
        summary["kriging_r2"] = cv.get("r2")

    if comp and comp.status == "ok":
        cm = comp.metrics or {}
        summary["best_method"] = cm.get("best_method")
        tbl = cm.get("table") or []
        if tbl:
            summary["best_method_rmse"] = tbl[0].get("rmse")
            summary["best_method_mae"] = tbl[0].get("mae")
            summary["best_method_r2"] = tbl[0].get("r2")

    summary["steps_ok"] = [r.key for r in results if r.status == "ok"]
    summary["steps_skipped"] = [
        {"key": r.key, "title": r.title, "reason": r.reason} for r in results if r.status == "skipped"
    ]
    summary["steps_failed"] = [
        {"key": r.key, "title": r.title, "reason": r.reason} for r in results if r.status == "failed"
    ]
    return _safe_metrics(summary)


def _findings(ctx: AnalysisContext, results: list[StepResult], comp: StepResult) -> dict[str, Any]:
    esda = _get(results, "esda_univariate")
    pm = None
    if esda and esda.status == "ok":
        pm = (esda.metrics or {}).get("primary_moran") or (esda.metrics or {}).get("morans", {}).get(ctx.primary)
    best = None
    if comp and comp.status == "ok" and (comp.metrics or {}).get("table"):
        best = comp.metrics["table"][0]
    return {
        "primary": ctx.primary,
        "alpha": ctx.alpha,
        "moran_primary": pm,
        "best_method": best,
        "skipped": [
            {"title": r.title, "reason": r.reason} for r in results if r.status in ("skipped", "failed")
        ],
    }


def _build_manifest(
    ctx: AnalysisContext, results: list[StepResult], lib_versions: dict[str, str]
) -> dict[str, Any]:
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "context": ctx.snapshot(),
        "project": {"name": ctx.project_name, "client": ctx.client, "units": ctx.units},
        "steps": [
            {
                "key": r.key, "title": r.title, "status": r.status, "reason": r.reason,
                "interpretation": r.interpretation,
                "n_tables": len(r.tables), "n_figures": len(r.figures),
                "params_used": {k: v for k, v in (r.params_used or {}).items() if k != "traceback"},
                "metrics": r.metrics,
            }
            for r in results
        ],
        "library_versions": lib_versions,
    }
