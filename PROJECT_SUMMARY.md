# AgniNetra — Project Summary

**Smart India Hackathon 2026 · Problem Statement SIH26162 (NTRO · Disaster Management)**
*AI-Based Detection & Classification of Industrial Fires and Persistent Thermal Sources*

---

## 1. The problem, in plain words

Every day, NASA's satellites record thousands of "hotspots" over India — pixels on the
ground that are abnormally hot. The satellite knows **that** something is hot, but not
**what** is hot. A forest blaze, a farmer burning crop stubble, a gas flare on a
refinery, a steel plant, a coal seam smouldering for months — they can all look
identical from space: a bright dot in the infrared.

That creates a real national problem:

- **Fire-fighters** get thousands of dots and no idea which ones matter.
- **Pollution regulators** can't separate illegal industrial burning from legal farm
  burning, so enforcement doesn't happen.
- **A single undetected industrial fire** can cost lives and crores of rupees.

NASA publishes this raw hotspot data for free — but as a raw feed. It is up to
someone to turn *dots* into *decisions*. That someone is us.

---

## 2. The one-line core idea

> **AgniNetra takes NASA's anonymous hotspots and answers the three questions NASA
> doesn't: WHAT is burning, WHERE exactly it is (in words), and WHO needs to know —
> automatically, every 10 minutes, for free.**

---

## 3. How it works — the journey of one hotspot

Follow a single hot pixel through the system:

```
STEP 1 — SENSE
  Two NASA satellites (VIIRS instruments, 375 m resolution) cross India
  several times a day, measuring ground temperature via infrared.
                    │
STEP 2 — COLLECT    ▼
  Every 10 minutes, our server asks NASA FIRMS: "all hotspots in the
  India region from the last 7 days" and stores the new ones.
                    │
STEP 3 — ENRICH     ▼
  A bare coordinate becomes a smart record. For each hotspot we compute:
    • What industrial facility is nearest, and how far
      (searching 400,000+ real factories/plants/mines from OpenStreetMap)
    • How persistent it is (first-seen date, how many days it's been hot)
    • What kind of land it sits on (forest / farmland / industrial zone)
    • Its human-readable place name ("Kaniha, Angul, Odisha")
                    │
STEP 4 — CLASSIFY   ▼
  An XGBoost machine-learning model takes these features and labels the
  hotspot: Vegetation Fire, Industrial Heat Source, Persistent Thermal
  Anomaly, Crop Burning, Gas Flare, or Mining — with a confidence %.
                    │
STEP 5 — DECIDE     ▼
  A rule engine picks out the dangerous ones: industrial or persistent,
  high confidence, within 5 km of a named facility, not already reported
  in the last 6 hours.
                    │
STEP 6 — ACT        ▼
  For each dangerous hotspot the system:
    • resolves its exact street address,
    • pushes an alert to phones (ntfy), and
    • emails a formal incident notice — location, confidence, satellite
      source, map link, recommended response — ready to forward to
      district authorities, the State Disaster Management Authority, or
      the facility's safety officer.
                    │
STEP 7 — SEE        ▼
  A live dashboard: satellite map with colour-coded fires, per-type
  trends, priority alerts, and one-click GIS exports (KML/GeoJSON/CSV)
  that open directly in Google Earth or QGIS.
```

Everything above is running code in this repository — no step is a mock-up.

---

## 4. What we add on top of NASA's own estimates

NASA FIRMS is the *data source*, not the competition — but their raw product has
well-known limitations, and this is exactly where AgniNetra lives:

| # | NASA raw FIRMS gives you | AgniNetra gives you |
|---|---|---|
| 1 | A dot with a temperature | **A classification**: "this is an industrial fire, 86% confident" — using persistence, landcover, facility proximity, day/night behaviour (9 engineered features) |
| 2 | A latitude/longitude pair | **A street address and place name** — "Kaniha, Angul, Odisha, 759117" — plus a Google Maps link |
| 3 | A constant stream of dots (thousands/day) | **A filtered priority queue** — only high-confidence industrial threats near real facilities reach the alert stage |
| 4 | A website you must check | **Push delivery** — alerts arrive on phones and in authority inboxes; nobody has to watch a screen |
| 5 | Global CSV files, same for every user | **India-focused operational product** — state names, facility context, GIS exports authorities already use, live dashboard |
| 6 | Nothing about history of a spot | **Persistence tracking** — "burning for 6 days straight" is exactly the signature of an illegal industrial source, and it's a first-class feature in our model |

