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

# every detection must come from a real FIRMS satellite feed — seed rows used
# generic satellite names ("seed", "test"...) or had no satellite at all
import sqlite3
from app.config import settings
conn = sqlite3.connect(settings.db_path)
total = conn.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
fake = conn.execute(
    "SELECT COUNT(*) FROM detections WHERE satellite IS NULL "
    "OR satellite NOT IN ('VIIRS-SNPP', 'VIIRS-NOAA20', 'MODIS')"
).fetchone()[0]
conn.close()
assert fake == 0, f"{fake} of {total} rows are not real FIRMS satellite data!"
print(f"data purity        -> {total} rows, all from real FIRMS satellites (0 fake)")

print("\nALL SMOKE TESTS PASSED ✅")
