"""Regime-split validation check.

Splits the test window into two regimes (by default at the midpoint),
computes the predictor-target correlation on each, and flags when they
diverge materially. A signal that works in one regime and not the other is
conditionally useful, not universally true.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data_quality import Check


def _safe_corr(predictor: pd.Series, target: pd.Series) -> float:
    joined = pd.concat([predictor.rename("p"), target.rename("t")], axis=1).dropna()
    if len(joined) < 3:
        return float("nan")
    return float(joined["p"].corr(joined["t"]))


def check_regime_split(
    predictor: pd.Series,
    target: pd.Series,
    *,
    split_date: pd.Timestamp | str | None = None,
    headline_corr: float | None = None,
    max_relative_dispersion_pct: float = 50.0,
    min_samples_per_regime: int = 8,
) -> Check:
    """Split predictor and target by ``split_date`` and compare correlations.

    If ``split_date`` is None, splits at the midpoint of the shared index.
    """
    joined = pd.concat([predictor.rename("p"), target.rename("t")], axis=1).dropna()
    if len(joined) < min_samples_per_regime * 2:
        return Check(
            name="regime_split",
            verdict="warn",
            value=None,
            threshold=max_relative_dispersion_pct,
            explanation=(
                f"not enough paired observations ({len(joined)}) for a regime split; "
                f"each regime would need at least {min_samples_per_regime}."
            ),
        )

    if split_date is None:
        midpoint = joined.index[len(joined) // 2]
        split_ts = midpoint
    else:
        split_ts = pd.Timestamp(split_date)

    pre = joined[joined.index < split_ts]
    post = joined[joined.index >= split_ts]

    if len(pre) < min_samples_per_regime or len(post) < min_samples_per_regime:
        return Check(
            name="regime_split",
            verdict="warn",
            value=None,
            threshold=max_relative_dispersion_pct,
            explanation=(
                f"regime split at {split_ts.date()} produces unbalanced subsamples "
                f"(pre={len(pre)}, post={len(post)}); need {min_samples_per_regime} each."
            ),
        )

    pre_corr = _safe_corr(pre["p"], pre["t"])
    post_corr = _safe_corr(pre["p"].combine_first(post["p"]).loc[post.index], post["t"])
    # Re-compute post_corr cleanly to avoid the above accident.
    post_corr = _safe_corr(post["p"], post["t"])

    if np.isnan(pre_corr) or np.isnan(post_corr):
        return Check(
            name="regime_split",
            verdict="warn",
            value=None,
            threshold=max_relative_dispersion_pct,
            explanation="one regime produced a NaN correlation; check sample sufficiency.",
        )

    # Dispersion is how much one regime deviates from the other relative to
    # the stronger of the two. Sign disagreement caps at 100%.
    stronger = max(abs(pre_corr), abs(post_corr))
    if stronger == 0:
        dispersion = 0.0
    elif np.sign(pre_corr) != np.sign(post_corr):
        dispersion = 100.0
    else:
        dispersion = float(abs(pre_corr - post_corr) / stronger * 100)
    dispersion = round(dispersion, 2)

    if dispersion <= max_relative_dispersion_pct:
        verdict = "pass"
        explanation = (
            f"correlations stable across the split at {split_ts.date()} "
            f"(pre={pre_corr:.2f}, post={post_corr:.2f}, dispersion={dispersion:.1f}%)."
        )
    else:
        verdict = "warn"
        explanation = (
            f"correlations diverge across the split at {split_ts.date()} "
            f"(pre={pre_corr:.2f}, post={post_corr:.2f}, dispersion={dispersion:.1f}%); "
            "signal is regime-dependent."
        )
    return Check(
        name="regime_split",
        verdict=verdict,
        value=dispersion,
        threshold=max_relative_dispersion_pct,
        explanation=explanation,
    )
