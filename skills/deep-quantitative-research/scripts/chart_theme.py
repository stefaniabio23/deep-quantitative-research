"""
Shared chart theme for deep-quant-research.

Usage:
    from chart_theme import apply_theme, COLORS, save_chart
    apply_theme()
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path

COLORS = {
    "blue":       "#2563eb",
    "red":        "#dc2626",
    "green":      "#16a34a",
    "orange":     "#ea580c",
    "purple":     "#7c3aed",
    "teal":       "#0891b2",
    "positive":   "#16a34a",
    "negative":   "#dc2626",
    "neutral":    "#6b7280",
    "warning":    "#d97706",
    "upstream":   "#dc2626",
    "downstream": "#f59e0b",
    "receptor":   "#3b82f6",
    "immune":     "#10b981",
    "bg":         "#f7f5f0",
    "grid":       "#e0ddd8",
    "muted":      "#888888",
}

PALETTE = [
    COLORS["blue"], COLORS["red"], COLORS["green"],
    COLORS["orange"], COLORS["purple"], COLORS["teal"],
]

SIZES = {
    "single": (10, 6),
    "double": (14, 6),
    "triple": (18, 6),
    "tall":   (12, 8),
    "small":  (7, 4.5),
}


def apply_theme():
    mpl.rcParams.update({
        "figure.facecolor":   COLORS["bg"],
        "axes.facecolor":     COLORS["bg"],
        "axes.grid":          True,
        "axes.grid.axis":     "y",
        "grid.color":         COLORS["grid"],
        "grid.linestyle":     "--",
        "grid.linewidth":     0.6,
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.spines.left":   True,
        "axes.spines.bottom": True,
        "axes.linewidth":     0.8,
        "axes.edgecolor":     COLORS["grid"],
        "xtick.major.size":   0,
        "ytick.major.size":   0,
        "font.family":        "sans-serif",
        "font.size":          9,
        "axes.titlesize":     12,
        "axes.titleweight":   "bold",
        "axes.titlepad":      10,
        "axes.labelsize":     9,
        "xtick.labelsize":    8.5,
        "ytick.labelsize":    8.5,
        "legend.fontsize":    8.5,
        "legend.frameon":     False,
        "savefig.dpi":        150,
        "savefig.bbox":       "tight",
        "savefig.facecolor":  COLORS["bg"],
    })


def new_fig(size="single", nrows=1, ncols=1, **kwargs):
    apply_theme()
    w, h = SIZES.get(size, size)
    fig, axes = plt.subplots(nrows, ncols, figsize=(w, h), **kwargs)
    fig.patch.set_facecolor(COLORS["bg"])
    return fig, axes


def add_source(fig, text, x=0.99, y=0.01, ha="right"):
    fig.text(x, y, text, ha=ha, fontsize=7.5, color=COLORS["muted"])


def save_chart(fig, name: str, output_dir) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"chart_{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved: {path}")
    return path
