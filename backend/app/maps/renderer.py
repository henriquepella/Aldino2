"""Renderização de mapas profissionais (seção 24).

Todos os mapas incluem: mapa-base (OpenStreetMap / CartoDB via contextily),
título, subtítulo com método/unidade, legenda (colorbar), barra de escala,
seta de norte, eixos com coordenadas, pontos amostrais e um rodapé com fonte
dos dados e CRS.

Saídas: PNG + SVG + PDF (alta resolução). GeoTIFF é gerado quando ``rasterio``
está instalado (import protegido).

O mapa-base exige acesso à internet no momento da renderização. Se não houver
(ou se o serviço de tiles falhar), o mapa é gerado sem o fundo — sem quebrar.
"""
from __future__ import annotations

import math
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import cm  # noqa: E402
from matplotlib.patches import FancyArrow  # noqa: E402

from app.analysis.base import AnalysisContext, FigureResult  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.logging import get_logger  # noqa: E402

log = get_logger("maps")

_DEF_CMAP = "viridis"
_DIVERGING = "RdBu_r"

# Provedores de mapa-base (contextily) que funcionam SEM chave de API.
# 'satellite' (Esri World Imagery) é o padrão — mostra o terreno real onde os
# pontos estão amostrados, ideal para solo/geologia/agronomia.
_BASEMAP_PROVIDERS = {
    "satellite": ("Esri", "WorldImagery"),
    "imagery": ("Esri", "WorldImagery"),
    "gray": ("Esri", "WorldGrayCanvas"),
    "light": ("Esri", "WorldGrayCanvas"),
    "streets": ("Esri", "WorldStreetMap"),
    "topo": ("Esri", "WorldTopoMap"),
    "terrain": ("OpenTopoMap", None),
    "osm": ("OpenStreetMap", "Mapnik"),
    "none": None,
}
_BASEMAP_CACHE = Path(tempfile.gettempdir()) / "geo_tiles_cache"
_USER_AGENT = "PlataformaGeoestatistica/0.1 (+analise geoestatistica)"


def _bounds_wgs84(ctx: AnalysisContext, xmin, ymin, xmax, ymax) -> list[float] | None:
    """Converte a extensão métrica do mapa para lon/lat (para overlays web)."""
    try:
        from pyproj import Transformer

        tr = Transformer.from_crs(ctx.crs_metric, "EPSG:4326", always_xy=True)
        lons, lats = tr.transform([xmin, xmax, xmin, xmax], [ymin, ymin, ymax, ymax])
        return [min(lons), min(lats), max(lons), max(lats)]  # [W, S, E, N]
    except Exception:  # noqa: BLE001
        return None


def _add_basemap(ctx: AnalysisContext, ax, *, kind: str) -> bool:
    """Adiciona o mapa-base ao eixo (em metros, CRS = ctx.crs_metric).

    ``kind`` = "surface" | "points". Retorna True se conseguiu.
    """
    choice = str(ctx.param("basemap", settings.default_basemap) or "none").lower()
    if choice in ("false", "0", "no", "off"):
        choice = "none"
    if choice in ("true", "1", "yes", "on"):
        choice = "satellite"
    if choice == "none":
        return False
    prov = _BASEMAP_PROVIDERS.get(choice)
    if prov is None:
        return False

    try:
        import contextily as cx

        _BASEMAP_CACHE.mkdir(parents=True, exist_ok=True)
        try:
            cx.set_cache_dir(str(_BASEMAP_CACHE))
        except Exception:  # noqa: BLE001
            pass

        name, variant = prov
        source = getattr(cx.providers, name)
        if variant:
            source = getattr(source, variant)
        try:
            source = source(headers={"User-Agent": _USER_AGENT})  # xyzservices provider
        except Exception:  # noqa: BLE001
            pass

        cx.add_basemap(
            ax, crs=ctx.crs_metric, source=source,
            attribution_size=5, zorder=-10, zoom="auto",
        )
        return True
    except Exception as exc:  # noqa: BLE001  (sem internet / tile indisponível)
        log.info("Mapa-base indisponível (%s) — mapa gerado sem fundo.", exc)
        return False


