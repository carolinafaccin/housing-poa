"""OpenStreetMap streets via the Overpass API, cached as JSON in outputs_dir/cache/."""
import json
import time

import geopandas as gpd
import requests
from shapely.geometry import LineString

OVERPASS = "https://overpass-api.de/api/interpreter"
MAIN = ("motorway", "trunk", "primary", "secondary")
STREETS = MAIN + ("tertiary", "unclassified", "residential", "living_street")


def roads(bbox, cache, kinds=STREETS, crs=31982):
    """Return OSM ways with a `highway` tag in `kinds` inside bbox = (south, west, north, east), EPSG:4326."""
    if not cache.exists():
        s, w, n, e = bbox
        pattern = "|".join(kinds)
        query = f'[out:json][timeout:180];way["highway"~"^({pattern})$"]({s},{w},{n},{e});out geom;'
        headers = {"User-Agent": "carolinafaccin-portfolio/1.0", "Accept": "application/json"}
        for attempt in range(3):
            r = requests.post(OVERPASS, data={"data": query}, headers=headers, timeout=240)
            if r.ok and r.text.startswith("{"):
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_text(r.text)
                break
            time.sleep(20 * (attempt + 1))
        else:
            raise RuntimeError(f"Overpass request failed ({r.status_code})")
    elements = json.loads(cache.read_text())["elements"]
    rows = [{"highway": el["tags"].get("highway"), "name": el["tags"].get("name"), "ref": el["tags"].get("ref"),
             "geometry": LineString([(p["lon"], p["lat"]) for p in el["geometry"]])}
            for el in elements if el.get("geometry") and len(el["geometry"]) > 1]
    return gpd.GeoDataFrame(rows, crs=4326).to_crs(crs)
