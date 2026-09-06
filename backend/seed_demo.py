"""Seed the DB with realistic demo detections (Indian industrial/forest sites)
so the frontend dashboard works before FIRMS data flows. Safe to re-run.

    python seed_demo.py
"""
import sqlite3
from datetime import datetime, timedelta, timezone

DB = "data/fires.db"

SITES = [
    # (name, lat, lng, classification, brightness, frp, conf)
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
SATELLITES = ["VIIRS-NOAA20", "VIIRS-SNPP", "MODIS-Aqua", "MODIS-Terra"]

conn = sqlite3.connect(DB)
now = datetime.now(timezone.utc)
for i, (name, lat, lng, cls, bright, frp, conf) in enumerate(SITES):
    mins_ago = (i * 17 + 5) % 180
    acquired = (now - timedelta(minutes=mins_ago)).isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT INTO detections
            (latitude, longitude, brightness, frp, confidence, satellite,
             acquired_at, daynight, classification, ml_confidence, location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (lat, lng, bright, frp, conf, SATELLITES[i % 4], acquired,
         "n" if i % 3 == 0 else "d", cls, float(conf), name),
    )
conn.commit()
print(f"Seeded {len(SITES)} demo detections into {DB}")
conn.close()
