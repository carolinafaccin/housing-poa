"""Paths: read from config/config.local.json (gitignored), like the other repositories.

- dataset_dir  the open dataset (Zenodo). Downloaded there if the files are missing.
- sources_dir      shared raw-data catalog (optional: federal housing program developments, water bodies)
- outputs_dir     this project's outputs (tables, figures, cache/ for OpenStreetMap downloads)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ZENODO_RECORD = "17023732"   # DOI 10.5281/zenodo.17023731 (all versions)
DATASET_FILES = ["poa_condominios_2022_pol.gpkg", "poa_bairros_lc12112_2016_pol.gpkg",
                 "poa_app_2020_pol.gpkg", "poa_condominios_dicionario.csv"]

# Optional layers in sources_dir (not part of the open dataset)
MCMV = "prefeituras_municipais/porto_alegre/mcmv_2/t0/mcmv_corrigido.shp"
WATER = "ibge/hidrografia/2017/t0/hid_trecho_massa_dagua_a.shp"

CRS = 31982  # SIRGAS 2000 / UTM 22S
MIN_WAGE_2010 = 510.0


def load():
    """Return (dataset_dir, sources_dir, outputs_dir); create outputs_dir subfolders."""
    cfg_path = ROOT / "config" / "config.local.json"
    if not cfg_path.exists():
        raise SystemExit(f"Missing {cfg_path.name}: copy config/config.local.json.example and set the folders.")
    cfg = json.loads(cfg_path.read_text())
    dataset_dir = Path(cfg["dataset_dir"])
    sources_dir = Path(cfg["sources_dir"]) if cfg.get("sources_dir") else None
    outputs_dir = Path(cfg["outputs_dir"])
    for sub in ("tables", "figures"):
        (outputs_dir / sub).mkdir(parents=True, exist_ok=True)
    return dataset_dir, sources_dir, outputs_dir
