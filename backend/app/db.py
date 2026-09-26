import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import settings

DB_PATH = Path(settings.db_path)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS detections (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    latitude      REAL NOT NULL,
    longitude     REAL NOT NULL,
    brightness    REAL,
    bright_ti5    REAL,
    frp           REAL,
    confidence    INTEGER,
    confidence_raw TEXT,
    satellite     TEXT,
    acquired_at   TEXT,
    daynight      TEXT DEFAULT 'd',
    classification TEXT NOT NULL DEFAULT 'Unclassified',
    ml_confidence REAL,
    location      TEXT,
    detection_count INTEGER,
    unique_days   INTEGER,
    distance_to_facility_m REAL,
    nearest_facility_category TEXT,
    landcover_class TEXT,
    is_persistent INTEGER NOT NULL DEFAULT 0,
    first_seen    TEXT,
    last_seen     TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- one row per hotspot; updated on every ingest so we can compute
-- persistence (same spot seen again and again = flare / plant) later
CREATE UNIQUE INDEX IF NOT EXISTS idx_hotspot
    ON detections (satellite, round(latitude, 3), round(longitude, 3), acquired_at);

CREATE INDEX IF NOT EXISTS idx_class ON detections (classification);
CREATE INDEX IF NOT EXISTS idx_time  ON detections (acquired_at);

-- key/value store for pipeline state (e.g. last successful NASA sync)
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# Columns added after the first schema release; existing DBs get them via ALTER TABLE.
MIGRATION_COLUMNS = [
    ("bright_ti5", "REAL"),
    ("confidence_raw", "TEXT"),
    ("detection_count", "INTEGER"),
    ("unique_days", "INTEGER"),
    ("distance_to_facility_m", "REAL"),
    ("nearest_facility_category", "TEXT"),
    ("landcover_class", "TEXT"),
]


def _seed_initial_data(conn) -> None:
    count = conn.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
    if count > 0:
        return
    from datetime import datetime, timedelta, timezone
    sites = [
        ("Jamshedpur Steel Belt",          22.8046, 86.2029, "Industrial Heat Source",       412, 61.0, 93),
        ("Paradip Refinery",               20.3167, 86.6167, "Industrial Heat Source",       398, 55.5, 91),
        ("Angul Industrial Zone",          20.8400, 85.1000, "Persistent Thermal Anomaly",   371, 22.4, 88),
        ("Bokaro Steel City",              23.6693, 86.1511, "Industrial Heat Source",       405, 48.2, 90),
        ("Jamnagar Refinery Complex",      22.2394, 70.0119, "Persistent Thermal Anomaly",   383, 30.1, 94),
        ("Rourkela Steel Plant",           22.2604, 84.8536, "Industrial Heat Source",       391, 41.7, 87),
        ("Bastar Forest Belt",             19.1071, 81.9550, "Vegetation Fire",              334, 18.9, 82),
        ("Similipal Reserve",              21.6167, 86.2333, "Vegetation Fire",              342, 25.3, 86),
        ("Nagarhole Forest",               12.0000, 76.1333, "Vegetation Fire",              328, 14.6, 79),
        ("Barmer Gas Field",               25.7521, 71.3967, "Persistent Thermal Anomaly",   377, 27.8, 95),
        ("Raigad MIDC",                    18.5158, 73.1822, "Industrial Heat Source",       386, 35.0, 84),
        ("Vizag Steel Plant",              17.6868, 83.2185, "Industrial Heat Source",       402, 52.4, 89),
        ("Bandhavgarh Buffer Zone",        23.6900, 81.0000, "Vegetation Fire",              331, 16.2, 77),
        ("Durgapur Industrial Area",       23.5204, 87.3119, "Persistent Thermal Anomaly",   368, 20.5, 91),
    ]
    satellites = ["VIIRS-NOAA20", "VIIRS-SNPP", "MODIS-Aqua", "MODIS-Terra"]
    now = datetime.now(timezone.utc)
    for i, (name, lat, lng, cls, bright, frp, conf) in enumerate(sites):
        mins_ago = (i * 17 + 5) % 180
        acquired = (now - timedelta(minutes=mins_ago)).isoformat(timespec="seconds")
        conn.execute(
            """
            INSERT INTO detections
                (latitude, longitude, brightness, frp, confidence, satellite,
                 acquired_at, daynight, classification, ml_confidence, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (lat, lng, bright, frp, conf, satellites[i % 4], acquired,
             "n" if i % 3 == 0 else "d", cls, float(conf), name),
        )


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("PRAGMA journal_mode=WAL")  # concurrent readers + scheduler writer
        conn.executescript(SCHEMA)
        existing = {r["name"] for r in conn.execute("PRAGMA table_info(detections)").fetchall()}
        for col, coltype in MIGRATION_COLUMNS:
            if col not in existing:
                conn.execute(f"ALTER TABLE detections ADD COLUMN {col} {coltype}")
        _seed_initial_data(conn)


def set_meta(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def get_meta(key: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None
