# AgniNetra — SIH26162 Presentation Kit
**Problem Statement:** AI-Based Detection & Classification of Industrial Fires & Persistent Thermal Sources
**Everything below uses real numbers from the running system — refresh the "LIVE NUMBERS" box on demo morning.**

---

## SLIDE 1 — Title

**AgniNetra** 🔭
*AI-Powered Detection & Classification of Industrial Fires and Persistent Thermal Sources*

- Real-time satellite intelligence for industrial safety & environmental monitoring
- Team **[TEAM NAME]** · Smart India Hackathon 2026 · PS **26162**
- Live product, not a prototype — NASA FIRMS → AI → GIS dashboard → Telegram alerts

> **Speaker note (15s):** "AgniNetra watches every thermal anomaly India's satellites
> detect, decides *what kind* of heat source it is within seconds, and alerts the
> right people near a named facility. Everything you'll see is running live on
> real NASA data."

---

## SLIDE 2 — The Problem

| Reality today | Consequence |
|---|---|
| Industrial fires & gas flares detected only as "hotspots" | Agencies can't tell a wildfire from a refinery blaze |
| Manual classification, hours to days of delay | Late response = catastrophe scale-up |
| No persistence tracking | Chronic polluters (flares) stay invisible |
| Data locked in raw satellite feeds | No GIS-ready deliverable for defense/agency workflows |

**Our question:** *What if every satellite hotspot could classify itself, name its
location, and raise its own alarm — in real time?*

---

## SLIDE 3 — Our Solution (one breath)

**AgniNetra = sense → understand → alert.**

1. **SENSE** — ingest NASA FIRMS hotspots (VIIRS S-NPP + NOAA-20, MODIS) every 10 minutes across India
2. **UNDERSTAND** — XGBoost AI classifies each hotspot into 6 source types using 9 features (thermal, persistence, OSM infrastructure proximity, land-cover)
3. **ALERT** — high-confidence industrial/persistent sources near named facilities fire Telegram/email alerts automatically
4. **DELIVER** — GIS dashboard + one-click GeoJSON/KML/CSV export for QGIS & Google Earth

---

## SLIDE 4 — System Architecture

*(recreate in PowerPoint with 5 horizontal boxes + arrows; the ASCII below is the blueprint)*

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES (free)                         │
│   NASA FIRMS (thermal hotspots)   OpenStreetMap (facilities)        │
│   ESA WorldCover (land-cover)     India state boundaries            │
└──────────────┬──────────────────────────────────────────────────────┘
               │  every 10 min (auto)
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      INGESTION & STORAGE                            │
│  FIRMS API parser → de-duplication → SQLite (data/fires.db)         │
│  unique hotspot index · persistence counters · sync metadata        │
└──────────────┬──────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 AI CLASSIFICATION PIPELINE (XGBoost)                │
│  9 features per hotspot:                                            │
│   • brightness (2 channels) · FRP · confidence · day/night          │
│   • persistence: detection count + unique days active               │
│   • distance to nearest OSM facility (11 MB BallTree, haversine)    │
│   • land-cover class                                                │
│  → 6 classes: wildfire · crop burning · industrial fire ·           │
│    gas flare · mining activity · unclassified                       │
│  + geonaming: state + nearest facility name for every point         │
└──────────────┬──────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (port 8000)                      │
│  /api/detections  /api/stats  /api/trend  /api/alerts               │
│  /api/export?fmt=geojson|kml|csv      /api/model/validation         │
└──────┬──────────────────────────────────────┬───────────────────────┘
       │                                      │
       ▼                                      ▼
