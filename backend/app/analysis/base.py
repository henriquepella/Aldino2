"""Interface TRAVADA para todos os módulos de análise (seção 34).

Cada módulo em ``app/analysis/`` expõe:

    KEY: str
    TITLE: str
    def applicable(ctx: AnalysisContext) -> tuple[bool, str]
    def run(ctx: AnalysisContext) -> StepResult

O ``PipelineRunner`` chama ``applicable`` e, se ``True``, ``run``. Exceções em
``run`` são capturadas pelo runner e viram ``StepResult`` com status ``failed``
(o pipeline nunca aborta — seção 38).

Todas as coordenadas para cálculos de distância (variograma, IDW, pesos
espaciais, krigagem) devem usar ``ctx.mx`` / ``ctx.my`` (metros). ``ctx.x`` /
``ctx.y`` preservam as coordenadas originais para rótulos de mapa.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

# Backend headless obrigatório: os módulos de análise geram figuras em threads
# de worker (nunca na thread principal). Fixado aqui porque todo módulo de
# análise importa este arquivo.
os.environ.setdefault("MPLBACKEND", "Agg")
# Evita que libs (esda.G_Local, mgwr, sklearn) abram dezenas de subprocessos
# joblib/loky que ficam ociosos por minutos após cada análise.
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "2")
os.environ.setdefault("LOKY_IDLE_WORKER_TIMEOUT", "20")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
import matplotlib  # noqa: E402

matplotlib.use("Agg", force=True)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

Status = Literal["ok", "skipped", "failed"]


# --------------------------------------------------------------------------- #
# Resultados
# --------------------------------------------------------------------------- #
@dataclass
class TableResult:
    name: str
    df: pd.DataFrame
    title: str = ""
    caption: str = ""
    # índices de linha a destacar (ex.: melhor modelo — seções 14, 16, 18, 23)
    highlight_rows: list[int] = field(default_factory=list)
    # coluna usada para ordenar / formatação por coluna
    meta: dict[str, Any] = field(default_factory=dict)

    def to_payload(self, float_fmt: int = 4) -> dict[str, Any]:
        df = self.df.copy()
        columns = [{"key": str(c), "label": str(c)} for c in df.columns]
        rows: list[dict[str, Any]] = []
        for _, r in df.iterrows():
            row: dict[str, Any] = {}
            for c in df.columns:
                v = r[c]
                if isinstance(v, (np.floating, float)) and np.isfinite(v):
                    row[str(c)] = round(float(v), float_fmt)
                elif isinstance(v, (np.integer,)):
                    row[str(c)] = int(v)
                elif v is None or (isinstance(v, float) and not np.isfinite(v)):
                    row[str(c)] = None
                else:
                    row[str(c)] = str(v)
            rows.append(row)
        return {
            "name": self.name,
            "title": self.title,
            "caption": self.caption,
            "columns": columns,
            "rows": rows,
            "highlight_rows": self.highlight_rows,
            "meta": self.meta,
        }


@dataclass
class FigureResult:
    name: str
    title: str = ""
    caption: str = ""
    kind: Literal["chart", "map"] = "chart"
    paths: dict[str, str] = field(default_factory=dict)  # {"png": "...", "svg": "...", ...}
    meta: dict[str, Any] = field(default_factory=dict)  # bounds, crs, unidade, método...


@dataclass
class StepResult:
    key: str
    title: str
    status: Status = "ok"
    reason: str | None = None
    tables: list[TableResult] = field(default_factory=list)
    figures: list[FigureResult] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    interpretation: str | None = None
    params_used: dict[str, Any] = field(default_factory=dict)

    # -- construtores auxiliares --
    @classmethod
    def skipped(cls, key: str, title: str, reason: str) -> "StepResult":
        return cls(key=key, title=title, status="skipped", reason=reason)

    @classmethod
    def failed(cls, key: str, title: str, reason: str) -> "StepResult":
        return cls(key=key, title=title, status="failed", reason=reason)


# --------------------------------------------------------------------------- #
# Contexto
# --------------------------------------------------------------------------- #
@dataclass
class AnalysisContext:
    df: pd.DataFrame
    x_col: str
    y_col: str
    crs: str
    primary: str
    secondary: list[str] = field(default_factory=list)
    explanatory: list[str] = field(default_factory=list)
    aux_drift: str | None = None
    id_col: str | None = None

    dirs: dict[str, Path] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)

    alpha: float = 0.05
    n_perm: int = 999
    random_seed: int = 42

    project_name: str = ""
    client: str = ""
    units: str = ""
    data_source: str = ""

    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("analysis"))

    # caches internos
    _mx: np.ndarray | None = field(default=None, repr=False)
    _my: np.ndarray | None = field(default=None, repr=False)
    _crs_metric: str = field(default="", repr=False)

    # ---------------------------------------------------------------- #
    def __post_init__(self) -> None:
        self.df = self.df.reset_index(drop=True)
        self._project_metric()

    def _project_metric(self) -> None:
        from pyproj import CRS, Transformer

        x = pd.to_numeric(self.df[self.x_col], errors="coerce").to_numpy(float)
        y = pd.to_numeric(self.df[self.y_col], errors="coerce").to_numpy(float)
        try:
            src = CRS.from_user_input(self.crs or "EPSG:4326")
        except Exception:  # noqa: BLE001
            src = CRS.from_epsg(4326)

        if src.is_geographic:
            lon = float(np.nanmean(x))
            lat = float(np.nanmean(y))
            zone = int((lon + 180) // 6) + 1
            epsg = (32700 if lat < 0 else 32600) + zone
            dst = CRS.from_epsg(epsg)
            tr = Transformer.from_crs(src, dst, always_xy=True)
            mx, my = tr.transform(x, y)
            self._mx, self._my = np.asarray(mx, float), np.asarray(my, float)
            self._crs_metric = f"EPSG:{epsg}"
        else:
            self._mx, self._my = x, y
            self._crs_metric = self.crs or "unknown"

    # ---- coordenadas ---------------------------------------------------- #
    @property
    def n(self) -> int:
        return int(len(self.df))

    @property
    def x(self) -> np.ndarray:
        return pd.to_numeric(self.df[self.x_col], errors="coerce").to_numpy(float)

    @property
    def y(self) -> np.ndarray:
        return pd.to_numeric(self.df[self.y_col], errors="coerce").to_numpy(float)

    @property
    def mx(self) -> np.ndarray:
        if self._mx is None:
            self._project_metric()
        return self._mx  # type: ignore[return-value]

    @property
    def my(self) -> np.ndarray:
        if self._my is None:
            self._project_metric()
        return self._my  # type: ignore[return-value]

    @property
    def crs_metric(self) -> str:
        return self._crs_metric

    @property
    def coords_metric(self) -> np.ndarray:
        return np.c_[self.mx, self.my]

    @property
    def extent_metric(self) -> tuple[float, float, float, float]:
        return (
            float(np.nanmin(self.mx)),
            float(np.nanmin(self.my)),
            float(np.nanmax(self.mx)),
            float(np.nanmax(self.my)),
        )

    @property
    def extent_native(self) -> tuple[float, float, float, float]:
        return (
            float(np.nanmin(self.x)),
            float(np.nanmin(self.y)),
            float(np.nanmax(self.x)),
            float(np.nanmax(self.y)),
        )

    # ---- variáveis ---------------------------------------------------- #
    def values(self, name: str) -> np.ndarray:
        """Série numérica como array float (com NaN preservado)."""
        return pd.to_numeric(self.df[name], errors="coerce").to_numpy(float)

    def clean_xyz(self, name: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """(mx, my, z) apenas nas linhas com coordenada e valor finitos."""
        z = self.values(name)
        m = np.isfinite(self.mx) & np.isfinite(self.my) & np.isfinite(z)
        return self.mx[m], self.my[m], z[m]

    @property
    def analysis_variables(self) -> list[str]:
        seen: list[str] = []
        for v in [self.primary, *self.secondary, *self.explanatory, self.aux_drift]:
            if v and v not in seen and v in self.df.columns:
                seen.append(v)
        return seen

    # ---- parâmetros avançados (seção 36) ----------------------------- #
    def param(self, key: str, default: Any = None) -> Any:
        adv = self.config.get("advanced", {}) if isinstance(self.config, dict) else {}
        if key in adv:
            return adv[key]
        if key in self.config:
            return self.config[key]
        return default

    # ---- grade de interpolação ------------------------------------- #
    def make_grid(
        self, resolution: int | None = None, margin: float = 0.05
    ) -> tuple[np.ndarray, np.ndarray]:
        res = int(resolution or self.param("grid_resolution", 80))
        xmin, ymin, xmax, ymax = self.extent_metric
        dx, dy = (xmax - xmin) or 1.0, (ymax - ymin) or 1.0
        gx = np.linspace(xmin - margin * dx, xmax + margin * dx, res)
        gy = np.linspace(ymin - margin * dy, ymax + margin * dy, res)
        return gx, gy

    # ---- salvar figura ------------------------------------------------ #
    def save_fig(
        self,
        fig,
        name: str,
        *,
        subdir: str = "figures",
        title: str = "",
        caption: str = "",
        kind: Literal["chart", "map"] = "chart",
        formats: tuple[str, ...] = ("png", "svg"),
        dpi: int | None = None,
        meta: dict[str, Any] | None = None,
    ) -> FigureResult:
        import matplotlib.pyplot as plt

        outdir: Path = self.dirs.get(subdir, self.dirs.get("figures", Path(".")))
        outdir.mkdir(parents=True, exist_ok=True)
        dpi = int(dpi or self.param("map_dpi", 120))
        paths: dict[str, str] = {}
        for ext in formats:
            p = outdir / f"{name}.{ext}"
            fig.savefig(p, dpi=dpi, bbox_inches="tight", facecolor="white")
            paths[ext] = str(p)
        plt.close(fig)
        return FigureResult(
            name=name, title=title or name, caption=caption, kind=kind,
            paths=paths, meta=meta or {},
        )

    def table_path(self, name: str) -> Path:
        d: Path = self.dirs.get("tables", Path("."))
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{name}.csv"

    def snapshot(self) -> dict[str, Any]:
        return {
            "x_col": self.x_col, "y_col": self.y_col, "crs": self.crs,
            "crs_metric": self.crs_metric, "primary": self.primary,
            "secondary": list(self.secondary), "explanatory": list(self.explanatory),
            "aux_drift": self.aux_drift, "id_col": self.id_col,
            "n": self.n, "alpha": self.alpha, "n_perm": self.n_perm,
            "seed": self.random_seed,
            "advanced": self.config.get("advanced", {}),
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }


def dataclass_asdict(obj) -> dict:
    return dataclasses.asdict(obj)
