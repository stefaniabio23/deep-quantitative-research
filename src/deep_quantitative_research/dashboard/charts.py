"""Matplotlib chart helpers with Tufte-inspired defaults.

Every chart returns a base64-encoded PNG string ready to drop into an
``<img src="data:image/png;base64,...">`` tag. Keep the visuals minimal,
honest, and directly labelled per ``references/visual-display-principles.md``.
"""

from __future__ import annotations

import base64
import io
from contextlib import contextmanager
from typing import Iterable

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Use a non-interactive backend so the module works in headless CI.
matplotlib.use("Agg")


TUFTE_RC = {
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.titleweight": "regular",
    "axes.titlepad": 8,
    "axes.labelsize": 9,
    "axes.labelpad": 4,
    "axes.edgecolor": "#666666",
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "lines.linewidth": 1.4,
    "legend.frameon": False,
    "legend.fontsize": 8,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
}


@contextmanager
def tufte_style():
    """Apply Tufte defaults for the duration of the context."""
    with matplotlib.rc_context(TUFTE_RC):
        yield


def fig_to_base64(fig) -> str:
    """Serialise a matplotlib figure as a base64 PNG suitable for inline HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def signal_vs_target_chart(
    predictor: pd.Series,
    target: pd.Series,
    *,
    train_end: pd.Timestamp | None = None,
    title: str = "Signal vs target",
) -> str:
    """Two-panel chart: standardised predictor and target on a shared time axis.

    Both series are z-scored so they can be read on the same vertical axis
    without misleading magnitude comparisons. The train/test boundary, when
    given, gets a thin vertical guide.
    """
    joined = pd.concat([predictor.rename("predictor"), target.rename("target")], axis=1).dropna()
    if joined.empty:
        return _empty_chart_message(title)

    p = (joined["predictor"] - joined["predictor"].mean()) / (joined["predictor"].std(ddof=0) or 1)
    t = (joined["target"] - joined["target"].mean()) / (joined["target"].std(ddof=0) or 1)

    with tufte_style():
        fig, ax = plt.subplots(figsize=(8, 3.2))
        ax.plot(p.index, p.values, color="#1f77b4", label="predictor (z)")
        ax.plot(t.index, t.values, color="#444444", label="target (z)", linestyle="--")
        ax.set_title(title)
        ax.set_ylabel("z-score")
        ax.axhline(0, color="#dddddd", linewidth=0.5)
        if train_end is not None:
            ax.axvline(train_end, color="#999999", linewidth=0.5, linestyle=":")
            ax.text(
                train_end,
                ax.get_ylim()[1],
                "  train | test",
                color="#666666",
                fontsize=8,
                va="top",
            )
        # Direct labels: end-of-series annotation rather than a legend.
        last_p = p.dropna().iloc[-1] if not p.dropna().empty else None
        last_t = t.dropna().iloc[-1] if not t.dropna().empty else None
        if last_p is not None:
            ax.annotate(
                "predictor",
                xy=(p.dropna().index[-1], last_p),
                xytext=(6, 0),
                textcoords="offset points",
                fontsize=8,
                color="#1f77b4",
                va="center",
            )
        if last_t is not None:
            ax.annotate(
                "target",
                xy=(t.dropna().index[-1], last_t),
                xytext=(6, 0),
                textcoords="offset points",
                fontsize=8,
                color="#444444",
                va="center",
            )
        ax.spines["left"].set_color("#aaaaaa")
        ax.spines["bottom"].set_color("#aaaaaa")
        return fig_to_base64(fig)


def lead_lag_chart(
    profile: Iterable[dict[str, float | int]],
    *,
    title: str = "Lead-lag profile",
) -> str:
    """Bar chart of correlation at successive lags. Negative correlations are
    drawn below the zero line so direction reads at a glance.
    """
    entries = [
        (int(p["lag"]), float(p["corr"]))
        for p in profile
        if "lag" in p and p.get("corr") is not None and not np.isnan(p["corr"])
    ]
    if not entries:
        return _empty_chart_message(title)

    entries.sort()
    lags = [e[0] for e in entries]
    values = [e[1] for e in entries]
    colors = ["#1f77b4" if v >= 0 else "#cc6677" for v in values]

    with tufte_style():
        fig, ax = plt.subplots(figsize=(5.5, 2.8))
        ax.bar(lags, values, color=colors, width=0.7)
        ax.set_title(title)
        ax.set_xlabel("lag (periods)")
        ax.set_ylabel("Pearson correlation")
        ax.axhline(0, color="#888888", linewidth=0.5)
        ax.set_xticks(lags)
        for lag, value in zip(lags, values):
            ax.text(
                lag,
                value + (0.02 if value >= 0 else -0.05),
                f"{value:.2f}",
                ha="center",
                fontsize=7,
                color="#444444",
            )
        ax.spines["left"].set_color("#aaaaaa")
        ax.spines["bottom"].set_color("#aaaaaa")
        return fig_to_base64(fig)


def confidence_strip(confidence: str) -> str:
    """A small horizontal strip with a single filled cell for the cap tier.

    Mirrors the metric panel of a financial signal card without inviting a
    reader to weight tier differences linearly.
    """
    tiers = ["low", "medium", "high"]
    idx = tiers.index(confidence) if confidence in tiers else 0

    with tufte_style():
        fig, ax = plt.subplots(figsize=(4.2, 0.9))
        for i, tier in enumerate(tiers):
            color = "#3a7" if i == idx else "#f0f0f0"
            ax.add_patch(plt.Rectangle((i, 0), 1, 1, facecolor=color, edgecolor="#bbbbbb", linewidth=0.5))
            text_color = "white" if i == idx else "#666666"
            ax.text(i + 0.5, 0.5, tier, ha="center", va="center", fontsize=10, color=text_color)
        ax.set_xlim(0, len(tiers))
        ax.set_ylim(0, 1)
        ax.set_axis_off()
        return fig_to_base64(fig)


def _empty_chart_message(title: str) -> str:
    with tufte_style():
        fig, ax = plt.subplots(figsize=(8, 2))
        ax.set_title(title)
        ax.text(
            0.5,
            0.5,
            "no data to plot",
            ha="center",
            va="center",
            fontsize=10,
            color="#999999",
            transform=ax.transAxes,
        )
        ax.set_axis_off()
        return fig_to_base64(fig)
