"""GIS export: detections -> GeoJSON / KML / CSV.

Deliverable (ii) of SIH26162: "GIS based solution ... visualization of the
output as an overlay over maps". Files open directly in Google Earth (KML),
QGIS (GeoJSON/CSV), or any spreadsheet.
"""
import csv
import io
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from fastapi import HTTPException

from .db import get_connection
from .schemas import Stats  # noqa: F401  (kept for typing parity)

VALID_FORMATS = ("geojson", "kml", "csv")

# dashboard color #rrggbb -> KML needs <color>aabbggrr</color> (alpha,blue,green,red)
KML_COLORS = {
    "Vegetation Fire": "ff5747ff",          # #ff4757
    "Industrial Heat Source": "ff439fff",   # #ff9f43
    "Persistent Thermal Anomaly": "ffea5ea5",  # #a55eea
    "Unclassified": "ffa38c77",             # #778ca3
}


def fetch_rows(limit: int = 20000):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, latitude, longitude, brightness, bright_ti5, frp,
                   confidence, ml_confidence, satellite, acquired_at, daynight,
                   classification, location, detection_count, unique_days,
                   distance_to_facility_m, nearest_facility_category, landcover_class
            FROM detections
            ORDER BY acquired_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def _display_name(r) -> str:
    return r["location"] or f"{r['latitude']:.3f}, {r['longitude']:.3f}"


# ---------------------------------------------------------------- GeoJSON ----
def build_geojson(rows) -> dict:
    features = []
    for r in rows:
        props = {
            "id": r["id"],
            "location": _display_name(r),
            "classification": r["classification"],
            "confidence": r["ml_confidence"] if r["ml_confidence"] is not None else r["confidence"],
            "brightness_ti4_k": r["brightness"],
            "brightness_ti5_k": r["bright_ti5"],
            "frp_mw": r["frp"],
            "satellite": r["satellite"],
            "acquired_at": r["acquired_at"],
            "daynight": r["daynight"],
            "detection_count": r["detection_count"],
            "unique_days": r["unique_days"],
            "distance_to_facility_m": r["distance_to_facility_m"],
            "nearest_facility_category": r["nearest_facility_category"],
            "landcover_class": r["landcover_class"],
        }
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["longitude"], r["latitude"]]},
            "properties": props,
        })
    return {
        "type": "FeatureCollection",
        "name": "SIH26162_thermal_detections",
        "features": features,
    }


# -------------------------------------------------------------------- KML ----
KML_HEAD = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>SIH26162 Thermal Detections</name>
  <description>Industrial fires &amp; persistent thermal sources - NASA FIRMS + OSM + landcover (AgniNetra)</description>
{styles}
"""

_STYLE = """  <Style id="style_{cls}">
    <IconStyle><color>{color}</color><scale>0.9</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/shapes/fire.png</href></Icon>
    </IconStyle>
  </Style>"""


def build_kml(rows) -> str:
    styles = "\n".join(
        _STYLE.format(cls=cls.replace(" ", "_"), color=color)
        for cls, color in KML_COLORS.items()
    )
    parts = [KML_HEAD.format(styles=styles)]

    for r in rows:
        cls = r["classification"] if r["classification"] in KML_COLORS else "Unclassified"
        name = escape(_display_name(r))
        desc = escape(
            f"{r['classification']}\n"
            f"Confidence: {r['ml_confidence'] or r['confidence'] or '?'}%\n"
            f"Brightness: {r['brightness']} K | FRP: {r['frp']} MW\n"
            f"Satellite: {r['satellite']} ({r['acquired_at']})\n"
            f"Nearest facility: {r['nearest_facility_category'] or '?'} "
            f"at {round(r['distance_to_facility_m']) if r['distance_to_facility_m'] is not None else '?'} m\n"
            f"Landcover: {r['landcover_class'] or '?'}"
        )
        when = ""
        if r["acquired_at"]:
            when = f"<TimeStamp><when>{r['acquired_at']}</when></TimeStamp>"
        parts.append(
            f"""  <Placemark>
    <name>{name}</name>
    <description>{desc}</description>
    <styleUrl>#style_{cls.replace(' ', '_')}</styleUrl>
    {when}
    <Point><coordinates>{r['longitude']},{r['latitude']},0</coordinates></Point>
  </Placemark>"""
        )
    parts.append("</Document>\n</kml>")
    return "\n".join(parts)


# -------------------------------------------------------------------- CSV ----
CSV_COLS = ["id", "latitude", "longitude", "location", "classification",
            "confidence", "ml_confidence", "brightness", "bright_ti5", "frp",
            "satellite", "acquired_at", "daynight", "detection_count",
            "unique_days", "distance_to_facility_m", "nearest_facility_category",
            "landcover_class"]


def build_csv(rows) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_COLS)
    for r in rows:
        writer.writerow([r[c] for c in CSV_COLS])
    return buf.getvalue()


# ----------------------------------------------------------------- router ----
def export_detections(fmt: str) -> tuple[str, str, str]:
    """Returns (content, media_type, filename). Raises 400 on bad format."""
    fmt = (fmt or "").lower()
    if fmt not in VALID_FORMATS:
        raise HTTPException(status_code=400, detail=f"format must be one of {VALID_FORMATS}")

    rows = fetch_rows()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")

    if fmt == "geojson":
        import json
        return (json.dumps(build_geojson(rows), indent=None),
                "application/geo+json", f"detections_{stamp}.geojson")
    if fmt == "kml":
        return (build_kml(rows),
                "application/vnd.google-earth.kml+xml", f"detections_{stamp}.kml")
    return (build_csv(rows),
            "text/csv", f"detections_{stamp}.csv")
