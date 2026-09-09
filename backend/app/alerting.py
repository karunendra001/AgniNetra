"""Alerting — ntfy phone push + formal email to concerned authorities.

Trigger rule (per ingest):
  a detection classified as Industrial Heat Source or Persistent Thermal
  Anomaly, with ML confidence >= ALERT_MIN_CONFIDENCE, within
  ALERT_RADIUS_KM of a named OSM facility, that we have NOT alerted about
  in the last ALERT_COOLDOWN_HOURS.

Channels (link any of them live from Settings — no code or restart needed):
  - ntfy phone push: pick any topic name (NTFY_TOPIC); install the free ntfy
    app, subscribe to the same topic, alerts pop on your phone. No account.
  - Authority email: a formal, formatted incident notice (HTML) sent from your
    SMTP sender account to a list of concerned authorities — District
    Magistrate / SDMA / Pollution Control Board / factory safety officers.
    Configure sender + recipients in Settings or via SMTP_* / AUTHORITY_EMAILS.

Statuses stored per alert: sent | logged (no channel linked — record is still
complete and shown on the dashboard) | failed (a linked channel errored).
"""
import asyncio
import logging
import os
import re
import socket
import sqlite3
import time
from datetime import datetime, timezone

import httpx

from .config import settings
from .db import get_meta, set_meta

log = logging.getLogger(__name__)

# politeness state for the free OSM fallback + honesty flag for diagnostics
_NOMINATIM_BACKOFF = {"until": 0.0}
_google_denied = False

ALERT_CLASSES = ("Industrial Heat Source", "Persistent Thermal Anomaly")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# env fallbacks (DB meta overrides these so the dashboard can link channels live)
ENV_KEYS = {
    "ntfy_topic": "NTFY_TOPIC",
    "ntfy_server": "NTFY_SERVER",
    "smtp_host": "SMTP_HOST",
    "smtp_port": "SMTP_PORT",
    "smtp_user": "SMTP_USER",
    "smtp_pass": "SMTP_PASS",
    "authority_emails": "AUTHORITY_EMAILS",
    "google_maps_api_key": "GOOGLE_MAPS_API_KEY",
}
DEFAULTS = {"smtp_port": "587", "ntfy_server": "https://ntfy.sh"}


def cfg(key: str) -> str:
    """Channel config: DB meta first (set via Settings tab), then .env."""
    v = get_meta(key)
    if v:
        return v
    return os.getenv(ENV_KEYS.get(key, key.upper()), DEFAULTS.get(key, ""))


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _connect() -> sqlite3.Connection:
    """Autocommit connection — statements commit immediately, so concurrent
    writers (scheduler + API + backfill scripts) never deadlock each other."""
    return sqlite3.connect(settings.db_path, timeout=15, isolation_level=None)


# --------------------------------------------------------------- schema ----
def _ensure_alerts_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            detection_id INTEGER,
            latitude    REAL,
            longitude   REAL,
            classification TEXT,
            ml_confidence REAL,
            facility_name  TEXT,
            facility_distance_m REAL,
            message     TEXT,
            channels    TEXT,
            created_at  TEXT NOT NULL
        )
        """
    )
    # columns added after the first release; old DBs migrate in place
    existing = {r[1] for r in conn.execute("PRAGMA table_info(alerts)").fetchall()}
    for col, coltype in (("address", "TEXT"), ("status", "TEXT"),
                         ("delivery_detail", "TEXT")):
        if col not in existing:
            conn.execute(f"ALTER TABLE alerts ADD COLUMN {col} {coltype}")

    # 'pending' renamed to 'logged' — an unlinked channel is not a failure,
    # and not something waiting: the alert record is complete on its own.
    conn.execute("UPDATE alerts SET status='logged' WHERE status='pending'")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS geocode_cache (
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            address TEXT,
            source  TEXT,
            resolved_at TEXT,
            PRIMARY KEY (lat, lng)
        )
        """
    )


