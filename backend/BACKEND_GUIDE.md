# SIH26162 — Backend Work Guide

**Project:** AI-Based Detection & Classification of Industrial Fires & Persistent Thermal Sources (NASA FIRMS + OSM)
**Stack:** FastAPI + SQLite (Python 3.13) — serves the CRA frontend on :3000, feeds off the ML teammate's model

---

## 0. Team split (who owns what)

| You (Backend) | ML teammate |
|---|---|
| FIRMS ingestion pipeline, SQLite DB, REST API, scheduler, CORS | Feature engineering + training the classifier |
| Rule-based fallback classifier (works from day 1) | Producing `ml/model.pkl` (joblib sklearn pipeline) |
| Labeled-sample collection to hand them for training | Model evaluation / accuracy improvements |
| Deploy + demo infra | Model retraining loop |

**The single contract between you:** `app/ml/classifier.py`. They save a joblib pipeline at `ml/model.pkl`;
you load it. Feature order: `[brightness, frp, confidence, daynight(0/1), is_persistent(0/1), hours_seen]`.
Labels: `industrial_fire | gas_flare | vegetation_fire | agricultural_burning` (mapped to frontend display names in `LABEL_MAP`).

---

## 1. What already exists (built & smoke-tested)

```
SIH-HackSphere/
├── fire-detection-app/        # CRA frontend (port 3000) — teammate's or yours to wire
└── backend/
    ├── requirements.txt       # fastapi, uvicorn, httpx, apscheduler, scikit-learn, joblib
    ├── .env.example           # copy to .env, add FIRMS_MAP_KEY
    ├── seed_demo.py           # 14 realistic Indian demo detections
    ├── smoke_test.py          # in-process API verification
    └── app/
        ├── main.py            # FastAPI app: CORS for :3000, APScheduler ingest every 10 min
        ├── config.py          # env-driven settings
        ├── db.py              # SQLite schema (detections table, dedup index)
        ├── schemas.py         # pydantic models = the frontend contract
        ├── routes.py          # /api/detections, /api/stats, /api/admin/ingest, /api/admin/train
        ├── services.py        # DB queries (windowed, classified counts)
        ├── ingestion/firms.py # NASA FIRMS CSV API → SQLite (INSERT OR IGNORE dedup)
        └── ml/classifier.py   # model adapter + rule-based fallback
```

Verified working: `python smoke_test.py` → stats `{fire:4, industrial:6, persistent:4, highConfidence:10}`,
detections match the exact field names the frontend expects.

---

## 2. Run it

```bash
cd backend
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # paste your free FIRMS_MAP_KEY (see §5)

python seed_demo.py           # optional: demo data so the dashboard isn't empty
uvicorn app.main:app --reload --port 5000
```

- Swagger UI: http://localhost:5000/docs
- Frontend talks to `http://localhost:5000` (already hardcoded in `src/api/detections.js`).
- Frontend still renders `mockData.js` — frontend teammate must swap in `fetchDetections()` /
  `fetchStats()` from `src/api/detections.js` (the functions are already written).

## 3. How the data flows

1. **Ingest** (scheduler every 10 min, or `POST /api/admin/ingest`): FIRMS CSV for the India
   bbox, last 7 days → rows inserted with `classification='Unclassified'`. Dedup on
   (satellite, rounded lat/lng, acquisition time).
2. **Classify**: `classify_unclassified()` scores new rows — model if `USE_ML_MODEL=true` and
   `ml/model.pkl` exists, else threshold rules (brightness/FRP/persistence).
3. **Serve**: frontend polls `GET /api/detections` + `GET /api/stats`. Filter pills match
   `"Vegetation Fire" | "Industrial Heat Source" | "Persistent Thermal Anomaly" | "Unclassified"`.

## 4. Your backend roadmap (2 weeks to 20 Sep)

**Week 1 — make it real**
- [ ] Get FIRMS MAP_KEY, set `.env`, run one manual ingest (`POST /api/admin/ingest`), inspect `/docs`.
- [ ] `hours_seen` / `is_persistent`: currently naive — write an enrichment step that counts
      detections per rounded (lat,lng) across days and flags persistent sources (>5 passes).
- [ ] Add OSM enrichment: query Overpass API for industrial sites (refineries, power plants,
      steel, mining) within ~5 km of each hotspot → store `nearest_industry_km`, `industry_type`.
      This single feature is what makes classification credible — coordinate with ML teammate.
- [ ] TrendChart: frontend hardcodes weekly data; add `GET /api/trend?days=7` returning
      `[{day, fires, industrial}]` and hand it to the frontend teammate.

**Week 2 — polish for the jury**
- [ ] Export deliverable: `GET /api/export?format=geojson` (PS asks for GIS overlays; GeoJSON
      drops straight into QGIS/Google My Maps).
- [ ] Hand ML teammate labeled samples: `SELECT ... WHERE classification != 'Unclassified'`
      from demo regions (Jamnagar refinery, Jharia coalfield = industrial; Punjab belt Oct-Nov =
      crop burning; Similipal = forest).
- [ ] Wire `USE_ML_MODEL=true` once `ml/model.pkl` lands; keep rules as fallback.
- [ ] Demo script: start backend → trigger ingest live → show dashboard update → toggle filters.

## 5. Free data sources (no keys except FIRMS)

| Source | What | Access |
|---|---|---|
| NASA FIRMS | hotspots: lat/lng, brightness, FRP, confidence, satellite | free MAP_KEY: firms.modaps.eosdis.nasa.gov/api/map_key/ |
| Overpass (OSM) | industrial facilities near a point | POST overpass-api.de — no key |
| ESA WorldCover | land-cover class per pixel (built-up/forest/cropland) | Planetary Computer / AWS open data |

## 6. Demo regions (already visible in FIRMS)

- **Industrial/persistent:** Jamnagar refinery (Gujarat), Jharia coalfields (Jharkhand), Vizag steel
- **Crop burning:** Punjab/Haryana, mid-Oct to Nov
- **Forest fires:** Similipal (Odisha), Uttarakhand summer

Filter FIRMS API by these bboxes during the demo for fast, focused results.
