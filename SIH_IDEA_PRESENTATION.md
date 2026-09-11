# SIH26162 — Idea Presentation (official SIH 4-slide format)

Copy-paste text for the standard SIH idea-presentation template.
The editable deck `SIH26162_AgniNetra_Idea_Presentation.pptx` was generated from
`make_sih_ppt.py` — edit the FILL placeholders there (or directly in PowerPoint) and re-run.

---

## SLIDE 1 — Basic Details of the Team and Problem Statement

- **Idea Title:** AgniNetra — AI-Powered Detection & Classification of Industrial Fires and Persistent Thermal Sources
- **Ministry/Organization Name:** National Technical Research Organisation (NTRO)
- **PS Code:** SIH26162
- **Problem Statement Title:** AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources Using NASA FIRMS, OSM & Satellite Data
- **Theme Name:** Disaster Management (Software Edition)
- **Team Name:** AgniNetra
- **Team Leader Name:** [FILL: Leader Name]
- **Institute Code (AISHE):** [FILL: AISHE code]
- **Institute Name:** [FILL: Institute Name]

---

## SLIDE 2 — Problem | Idea/Solution | Technology Stack | Flow Chart

### Problem :
- **Anonymous hotspots:** satellites report every fire as a bare coordinate — a wildfire, a refinery blaze and a gas flare look identical.
- **Slow manual classification:** hours-to-days delay lets industrial fires escalate into catastrophes.
- **Invisible chronic polluters:** no persistence tracking — gas flares burning for weeks go unnoticed.
- **Data is not GIS-ready:** raw satellite feeds give agencies nothing they can drop into QGIS / Google Earth workflows.
- **No automatic alerting:** nobody is woken when an industrial fire ignites near a facility.

### Idea/Solution :
- **Real-Time Ingestion:** NASA FIRMS (VIIRS S-NPP, NOAA-20, MODIS) hotspots pulled every 10 minutes across India, de-duplicated into SQLite — 100% real satellite data, zero synthetic rows.
- **AI Classification (XGBoost):** each hotspot auto-classified into 6 source types (wildfire | crop burning | industrial fire | gas flare | mining | other) using 9 engineered features — brightness, FRP, day/night, persistence, distance to nearest OSM facility, land-cover. **95.4% test accuracy.**
- **Geospatial Intelligence:** every detection auto-named with its Indian state + nearest named facility via OSM data & official state boundaries — *"Odisha — 0.8 km from power plant."*
- **Real Alerting Engine:** industrial/persistent source + ≥85% confidence + ≤5 km from a named facility → instant Telegram/email alert with Google Maps link (6-h dedup). **96 alerts already fired on live data.**
- **GIS Dashboard + Export:** React dashboard on Google satellite imagery, 10-min live refresh, filters & trends; one-click GeoJSON / KML / CSV export for QGIS & Google Earth.
- **Model Transparency:** published validation report — confusion matrix, feature importance — served via API and rendered inside the dashboard.

### Technology Stack :
Python 3.13 | FastAPI | SQLite | XGBoost + scikit-learn | httpx | APScheduler | React (CRA) + Leaflet (Google Satellite layers) | NASA FIRMS API | OpenStreetMap Overpass | ESA WorldCover | Telegram Bot API | GeoJSON / KML / CSV

### Flow Chart :
NASA FIRMS API → Ingestion + Dedup (every 10 min) → SQLite fires.db (persistence counters) → Enrichment (facility distance | landcover | state) → XGBoost AI (6 source classes) → FastAPI REST (10+ endpoints) → { GIS Dashboard · Telegram/Email Alerts · GeoJSON/KML/CSV Export }

*(the generated .pptx draws this as an editable colored shape diagram on slide 2)*

---

## SLIDE 3 — Idea/Approach Details

### Use Cases :
- **Industrial Safety & Disaster Response:** district authorities get a named alert ("Chhattisgarh — 0.6 km from refinery works") within minutes of ignition — not days.
- **Environmental Regulation:** pollution boards use persistence analytics (detection count + active days) to catch chronic flare operators, not one-off events.
- **Defense / Geospatial Intelligence:** GIS-ready KML/GeoJSON feeds plug straight into NTRO & agency QGIS workflows, including sensitive border regions.
- **Agricultural Smoke Management:** the crop-burning class + seasonal trends let state agencies target stubble-burning crackdowns precisely.
- **Research & Insurance Forensics:** 18-column CSV export reproduces the full feature vector per hotspot for auditable analysis.

### Dependencies / Show Stoppers :
- **NASA FIRMS cadence & availability:** mitigated by de-duplication, local DB persistence, and a live "last sync" banner on the dashboard.
- **Land-cover coverage gap:** current lookup covers ~43% of live points; direct ESA WorldCover sampling is the scoped fix (next sprint).
- **Label provenance:** labels bootstrapped from a rule-based pipeline; a human-labeled subset + spatial cross-validation are planned hardening steps.
- **Class imbalance:** gas-flare F1 (66%) limited by a 45-row test class; more flare training data is the known fix.
- **Live-demo connectivity:** offline fallback — pre-exported KML in Google Earth + cached SQLite snapshot.

### Channels :
NTRO & defense geospatial cells | State Pollution Control Boards | SDMA / NDMA disaster authorities | Forest departments | Refinery & plant HSE teams

### Revenue Streams :
SaaS subscription for industrial HSE compliance monitoring | API licensing to insurers / logistics / ESG analytics | Custom on-prem deployments for government agencies

---

## SLIDE 4 — Team Member Details

- **Team Leader Name:** [FILL] — Branch: B.Tech · Stream: [FILL] · Year: [FILL]
- **Team Member 1 Name:** [FILL] — Branch: B.Tech · Stream: [FILL] · Year: [FILL]
- **Team Member 2 Name:** [FILL] — Branch: B.Tech · Stream: [FILL] · Year: [FILL]
- **Team Member 3 Name:** [FILL] — Branch: B.Tech · Stream: [FILL] · Year: [FILL]
- **Team Member 4 Name:** [FILL] — Branch: B.Tech · Stream: [FILL] · Year: [FILL]
- **Team Member 5 Name:** [FILL] — Branch: B.Tech · Stream: [FILL] · Year: [FILL]
- **Team Mentor 1 Name:** [FILL] — Category: [Academic] · Expertise: [FILL, e.g. AI/ML, GIS] · Domain Experience (in years): [FILL]

---

## How to finish the deck (5 minutes)

1. Open `SIH26162_AgniNetra_Idea_Presentation.pptx` (double-click — it's a normal PowerPoint file, 16:9, 4 slides).
2. Replace every `FILL:` placeholder with real team details (slides 1 & 4). Or edit the `TEAM` / `MEMBERS` / `MENTORS` blocks at the top of `make_sih_ppt.py` and re-run `backend/.venv/bin/python make_sih_ppt.py`.
3. Optional inserts: `backend/reports/confusion_matrix.png` + `feature_importance.png` next to the solution bullets, and a dashboard screenshot for slide 3.
4. The flow chart on slide 2 is made of real PowerPoint shapes — click any box to edit its text; nothing is a baked image.