def _recently_alerted(conn: sqlite3.Connection, lat: float, lng: float) -> bool:
    """Same spot (~1 km) alerted within the cooldown window -> skip."""
    cooldown = float(os.getenv("ALERT_COOLDOWN_HOURS", "6"))
    row = conn.execute(
        """
        SELECT 1 FROM alerts
        WHERE created_at >= strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?)
          AND round(latitude, 2) = round(?, 2)
          AND round(longitude, 2) = round(?, 2)
        LIMIT 1
        """,
        (f"-{cooldown} hours", lat, lng),
    ).fetchone()
    return row is not None


def _row_get(row, key, default=None):
    """sqlite3.Row raises IndexError on unknown keys; treat that as None."""
    try:
        v = row[key]
        return default if v is None else v
    except (IndexError, KeyError):
        return default


# ---------------------------------------------------- address resolution ----
async def resolve_address(lat: float, lng: float) -> tuple[str, str]:
    """Human-readable address for a hotspot. Google Geocoding first (uses the
    Maps key), Nominatim (free OSM) fallback. Cached per ~100 m cell."""
    flat, flng = round(lat, 3), round(lng, 3)
    try:
        conn = _connect()
        conn.execute(
            """CREATE TABLE IF NOT EXISTS geocode_cache (
                lat REAL NOT NULL, lng REAL NOT NULL, address TEXT,
                source TEXT, resolved_at TEXT, PRIMARY KEY (lat, lng))"""
        )
        row = conn.execute(
            "SELECT address, source FROM geocode_cache WHERE lat = ? AND lng = ?",
            (flat, flng),
        ).fetchone()
    finally:
        conn.close()
    if row and row[0]:
        return row[0], row[1]

    address, source = "", ""
    key = cfg("google_maps_api_key")
    if key:
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params={"latlng": f"{lat},{lng}", "key": key},
                )
                data = r.json()
                if data.get("status") == "OK" and data.get("results"):
                    address = data["results"][0].get("formatted_address", "")
                    source = "google"
                elif data.get("status") in ("REQUEST_DENIED", "INVALID_REQUEST"):
                    global _google_denied
                    _google_denied = True
                    log.warning("Google geocode denied: %s — using OSM fallback", data.get("status"))
        except Exception:
            log.exception("Google geocode failed")

    if not address:  # free fallback — no key needed (polite: 1 req/s)
        await asyncio.sleep(_NOMINATIM_BACKOFF["until"] - time.monotonic()) \
            if _NOMINATIM_BACKOFF["until"] > time.monotonic() else None
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.get(
                    "https://nominatim.openstreetmap.org/reverse",
                    params={"lat": lat, "lon": lng, "zoom": "12", "format": "jsonv2"},
                    headers={"User-Agent": "AgniNetra-SIH26162/1.0"},
                )
                data = r.json()
                address = (data.get("display_name") or "").split(", Distr.")[0]
                source = "osm" if address else ""
        except Exception:
            log.exception("Nominatim geocode failed")
        finally:
            _NOMINATIM_BACKOFF["until"] = time.monotonic() + 1.1

    if address:
        try:
            conn = _connect()
            conn.execute(
                "INSERT OR REPLACE INTO geocode_cache VALUES (?, ?, ?, ?, ?)",
                (flat, flng, address, source, _utcnow_iso()),
            )
        finally:
            conn.close()
    return address, source


# ------------------------------------------------------------ messaging ----
async def _send_ntfy(text: str) -> tuple[bool, str]:
    """ntfy.sh push — pick any topic name; the phone app subscribed to that
    topic receives it instantly. Free, no account."""
    topic = cfg("ntfy_topic")
    if not topic:
        return False, "not configured — pick a topic name in Settings"
    server = (cfg("ntfy_server") or "https://ntfy.sh").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{server}/{topic}",
                content=text,
                headers={"Title": "AgniNetra fire alert", "Tags": "fire"},
            )
            if r.status_code < 300:
                return True, "sent"
            return False, f"HTTP {r.status_code} from {server}"
    except Exception as e:
        return False, f"network error: {e}"


