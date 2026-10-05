"""Load the gated-community dataset and the context layers."""
import urllib.request

import geopandas as gpd
import pandas as pd

from . import osm
from .config import CRS, DATASET_FILES, MCMV, MIN_WAGE_2010, WATER, ZENODO_RECORD

# Typology of Faccin, Almeida & Campos (2024): code -> (label, family)
TYPES = {
    "A1": ("Apartment blocks up to 4 floors, no amenities", "A"),
    "A2": ("Apartment blocks up to 4 floors, with amenities", "A"),
    "B1": ("Towers of 5+ floors, no amenities", "B"),
    "B2": ("Towers of 5+ floors, with amenities", "B"),
    "C1-a": ("Small house clusters, no amenities", "C"),
    "C1-b": ("Medium house clusters, no amenities", "C"),
    "C2": ("House clusters with amenities", "C"),
    "D": ("Large gated developments", "D"),
    "E": ("Mixed houses and apartment blocks", "E"),
}
FAMILIES = {
    "A": "Apartment blocks (up to 4 floors)",
    "B": "Towers (5+ floors)",
    "C": "House clusters",
    "D": "Large developments",
    "E": "Mixed",
}
FORM = {1: "Horizontal (1–2 floors)", 2: "Low-rise (3–4 floors)", 3: "High-rise (5+ floors)", 4: "Mixed"}
PERIOD = {1: "Before 2002", 2: "2002–2012", 3: "2012–2017", 4: "2017–2022", 5: "Under construction"}
# The paper groups the satellite-image dates into three periods
PERIOD3 = {1: "Before 2000", 2: "2000–2010", 3: "2010–2022", 4: "2010–2022", 5: "2010–2022"}
SIZE = {1: "Small", 2: "Medium", 3: "Large"}
INCOME = ["E", "D", "C", "B", "A"]  # low to high
INCOME_LABEL = {"E": "E: < 2 MW", "D": "D: 2–4 MW", "C": "C: 4–10 MW", "B": "B: 10–20 MW", "A": "A: > 20 MW"}


def fetch_dataset(dataset_dir):
    """Download the open dataset from Zenodo into dataset_dir when files are missing."""
    dataset_dir.mkdir(parents=True, exist_ok=True)
    for name in DATASET_FILES:
        dest = dataset_dir / name
        if dest.exists():
            continue
        url = f"https://zenodo.org/records/{ZENODO_RECORD}/files/{name}?download=1"
        print(f"downloading {name} from Zenodo")
        req = urllib.request.Request(url, headers={"User-Agent": "housing-poa (github.com/carolinafaccin/housing-poa)"})
        with urllib.request.urlopen(req, timeout=120) as r:
            dest.write_bytes(r.read())


def income_class(values, min_wage=MIN_WAGE_2010):
    """Income class (E to A) from a monthly income in reais, in minimum wages."""
    return pd.cut(values / min_wage, [0, 2, 4, 10, 20, float("inf")], labels=INCOME, right=False)


def load_condominiums(dataset_dir):
    c = gpd.read_file(dataset_dir / "poa_condominios_2022_pol.gpkg").to_crs(CRS)
    c["geometry"] = c.geometry.force_2d()
    c["family"] = c["tipo24"].map({k: v[1] for k, v in TYPES.items()})
    c["form"] = c["tipo"].map(FORM)
    c["period"] = c["tempo"].map(PERIOD)
    c["period3"] = c["tempo"].map(PERIOD3)
    c["size"] = c["porte"].map(SIZE)
    # Household income of the census tract (2010), in the classes of the dataset dictionary
    c["income"] = income_class(c["renda_dom10t"])
    c["bairro"] = c["bairro"].str.strip().str.upper()
    return c


def load_neighborhoods(dataset_dir):
    b = gpd.read_file(dataset_dir / "poa_bairros_lc12112_2016_pol.gpkg").to_crs(CRS)
    b["NOME"] = b["NOME"].str.strip().str.upper()
    return b.dissolve("NOME", as_index=False)[["NOME", "geometry"]]


def city_outline(neighborhoods):
    return gpd.GeoSeries([neighborhoods.union_all()], crs=neighborhoods.crs)


def load_mcmv(sources_dir):
    """Federal housing program (Minha Casa Minha Vida) developments, as points. None if missing."""
    if sources_dir is None or not (sources_dir / MCMV).exists():
        return None
    m = gpd.read_file(sources_dir / MCMV).to_crs(CRS)
    m = m[m.geometry.notna() & ~m.geometry.is_empty]
    m["geometry"] = m.geometry.force_2d().representative_point()
    m["Name"] = m["Name"].str.strip()
    return m.drop_duplicates("Name")[["Name", "geometry"]]


def load_water(sources_dir, city, outputs_dir):
    """Lake Guaíba and the Jacuí delta channels (IBGE BC250), clipped and cached in outputs_dir/cache."""
    cache = outputs_dir / "cache" / "water.gpkg"
    if cache.exists():
        return gpd.read_file(cache)
    if sources_dir is None or not (sources_dir / WATER).exists():
        return None
    w, s, e, n = city.to_crs(4674).total_bounds
    g = gpd.read_file(sources_dir / WATER, bbox=(w - 0.1, s - 0.1, e + 0.1, n + 0.1)).to_crs(CRS)[["geometry"]]
    cache.parent.mkdir(parents=True, exist_ok=True)
    g.to_file(cache)
    return g


def load_streets(city, outputs_dir):
    """OpenStreetMap streets around the city (downloaded once, cached in outputs_dir/cache)."""
    w, s, e, n = city.to_crs(4326).total_bounds
    return osm.roads((s - 0.01, w - 0.01, n + 0.01, e + 0.01), outputs_dir / "cache" / "osm_streets.json", crs=CRS)
