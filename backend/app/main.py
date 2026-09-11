"""FastAPI entrypoint.

Run from backend/:
    uvicorn app.main:app --reload --port 5000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("fire-backend")


async def _scheduled_ingest():
    from .ingestion.firms import run_ingest
    from .ml.classifier import run_ml_pipeline
    from .alerting import check_and_alert
    result = await run_ingest()
    ml = run_ml_pipeline()
    alerts = await check_and_alert()
    log.info("Scheduled ingest: %s | ML: %s | alerts: %s", result, ml, alerts)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.firms_configured:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            _scheduled_ingest, "interval",
            minutes=settings.ingest_interval_minutes, id="firms_ingest",
        )
        scheduler.start()
        log.info("Scheduler started: FIRMS ingest every %d min", settings.ingest_interval_minutes)
    else:
        log.warning("FIRMS_MAP_KEY missing - running without auto-ingest (set it in .env)")
    yield
    if settings.firms_configured:
        scheduler.shutdown(wait=False)


app = FastAPI(title="SIH26162 Fire Detection Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    from .ml.classifier import _load_payload
    return {
        "service": "SIH26162 fire-detection backend",
        "endpoints": ["/api/detections", "/api/stats", "/api/alerts",
                      "/api/model/validation", "/api/export", "/docs"],
        "firms_configured": settings.firms_configured,
        "ml_model_active": _load_payload() is not None,
    }