def _authority_recipients() -> list[str]:
    """Configured authority addresses (comma/semicolon/newline separated)."""
    raw = cfg("authority_emails")
    return [e.strip() for e in re.split(r"[,;\n]+", raw) if e.strip()]


def _smtp_configured() -> bool:
    return bool(cfg("smtp_host") and cfg("smtp_user")
                and cfg("smtp_pass") and _authority_recipients())


def _send_authority_email(subject: str, plain: str, html: str) -> tuple[bool, str]:
    """Send the formal notice from the SMTP sender account to every
    configured authority. Returns (ok, human-readable detail)."""
    to = _authority_recipients()
    if not to:
        return False, "no authority recipients — add them in Settings"
    host, port = cfg("smtp_host"), int(cfg("smtp_port") or 587)
    user, pwd = cfg("smtp_user"), cfg("smtp_pass")
    if not (host and user and pwd):
        return False, "sender account not configured — link it in Settings"
    try:
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"AgniNetra Alerts <{user}>"
        msg["To"] = ", ".join(to)
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))
        smtplib_send(host, port, user, pwd, msg, to)
        return True, f"delivered to {len(to)} authority address(es)"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def smtplib_send(host, port, user, pwd, msg, to):
    import smtplib
    with smtplib.SMTP(host, port, timeout=15) as server:
        server.starttls()
        server.login(user, pwd)
        server.send_message(msg, from_addr=user, to_addrs=to)


def _format_message(d, address: str) -> str:
    """Compact plain-text alert (ntfy push / email fallback part)."""
    km = (_row_get(d, "facility_distance_m", 0)) / 1000.0
    emoji = "🏭" if d["classification"] == "Industrial Heat Source" else "♨️"
    loc = _row_get(d, "location") or f"{d['latitude']:.3f}, {d['longitude']:.3f}"
    conf = _row_get(d, "ml_confidence", 0)
    bright = _row_get(d, "brightness", 0)
    frp = _row_get(d, "frp", 0)
    place = f"📍 {address}\n🗺️ {loc}" if address else f"📍 {loc}"
    return (
        f"{emoji} AGNI ALERT · {d['classification']}\n"
        f"{place}\n"
        f"🎯 confidence: {conf:.0f}%\n"
        f"🏢 {km:.1f} km from {_row_get(d, 'nearest_facility_category') or _row_get(d, 'location') or 'industrial facility'}\n"
        f"🔥 brightness {bright:.0f} K · FRP {frp:.1f} MW\n"
        f"🛰️ {d['satellite']} · {d['acquired_at']}\n"
        f"🔗 https://maps.google.com/?q={d['latitude']:.5f},{d['longitude']:.5f}\n"
        f"— AgniNetra (SIH26162)"
    )


def _alert_subject(d, address: str, test: bool = False) -> str:
    prefix = "🧪 TEST — " if test else ""
    where = address or f"{d['latitude']:.3f}, {d['longitude']:.3f}"
    conf = _row_get(d, "ml_confidence", 0)
    return (f"{prefix}AgniNetra Alert: {d['classification']} near {where} "
            f"({conf:.0f}% confidence)")


