"""Figures in the project's visual identity (brand palette, Source Code Pro)."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from . import metrics, style
from .data import FAMILIES, FORM, INCOME, INCOME_LABEL, TYPES

FAMILY_COLORS = {"A": style.CAT[0], "B": style.CAT[1], "C": style.CAT[2], "D": style.CAT[3], "E": style.OTHER}
FORM_COLORS = dict(zip(FORM.values(), [style.SEQ[0], style.SEQ[2], style.SEQ[4], style.OTHER]))
PERIOD3_COLORS = {"Before 2000": style.SEQ_GREEN[0], "2000–2010": style.SEQ_GREEN[1], "2010–2022": style.SEQ_GREEN[3]}
INCOME_COLORS = dict(zip(INCOME, style.SEQ))

HEAD, FOOT = 1.5, 0.6  # inches reserved for header and footer


class Context:
    """Layers shared by the maps: city outline, neighborhoods, water, streets."""

    def __init__(self, nb, city, water=None, streets=None):
        self.nb, self.city, self.water, self.streets = nb, city, water, streets


def _map_fig(width=9.8, height=10.5, legend=0.3):
    """One map on the left, a legend column on the right."""
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([0.01, FOOT / height, 1 - legend - 0.01, 1 - (HEAD + FOOT) / height])
    return fig, ax, 1 - legend + 0.01, 1 - HEAD / height


def _points(c):
    """Condominium centroids with a marker size that grows with the gated area."""
    p = c.copy()
    p["geometry"] = c.geometry.representative_point()
    p["s"] = _size(c["area"])
    return p


def _size(area):
    return np.clip(4 + 60 * np.sqrt(np.asarray(area, float) / 40000), 4, 140)


def _base(ax, ctx, neighborhoods=True, bounds=None):
    ctx.city.plot(ax=ax, color=style.LAND, linewidth=0, zorder=0)
    if ctx.water is not None:
        ctx.water.plot(ax=ax, color=style.WATER, linewidth=0, zorder=1)
    if neighborhoods:
        ctx.nb.boundary.plot(ax=ax, color="white", linewidth=0.7, zorder=1.5)
    ctx.city.boundary.plot(ax=ax, color=style.INK, linewidth=0.7, zorder=2)
    style.map_axes(ax, ctx.city.total_bounds if bounds is None else bounds, pad=500)


def _dots(ax, p, color, zorder=3):
    ax.scatter(p.geometry.x, p.geometry.y, s=p["s"], color=color, edgecolor="white", linewidth=0.4, zorder=zorder)


def _label(ax, nb, names, fontsize=8, min_dist=0):
    """Label neighborhoods, skipping any closer than min_dist metres to one already labeled."""
    placed = []
    for name in names:
        g = nb.loc[nb["NOME"] == name, "geometry"]
        if len(g):
            pt = g.iloc[0].representative_point()
            if any(pt.distance(q) < min_dist for q in placed):
                continue
            placed.append(pt)
            ax.text(pt.x, pt.y, name.title(), ha="center", va="center", fontsize=fontsize, fontweight="semibold",
                    color=style.INK, path_effects=style.halo(), zorder=6)


def _legend(fig, handles, x, y, title=None, **kw):
    opts = dict(loc="upper left", bbox_to_anchor=(x, y), fontsize=8.5, title_fontsize=9, handlelength=1.2,
                alignment="left", labelspacing=0.7)
    opts.update(kw)
    leg = fig.legend(handles=handles, title=title, **opts)
    leg.get_title().set_fontweight("semibold")
    return leg


def _size_handles():
    return [Line2D([], [], marker="o", ls="", color=style.MUTED, mec="white", markersize=np.sqrt(_size(a)), label=lab)
            for a, lab in [(1000, "0.1 ha"), (10000, "1 ha"), (100000, "10 ha")]]


def _water_handle(ctx):
    return [Patch(facecolor=style.WATER, label="Lake Guaíba and rivers")] if ctx.water is not None else []


def map_neighborhoods(c, ctx, out):
    """Number of gated communities per neighborhood, and their location."""
    n = c.groupby("bairro").size()
    breaks, labels = [1, 7, 19, 35, 54, 10_000], ["1–6", "7–18", "19–34", "35–53", "54–94"]
    nb = ctx.nb.assign(n=ctx.nb["NOME"].map(n).fillna(0))
    nb["cls"] = pd.cut(nb["n"], breaks, labels=labels, right=False)
    fig, ax, lx, ly = _map_fig()
    _base(ax, ctx, neighborhoods=False)
    for lab, color in zip(labels, style.SEQ):
        sub = nb[nb["cls"] == lab]
        if len(sub):
            sub.plot(ax=ax, color=color, linewidth=0, zorder=1.2)
    nb.boundary.plot(ax=ax, color="white", linewidth=0.7, zorder=1.5)
    p = c.geometry.representative_point()
    ax.scatter(p.x, p.y, s=3, color=style.INK, linewidth=0, zorder=4)
    _label(ax, nb, n.sort_values(ascending=False).index[:5], min_dist=1500)
    style.scalebar(ax, km=5)
    handles = [Patch(facecolor=style.LAND, edgecolor=style.GREY, label="None")]
    handles += [Patch(facecolor=col, label=lab) for lab, col in zip(labels, style.SEQ)]
    _legend(fig, handles, lx, ly, "Gated communities\nper neighborhood")
    _legend(fig, [Line2D([], [], marker="o", ls="", color=style.INK, markersize=3, label="Gated community")]
            + _water_handle(ctx), lx, ly - 0.26)
    style.header(fig, "Gated communities by neighborhood",
                 f"Porto Alegre, 2022: {len(c):,} gated communities in {c['bairro'].nunique()} of the city's "
                 f"{len(ctx.nb)} neighborhoods.\nTristeza, Ipanema, Camaquã and Cristal, in the south zone, have the most.")
    style.footer(fig)
    style.save(fig, out)


def map_form(c, ctx, out):
    """Gated communities by building form."""
    p = _points(c)
    fig, ax, lx, ly = _map_fig()
    _base(ax, ctx)
    for form, color in FORM_COLORS.items():
        _dots(ax, p[p["form"] == form], color)
    style.scalebar(ax, km=5)
    counts = c["form"].value_counts()
    _legend(fig, [Patch(facecolor=col, label=f"{f}: {counts.get(f, 0)}") for f, col in FORM_COLORS.items()],
            lx, ly, "Building form")
    _legend(fig, _size_handles(), lx, ly - 0.2, "Gated area", labelspacing=1.2)
    style.header(fig, "Houses in the south, towers in the center-east",
                 "Gated communities by building form. Horizontal clusters (1–2 floors) dominate the south zone;\n"
                 "high-rise towers concentrate in the center-east zone.")
    style.footer(fig)
    style.save(fig, out)


def form_by_neighborhood(c, out, top=20):
    """Stacked bars: building form in the neighborhoods with most gated communities."""
    t = metrics.by_neighborhood(c).head(top).iloc[::-1]
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_axes([0.2, 0.13, 0.76, 1 - (HEAD + 1.0) / 8])
    y = np.arange(len(t))
    left = np.zeros(len(t))
    for form, color in FORM_COLORS.items():
        ax.barh(y, t[form], left=left, color=color, edgecolor="white", linewidth=1.2, height=0.62)
        left += t[form].values
    for i, total in enumerate(t["total"]):
        ax.text(total + 0.8, i, str(total), va="center", fontsize=8.5, color=style.INK)
    ax.set_yticks(y)
    ax.set_yticklabels([s.title() for s in t.index], fontsize=8.5)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Gated communities")
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, t["total"].max() * 1.08)
    _legend(fig, [Patch(facecolor=col, label=f) for f, col in FORM_COLORS.items()], 0.035, 1 - 1.15 / 8,
            ncol=4, columnspacing=1.4)
    style.header(fig, "Where the gated communities are",
                 f"The {top} neighborhoods with the most gated communities, by building form.")
    style.footer(fig)
    style.save(fig, out)


def map_period_income(c, ctx, out):
    """Two maps: period of construction and household income of the census tract (2010)."""
    p = _points(c)
    W, H = 12, 9.6
    fig = plt.figure(figsize=(W, H))
    panels = [("Period of construction", "period3", PERIOD3_COLORS, {k: k for k in PERIOD3_COLORS}),
              ("Household income of the census tract, 2010", "income", INCOME_COLORS, INCOME_LABEL)]
    for i, (title, col, colors, labels) in enumerate(panels):
        ax = fig.add_axes([0.01 + i * 0.5, 1.5 / H, 0.48, 1 - (HEAD + 0.35 + 1.5) / H])
        _base(ax, ctx)
        for key, color in colors.items():
            _dots(ax, p[p[col] == key], color)
        fig.text(0.03 + i * 0.5, 1 - (HEAD + 0.1) / H, title, fontsize=10.5, fontweight="semibold", color=style.INK, va="top")
        counts = c[col].value_counts()
        _legend(fig, [Patch(facecolor=v, label=f"{labels[k]}: {counts.get(k, 0)}") for k, v in colors.items()],
                0.03 + i * 0.5, 1.45 / H, ncol=2 if len(colors) > 3 else 1, labelspacing=0.5, columnspacing=1.2)
        if i == 0:
            style.scalebar(ax, km=5)
    period = c["period3"].value_counts(normalize=True).mul(100)
    style.header(fig, "Age and income of the gated communities",
                 f"{period['Before 2000']:.0f}% were built before 2000 and {period['2010–2022']:.0f}% between 2010 and 2022, "
                 "mostly toward the eastern and southern edges.\nIncome classes in minimum wages (MW) of 2010 (R$ 510).")
    style.footer(fig)
    style.save(fig, out)


def map_typology(c, ctx, out):
    """Small multiples: one map per typology."""
    W, H = 11, 14
    fig, axes = plt.subplots(3, 3, figsize=(W, H))
    fig.subplots_adjust(left=0.02, right=0.98, top=1 - (HEAD + 0.95) / H, bottom=FOOT / H, wspace=0.04, hspace=0.18)
    p = _points(c)
    for ax, (code, (label, fam)) in zip(axes.flat, TYPES.items()):
        ctx.city.plot(ax=ax, color=style.LAND, linewidth=0)
        if ctx.water is not None:
            ctx.water.plot(ax=ax, color=style.WATER, linewidth=0)
        style.map_axes(ax, ctx.city.total_bounds, pad=300)
        ax.scatter(p.geometry.x, p.geometry.y, s=1.5, color=style.GREY, linewidth=0, zorder=2)
        _dots(ax, p[p["tipo24"] == code], FAMILY_COLORS[fam])
        n = int((c["tipo24"] == code).sum())
        ax.set_title(f"{code}  ·  {n}", loc="left", fontsize=10.5, fontweight="semibold", color=style.INK, pad=14)
        ax.text(0.0, 1.0, label, transform=ax.transAxes, fontsize=7.5, color=style.MUTED, va="bottom")
    style.header(fig, "Nine types of gated community",
                 "Each map highlights one type of the typology of Faccin, Almeida & Campos (2024); grey dots are all\n"
                 "other gated communities. Colors group the types into apartment blocks, towers, houses, large and mixed.")
    _legend(fig, [Patch(facecolor=FAMILY_COLORS[k], label=v) for k, v in FAMILIES.items()], 0.035, 1 - (HEAD - 0.05) / H,
            ncol=5, columnspacing=1.2, fontsize=8)
    style.footer(fig)
    style.save(fig, out)


def typology_profile(c, out):
    """Per type: share by period of construction and by income class (the paper's Quadro 2)."""
    period = metrics.crosstab_share(c, "period3", list(PERIOD3_COLORS))
    income = metrics.crosstab_share(c, "income", INCOME)
    rows = list(period.index)[::-1]
    n = c["tipo24"].value_counts()
    W, H = 12, 7.4
    fig, axes = plt.subplots(1, 2, figsize=(W, H), sharey=True)
    fig.subplots_adjust(left=0.1, right=0.98, top=1 - (HEAD + 0.4) / H, bottom=1.35 / H, wspace=0.08)
    for ax, (t, colors, title, labels) in zip(axes, [
            (period, PERIOD3_COLORS, "Period of construction", {k: k for k in PERIOD3_COLORS}),
            (income, INCOME_COLORS, "Household income class of the tract, 2010", INCOME_LABEL)]):
        y = np.arange(len(rows))
        left = np.zeros(len(rows))
        for key, color in colors.items():
            w = t.loc[rows, key].values
            ax.barh(y, w, left=left, color=color, edgecolor="white", linewidth=1.2, height=0.64)
            for i, (wi, li) in enumerate(zip(w, left)):
                if wi >= 12:
                    ax.text(li + wi / 2, i, f"{wi:.0f}", ha="center", va="center", fontsize=7.5,
                            color=style.text_on(color))
            left += w
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_xticklabels(["0", "25", "50", "75", "100%"], fontsize=8)
        ax.grid(axis="y", visible=False)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.set_title(title, loc="left", fontsize=10.5, fontweight="semibold", color=style.INK, pad=10)
        ax.legend(handles=[Patch(facecolor=v, label=labels[k]) for k, v in colors.items()], loc="upper left",
                  bbox_to_anchor=(0, -0.07), ncol=3, fontsize=8, handlelength=1.1, columnspacing=1.0)
    axes[0].set_yticks(np.arange(len(rows)))
    axes[0].set_yticklabels([f"All ({len(c)})" if r == "Total" else f"{r} ({n.get(r, 0)})" for r in rows], fontsize=8.5)
    axes[0].get_yticklabels()[-1].set_fontweight("semibold")
    style.header(fig, "Who each type is built for",
                 "Share of each type by period of construction and by household income class of its census tract.\n"
                 "Towers with amenities (B2) and house clusters with amenities (C2) lean to the higher classes.")
    style.footer(fig)
    style.save(fig, out)


def map_mcmv(c, ctx, mcmv, out):
    """Gated communities, federal housing program developments and the main road structure."""
    p = _points(c)
    fig, ax, lx, ly = _map_fig()
    _base(ax, ctx, neighborhoods=False)
    if ctx.streets is not None:
        area = ctx.city.buffer(200)
        ctx.streets.clip(area).plot(ax=ax, color=style.GREY, linewidth=0.25, zorder=1.6)
        main = ctx.streets[ctx.streets["highway"].isin(["motorway", "trunk", "primary"])]
        main.clip(area).plot(ax=ax, color=style.INK, linewidth=0.9, zorder=2)
    _dots(ax, p, style.CAT[2])
    handles = [Line2D([], [], marker="o", ls="", color=style.CAT[2], mec="white", markersize=7,
                      label=f"Gated communities ({len(c):,})")]
    n_mcmv = 0
    if mcmv is not None:
        m = mcmv.clip(ctx.city)
        n_mcmv = len(m)
        ax.scatter(m.geometry.x, m.geometry.y, s=30, marker="D", color=style.CAT[1], edgecolor="white", linewidth=0.6, zorder=4)
        handles.append(Line2D([], [], marker="D", ls="", color=style.CAT[1], mec="white", markersize=6,
                              label=f"Federal housing program\ndevelopments, MCMV ({n_mcmv})"))
    handles += [Line2D([], [], color=style.INK, lw=1.2, label="Main roads"),
                Line2D([], [], color=style.GREY, lw=1, label="Other streets")] + _water_handle(ctx)
    style.scalebar(ax, km=5)
    _legend(fig, handles, lx, ly, labelspacing=1.0)
    style.header(fig, "Gated communities and social housing",
                 "Market-built gated communities follow the radial roads and the south shore; developments of the\n"
                 "federal housing program (Minha Casa Minha Vida) sit at the eastern and southern edges.")
    style.footer(fig, style.SOURCE.replace("IBGE Census 2010.", "City of Porto Alegre (MCMV); OpenStreetMap."))
    style.save(fig, out)


def map_case_studies(c, ctx, out):
    """Typology in the two pairs of neighborhoods studied in the paper."""
    pairs = [("South zone: Tristeza and Camaquã", ["TRISTEZA", "CAMAQUÃ"]),
             ("Center-east: Boa Vista and Jardim Europa", ["BOA VISTA", "JARDIM EUROPA"])]
    W, H = 12, 8.4
    fig = plt.figure(figsize=(W, H))
    for i, (title, names) in enumerate(pairs):
        ax = fig.add_axes([0.02 + i * 0.49, 1.3 / H, 0.47, 1 - (HEAD + 0.75 + 1.3) / H])
        area = ctx.nb[ctx.nb["NOME"].isin(names)]
        minx, miny, maxx, maxy = area.total_bounds
        pad = 300
        box = (minx - pad, miny - pad, maxx + pad, maxy + pad)
        ctx.nb.plot(ax=ax, color="#FAF8F5", edgecolor=style.GREY, linewidth=0.5, zorder=0)
        if ctx.water is not None:
            ctx.water.plot(ax=ax, color=style.WATER, linewidth=0, zorder=0.5)
        area.plot(ax=ax, color=style.LAND, linewidth=0, zorder=0.8)
        if ctx.streets is not None:
            ctx.streets.cx[box[0]:box[2], box[1]:box[3]].plot(ax=ax, color=style.GREY, linewidth=0.5, zorder=1)
        area.boundary.plot(ax=ax, color=style.INK, linewidth=0.9, zorder=3)
        sub = c[c["bairro"].isin(names)]
        for fam, color in FAMILY_COLORS.items():
            s = sub[sub["family"] == fam]
            if len(s):
                s.plot(ax=ax, color=color, edgecolor="white", linewidth=0.3, zorder=4)
        ax.set_xlim(box[0], box[2])
        ax.set_ylim(box[1], box[3])
        ax.set_aspect("equal")
        ax.axis("off")
        _label(ax, area, names, fontsize=9)
        top = ", ".join(f"{k} ({v})" for k, v in sub["tipo24"].value_counts().head(3).items())
        fig.text(0.03 + i * 0.49, 1 - (HEAD + 0.1) / H, title, fontsize=10.5, fontweight="semibold", color=style.INK, va="top")
        fig.text(0.03 + i * 0.49, 1 - (HEAD + 0.38) / H, f"{len(sub)} gated communities; most common: {top}",
                 fontsize=8.5, color=style.MUTED, va="top")
        style.scalebar(ax, km=0.5, loc=(0.04, 0.04))
    _legend(fig, [Patch(facecolor=FAMILY_COLORS[k], label=v) for k, v in FAMILIES.items()], 0.035, 1.15 / H,
            ncol=5, columnspacing=1.2)
    style.header(fig, "Two high-income axes, two built forms",
                 "Small house clusters dominate the south zone; towers with amenities dominate the center-east.")
    style.footer(fig, style.SOURCE.replace("IBGE Census 2010.", "OpenStreetMap."))
    style.save(fig, out)
