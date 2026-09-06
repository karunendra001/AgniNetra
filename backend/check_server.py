"""Hit the LIVE running server and print what the frontend would receive."""
import httpx

base = "http://127.0.0.1:8000"
try:
    c = httpx.Client(trust_env=False, timeout=5)   # bypass system proxy
except Exception as e:
    raise SystemExit(f"client error: {e}")

try:
    root = c.get(f"{base}/").json()
    print("GET /              ->", root)
    print("\nGET /api/stats     ->", c.get(f"{base}/api/stats").json())

    dets = c.get(f"{base}/api/detections", params={"limit": 5}).json()
    print(f"\nGET /api/detections -> {len(dets)} rows (limit 5). Sample:")
    for d in dets[:3]:
        print(f"   #{d['id']} {d['location']:<28} {d['classification']:<28} conf={d['confidence']} {d['time']}")
    print(f"\n✅ SERVER IS LIVE  —  Swagger UI: {base}/docs")
except httpx.ConnectError:
    raise SystemExit("❌ Server not responding on :5000")