def _align_points(ctx: AnalysisContext, values) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """Alinha um vetor de valores às coordenadas amostrais.

    Módulos frequentemente ajustam modelos sobre o subconjunto finito de uma
    variável (``ctx.clean_xyz``). Se o comprimento não bate com ``ctx.n``,
    tentamos a máscara finita da variável principal; senão devolvemos ``None``
    (o mapa é desenhado sem colorir os pontos, sem quebrar).
    """
    if values is None:
        return ctx.mx, ctx.my, None
    v = np.asarray(values)
    if v.dtype != object:
        v = v.astype(float)
    if len(v) == len(ctx.mx):
        return ctx.mx, ctx.my, v
    for cand in (ctx.primary, *ctx.secondary, *ctx.explanatory):
        try:
            mask = np.isfinite(ctx.values(cand))
        except Exception:  # noqa: BLE001
            continue
        if int(mask.sum()) == len(v):
            return ctx.mx[mask], ctx.my[mask], v
    return ctx.mx, ctx.my, None


def _nice_scale_length(span: float) -> float:
    raw = span / 4.0
    if raw <= 0:
        return 1.0
    p = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if m * p >= raw:
            return m * p
    return 10 * p


def _fmt_dist(m: float) -> str:
    if m >= 1000:
        return f"{m/1000:g} km"
    return f"{m:g} m"


def _add_scalebar(ax, xmin, xmax, ymin, ymax) -> None:
    span = xmax - xmin
    length = _nice_scale_length(span)
    x0 = xmin + 0.05 * span
    y0 = ymin + 0.06 * (ymax - ymin)
    ax.plot([x0, x0 + length], [y0, y0], color="black", lw=3, solid_capstyle="butt", zorder=6)
    ax.plot([x0, x0], [y0, y0 + 0.012 * (ymax - ymin)], color="black", lw=3, zorder=6)
    ax.plot([x0 + length, x0 + length], [y0, y0 + 0.012 * (ymax - ymin)], color="black", lw=3, zorder=6)
    ax.text(x0 + length / 2, y0 + 0.02 * (ymax - ymin), _fmt_dist(length),
            ha="center", va="bottom", fontsize=8, zorder=6)


def _add_north(ax, xmin, xmax, ymin, ymax) -> None:
    x = xmax - 0.06 * (xmax - xmin)
    y0 = ymax - 0.16 * (ymax - ymin)
    dy = 0.10 * (ymax - ymin)
    ax.add_patch(FancyArrow(x, y0, 0, dy, width=0.0, head_width=0.02 * (xmax - xmin),
                            head_length=0.03 * (ymax - ymin), fc="black", ec="black", zorder=6))
    ax.text(x, y0 + dy + 0.015 * (ymax - ymin), "N", ha="center", va="bottom",
            fontsize=10, fontweight="bold", zorder=6)


def _footer(fig, ctx: AnalysisContext, method: str, *, basemap: bool = False) -> None:
    src = ctx.data_source or "dados enviados pelo usuário"
    txt = (
        f"Método: {method}  ·  Unidade: {ctx.units or 'n/d'}  ·  "
        f"CRS de análise: {ctx.crs_metric}  ·  CRS de origem: {ctx.crs or 'n/d'}  ·  "
        f"Fonte: {src}  ·  Projeto: {ctx.project_name or 'n/d'}"
    )
    if basemap:
        txt += "  ·  Mapa-base: atribuição no rodapé do mapa"
    fig.text(0.5, 0.005, txt, ha="center", va="bottom", fontsize=6.5, color="#555555")