def _alert_email_html(d, address: str, test: bool = False) -> str:
    """Formal HTML incident notice suitable for forwarding to authorities."""
    km = (_row_get(d, "facility_distance_m", 0)) / 1000.0
    conf = _row_get(d, "ml_confidence", 0)
    loc = _row_get(d, "location") or f"{d['latitude']:.3f}, {d['longitude']:.3f}"
    facility = (_row_get(d, "nearest_facility_category")
                or _row_get(d, "facility_name") or "industrial facility")
    maps = f"https://maps.google.com/?q={d['latitude']:.5f},{d['longitude']:.5f}"
    when = d["acquired_at"]
    rows = [
        ("Alert type", f"{d['classification']}{' (test)' if test else ''}"),
        ("Location", address or loc),
        ("Coordinates", f"{d['latitude']:.5f}, {d['longitude']:.5f}"),
        ("Detected at (UTC)", str(when)),
        ("Satellite source", str(d["satellite"])),
        ("AI confidence", f"{conf:.0f}%"),
        ("Nearest industrial facility", f"{facility} — {km:.1f} km away"),
        ("Radiative power (FRP)", f"{_row_get(d, 'frp', 0):.1f} MW"),
        ("Brightness", f"{_row_get(d, 'brightness', 0):.0f} K"),
        ("Map link", f'<a href="{maps}">{maps}</a>'),
    ]
    trs = "".join(
        f'<tr><td style="padding:6px 14px;border:1px solid #e0e4ec;'
        f'font-weight:600;background:#f7f9fc;">{k}</td>'
        f'<td style="padding:6px 14px;border:1px solid #e0e4ec;">{v}</td></tr>'
        for k, v in rows
    )
    return f"""
<div style="font-family:Segoe UI,Arial,sans-serif;max-width:640px;margin:auto;
     border:1px solid #e0e4ec;border-radius:10px;overflow:hidden;">
  <div style="background:#b3001b;color:#fff;padding:14px 20px;">
    <div style="font-size:18px;font-weight:700;">
      {'🧪 ' if test else ''}AgniNetra Industrial Fire Alert
    </div>
    <div style="font-size:12px;opacity:.85;">
      AI-based detection of industrial fires &amp; persistent thermal sources —
      NASA FIRMS satellite feed
    </div>
  </div>
  <div style="padding:16px 20px;">
    <p style="margin:0 0 12px;font-size:14px;">
      Dear Sir/Madam, the AgniNetra monitoring system has detected and
      classified the following thermal anomaly as a
      <b>{d['classification']}</b> near named industrial infrastructure.
      Kindly arrange verification and necessary action.
    </p>
    <table style="border-collapse:collapse;font-size:13px;width:100%;">{trs}</table>
    <p style="margin:14px 0 0;font-size:12px;color:#555;">
      Recommended first response: verify visually or via district authorities,
      inform the facility's safety officer, and escalate to the State Disaster
      Management Authority if the source persists beyond one satellite cycle.
    </p>
  </div>
  <div style="background:#f7f9fc;padding:10px 20px;font-size:11px;color:#777;">
    Auto-generated by AgniNetra — Smart India Hackathon 2026, PS SIH26162
    (NTRO · Disaster Management). Detection data: NASA FIRMS VIIRS/MODIS.
    This is an automated message; please verify on ground before action.
  </div>
</div>"""


# --------------------------------------------------------------- scanning ----
def _candidate_alerts(conn: sqlite3.Connection, limit: int | None = None) -> list[sqlite3.Row]:
    min_conf = float(os.getenv("ALERT_MIN_CONFIDENCE", "85"))
    radius_km = float(os.getenv("ALERT_RADIUS_KM", "5"))
    q = """
        SELECT * FROM detections
        WHERE classification IN (?, ?)
          AND COALESCE(ml_confidence, confidence, 0) >= ?
          AND distance_to_facility_m IS NOT NULL
          AND distance_to_facility_m <= ?
          AND nearest_facility_category IS NOT NULL
          AND acquired_at >= strftime('%Y-%m-%dT%H:%M:%S', 'now', '-24 hours')
        ORDER BY ml_confidence DESC
    """
    params = (*ALERT_CLASSES, min_conf, radius_km * 1000)
    if limit:
        q += " LIMIT ?"
        params += (limit,)
    return conn.execute(q, params).fetchall()


