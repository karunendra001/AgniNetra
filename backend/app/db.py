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


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("PRAGMA journal_mode=WAL")  # concurrent readers + scheduler writer
        conn.executescript(SCHEMA)
        existing = {r["name"] for r in conn.execute("PRAGMA table_info(detections)").fetchall()}
        for col, coltype in MIGRATION_COLUMNS:
            if col not in existing:
                conn.execute(f"ALTER TABLE detections ADD COLUMN {col} {coltype}")


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
