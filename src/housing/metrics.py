"""Tables behind the paper's figures and charts, and the check against the published values."""
import pandas as pd

from .data import FORM, INCOME, TYPES

# Values published in Faccin, Almeida & Campos (2024), PosFAUUSP 31(59), e226515
PUBLISHED = {
    "total": 1024,
    "horizontal": 459, "vertical": 560, "mixed": 5,
    "neighborhoods_with_condos": 76,
    "before_2000": 585, "2000_2010": 250, "2010_2022": 189,
    "size_small": 173, "size_medium": 826, "size_large": 25,
    "tristeza": 94, "camaqua": 49,
    "type_A1": 260, "type_A2": 56, "type_B1": 58, "type_B2": 179, "type_C1-a": 148,
    "type_C1-b": 153, "type_C2": 140, "type_D": 25, "type_E": 5,
}
# Quadro 2, "% by income class" (total row)
PUBLISHED_INCOME = {"A": 8, "B": 25, "C": 47, "D": 16, "E": 3}


def counts_by_type(c):
    t = c.groupby("tipo24").agg(n=("cod", "size"), area_ha=("area", lambda a: a.sum() / 1e4),
                                median_area_m2=("area", "median"))
    t.insert(0, "description", [TYPES[k][0] for k in t.index])
    return t.reindex(list(TYPES)).reset_index()


def crosstab_share(c, col, order, by="tipo24"):
    """Share (%) of each category of `col` within each type, plus a total row."""
    t = pd.crosstab(c[by], c[col]).reindex(columns=order, fill_value=0).reindex(list(TYPES))
    t.loc["Total"] = t.sum()
    return t.div(t.sum(axis=1), axis=0).mul(100)


def by_neighborhood(c):
    t = pd.crosstab(c["bairro"], c["form"]).reindex(columns=list(FORM.values()), fill_value=0)
    t["total"] = t.sum(axis=1)
    return t.sort_values("total", ascending=False)


def validate(c):
    computed = {
        "total": len(c),
        "horizontal": int((c["tipo"] == 1).sum()),
        "vertical": int(c["tipo"].isin([2, 3]).sum()),
        "mixed": int((c["tipo"] == 4).sum()),
        "neighborhoods_with_condos": c["bairro"].nunique(),
        "before_2000": int((c["tempo"] == 1).sum()),
        "2000_2010": int((c["tempo"] == 2).sum()),
        "2010_2022": int(c["tempo"].isin([3, 4, 5]).sum()),
        "size_small": int((c["porte"] == 1).sum()),
        "size_medium": int((c["porte"] == 2).sum()),
        "size_large": int((c["porte"] == 3).sum()),
        "tristeza": int((c["bairro"] == "TRISTEZA").sum()),
        "camaqua": int((c["bairro"] == "CAMAQUÃ").sum()),
    }
    computed.update({f"type_{k}": int((c["tipo24"] == k).sum()) for k in TYPES})
    rows = [{"check": k, "published": v, "computed": computed[k], "tolerance": 1,
             "ok": abs(computed[k] - v) <= 1} for k, v in PUBLISHED.items()]
    return pd.DataFrame(rows)


def income_comparison(c):
    """Income-class shares vs the paper. Reported, not enforced (see README)."""
    share = c["income"].value_counts(normalize=True).reindex(INCOME).mul(100)
    return pd.DataFrame({"class": INCOME, "published_pct": [PUBLISHED_INCOME[k] for k in INCOME],
                         "computed_pct": share.round(1).values})
