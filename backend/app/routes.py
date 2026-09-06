"""REST API - the only contract the CRA frontend needs (src/api/detections.js):
  GET /api/detections -> [ { id, location, lat, lng, classification, confidence,
                             brightness, frp, satellite, time }, ... ]
  GET /api/stats      -> { fire, industrial, persistent, highConfidence }
"""
import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from .db import get_connection
from .exporters import export_detections
from .schemas import Detection, Stats
from .services import latest_detections, compute_stats, compute_trend

router = APIRouter(prefix="/api")


def row_to_detection(r) -> Detection:
    acquired = r["acquired_at"] or r["created_at"]
    try:
        dt = datetime.fromisoformat(acquired)
        mins = max(0, int((datetime.now(timezone.utc) - dt).total_seconds() // 60))
        ago = f"{mins}m ago" if mins < 60 else f"{mins // 60}h ago"
    except ValueError:
        ago = "unknown"

    lat, lng = r["latitude"], r["longitude"]
    location = r["location"] or f"{lat:.3f}, {lng:.3f}"

    return Detection(
        id=r["id"],
        location=location,
        lat=round(lat, 5),
        lng=round(lng, 5),
        classification=r["classification"],
        confidence=float(r["ml_confidence"] or r["confidence"] or 50),
        brightness=float(r["brightness"] or 0),
        frp=float(r["frp"] or 0),
        satellite=r["satellite"] or "unknown",
        time=ago,
    )


@router.get("/detections", response_model=list[Detection])
def get_detections(
    classification: str | None = Query(None, description="e.g. 'Vegetation Fire'"),
    min_confidence: float = Query(0, ge=0, le=100),
    limit: int = Query(1000, ge=1, le=5000),
):
    rows = latest_detections(limit=limit)
    dets = [row_to_detection(r) for r in rows]
    if classification:
        dets = [d for d in dets if d.classification == classification]
    return [d for d in dets if d.confidence >= min_confidence]


@router.get("/stats", response_model=Stats)
def get_stats():
    return compute_stats()


@router.get("/trend")
def get_trend(days: int = Query(7, ge=1, le=30)):
    """Per-day counts feeding the frontend TrendChart."""
    return compute_trend(days=days)


@router.get("/export")
def export(fmt: str = Query("geojson", description="geojson | kml | csv")):
    """Download all detections as a GIS file (PS deliverable ii).
    GeoJSON -> QGIS, KML -> Google Earth, CSV -> any spreadsheet."""
    content, media_type, filename = export_detections(fmt)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---- optional extras: useful for debugging/demo, frontend ignores them ----

@router.post("/admin/ingest")
async def trigger_ingest():
    """Manual refresh button for the demo. Scheduler runs this automatically too."""
    from .ingestion.firms import run_ingest
    from .ml.classifier import run_ml_pipeline
    result = await run_ingest()
    if result.get("ok"):
        result.update(run_ml_pipeline())
    return result


@router.post("/admin/reclassify")
def reclassify_all():
    """Re-run ML classification over ALL rows (e.g. after swapping in a new model)."""
    from .ml.classifier import run_ml_pipeline
    return run_ml_pipeline()


class TrainRequest(BaseModel):
    dataset_path: str


@router.post("/admin/train")
def trigger_train(req: TrainRequest):
    """Hook for your ML teammate's training run (Week 3)."""
    try:
        from .ml.train import train_from_csv
        return train_from_csv(req.dataset_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"dataset not found: {req.dataset_path}")
    except ImportError:
        raise HTTPException(status_code=501, detail="training module not implemented yet")
