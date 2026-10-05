"""HOUSING-POA pipeline: open dataset of gated communities -> tables, validation and figures.

    python pipeline.py                       # everything
    python pipeline.py --only tables         # tables and validation against the paper
    python pipeline.py --only figures docs   # redraw figures and copy the README ones

Folders come from config/config.local.json (dataset_dir, sources_dir, outputs_dir).
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from housing import config, data, figures, metrics, style  # noqa: E402

README_FIGURES = ["map_neighborhoods", "map_form", "form_by_neighborhood", "map_period_income",
                  "map_typology", "typology_profile", "map_mcmv", "map_case_studies"]


def run_tables(c, outputs_dir):
    t = outputs_dir / "tables"
    metrics.counts_by_type(c).round(1).to_csv(t / "types.csv", index=False)
    metrics.crosstab_share(c, "period3", ["Before 2000", "2000–2010", "2010–2022"]).round(1).to_csv(t / "types_by_period.csv")
    metrics.crosstab_share(c, "income", data.INCOME).round(1).to_csv(t / "types_by_income.csv")
    metrics.by_neighborhood(c).to_csv(t / "neighborhoods.csv")
    inc = metrics.income_comparison(c)
    inc.to_csv(t / "income_vs_paper.csv", index=False)
    val = metrics.validate(c)
    val.to_csv(t / "validation.csv", index=False)
    for _, r in val.iterrows():
        print(f"  {'ok ' if r['ok'] else 'FAIL'} {r['check']}: published {r['published']}, computed {r['computed']}")
    print("  income classes (reported, not enforced):",
          ", ".join(f"{r['class']} {r['published_pct']}% vs {r['computed_pct']}%" for _, r in inc.iterrows()))
    return val["ok"].all()


def run_figures(c, nb, sources_dir, outputs_dir):
    style.setup()
    f = outputs_dir / "figures"
    city = data.city_outline(nb)
    ctx = figures.Context(nb, city, water=data.load_water(sources_dir, city, outputs_dir),
                          streets=data.load_streets(city, outputs_dir))
    figures.map_neighborhoods(c, ctx, f / "map_neighborhoods.png")
    figures.map_form(c, ctx, f / "map_form.png")
    figures.form_by_neighborhood(c, f / "form_by_neighborhood.png")
    figures.map_period_income(c, ctx, f / "map_period_income.png")
    figures.map_typology(c, ctx, f / "map_typology.png")
    figures.typology_profile(c, f / "typology_profile.png")
    figures.map_mcmv(c, ctx, data.load_mcmv(sources_dir), f / "map_mcmv.png")
    figures.map_case_studies(c, ctx, f / "map_case_studies.png")
    print(f"figures written to {f}")


def run_docs(outputs_dir):
    dest = Path(__file__).parent / "docs" / "img"
    dest.mkdir(parents=True, exist_ok=True)
    for name in README_FIGURES:
        shutil.copy(outputs_dir / "figures" / f"{name}.png", dest / f"{name}.png")
    print(f"copied {len(README_FIGURES)} figures to {dest}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--only", nargs="+", choices=["tables", "figures", "docs"])
    args = p.parse_args()
    steps = args.only or ["tables", "figures", "docs"]

    dataset_dir, sources_dir, outputs_dir = config.load()
    data.fetch_dataset(dataset_dir)
    c = data.load_condominiums(dataset_dir)
    nb = data.load_neighborhoods(dataset_dir)
    print(f"{len(c)} gated communities, {len(nb)} neighborhoods")
    ok = True
    if "tables" in steps:
        ok = run_tables(c, outputs_dir)
    if "figures" in steps:
        run_figures(c, nb, sources_dir, outputs_dir)
    if "docs" in steps:
        run_docs(outputs_dir)
    if not ok:
        sys.exit("validation failed: computed values differ from the published ones (see tables/validation.csv)")


if __name__ == "__main__":
    main()
