# 🚀 Deploying AgniNetra to Render

One Blueprint file (`render.yaml`) deploys **both** services:

| Service | Type | URL (after deploy) |
|---|---|---|
| `agninetra-api` | Python (FastAPI + APScheduler + ML + SQLite) | `https://agninetra-api.onrender.com` |
| `agninetra-web` | Static site (React build) | `https://agninetra-web.onrender.com` |

---

## Step 0 — Prerequisites

- The repo pushed to GitHub (branch `feature-cs56` or merged to main)
- A free [render.com](https://render.com) account (sign in with GitHub)
- Your **NASA FIRMS MAP_KEY** (the same one in `backend/.env` locally)

## Step 1 — Push this branch

```bash
cd SIH-HackSphere
git push origin feature-cs56
```

(Adds `render.yaml`, `.env.production`, and this guide.)

## Step 2 — One-click deploy

1. Render Dashboard → **New +** → **Blueprint**
2. Pick the `swastik20-7/SIH-HackSphere` repo → branch `feature-cs56` → **Apply**
3. Render reads `render.yaml` and creates both services automatically.

## Step 3 — Add the secret

`agninetra-api` → **Environment** → add:

| Key | Value |
|---|---|
| `FIRMS_MAP_KEY` | your NASA FIRMS key |
| `GOOGLE_MAPS_API_KEY` | *(optional — leave blank to use free OSM geocoding)* |

Save → the service redeploys automatically.

## Step 4 — Verify

- `https://agninetra-api.onrender.com/` → `{"status": "ok", ...}`
- First ingest populates the DB within ~10 minutes of startup (scheduler runs immediately + every 10 min)
- `https://agninetra-web.onrender.com/` → dashboard live, showing detections

If the web service was created with a different name, the URL differs — update
`CORS_ORIGINS` (backend) and `REACT_APP_API_URL` (frontend env var) to match, then redeploy.

## Step 5 — Alerting on the cloud (optional)

Same as local: open the deployed dashboard → **Settings** → connect the Gmail
sender (16-char app password) + authority emails → **Send test alert**.
Nothing in the code changes — config lives in the backend DB.

---

## ⚠️ Free-tier caveats (know before the demo)

| Caveat | Impact | Workaround |
|---|---|---|
| **Sleep after 15 min idle** | First request takes ~50 s to wake | Open the dashboard 2 min before judging |
| **Ephemeral disk** | SQLite DB resets on every redeploy | Acceptable for demo; alerts re-accumulate within one ingest cycle |
| **512 MB RAM** | ML pipeline fits comfortably; just don't add heavy jobs | — |
| **Build minutes** | Unlimited on free tier for these two services | — |

**Pro demo tip:** hit `https://agninetra-api.onrender.com/` once (or open the
dashboard) a few minutes before presenting so both services are warm.