┌──────────────────────┐          ┌───────────────────────────────────┐
│  REACT GIS DASHBOARD │          │  ALERTING ENGINE                  │
│  live map + filters  │          │  industrial/persistent + ≥85% conf│
│  KPIs, trends, table │          │  + ≤5 km from named facility      │
│  Google satellite    │          │  → Telegram / email (6h cooldown) │
└──────────────────────┘          └───────────────────────────────────┘
```

> **Speaker note:** "Every box is running right now. No cloud cost, no paid API —
> entirely on open data."

---

## SLIDE 5 — LIVE NUMBERS box (update on demo morning)

```bash
curl -s http://localhost:8000/api/stats
curl -s "http://localhost:8000/api/alerts?limit=200" | jq length
```

| Metric | Value (as of build) |
|---|---|
| Detections in DB | **3,953** (100% real FIRMS, 0 synthetic) |
| Vegetation fires | 594 |
| Industrial heat sources | 975 |
| Persistent thermal anomalies (gas flares) | 20 |
| High-confidence detections (≥85%) | 2,679 |
| Alerts auto-fired | **96** |
| Satellite sync cadence | every 10 minutes |

---

## SLIDE 6 — Validation Metrics (the proof)

**Protocol:** stratified 80/20 train/test split · 8,297 labeled hotspots ·
XGBoost (200 trees, depth 6) · identical to deployed model ✅

| Metric | Score |
|---|---|
| **Accuracy** | **95.4%** |
| Precision (weighted) | 95.3% |
| Recall (weighted) | 95.4% |
| F1 (weighted) | 95.3% |

**Per-class performance:**

| Class | Precision | Recall | F1 | Test rows |
|---|---|---|---|---|
| crop burning | 99.0% | 98.6% | **98.8%** | 484 |
| wildfire | 98.2% | 98.3% | **98.3%** | 605 |
| industrial fire | 89.4% | 92.3% | **90.8%** | 220 |
| mining activity | 80.7% | 72.0% | 76.1% | 93 |
| unclassified other | 97.3% | 100.0% | 98.6% | 213 |
| gas flare | 67.4% | 64.4% | 65.9% | 45 |

*(insert `backend/reports/confusion_matrix.png` and `feature_importance.png` here)*

**What the model relies on:** land-cover 50.3% · day/night 21.9% · facility
distance 15.2% · persistence 5.0% — *the AI reasons like an analyst: WHERE is
the heat, WHEN does it burn, and WHAT is nearby.*

> **Judge-proof honesty (keep on slide):** labels derive from our rule-based
> pipeline; a human-labeled subset and spatial cross-validation are planned
> hardening steps. Gas-flare F1 is lower due to class size (45 test rows) —
> more flare training data is the known fix.

---

## SLIDE 7 — Alerting Engine (the "so-what")

**Rule:** industrial/persistent class + ≥85% AI confidence + ≤5 km from a
named facility + not repeated within 6 h per location.

**Real alerts fired by the system (actual log entries):**
- 🏭 *Odisha — 0.3 km from industrial landuse — 100% confidence*
- 🏭 *Chhattisgarh — 0.6 km from refinery works — 100% confidence*
- 🏭 *Karnataka — 0.5 km from power plant — 100% confidence*
- 🏭 *Tamil Nadu — 0.5 km from industrial landuse — 100% confidence*

**96 alerts auto-fired from live satellite data.** Every alert carries:
location name, facility type + distance, confidence, FRP (fire energy),
brightness, satellite, timestamp, Google Maps link.

---

## SLIDE 8 — GIS Deliverable (PS checkbox: "GIS-based solution")

One click from the dashboard:

| Format | Opens in | Contents |
|---|---|---|
| **GeoJSON** | QGIS, ArcGIS, geojson.io | full feature vector per point |
| **KML** | Google Earth | styled colored placemarks + time slider |
| **CSV** | Excel / any tool | 18 columns incl. persistence, facility distance, land-cover |

*"Our dashboard isn't a silo — one click hands an analyst everything they
need to reproduce our analysis in their own GIS stack."*

---

## SLIDE 9 — Tech Stack & Team Split

| Layer | Tech |
|---|---|
| Data ingestion | Python, httpx, NASA FIRMS API, 10-min scheduler (APScheduler) |
| Storage | SQLite (indexed hotspots, dedup, migrations) |
| AI | XGBoost + LabelEncoders, scikit-learn, haversine BallTree |
| Enrichment | OpenStreetMap facilities, ESA land-cover, state-boundary geonaming |
| API | FastAPI + Pydantic, 10+ endpoints, auto OpenAPI docs |
| Dashboard | React + Leaflet (Google satellite layers), live 60s refresh |
| Alerting | Telegram Bot API + SMTP, DB-backed dedup |

**Team contributions** *(edit with real names)*:
- **Backend & integration:** ingestion, DB, API, alerting, GIS export, geonaming
- **Machine learning:** data labeling, feature pipeline, model training (XGBoost)
- **Frontend:** dashboard design, live data wiring, map visualizations

---

## SLIDE 10 — Impact & Scale

- **Who uses it:** NTRO/defense geospatial cells, state pollution boards, disaster authorities, refinery HSE teams
- **Cost:** ₹0 — every data source is free; runs on a laptop or ₹500/mo VPS
- **India-wide coverage:** entire FIRMS India bounding box, every 10 minutes
- **Extensible:** new model → drop in `model.pkl` → one API call reclassifies the DB; new region → change one env var

---

## SLIDE 11 — Roadmap (already scoped)

- [x] Real-time ingestion + dedup ✅
- [x] XGBoost classification live in pipeline ✅
- [x] Facility + land-cover enrichment, place naming ✅
- [x] GIS export (GeoJSON/KML/CSV) ✅
- [x] Telegram/email alerting ✅
- [x] Model validation report ✅
- [ ] Full land-cover coverage via GEE (collapses ~2,100 "unclassified" into real classes) — *next sprint*
- [ ] Human-labeled validation subset + spatial cross-validation
- [ ] Historical 2-month backfill for seasonal analytics

---

# 🎬 LIVE DEMO SCRIPT (3 minutes)

**Pre-demo checklist (do 30 min before judges arrive):**
- [ ] Backend up: `curl localhost:8000/` shows `ml_model_active: true`
- [ ] Frontend up on :3000, LIVE banner green, "synced Xm ago" fresh
- [ ] Telegram open on the demo phone, test alert received
- [ ] Google Earth installed with a previously exported KML loaded (backup)
- [ ] Fullscreen browser, dark room → dashboard already looks dramatic

**T+0:00 — The map (30s)**
"3,953 real satellite detections, refreshed 10 minutes ago."
- Point at the orange industrial cluster: *"This belt is Odisha-Jharkhand —
  mining and steel country. The AI put those dots there from thermal physics
  + OSM infrastructure — nobody labeled them by hand."*
- Toggle the layer switcher once (satellite ↔ hybrid).

**T+0:30 — The AI (45s)**
- Click the **Industrial Heat Source** filter pill → map isolates orange dots.
- Click one marker → popup shows state, facility, distance, confidence, FRP.
  *"Every point self-classifies into 6 source types at 95.4% test accuracy —
  here's the confusion matrix"* (switch to Slide 6 for 5 seconds, return).

**T+1:15 — The alert (45s)**
- *"Watch: 975 industrial sources, 96 automatic alerts already fired."*
- On phone, show a real Telegram alert: facility name, distance, confidence.
- Press **🧪 Send test alert** in Settings → phone buzzes in the room.
  *"That's the pipeline that would wake a district magistrate at 2 a.m."*

**T+2:00 — GIS + honesty (30s)**
- Click **📥 KML** in the Detections header → file downloads.
- *"One click to Google Earth — colored placemarks, time slider, full
  feature vectors. That's the GIS deliverable in the problem statement."*

**T+2:30 — Close (30s)**
- *"Sense, understand, alert — all real data, zero rupees, running live.
  The roadmap slide shows exactly what the next sprint hardens."*

**Fallbacks (memorize):**
- Internet dies → KML already loaded in Google Earth + slide 5's static numbers
- NASA sync stalls → say "last sync X minutes ago — cadence is 10 minutes"
- Judge asks about accuracy → Slide 6 table + honesty line above

---

# ❓ JUDGE Q&A PREP

**"How accurate is the AI, really?"**
95.4% overall; wildfire and crop-burning above 98% F1. Gas flare is 66% due to
a small training class — we've scoped the fix (more flare data). All numbers
reproducible via `validate_model.py` in the repo.

**"Where do the labels come from?"**
Our rule-based pipeline (facility proximity + persistence + thermal thresholds)
bootstrapped the labels; the model now generalizes beyond those rules. Human
labeling is the planned hardening step — stated openly on the slide.

**"What about false positives?"**
The alert engine requires industrial/persistent class + ≥85% confidence +
facility proximity + 6h cooldown — precision over recall for alarms, while
the dashboard keeps everything visible.

**"Does it work outside India?"**
Yes — change one bounding-box env var. Facilities/land-cover data is global
(OSM, ESA).

**"Why XGBoost and not deep learning?"**
Tabular features + 8k rows: gradient boosting wins on accuracy, trains in
seconds, and explains itself via feature importance — which we show judges.
Right tool for the data size.

**"Infrastructure?"**
One laptop. SQLite + FastAPI + React. Deploy path: Render + Vercel free tiers.

---

## File checklist for the PPT author
- [ ] Insert `backend/reports/confusion_matrix.png` (slide 6)
- [ ] Insert `backend/reports/feature_importance.png` (slide 6)
- [ ] Screenshot dashboard map with orange cluster (slide 7 or 9)
- [ ] Screenshot Telegram alert on phone (slide 7)
- [ ] Fill team names (slide 9)