def _save(
    fig, ctx: AnalysisContext, name: str, title: str, caption: str, meta: dict[str, Any]
) -> FigureResult:
    outdir: Path = ctx.dirs.get("maps", ctx.dirs.get("figures", Path(".")))
    outdir.mkdir(parents=True, exist_ok=True)
    dpi = int(ctx.param("report_map_dpi", 150))
    # Rasteriza as camadas pesadas (superfície/pontos/mapa-base) para SVG/PDF
    # compactos; rótulos, eixos e legendas continuam vetoriais.
    for ax in fig.get_axes():
        ax.set_rasterization_zorder(4)

    if meta.get("basemap"):
        # SVG/PDF que só embutem uma foto de satélite pesam vários MB e não têm
        # valor vetorial — com mapa-base geramos apenas PNG (+ GeoTIFF nas
        # superfícies). Sem mapa-base, mantemos os formatos vetoriais.
        formats: tuple[str, ...] = ("png",)
        dpi = min(dpi, 135)
    else:
        formats = ("png", "pdf", "svg") if ctx.param("map_svg", True) else ("png", "pdf")

    paths: dict[str, str] = {}
    for ext in formats:
        p = outdir / f"{name}.{ext}"
        kw: dict[str, Any] = {"pil_kwargs": {"optimize": True}} if ext == "png" else {}
        fig.savefig(p, dpi=dpi, bbox_inches="tight", facecolor="white", **kw)
        paths[ext] = str(p)
    plt.close(fig)
    return FigureResult(name=name, title=title, caption=caption, kind="map",
                        paths=paths, meta=meta)


def _write_geotiff(path: Path, Z: np.ndarray, gx: np.ndarray, gy: np.ndarray, crs: str) -> str | None:
    try:
        import rasterio
        from rasterio.transform import from_origin
    except Exception:  # noqa: BLE001
        return None
    res_x = (gx[-1] - gx[0]) / (len(gx) - 1)
    res_y = (gy[-1] - gy[0]) / (len(gy) - 1)
    transform = from_origin(gx[0] - res_x / 2, gy[-1] + res_y / 2, res_x, res_y)
    arr = np.asarray(Z, dtype="float32")[::-1]
    try:
        with rasterio.open(
            path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1],
            count=1, dtype="float32", crs=crs, transform=transform, nodata=np.nan,
        ) as dst:
            dst.write(arr, 1)
        return str(path)
    except Exception:  # noqa: BLE001
        return None


def render_surface(
    ctx: AnalysisContext,
    Z: np.ndarray,
    gx: np.ndarray,
    gy: np.ndarray,
    *,
    name: str,
    title: str,
    method: str,
    cbar_label: str = "",
    sample_values: np.ndarray | None = None,
    show_points: bool = True,
    diverging: bool = False,
    caption: str = "",
    write_tiff: bool = True,
) -> FigureResult:
    Z = np.asarray(Z, float)
    xmin, xmax = float(np.min(gx)), float(np.max(gx))
    ymin, ymax = float(np.min(gy)), float(np.max(gy))
    cmap = _DIVERGING if diverging else ctx.param("cmap", _DEF_CMAP)

    fig, ax = plt.subplots(figsize=(8.2, 7.0))
    vmin = np.nanpercentile(Z, 1) if np.isfinite(Z).any() else 0
    vmax = np.nanpercentile(Z, 99) if np.isfinite(Z).any() else 1
    if diverging:
        m = max(abs(vmin), abs(vmax))
        vmin, vmax = -m, m

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal", adjustable="box")

    # 1) mapa-base primeiro (define se a superfície fica translúcida)
    has_basemap = _add_basemap(ctx, ax, kind="surface")
    default_alpha = 0.80 if has_basemap else 0.96
    surf_alpha = float(ctx.param("surface_alpha", default_alpha))

    mesh = ax.pcolormesh(
        gx, gy, Z, cmap=cmap, shading="auto", vmin=vmin, vmax=vmax,
        alpha=surf_alpha, zorder=1,
    )
    try:
        ax.contour(gx, gy, Z, colors="k", linewidths=0.3, alpha=0.35, levels=8, zorder=2)
    except Exception:  # noqa: BLE001
        pass

    if show_points:
        px, py, cvals = _align_points(ctx, sample_values)
        if cvals is not None and cvals.dtype != object:
            ax.scatter(px, py, c=cvals, cmap=cmap, vmin=vmin, vmax=vmax,
                       edgecolors="black", linewidths=0.4, s=22, zorder=5)
        else:
            ax.scatter(px, py, c="white", edgecolors="black", linewidths=0.5,
                       s=14, alpha=0.85, zorder=5)

    cbar = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label(cbar_label or (ctx.units or "valor"))

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel(f"Este (m) — {ctx.crs_metric}")
    ax.set_ylabel("Norte (m)")
    ax.ticklabel_format(style="plain", useOffset=False)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=12)

    _add_scalebar(ax, xmin, xmax, ymin, ymax)
    _add_north(ax, xmin, xmax, ymin, ymax)
    _footer(fig, ctx, method, basemap=has_basemap)
    fig.subplots_adjust(bottom=0.12)

    meta = {
        "bounds_metric": [xmin, ymin, xmax, ymax],
        "bounds_wgs84": _bounds_wgs84(ctx, xmin, ymin, xmax, ymax),
        "crs_metric": ctx.crs_metric,
        "method": method,
        "unit": ctx.units,
        "grid_shape": list(np.asarray(Z).shape),
        "basemap": has_basemap,
    }
    fr = _save(fig, ctx, name, title, caption, meta)
    if write_tiff:
        tif = _write_geotiff(Path(fr.paths["png"]).with_suffix(".tif"), Z, gx, gy, ctx.crs_metric)
        if tif:
            fr.paths["tif"] = tif
    return fr


