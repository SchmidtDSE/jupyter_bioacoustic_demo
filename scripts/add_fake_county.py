"""
Add Fake County Column

For each row in detections.N-dse.csv, creates 4 copies with random
lat/lon anywhere within California land, then assigns the county.

Output: data/detections.N-dse.dummy-geo.csv

License: BSD 3-Clause
"""
import csv
import random
import requests
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from shapely.prepared import prep


#
# CONSTANTS
#
GEOJSON_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/"
    "geojson-counties-fips.json"
)
CA_FIPS_PREFIX = "06"
INPUT_PATH = "data/detections.N-dse.csv"
OUTPUT_PATH = "data/detections.N-dse.dummy-geo.csv"
COPIES_PER_ROW = 1
MAX_ATTEMPTS = 500
SEED = 42


#
# PUBLIC
#
def main() -> None:
    """Generate 4 randomly-placed CA copies per row, tag with county."""
    random.seed(SEED)

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
    ca_boundary = unary_union([geom for _, geom in counties])
    ca_prepared = prep(ca_boundary)
    min_lon, min_lat, max_lon, max_lat = ca_boundary.bounds
    print(f"Loaded {len(counties)} CA counties")
    print(f"Bounding box: lat [{min_lat:.2f}, {max_lat:.2f}] "
          f"lon [{min_lon:.2f}, {max_lon:.2f}]")

    with open(INPUT_PATH) as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or []) + ["county"]
        rows = list(reader)

    print(f"Expanding {len(rows)} rows x {COPIES_PER_ROW}...")
    out_rows: list[dict[str, str]] = []
    for row in rows:
        for _ in range(COPIES_PER_ROW):
            copy = dict(row)
            lat, lon, county = _random_ca_point(
                min_lat, max_lat, min_lon, max_lon,
                ca_prepared, counties,
            )
            copy["lat"] = str(lat)
            copy["lon"] = str(lon)
            copy["county"] = county
            out_rows.append(copy)

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    matched = sum(1 for r in out_rows if r["county"])
    print(f"Wrote {OUTPUT_PATH}: {len(out_rows)} rows, "
          f"{matched} with county")


#
# INTERNAL
#
def _random_ca_point(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    ca_prepared: object,
    counties: list[tuple[str, object]],
) -> tuple[float, float, str]:
    """Pick a random point within CA land, return (lat, lon, county)."""
    for _ in range(MAX_ATTEMPTS):
        lat = random.uniform(min_lat, max_lat)
        lon = random.uniform(min_lon, max_lon)
        pt = Point(lon, lat)
        if ca_prepared.contains(pt):
            county = _find_county(pt, counties) or ""
            return round(lat, 6), round(lon, 6), county
    return round((min_lat + max_lat) / 2, 6), round((min_lon + max_lon) / 2, 6), ""


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