async def check_and_alert() -> dict:
    """Scan recent detections for alert-worthy hotspots. Called after each ingest."""
    fired = 0
    skipped_cooldown = 0
    sent_channels: list[str] = []
    failures: list[str] = []

    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        _ensure_alerts_table(conn)

        for d in _candidate_alerts(conn):
            if _recently_alerted(conn, d["latitude"], d["longitude"]):
                skipped_cooldown += 1
                continue

            address, source = await resolve_address(d["latitude"], d["longitude"])
            text = _format_message(d, address)

            channels = {
                "ntfy": await _send_ntfy(text),
                "email": _send_authority_email(
                    _alert_subject(d, address),
                    text + "\n\n(Satellite-verified detection — see attached notice.)",
                    _alert_email_html(d, address),
                ),
            }
            configured = [n for n, (_ok, det) in channels.items()
                          if "not configured" not in det and "no authority" not in det]
            used = [n for n, (ok, _det) in channels.items() if ok]

            if used:
                status = "sent"
                detail = "; ".join(f"{n}: ok" for n in used)
                sent_channels += used
            elif not configured:
                status = "logged"
                detail = "stored — no channel linked yet (Settings → Notification Channels)"
            else:
                status = "failed"
                detail = "; ".join(f"{n}: {channels[n][1]}" for n in configured)
                failures.append(detail)

            facility = (
                _row_get(d, "nearest_facility_category")
                or _row_get(d, "facility_name")
                or "industrial facility"
            )
            conn.execute(
                """
                INSERT INTO alerts
                  (detection_id, latitude, longitude, classification,
                   ml_confidence, facility_name, facility_distance_m,
                   address, message, channels, status, delivery_detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    d["id"], d["latitude"], d["longitude"], d["classification"],
                    _row_get(d, "ml_confidence"),
                    facility,
                    _row_get(d, "distance_to_facility_m"),
                    address or None,
                    text, ",".join(used) or "none", status, detail, _utcnow_iso(),
                ),
            )
            fired += 1

    if fired:
        log.info("Alerts fired: %d (skipped %d by cooldown) sent=%s failed=%d",
                 fired, skipped_cooldown, sent_channels or ["none"], len(failures))
    return {"fired": fired, "skipped_cooldown": skipped_cooldown,
            "sent_via": sorted(set(sent_channels)), "failures": failures[:3]}


def list_alerts(limit: int = 50) -> list[dict]:
    """Recent alerts for the dashboard."""
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        _ensure_alerts_table(conn)
        rows = conn.execute(
            "SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ------------------------------------------------------- channel linking ----
async def ntfy_activate(topic: str, server: str = "") -> dict:
    """Save the ntfy topic and send a confirmation push to it."""
    t = topic.strip()
    if not t or not all(c.isalnum() or c in "-_" for c in t):
        return {"ok": False,
                "detail": "topic must be letters/numbers/-/_ only (e.g. agni-fire-26162)"}
    srv = (server.strip() or "https://ntfy.sh").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{srv}/{t}",
                content="✅ AgniNetra linked to this topic. Subscribe to this exact topic "
                        "in the ntfy app and fire alerts will pop on your phone. — SIH26162",
                headers={"Title": "AgniNetra linked", "Tags": "fire"},
            )
    except Exception as e:
        return {"ok": False, "detail": f"network error: {e}"}
    if r.status_code >= 300:
        return {"ok": False, "detail": f"ntfy server rejected the topic (HTTP {r.status_code})"}
    set_meta("ntfy_topic", t)
    set_meta("ntfy_server", srv)
    return {"ok": True, "detail": f"linked — subscribe to topic '{t}' in the ntfy app ({srv})"}


def email_activate(host: str, port: int, user: str, password: str) -> dict:
    """Save the SMTP sender account and verify the server is reachable."""
    try:
        with socket.create_connection((host, port), timeout=6):
            reachable = True
            detail = f"{host}:{port} reachable"
    except Exception as e:
        return {"ok": False, "detail": f"{host}:{port} unreachable: {e}"}
    set_meta("smtp_host", host)
    set_meta("smtp_port", str(port))
    set_meta("smtp_user", user)
    set_meta("smtp_pass", password)
    return {"ok": True, "detail": detail + f" — alerts will be sent from {user}"}


def authorities_activate(emails: str) -> dict:
    """Save the authority recipient list (validated) and confirm count."""
    to = [e.strip() for e in re.split(r"[,;\n]+", emails) if e.strip()]
    bad = [e for e in to if not EMAIL_RE.match(e)]
    if bad:
        return {"ok": False, "detail": f"invalid address(es): {', '.join(bad)}"}
    if not to:
        return {"ok": False, "detail": "add at least one authority email"}
    set_meta("authority_emails", ",".join(to))
    return {"ok": True,
            "detail": f"{len(to)} authority recipient(s) saved — use Send test alert to verify delivery"}


# ------------------------------------------------------------ diagnostics ----
def alert_status() -> dict:
    """Everything you need to answer: 'is alerting actually working?'"""
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        _ensure_alerts_table(conn)
        counts = conn.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(status = 'sent') AS sent,
                   SUM(status = 'logged') AS logged,
                   SUM(status = 'failed') AS failed,
                   SUM(created_at >= strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-24 hours')) AS last_24h
            FROM alerts
            """
        ).fetchone()

    email = {
        "sender_configured": bool(cfg("smtp_host") and cfg("smtp_user")
                                  and cfg("smtp_pass")),
        "host": cfg("smtp_host") or None,
        "port": int(cfg("smtp_port") or 587),
        "sender": cfg("smtp_user") or None,
        "authorities": _authority_recipients(),
        "fully_configured": _smtp_configured(),
    }
    if email["sender_configured"]:
        try:
            with socket.create_connection((email["host"], email["port"]), timeout=5):
                email["reachable"] = True
        except Exception as e:
            email["reachable"] = False
            email["detail"] = str(e)
    else:
        email["reachable"] = None

    key = cfg("google_maps_api_key")
    return {
        "ntfy": {"configured": bool(cfg("ntfy_topic")),
                 "topic": cfg("ntfy_topic") or None,
                 "server": (cfg("ntfy_server") or "https://ntfy.sh")},
        "email": email,
        "geocoding": {
            "provider": "nominatim (osm fallback)" if _google_denied or not key
                        else "google",
            "key_set": bool(key),
            "google_denied": _google_denied,
            "note": ("GOOGLE_MAPS_API_KEY set but Geocoding API is not enabled for it — "
                     "enable 'Geocoding API' in Google Cloud Console, or ignore: the "
                     "free OSM fallback resolves addresses.") if _google_denied else None,
        },
        "rule": {
            "min_confidence": float(os.getenv("ALERT_MIN_CONFIDENCE", "85")),
            "radius_km": float(os.getenv("ALERT_RADIUS_KM", "5")),
            "cooldown_hours": float(os.getenv("ALERT_COOLDOWN_HOURS", "6")),
            "classes": list(ALERT_CLASSES),
        },
        "pipeline": {
            "total_alerts": counts["total"] or 0,
            "sent": counts["sent"] or 0,
            "logged": counts["logged"] or 0,
            "failed": counts["failed"] or 0,
            "last_24h": counts["last_24h"] or 0,
        },
    }


