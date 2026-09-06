"""Classifier — integrated with the ML teammate's trained XGBoost model.

Their model.pkl is a dict:
    { model, target_encoder, feature_encoders, feature_cols }
Feature order (MUST match):
    [bright_ti4, bright_ti5, frp, confidence, daynight,
     detection_count, unique_days, distance_to_facility_m, landcover_class]
Encoders: confidence {h,l,n}, daynight {D,N}, landcover_class {ESA classes + unknown}
Targets: crop_burning, gas_flare, industrial_fire, mining_activity,
         unclassified_other, wildfire

DB `classification` values shown on the frontend (via LABEL_MAP below):
    Vegetation Fire | Industrial Heat Source | Persistent Thermal Anomaly | Unclassified
"""
import logging
import sqlite3
from pathlib import Path

import joblib

from ..config import settings

log = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parents[2] / "ml" / "model.pkl"

_PAYLOAD = None
_LOAD_TRIED = False

# model label -> frontend display class
LABEL_MAP = {
    "wildfire": "Vegetation Fire",
    "crop_burning": "Vegetation Fire",
    "industrial_fire": "Industrial Heat Source",
    "gas_flare": "Persistent Thermal Anomaly",
    "mining_activity": "Industrial Heat Source",
    "unclassified_other": "Unclassified",
}

# legacy rule-based fallback (used only if model file missing/corrupt)
def rule_based(brightness: float, frp: float, daynight: str, persistent: bool) -> tuple[str, float]:
    if persistent:
        return "Persistent Thermal Anomaly", 90.0
    if brightness >= 360 and frp >= 25:
        return "Industrial Heat Source", 75.0
    if brightness >= 330:
        return "Vegetation Fire", 70.0
    return "Unclassified", 50.0


def _load_payload():
    global _PAYLOAD, _LOAD_TRIED
    if _LOAD_TRIED:
        return _PAYLOAD
    _LOAD_TRIED = True
    if MODEL_PATH.exists():
        try:
            _PAYLOAD = joblib.load(MODEL_PATH)
            log.info("ML model loaded: %s (features: %s)", MODEL_PATH.name, _PAYLOAD["feature_cols"])
        except Exception:
            log.exception("Failed to load model - will use rule fallback")
    else:
        log.warning("No model at %s - will use rule fallback", MODEL_PATH)
    return _PAYLOAD


def _encode_features(row, payload):
    """Build the feature vector in the model's expected order/encoding."""
    import numpy as np

    feature_cols = payload["feature_cols"]
    feature_encoders = payload["feature_encoders"]

    raw = {
        "bright_ti4": row["brightness"],
        "bright_ti5": row["bright_ti5"],
        "frp": row["frp"],
        "confidence": row["confidence_raw"] or "n",
        "daynight": (row["daynight"] or "d").upper(),
        "detection_count": row["detection_count"] or 1,
        "unique_days": row["unique_days"] or 1,
        "distance_to_facility_m": row["distance_to_facility_m"],
        "landcover_class": row["landcover_class"] or "unknown",
    }

    vals = []
    for col in feature_cols:
        v = raw.get(col)
        if col in feature_encoders:
            le = feature_encoders[col]
            known = set(le.classes_)
            s = str(v) if v is not None else "unknown"
            if s not in known:
                s = "unknown" if "unknown" in known else sorted(known)[0]
            v = int(le.transform([s])[0])
        elif v is None:
            v = 0
        vals.append(float(v))
    return np.array([vals])


def classify_row(row) -> tuple[str, float]:
    """Classify one sqlite Row. Returns (display_label, confidence_pct)."""
    payload = _load_payload()
    if payload is None:
        persistent = bool(row["detection_count"] and row["detection_count"] > 3)
        return rule_based(row["brightness"] or 0, row["frp"] or 0, row["daynight"], persistent)

    import numpy as np

    X = _encode_features(row, payload)
    model = payload["model"]
    target_encoder = payload["target_encoder"]

    pred_idx = int(model.predict(X)[0])
    label = str(target_encoder.inverse_transform([pred_idx])[0])

    proba = None
    try:
        probas = model.predict_proba(X)[0]
        proba = float(np.max(probas)) * 100
    except Exception:
        pass

    display = LABEL_MAP.get(label, "Unclassified")
    # flares are inherently persistent - display class carries that meaning
    return display, round(proba or 80.0, 1)


def classify_unclassified(limit: int | None = None) -> int:
    """Classify 'Unclassified' rows. Returns count updated."""
    with sqlite3.connect(settings.db_path) as conn:
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM detections WHERE classification = 'Unclassified'"
        if limit:
            sql += f" LIMIT {int(limit)}"
        rows = conn.execute(sql).fetchall()

        updated = 0
        for r in rows:
            display, proba = classify_row(r)
            conn.execute(
                "UPDATE detections SET classification = ?, ml_confidence = ? WHERE id = ?",
                (display, proba, r["id"]),
            )
            updated += 1
        return updated


def run_ml_pipeline() -> dict:
    """Enrich features, classify, then name locations. Called by ingest + admin."""
    from .enrichment import run_enrichment
    from .geonames import name_unnamed_locations
    enrich = run_enrichment()
    classified = classify_unclassified()
    named = name_unnamed_locations()
    return {"enrichment": enrich, "classified": classified, "named": named}
