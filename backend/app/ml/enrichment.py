"""Feature enrichment for the ML model.

Computes the engineered features the ML teammate's model expects:
  1. Persistence:  detection_count + unique_days per rounded location (~1km)
     (same logic as their scripts/5_classify_sources.py)
  2. distance_to_facility_m + nearest_facility_category from the OSM
     industrial facilities geojson (their fetch_osm_facilities.py output),
     via a haversine BallTree — no geopandas needed.

Run automatically before classification (see ml/classifier.py run_ml_pipeline).
"""
import json
import logging
import math
import sqlite3
from pathlib import Path

from ..config import settings

log = logging.getLogger(__name__)

FACILITIES_PATH = Path(__file__).resolve().parents[2] / "ml" / "osm_industrial_facilities.geojson"
LANDCOVER_LOOKUP = Path(__file__).resolve().parents[2] / "ml" / "landcover_lookup.csv"

_TREE = None
_FAC_CATEGORIES = None
_LC_INDEX = None


def _haversine_tree():
    """Build a BallTree over facility coords using haversine metric (radians)."""
    global _TREE, _FAC_CATEGORIES
    if _TREE is not None:
        return _TREE, _FAC_CATEGORIES

    import numpy as np
    from sklearn.neighbors import BallTree

    with open(FACILITIES_PATH) as f:
        gj = json.load(f)

    coords, cats = [], []
    for feat in gj.get("features", []):
        lon, lat = feat["geometry"]["coordinates"][:2]
        props = feat.get("properties", {})
        coords.append([math.radians(lat), math.radians(lon)])
        cats.append(props.get("category") or "unknown")

    if not coords:
        _TREE, _FAC_CATEGORIES = None, []
        return None, []

    _TREE = BallTree(np.array(coords), metric="haversine")
    _FAC_CATEGORIES = cats
    log.info("Loaded %d OSM facilities for distance features", len(cats))
    return _TREE, _FAC_CATEGORIES


def enrich_persistence() -> int:
    """Per rounded (~1km) location: detection_count + unique_days. Returns rows updated."""
    with sqlite3.connect(settings.db_path) as conn:
        conn.row_factory = sqlite3.Row
        agg = conn.execute(
            """
            SELECT id,
                   (SELECT COUNT(*) FROM detections d2
                     WHERE ROUND(d2.latitude, 2) = ROUND(d1.latitude, 2)
                       AND ROUND(d2.longitude, 2) = ROUND(d1.longitude, 2)) AS det_count,
                   (SELECT COUNT(DISTINCT substr(d2.acquired_at, 1, 10)) FROM detections d2
                     WHERE ROUND(d2.latitude, 2) = ROUND(d1.latitude, 2)
                       AND ROUND(d2.longitude, 2) = ROUND(d1.longitude, 2)) AS u_days
            FROM detections d1
            WHERE d1.detection_count IS NULL OR d1.unique_days IS NULL
            """
        ).fetchall()
        for row in agg:
            conn.execute(
                "UPDATE detections SET detection_count = ?, unique_days = ? WHERE id = ?",
                (row["det_count"], row["u_days"], row["id"]),
            )
        return len(agg)


def enrich_facilities() -> int:
    """Nearest OSM facility distance + category for rows missing it. Returns rows updated."""
    tree, cats = _haversine_tree()
    if tree is None:
        log.warning("No facility data - distance features left NULL")
        return 0

    import numpy as np

    with sqlite3.connect(settings.db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT id, latitude, longitude FROM detections
               WHERE distance_to_facility_m IS NULL"""
        ).fetchall()
        if not rows:
            return 0

        # query in chunks to keep memory sane
        CHUNK = 5000
        for i in range(0, len(rows), CHUNK):
            chunk = rows[i:i + CHUNK]
            coords = np.radians([[r["latitude"], r["longitude"]] for r in chunk])
            dists, idxs = tree.query(coords, k=1)
            for r, dist, idx in zip(chunk, dists[:, 0], idxs[:, 0]):
                meters = float(dist) * 6_371_000  # earth radius in meters
                conn.execute(
                    "UPDATE detections SET distance_to_facility_m = ?, nearest_facility_category = ? WHERE id = ?",
                    (meters, cats[idx], r["id"]),
                )
        return len(rows)


def _landcover_index():
    """Load ML teammate's GEE-derived landcover as a (lat2, lon2) -> class lookup."""
    global _LC_INDEX
    if _LC_INDEX is not None:
        return _LC_INDEX
    import pandas as pd
    if LANDCOVER_LOOKUP.exists():
        df = pd.read_csv(LANDCOVER_LOOKUP, usecols=["latitude", "longitude", "landcover_class"])
        df = df.dropna(subset=["landcover_class"])
        _LC_INDEX = {
            (round(r.latitude, 2), round(r.longitude, 2)): str(r.landcover_class)
            for r in df.itertuples()
        }
        log.info("Landcover lookup loaded: %d locations", len(_LC_INDEX))
    else:
        _LC_INDEX = {}
        log.warning("No landcover lookup file - all classes will be 'unknown'")
    return _LC_INDEX


def enrich_landcover() -> int:
    """Assign landcover_class from teammate's GEE dataset (match ~1km grid);
    'unknown' where no data. Model treats 'unknown' as a valid category."""
    lc_index = _landcover_index()
    with sqlite3.connect(settings.db_path) as conn:
        rows = conn.execute(
            "SELECT id, latitude, longitude FROM detections WHERE landcover_class IS NULL"
        ).fetchall()
        updated = 0
        for id_, lat, lon in rows:
            cls = lc_index.get((round(lat, 2), round(lon, 2)), "unknown")
            conn.execute("UPDATE detections SET landcover_class = ? WHERE id = ?", (cls, id_))
            updated += 1
        return updated


def run_enrichment() -> dict:
    return {
        "persistence": enrich_persistence(),
        "facilities": enrich_facilities(),
        "landcover": enrich_landcover(),
    }
