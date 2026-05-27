"""
Add County Column

Adds a 'county' column to detections.N-dse.csv by reverse-geocoding
each row's lat/lon against California county boundaries.

License: BSD 3-Clause
"""
import csv
import json
import requests
from shapely.geometry import shape, Point


#
# CONSTANTS
#
GEOJSON_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/"
    "geojson-counties-fips.json"
)
CA_FIPS_PREFIX = "06"
INPUT_PATH = "data/detections.N-dse.csv"
OUTPUT_PATH = "data/detections.N-dse.geo.csv"


#
# PUBLIC
#
def main() -> None:
    """Load county geometries, tag each detection row, write output."""
    print("Fetching county boundaries...")
    all_counties = requests.get(GEOJSON_URL).json()
    ca_features = [
        f for f in all_counties["features"]
        if f["id"].startswith(CA_FIPS_PREFIX)
    ]
    counties = [
        (f["properties"]["NAME"], shape(f["geometry"]))
        for f in ca_features
    ]
    print(f"Loaded {len(counties)} CA counties")

    with open(INPUT_PATH) as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or []) + ["county"]
        rows = list(reader)

    print(f"Processing {len(rows)} rows...")
    cache: dict[tuple[float, float], str | None] = {}
    for row in rows:
        lat_s, lon_s = row.get("lat", ""), row.get("lon", "")
        if not lat_s or not lon_s:
            row["county"] = ""
            continue
        lat, lon = float(lat_s), float(lon_s)
        coord = (lat, lon)
        if coord not in cache:
            cache[coord] = _find_county(Point(lon, lat), counties)
        row["county"] = cache[coord] or ""

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    matched = sum(1 for r in rows if r["county"])
    print(f"Wrote {OUTPUT_PATH}: {matched}/{len(rows)} rows matched a county")


#
# INTERNAL
#
def _find_county(
    point: Point,
    counties: list[tuple[str, object]],
) -> str | None:
    """Return county name containing the point, or None."""
    for name, geom in counties:
        if geom.contains(point):
            return name
    return None


if __name__ == "__main__":
    main()
