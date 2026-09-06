import requests
import pandas as pd
from pathlib import Path

# ⚠️ Apni MAP_KEY yahan daalo
MAP_KEY = "6c60776c3cd1eb8ff79db154fbce46c3"

SENSOR = "VIIRS_SNPP_NRT"
BBOX = "68,6,97,37"   # India ka bounding box: west,south,east,north
DAY_RANGE = 5           # area endpoint max 5 din tak deta hai ek call mein

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SENSOR}/{BBOX}/{DAY_RANGE}"

print(f"Fetching: {url}")

try:
    df = pd.read_csv(url)
except Exception as e:
    print(f"✗ Download fail ho gaya: {e}")
    raise SystemExit(1)

if df.empty:
    print("⚠️ Koi data nahi mila")
else:
    out_path = RAW_DIR / "firms_viirs_india_raw.csv"
    df.to_csv(out_path, index=False)
    print(f"✓ {len(df)} records saved: {out_path}")
    print("\nColumns:", df.columns.tolist())
    print("\nSample rows:")
    print(df.head())
