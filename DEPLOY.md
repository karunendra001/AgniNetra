# 🚀 AgniNetra — Live Cloud Deployment

**The app is deployed and running right now:**

| Layer | Platform | URL |
|---|---|---|
| Dashboard (React) | **Vercel** | **https://agninetra.vercel.app** |
| API (FastAPI + ML + scheduler) | **Render** | **https://agninetra-api-e4aw.onrender.com** |
| API docs | Render | https://agninetra-api-e4aw.onrender.com/docs |

Render service: `agninetra-api` (`srv-dalugou7bikc73akrg40`, free plan, Singapore).
Vercel project: `agninetra` (`prj_1aRo8AG0InOlrlFwRngi6YnYrSX6`), branch `main`.

---

## 1. How it is wired

```
Browser ──▶ https://agninetra.vercel.app        (static React build)
                │  axios baseURL = https://agninetra-api-e4aw.onrender.com
                ▼
            https://agninetra-api-e4aw.onrender.com   (FastAPI)
                ├── APScheduler: FIRMS ingest every 10 min + once at startup
                ├── ML classifier (ml/model.pkl) → detections table (SQLite)
                ├── Risk engine → alerts (ntfy push + authority email)
                └── /api/export → GeoJSON / KML / CSV
```

Cross-origin access is allowed by `CORS_ORIGINS` **plus** a regex that accepts
every `*.vercel.app` origin (production and preview deployments), so Vercel
deploys never need a backend config change.

## 2. Updating the deployment

**Backend** — Render auto-deploys on every push to `main`:

```bash
git push origin main
```

**Frontend** — the Vercel project is deployed via CLI (no Git link yet):

```bash
npm i -g vercel
cd fire-detection-app
vercel --prod --yes          # after `vercel login`
```

Set the API URL once per environment (already set for Production):

```bash
echo "https://agninetra-api-e4aw.onrender.com" | vercel env add REACT_APP_API_URL production
```

> To get auto-deploys from Git instead, connect the repo in the Vercel dashboard
> (Project → Settings → Git) — one click, needs GitHub authorization.

## 2b. Two GitHub remotes (why, and how to push)

The project repo `swastik20-7/SIH-HackSphere` belongs to a teammate. A private
repo can only be handed to Vercel/Render by its **owner** (installing their Git
app needs admin rights), so this clone also carries a fork on the maintainer's
own account: **`Manyaaa-ops/SIH-HackSphere`**, and the Vercel project is linked
to that fork.

`origin` is configured with **two push URLs**, so a single push updates both the
team repo and the fork (which is what triggers Vercel):

```bash
git push origin feature-cs56:main    # → swastik20-7/... AND Manyaaa-ops/...
```

Fetch still comes from the team repo, so `git pull` keeps working as before.
If the fork ever drifts: `git push mine main` (the `mine` remote is the fork).

## 3. Secrets and config

Render env vars (set on the service, never in the repo):

| Key | Notes |
|---|---|
| `FIRMS_MAP_KEY` | NASA FIRMS key. **Required** for auto-ingest |
| `GOOGLE_MAPS_API_KEY` | Optional; free OSM geocoding is the fallback |
| `FIRMS_DAY_RANGE` | **Must be ≤ 5** — this key returns `400 Bad Request` for 7+ |
| `CORS_ORIGINS`, `DB_PATH`, `MODEL_PATH`, `USE_ML_MODEL`, … | Sane defaults already applied |

Alert channels (ntfy topic, SMTP sender + app password, authority emails) are
configured **in the deployed dashboard → Settings**, stored in the backend DB.

## 3b. Commit identity (this blocks Vercel deployments)

Vercel refuses to build commits whose author email is not linked to a Vercel
account — the deployment shows up as **BLOCKED** with no build logs. On this
machine git had no identity configured, so commits were authored as
`manyadixit@<hostname>.local` and every Git deployment was blocked.

Set the email used by the Vercel account:

```bash
git config user.name  "Manya Dixit"
git config user.email "itsmadii0209@gmail.com"   # the Vercel account email
```

Add `--global` to apply it to every repo on the machine. After changing it,
verify with `git log -1 --format='%an <%ae>'` and push again — the deploy
should build instead of showing BLOCKED.

## 4. Gotchas worth knowing

| Issue | Why | What to do |
|---|---|---|
| Stats show `0` after a restart | SQLite is ephemeral on free tier and the DB starts empty | Wait ~2 min — the app now ingests **once on startup**, before the first 10-min tick |
| `400 Bad Request` from NASA FIRMS | `FIRMS_DAY_RANGE` > 5 is rejected for this map key | Keep it at `5` |
| First request after idle is slow (~50 s) | Render free instances sleep after 15 min | Open the dashboard a couple of minutes before presenting |
| Vercel rejects a new deploy as `BLOCKED` | Vercel anti-abuse hold on the (new) account | Verify the account in the Vercel dashboard, then redeploy. The **live deployment keeps serving** meanwhile |
| Data resets on redeploy | Free-tier ephemeral disk | The startup ingest refills it automatically |

## 5. Verify the deployment

```bash
curl https://agninetra-api-e4aw.onrender.com/            # service banner + flags
curl https://agninetra-api-e4aw.onrender.com/api/stats   # live detection counts
curl https://agninetra.vercel.app/                       # dashboard (200)
```
