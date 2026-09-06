"""NASA FIRMS ingestion -> SQLite.

FIRMS API (free MAP_KEY required):
  https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{BBOX}/{DAYS}

CSV columns:
latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,
instrument,confidence,version,bright_t31,frp,daynight
"""
import csv
import io
import logging
from datetime import datetime, timezone

import httpx

from ..config import settings
from ..db import get_connection, set_meta

log = logging.getLogger(__name__)

FIRMS_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


def _parse_acq_time(acq_date: str, acq_time: str) -> str:
    """FIRMS acq_time is UTC HHMM (e.g. '0418'). Normalize to ISO 8601."""
    hhmm = acq_time.strip().zfill(4)
    dt = datetime.strptime(f"{acq_date} {hhmm[:2]}{hhmm[2:]}", "%Y-%m-%d %H%M")
    return dt.replace(tzinfo=timezone.utc).isoformat()


# VIIRS reports single-letter satellites; MODIS spells them out
SATELLITE_NAMES = {"N": "VIIRS-SNPP", "S-NPP": "VIIRS-SNPP",
                   "O": "VIIRS-NOAA20", "N20": "VIIRS-NOAA20", "J1": "VIIRS-NOAA21",
                   "T": "MODIS-Terra", "A": "MODIS-Aqua"}

# VIIRS confidence is qualitative: l(ow) / n(ominal) / h(igh)
CONFIDENCE_LETTERS = {"l": 10.0, "n": 50.0, "h": 90.0}


async def fetch_firms(source: str) -> list[dict]:
    """Download one FIRMS product over the configured India bbox."""
    w, s, e, n = settings.firms_bbox
    url = f"{FIRMS_URL}/{settings.firms_map_key}/{source}/{w},{s},{e},{n}/{settings.firms_day_range}"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    rows = list(csv.DictReader(io.StringIO(resp.text)))
    parsed = []
    for r in rows:
        try:
            # MODIS calls it 'brightness', VIIRS calls it 'bright_ti4'
            bright_raw = (r.get("brightness") or r.get("bright_ti4") or "").strip()
            conf_raw = (r.get("confidence") or "").strip().lower()
            if conf_raw in CONFIDENCE_LETTERS:
                confidence = int(CONFIDENCE_LETTERS[conf_raw])
            elif conf_raw.replace(".", "", 1).isdigit():
                confidence = int(float(conf_raw))
            else:
                confidence = None
            sat = (r.get("satellite") or "").strip()
            ti5_raw = (r.get("bright_ti5") or "").strip()
            parsed.append({
                "latitude": float(r["latitude"]),
                "longitude": float(r["longitude"]),
                "brightness": float(bright_raw),
                "bright_ti5": float(ti5_raw) if ti5_raw else None,
                "frp": float(r["frp"] or 0),
                "confidence": confidence,
                "confidence_raw": conf_raw or None,
                "satellite": SATELLITE_NAMES.get(sat, sat or source),
                "acquired_at": _parse_acq_time(r["acq_date"], r["acq_time"]),
                "daynight": (r.get("daynight") or "d").strip(),
            })
        except (KeyError, ValueError) as exc:
            log.debug("Skipping malformed FIRMS row %s: %s", r, exc)
    return parsed


def persist(rows: list[dict]) -> int:
    """Insert rows, de-duplicating on (satellite, rounded coords, time)."""
    inserted = 0
    with get_connection() as conn:
        for r in rows:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO detections
                    (latitude, longitude, brightness, bright_ti5, frp, confidence,
                     confidence_raw, satellite, acquired_at, daynight)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (r["latitude"], r["longitude"], r["brightness"], r.get("bright_ti5"),
                 r["frp"], r["confidence"], r.get("confidence_raw"),
                 r["satellite"], r["acquired_at"], r["daynight"]),
            )
            inserted += cur.rowcount
    return inserted


async def run_ingest() -> dict:
    """Pull every configured FIRMS product and persist. Called by scheduler + API."""
    if not settings.firms_configured:
        log.warning("FIRMS_MAP_KEY not set - skipping ingest")
        return {"ok": False, "reason": "FIRMS_MAP_KEY not configured"}

    total_new, total_fetched = 0, 0
    any_ok = False
    for source in settings.firms_sources:
        try:
            rows = await fetch_firms(source)
            total_fetched += len(rows)
            total_new += persist(rows)
            any_ok = True
            log.info("%s: fetched %d, new %d", source, len(rows), total_new)
        except Exception:
            log.exception("Ingest failed for %s", source)

    if any_ok:
        set_meta("last_firms_sync", datetime.now(timezone.utc).isoformat())

    return {"ok": True, "fetched": total_fetched, "new_rows": total_new}
