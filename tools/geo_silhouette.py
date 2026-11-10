#!/usr/bin/env python3
"""Rendu des silhouettes de pays (Natural Earth, domaine public).

Extrait partage entre les cartes video et, plus tard, les pages pays du site :
meme source, meme projection, meme rendu. Aucune dependance externe.
"""
from __future__ import annotations

import json
from pathlib import Path

GEO = Path("sources/geo/ne_110m_countries.geojson")
_cache: dict | None = None


def load() -> dict:
    """Indexe les pays par code ISO A3, avec leur bbox en lon/lat."""
    global _cache
    if _cache is not None:
        return _cache
    data = json.loads(GEO.read_text(encoding="utf-8"))
    index = {}
    for f in data["features"]:
        p = f["properties"]
        iso = p.get("ADM0_A3") or p.get("ISO_A3")
        if not iso:
            continue
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        rings = [[[float(x), float(y)] for x, y in ring] for poly in polys for ring in poly]
        xs = [pt[0] for ring in rings for pt in ring]
        ys = [pt[1] for ring in rings for pt in ring]
        if not xs:
            continue
        index[iso] = {
            "rings": rings,
            "bbox": (min(xs), min(ys), max(xs), max(ys)),
            "name": p.get("ADMIN") or iso,
        }
    _cache = index
    return index


def world_rings() -> list[list[list[float]]]:
    """Toutes les frontières, pour une carte du monde en fond."""
    idx = load()
    return [ring for c in idx.values() for ring in c["rings"]]


def project(rings, bbox, box, keep_aspect=True):
    """Projette des anneaux lon/lat vers un rectangle cible (equirectangulaire).

    box = (x0, y0, x1, y1). Le pays est centré et mis à l'échelle pour tenir
    dans la boîte, en conservant les proportions.
    """
    x0, y0, x1, y1 = box
    lon0, lat0, lon1, lat1 = bbox
    w, h = max(1e-6, lon1 - lon0), max(1e-6, lat1 - lat0)
    bw, bh = x1 - x0, y1 - y0
    if keep_aspect:
        s = min(bw / w, bh / h)
    else:
        s = None
    out = []
    for ring in rings:
        pts = []
        for lon, lat in ring:
            if s is None:
                px = x0 + (lon - lon0) / w * bw
                py = y0 + (lat1 - lat) / h * bh
            else:
                cx = x0 + bw / 2 - (lon0 + lon1) / 2 * s
                cy = y0 + bh / 2 + (lat0 + lat1) / 2 * s
                px = cx + lon * s
                py = cy - lat * s
            pts.append((px, py))
        if len(pts) > 2:
            out.append(pts)
    return out
