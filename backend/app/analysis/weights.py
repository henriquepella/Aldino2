"""Construção de matrizes de pesos espaciais (reuso por ESDA / Moran / bivariada).

Para dados de pontos usamos KNN (padrão) ou banda de distância. As coordenadas
são sempre as métricas (``ctx.mx`` / ``ctx.my``).
"""
from __future__ import annotations

import warnings

import numpy as np

from app.analysis.base import AnalysisContext


def build_weights(
    ctx: AnalysisContext,
    *,
    kind: str | None = None,
    k: int | None = None,
    threshold: float | None = None,
    mask: np.ndarray | None = None,
):
    """Retorna ``(w, info)`` — ``w`` é um ``libpysal.weights.W`` row-standardized."""
    from libpysal.weights import KNN, DistanceBand

    coords = np.c_[ctx.mx, ctx.my]
    if mask is not None:
        coords = coords[mask]

    n = len(coords)
    kind = (kind or ctx.param("weights_kind", "knn")).lower()
    k = int(k or ctx.param("knn_k", 8))
    k = max(1, min(k, n - 1))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if kind in ("distance", "distanceband", "band"):
            if threshold is None:
                # menor limiar que garante todos com ≥1 vizinho
                from scipy.spatial import cKDTree

                tree = cKDTree(coords)
                d, _ = tree.query(coords, k=2)
                threshold = float(np.max(d[:, 1]) * 1.05)
            w = DistanceBand(coords, threshold=threshold, binary=False, silence_warnings=True)
            info = {"kind": "distance_band", "threshold": round(float(threshold), 3)}
        else:
            w = KNN.from_array(coords, k=k)
            info = {"kind": "knn", "k": k}

        w.transform = "r"

    info.update(n=int(n), n_islands=len(w.islands), pct_nonzero=round(w.pct_nonzero, 3))
    return w, info
