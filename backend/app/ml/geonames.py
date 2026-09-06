"""Human-readable place names for detections.

1. STATE: point-in-polygon against India states GeoJSON (Shapely STRtree).
2. NEAREST FACILITY NAME: full facility list with names (closer lookups than
   the category-only BallTree in enrichment.py).
3. REGION LABEL: 'Odisha - 0.8 km from Angul quarry' style string.

All offline. Cached lookups in the `location` column (NULL = not yet named).
"""
import json
import logging
import math
from pathlib import Path

from ..config import settings

log = logging.getLogger(__name__)

STATES_PATH = Path(__file__).resolve().parents[2] / "ml" / "india_states.geojson"
FACILITIES_PATH = Path(__file__).resolve().parents[2] / "ml" / "osm_industrial_facilities.geojson"

# older names in the boundaries dataset -> current official names
STATE_ALIASES = {
    "Orissa": "Odisha",
    "Uttaranchal": "Uttarakhand",
    "Pondicherry": "Puducherry",
    "NCT of Delhi": "Delhi",
}

_state_tree = None
_state_names = None
_fac_index = None


def _load_states():
    global _state_tree, _state_names
    if _state_tree is not None:
        return _state_tree, _state_names
    from shapely.geometry import shape, Point
    from shapely.strtree import STRtree

    gj = json.loads(STATES_PATH.read_text())
    geoms, names = [], []
    for feat in gj["features"]:
        name = (feat["properties"].get("NAME_1") or "").strip()
        if not name:
            continue
        geoms.append(shape(feat["geometry"]))
        names.append(name)

    _state_tree = STRtree(geoms)
    _state_names = names
    log.info("State boundaries loaded: %d states", len(names))
    return _state_tree, _state_names


def state_for(lat: float, lon: float) -> str | None:
    """Indian state containing this point, or None (outside land/boundaries)."""
    tree, names = _load_states()
    from shapely.geometry import Point

    idxs = tree.query(Point(lon, lat))
    for i in idxs:
        geom = tree.geometries[i]
        if geom.covers(Point(lon, lat)):
            return STATE_ALIASES.get(names[i], names[i])
    return None


def nearest_state_border(lat: float, lon: float) -> tuple[str | None, float]:
    """(state, approx_km) of the nearest state polygon for out-of-bounds points."""
    import numpy as np
    tree, names = _load_states()
    from shapely.geometry import Point

    try:
        idx_arr = np.atleast_1d(tree.query_nearest(Point(lon, lat)))
        idx = int(idx_arr[0])
        dist_deg = tree.geometries[idx].distance(Point(lon, lat))
        return STATE_ALIASES.get(names[idx], names[idx]), dist_deg * 111.32
    except Exception:
        return None, 999.0


def _load_facilities():
    global _fac_index
    if _fac_index is not None:
        return _fac_index
    import numpy as np
    from sklearn.neighbors import BallTree

    gj = json.loads(FACILITIES_PATH.read_text())
    coords, metas = [], []
    for feat in gj["features"]:
        lon, lat = feat["geometry"]["coordinates"][:2]
        props = feat.get("properties", {})
        name = (props.get("name") or "").strip()
        coords.append([math.radians(lat), math.radians(lon)])
        metas.append({
            "name": name,
            "category": props.get("category") or "industrial site",
        })

    _fac_index = {
        "tree": BallTree(np.array(coords), metric="haversine"),
        "metas": metas,
    }
    log.info("Facility name index loaded: %d facilities", len(metas))
    return _fac_index


def nearest_facility_named(lat: float, lon: float):
    """(distance_m, name_or_None, category) of nearest known facility."""
    import numpy as np

    idx = _load_facilities()
    dist, i = idx["tree"].query([[math.radians(lat), math.radians(lon)]], k=1)
    meta = idx["metas"][int(i[0][0])]
    return float(dist[0][0]) * 6_371_000, meta["name"] or None, meta["category"]


def build_region_label(lat: float, lon: float,
                       distance_m: float | None = None,
                       fac_name: str | None = None,
                       fac_category: str | None = None) -> str:
    """'Odisha - 0.8 km from Angul quarry' / 'Near Punjab border' style labels."""
    state = state_for(lat, lon)

    if state is None:
        # outside mapped polygons: international territory, coastal fringes,
        # disputed strips. Name the nearest Indian state as reference.
        near_state, km = nearest_state_border(lat, lon)
        if not near_state:
            state = "Outside mapped states"
        elif km < 1:
            state = f"Near {near_state} border (<1 km out)"
        elif km <= 60:
            state = f"Near {near_state} border ({km:.0f} km out)"
        else:
            state = f"Outside India (nearest: {near_state}, {km:.0f} km away)"

    if fac_name:
        return f"{state} - {distance_m/1000:.1f} km from {fac_name}"
    if fac_category and distance_m is not None and distance_m <= 5000:
        cat = fac_category.replace("_", " ")
        return f"{state} - {distance_m/1000:.1f} km from {cat}"
    return state


def name_unnamed_locations(limit: int | None = None) -> int:
    """Fill `location` for rows where it is NULL. Returns rows updated."""
    sql = "SELECT id, latitude, longitude, distance_to_facility_m, nearest_facility_category FROM detections WHERE location IS NULL"
    if limit:
        sql += f" LIMIT {int(limit)}"

    with __import__("sqlite3").connect(settings.db_path) as conn:
        conn.row_factory = __import__("sqlite3").Row
        rows = conn.execute(sql).fetchall()
        updated = 0
        for r in rows:
            dist_m = r["distance_to_facility_m"]
            fac_name = fac_cat = None
            if dist_m is None or dist_m > 2000:
                # enrich with named facility when we don't have a good one yet
                dist_m2, fac_name, fac_cat = nearest_facility_named(r["latitude"], r["longitude"])
                if dist_m is None or dist_m2 < dist_m:
                    dist_m = dist_m2
                if fac_name:
                    fac_cat = fac_cat or r["nearest_facility_category"]
                    conn.execute(
                        "UPDATE detections SET distance_to_facility_m = ?, nearest_facility_category = ? WHERE id = ?",
                        (dist_m, fac_cat, r["id"]),
                    )
            label = build_region_label(r["latitude"], r["longitude"], dist_m, fac_name, fac_cat or r["nearest_facility_category"])
            conn.execute("UPDATE detections SET location = ? WHERE id = ?", (label, r["id"]))
            updated += 1
        return updated
