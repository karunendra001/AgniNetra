"""Query helpers used by the API routes."""
from datetime import date, timedelta

from .config import settings
from .db import get_connection, get_meta
from .schemas import Stats


def settings_window_hours() -> int:
    return max(24, settings.firms_day_range * 24)


def latest_detections(limit: int = 1000):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM detections
            WHERE acquired_at >= datetime('now', ?)
            ORDER BY acquired_at DESC
            LIMIT ?
            """,
            (f"-{settings_window_hours()} hours", limit),
        ).fetchall()


def compute_stats() -> Stats:
    """Class counts + count of all detections with confidence >= 85."""
    window = f"-{settings_window_hours()} hours"
    with get_connection() as conn:
        by_class_rows = conn.execute(
            """
            SELECT classification, COUNT(*) AS n
            FROM detections
            WHERE acquired_at >= datetime('now', ?)
            GROUP BY classification
            """,
            (window,),
        ).fetchall()
        high_conf = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM detections
            WHERE acquired_at >= datetime('now', ?)
              AND COALESCE(ml_confidence, confidence, 0) >= 85
            """,
            (window,),
        ).fetchone()

    by_class = {r["classification"]: r["n"] for r in by_class_rows}
    return Stats(
        fire=by_class.get("Vegetation Fire", 0),
        industrial=by_class.get("Industrial Heat Source", 0),
        persistent=by_class.get("Persistent Thermal Anomaly", 0),
        highConfidence=high_conf["n"],
        total=sum(by_class.values()),
        lastSync=get_meta("last_firms_sync"),
    )


def compute_trend(days: int = 7) -> list[dict]:
    """Per-day counts per fire type for the TrendChart:
    [{day: 'Mon', vegetation, industrial, persistent}, ...]."""
    window = f"-{max(1, days) * 24} hours"
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT date(acquired_at) AS day,
                   SUM(CASE WHEN classification = 'Vegetation Fire'
                       THEN 1 ELSE 0 END) AS vegetation,
                   SUM(CASE WHEN classification = 'Industrial Heat Source'
                       THEN 1 ELSE 0 END) AS industrial,
                   SUM(CASE WHEN classification = 'Persistent Thermal Anomaly'
                       THEN 1 ELSE 0 END) AS persistent
            FROM detections
            WHERE acquired_at >= datetime('now', ?)
            GROUP BY day
            """,
            (window,),
        ).fetchall()

    by_day = {r["day"]: (r["vegetation"], r["industrial"], r["persistent"])
              for r in rows}
    out = []
    today = date.today()
    for i in range(max(1, days) - 1, -1, -1):
        d = today - timedelta(days=i)
        veg, ind, per = by_day.get(d.isoformat(), (0, 0, 0))
        out.append({"day": d.strftime("%a"), "vegetation": veg,
                    "industrial": ind, "persistent": per})
    return out
