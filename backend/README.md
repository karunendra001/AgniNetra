# SIH26162 Backend — Fire Detection API

Backend for the AI fire-detection dashboard (SIH problem statement 26162).
Frontend: `../fire-detection-app` (Create React App, runs on :3000).

## Quickstart

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then paste your FIRMS_MAP_KEY into .env
uvicorn app.main:app --reload --port 5000
```

- Swagger docs: http://localhost:5000/docs
- Health check:  http://localhost:5000/

## Endpoints (frontend contract)

| Endpoint | Returns |
|---|---|
| `GET /api/detections` | `[{id, location, lat, lng, classification, confidence, brightness, frp, satellite, time}]` |
| `GET /api/stats` | `{fire, industrial, persistent, highConfidence}` |
| `POST /api/admin/ingest` | Manual FIRMS refresh (scheduler also does this) |
| `POST /api/admin/train` | Train from a labeled CSV (ML teammate) |

Classification values (must match frontend filter pills):
`"Vegetation Fire" | "Industrial Heat Source" | "Persistent Thermal Anomaly" | "Unclassified"`

## Architecture

```
app/
├── main.py          # FastAPI app, CORS (:3000), APScheduler ingest loop
├── config.py        # reads .env
├── db.py            # SQLite schema + connection helper
├── schemas.py       # pydantic response models = frontend contract
├── routes.py        # the API
├── services.py      # DB queries for the API
├── ingestion/
│   └── firms.py     # NASA FIRMS CSV API -> SQLite (dedup via INSERT OR IGNORE)
└── ml/
    ├── classifier.py # loads ml/model.pkl (joblib) OR rule-based fallback
    └── train.py      # <-- ML teammate implements this
```

## Data flow

1. Every 10 min (configurable): pull FIRMS CSV for India bbox, upsert into SQLite.
2. New rows start as `Unclassified` and get classified (model if present, else rules).
3. Frontend polls `/api/detections` + `/api/stats` and renders map/table/charts.

## ML teammate contract (`app/ml/classifier.py`)

Train and save a sklearn pipeline as `ml/model.pkl` (joblib):

```python
joblib.dump(pipeline, "ml/model.pkl")
pipeline.predict(X)   # -> 'industrial_fire'|'gas_flare'|'vegetation_fire'|'agricultural_burning'
pipeline.predict_proba(X)  # optional, for confidence
```

Feature order: `[brightness, frp, confidence, daynight(0/1), is_persistent(0/1), hours_seen]`.

Set `USE_ML_MODEL=true` in `.env` when the model file is ready — nothing else changes.

## FIRMS API

Get a free MAP_KEY: https://firms.modaps.eosdis.nasa.gov/api/map_key/

```
https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{west},{south},{east},{north}/{days}
```

Sources: `VIIRS_SNPP_NRT`, `VIIRS_NOAA20_NRT`, `MODIS_NRT`.