def render_points(
    ctx: AnalysisContext,
    values: np.ndarray,
    *,
    name: str,
    title: str,
    method: str = "Pontos amostrais",
    cbar_label: str = "",
    categorical: bool = False,
    cat_labels: dict[Any, str] | None = None,
    diverging: bool = False,
    caption: str = "",
) -> FigureResult:
    px, py, aligned = _align_points(ctx, values)
    if aligned is None:  # comprimento incompatível — usa o vetor original truncado
        v = np.asarray(values)
        m = min(len(v), len(ctx.mx))
        px, py, aligned = ctx.mx[:m], ctx.my[:m], v[:m]
    values = aligned
    xmin, xmax = float(np.nanmin(px)), float(np.nanmax(px))
    ymin, ymax = float(np.nanmin(py)), float(np.nanmax(py))
    dx, dy = (xmax - xmin) or 1, (ymax - ymin) or 1
    xmin, xmax = xmin - 0.05 * dx, xmax + 0.05 * dx
    ymin, ymax = ymin - 0.05 * dy, ymax + 0.05 * dy

    fig, ax = plt.subplots(figsize=(8.2, 7.0))
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal", adjustable="box")
    has_basemap = _add_basemap(ctx, ax, kind="points")

    if categorical:
        uniq = [u for u in np.unique(values) if u == u]
        palette = cm.get_cmap("tab10", max(len(uniq), 1))
        for i, u in enumerate(uniq):
            mask = values == u
            lbl = (cat_labels or {}).get(u, (cat_labels or {}).get(float(u) if isinstance(u, (int, float, np.number)) else u, str(u)))
            ax.scatter(px[mask], py[mask], color=palette(i), s=34,
                       edgecolors="black", linewidths=0.4, label=str(lbl), zorder=5)
        ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    else:
        vals = values.astype(float)
        vfin = vals[np.isfinite(vals)]
        cmap = _DIVERGING if diverging else ctx.param("cmap", _DEF_CMAP)
        vmin = np.nanpercentile(vfin, 1) if len(vfin) else 0
        vmax = np.nanpercentile(vfin, 99) if len(vfin) else 1
        if diverging:
            m = max(abs(vmin), abs(vmax)) or 1.0
            vmin, vmax = -m, m
        sc = ax.scatter(px, py, c=vals, cmap=cmap, s=32,
                        vmin=vmin, vmax=vmax, edgecolors="black", linewidths=0.3, zorder=5)
        cbar = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.03)
        cbar.set_label(cbar_label or (ctx.units or "valor"))

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel(f"Este (m) — {ctx.crs_metric}")
    ax.set_ylabel("Norte (m)")
    ax.ticklabel_format(style="plain", useOffset=False)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=12)

    _add_scalebar(ax, xmin, xmax, ymin, ymax)
    _add_north(ax, xmin, xmax, ymin, ymax)
    _footer(fig, ctx, method, basemap=has_basemap)
    fig.subplots_adjust(bottom=0.12)

    meta = {
        "bounds_metric": [xmin, ymin, xmax, ymax],
        "bounds_wgs84": _bounds_wgs84(ctx, xmin, ymin, xmax, ymax),
        "crs_metric": ctx.crs_metric,
        "method": method,
        "unit": ctx.units,
        "basemap": has_basemap,
    }
    return _save(fig, ctx, name, title, caption, meta)
