"""Unit tests on synthetic data."""
import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from housing import data, metrics


def _condos():
    rows = [("A1", 2, 1, 1, 1500), ("B2", 3, 2, 2, 9000), ("C1-a", 1, 1, 3, 30000), ("C1-a", 1, 4, 3, 30000)]
    df = pd.DataFrame(rows, columns=["tipo24", "tipo", "tempo", "porte", "renda_dom10t"])
    df["cod"] = range(len(df))
    df["bairro"] = ["CENTRO", "CENTRO", "TRISTEZA", "CAMAQUÃ"]
    df["area"] = [2000, 5000, 1000, 1200]
    df["income"] = data.income_class(df["renda_dom10t"])
    df["period3"] = df["tempo"].map(data.PERIOD3)
    df["form"] = df["tipo"].map(data.FORM)
    return gpd.GeoDataFrame(df, geometry=[box(i, 0, i + 1, 1) for i in range(len(df))], crs=31982)


def test_income_class_breaks():
    s = data.income_class(pd.Series([500, 1020, 2039, 2040, 5100, 10200, 50000]))
    assert list(s) == ["E", "D", "D", "C", "B", "A", "A"]


def test_crosstab_shares_sum_to_100():
    t = metrics.crosstab_share(_condos(), "period3", ["Before 2000", "2000–2010", "2010–2022"])
    assert (t.loc[["A1", "B2", "C1-a", "Total"]].sum(axis=1).round(6) == 100).all()
    assert t.loc["C1-a", "2010–2022"] == 50


def test_by_neighborhood_totals():
    t = metrics.by_neighborhood(_condos())
    assert t.loc["CENTRO", "total"] == 2 and t["total"].sum() == 4


def test_validate_flags_differences():
    v = metrics.validate(_condos()).set_index("check")
    assert v.loc["tristeza", "computed"] == 1 and not v.loc["total", "ok"]
