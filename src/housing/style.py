"""Visual identity for the figures: Source Code Pro and the brand palette.

Palette roles (checked with the dataviz palette validator against a white surface):
- CAT: categorical, fixed order, never cycled. Passes lightness band, chroma floor,
  CVD separation (worst adjacent ΔE 12.8) and the normal-vision floor. The ochre slot is
  below 3:1 contrast, so figures that use it always carry a legend and direct labels.
- SEQ, SEQ_GREEN: one-hue ordinal ramps, light to dark (monotone lightness, lightest step >= 2:1).
- OTHER: neutral for "other / mixed" categories.
"""
import matplotlib as mpl
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

from .config import ROOT

# Brand anchors (designer juji, 2025)
INK = "#383C2F"       # dark olive: text and outlines
MUTED = "#737464"     # secondary text
GRID = "#E7E1DA"
LAND = "#F4F0EA"      # map background inside the study area
GREY = "#DAD2CC"
WATER = "#CDD7C5"     # light sage
SAGE_D = "#5C704C"
ORANGE = "#D94400"
RUST = "#7B2405"

CAT = ["#5E8A3F", "#8C2F0C", "#D94400", "#D4A72C"]          # green, rust, orange, ochre
SEQ = ["#F0A07A", "#E2733D", "#C24A12", "#8E300B", "#561A03"]  # orange ramp, 5 steps
SEQ_GREEN = ["#A3BC88", "#6E9A4D", "#40682A", "#26451A"]       # green ramp, 4 steps
OTHER = "#9A958F"

SOURCE = "Source: Faccin, Almeida & Campos (2024), open dataset on Zenodo; IBGE Census 2010."
REPO = "github.com/carolinafaccin/housing-poa"


def setup():
    """Register the bundled fonts (OFL) and set the matplotlib defaults."""
    for f in (ROOT / "assets" / "fonts").glob("*.ttf"):
        fm.fontManager.addfont(str(f))
    families = {f.name for f in fm.fontManager.ttflist}
    mpl.rcParams.update({
        "font.family": "Source Code Pro" if "Source Code Pro" in families else "monospace",
        "font.size": 9.5,
        "text.color": INK,
        "axes.edgecolor": GREY,
        "axes.labelcolor": MUTED,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "legend.frameon": False,
        "savefig.facecolor": "white",
    })


def header(fig, title, subtitle=None):
    """Title and subtitle at a fixed distance (in inches) from the top edge."""
    h = fig.get_figheight()
    fig.text(0.04, 1 - 0.35 / h, title, fontsize=15, fontweight="semibold", ha="left", va="top", color=INK)
    if subtitle:
        fig.text(0.04, 1 - 0.78 / h, subtitle, fontsize=9.5, ha="left", va="top", color=MUTED, linespacing=1.5)


def footer(fig, note=SOURCE):
    """Source and repository, two lines at a fixed distance (in inches) from the bottom."""
    h = fig.get_figheight()
    fig.text(0.04, 0.22 / h, note, fontsize=7.5, ha="left", va="bottom", color=MUTED)
    fig.text(0.04, 0.06 / h, REPO, fontsize=7.5, ha="left", va="bottom", color=MUTED)


def frac(fig, inches):
    """Inches from the top edge as a figure fraction (for subplots_adjust top=...)."""
    return 1 - inches / fig.get_figheight()


def bottom(fig, inches):
    return inches / fig.get_figheight()


def text_on(fill):
    """White or ink, whichever reads better on a filled mark."""
    r, g, b = mpl.colors.to_rgb(fill)
    lum = 0.2126 * r ** 2.2 + 0.7152 * g ** 2.2 + 0.0722 * b ** 2.2
    return "white" if lum < 0.3 else INK


def halo(width=2.5):
    return [pe.withStroke(linewidth=width, foreground="white")]


def scalebar(ax, km=2, loc=(0.05, 0.05)):
    """Scale bar in projected metres, placed in axes fraction."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    x, y = x0 + (x1 - x0) * loc[0], y0 + (y1 - y0) * loc[1]
    ax.plot([x, x + km * 1000], [y, y], color=INK, lw=2, solid_capstyle="butt")
    ax.text(x + km * 500, y + (y1 - y0) * 0.012, f"{km:g} km", ha="center", va="bottom", fontsize=8, color=INK)


def map_axes(ax, bounds, pad=600):
    minx, miny, maxx, maxy = bounds
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)
    ax.set_aspect("equal")
    ax.axis("off")


def save(fig, path):
    fig.savefig(path, dpi=200)
    plt.close(fig)