async def send_test_alert() -> dict:
    """Prove the channels work. Uses the most recent alert-worthy detection so
    the test looks exactly like a real alert (address included)."""
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        _ensure_alerts_table(conn)
        cands = _candidate_alerts(conn, limit=1)
    if cands:
        d = cands[0]
        address, source = await resolve_address(d["latitude"], d["longitude"])
        subject = _alert_subject(d, address, test=True)
        html = _alert_email_html(d, address, test=True)
        text = "🧪 TEST — " + _format_message(d, address)
        sample = {"lat": d["latitude"], "lng": d["longitude"]}
    else:
        address, source = "", ""
        subject = "🧪 TEST — AgniNetra alerting pipeline"
        html = ("<p>🧪 AgniNetra TEST — if you can read this, authority "
                "alert emails will arrive correctly.</p>")
        text = ("🧪 AGNI TEST ALERT\nThis is a test of the AgniNetra alerting pipeline.\n"
                "— AgniNetra (SIH26162)")
        sample = None

    results = {
        "ntfy": dict(zip(("ok", "detail"), await _send_ntfy(text))),
        "email": dict(zip(("ok", "detail"),
                          _send_authority_email(subject, text, html))),
    }
    return {
        "sent": [n for n, r in results.items() if r["ok"]],
        "results": results,
        "configured": {"ntfy": bool(cfg("ntfy_topic")),
                       "email": _smtp_configured()},
        "subject": subject,
        "address": address or None,
        "address_source": source or None,
        "used_detection": sample,
    }
