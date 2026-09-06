"""In-process smoke test - verifies routes, DB and response shapes without network.
Run:  python smoke_test.py
"""
from fastapi.testclient import TestClient

from app.main import app

# context manager form so the app lifespan runs (init_db, etc.)
client = TestClient(app)
client.__enter__()

r = client.get("/")
assert r.status_code == 200, r.text
print("GET /              ->", r.json())

r = client.get("/api/stats")
assert r.status_code == 200, r.text
stats = r.json()
assert set(stats) == {"fire", "industrial", "persistent", "highConfidence", "total", "lastSync"}, stats
print("GET /api/stats     ->", stats)

r = client.get("/api/detections?limit=5")
assert r.status_code == 200, r.text
dets = r.json()
expected = {"id", "location", "lat", "lng", "classification",
            "confidence", "brightness", "frp", "satellite", "time"}
for d in dets:
    assert set(d) == expected, set(d) ^ expected
print(f"GET /api/detections -> {len(dets)} items, fields OK")

r = client.get("/api/detections", params={"classification": "Vegetation Fire", "limit": 100})
assert r.status_code == 200
assert all(d["classification"] == "Vegetation Fire" for d in r.json())
print("filter by class    ->", len(r.json()), "Vegetation Fire rows")

r = client.get("/api/trend")
assert r.status_code == 200
assert all(set(x) == {"day", "fires", "industrial"} for x in r.json())
print("GET /api/trend     ->", r.json())

# every detection in the DB must come from a real satellite, not seeds
import sqlite3
from app.config import settings
conn = sqlite3.connect(settings.db_path)
named = conn.execute("SELECT COUNT(*) FROM detections WHERE location IS NOT NULL").fetchone()[0]
conn.close()
assert named == 0, f"{named} seed rows still present!"
print("data purity        -> 0 seed rows, all detections are real FIRMS data")

print("\nALL SMOKE TESTS PASSED ✅")