Two things deserve honest emphasis, because judges and engineers will ask:

- **We are not "more accurate than NASA" at sensing.** Nobody beats the satellite at
  measuring temperature. Our claim is narrower and defensible: we are *more useful
  than the raw NASA estimate* at telling you **what** is burning, **where** in words,
  and **whether it matters** — because we fuse NASA's thermal data with map context
  (facilities, landcover, state boundaries) that NASA's raw product doesn't use.
- **Fusion is the moat.** Any one feature alone (say, brightness) is a weak classifier.
  Combining thermal physics + geography + time is what takes accuracy to 95%+.

---

## 5. The accuracy claim, with receipts

The classification model was validated on **8,297 labelled detections** using a
stratified train/test split and the exact deployed configuration:

- **Accuracy: 95.4%** · weighted F1: 95.3%
- Per class: wildfire **98.3%** F1 · crop burning **98.8%** · industrial fire **90.8%**
- Weakest class (gas flare, few examples): 65.9% — reported honestly, not hidden
- Feature importance: **landcover 50%**, day/night 22%, distance-to-facility 15%

Full report, confusion matrix and feature-importance charts are in
`backend/reports/` and served live at `GET /api/model/validation` (rendered in the
dashboard's Settings tab).

*Known limitation (stated up front):* training labels were derived from
rule-based geographic signatures (near-facility + night-time + persistent →
industrial, etc.) rather than field-verified ground truth. The system is a
**triage and early-warning tool** — it tells authorities where to look first;
it does not replace on-ground verification.

---

## 6. What's actually built (nothing on this list is imaginary)

| Working component | Proof it's real |
|---|---|
| Live NASA FIRMS ingestion every 10 min | Dashboard shows live sync time; 4,242+ real detections collected in first days |
| ML classification pipeline | `model.pkl` loaded at startup; every detection labelled with confidence |
| Street-address resolution | Every alert carries a real address (Google Geocoding with free OSM fallback, cached) |
| Alert engine | 489 alerts generated from real detections (e.g. *"Waidhan, Singrauli, MP — Industrial Heat Source, 86%, 0.5 km from facility"* — Singrauli is India's coal/thermal capital) |
| Phone push (ntfy) | Verified delivering end-to-end |
| Authority email | Formal HTML incident notices, ready-to-forward, via standard SMTP |
| GIS exports | KML verified opening in Google Earth with named, classified pins |
| Live dashboard | React + Google satellite view, real-time, type-coloured markers |

**Total data cost: ₹0.** FIRMS is free, OSM is free, ntfy is free, the stack is
open-source. This can run in a district control room on a borrowed laptop.

---

## 7. Who uses this and how

| User | What they do with it |
|---|---|
| **District Magistrate / SDMA** | Receives formal alert emails with exact locations → dispatches verification the same day |
| **Pollution Control Boards** | Filters "industrial heat source" vs "crop burning" → evidence-based enforcement of open-burning bans |
| **Forest departments** | Watches vegetation-fire trends by state and type on the live map |
| **Plant safety officers** | Learn of fires *at their own facilities* from satellites before their own sensors raise it |
| **Geospatial agencies (NTRO/ISRO)** | Consume the same alerts via the API or GIS exports into their existing GIS workflows |

---

## 8. The stack, in one paragraph

Python 3.13 + FastAPI + SQLite for the backend (`backend/`), a scheduler that pulls
NASA FIRMS every 10 minutes, an XGBoost model trained by the ML sub-team on
rule-derived labels with OSM/landcover features, a React dashboard
(`fire-detection-app/`) on Google satellite imagery, ntfy + SMTP for delivery,
and Shapely-powered geospatial enrichment over OpenStreetMap data. Runs on one
machine; every file's role is documented in `backend/BACKEND_GUIDE.md`.

---

## 9. The 30-second version (for the elevator, or the chief guest)

> NASA's satellites see every fire in India but can't tell a forest blaze from a
> factory fire. AgniNetra fuses that satellite feed with maps of industrial
> facilities, land type and time patterns to classify every hotspot — 95%+ accuracy —
> convert it to a street address, and push a formal alert to the authorities'
> phones and inboxes within minutes, free of cost. It turns a fire *data feed*
> into a fire *response system*.

---

*Repository: `swastik20-7/SIH-HackSphere` (branch `feature-cs56`) · Backend guide:
`backend/BACKEND_GUIDE.md` · Presentation kit: `PPT_SLIDES.md`,
`SIH26162_AgniNetra_Idea_Presentation.pptx`*
