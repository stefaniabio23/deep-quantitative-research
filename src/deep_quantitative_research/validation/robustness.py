"""Robustness checks: lag sensitivity, outlier sensitivity.

These are the "does the headline result actually hold" diagnostics. A signal
that hinges on one specific lag or one extreme observation is brittle, even
if the headline metrics look good.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data_quality import Check


def check_lag_sensitivity(
    profile: list[dict[str, float | int]],
    best_lag: int,
    *,
    max_relative_drop_pct: float = 30.0,
) -> Check:
    """How much weaker is the result at adjacent lags?

    Pulls the lead-lag profile from the backtest. Compares the correlation at
    ``best_lag`` to the average of its neighbours (±1). A large gap means the
    headline rides on one magical lag.
    """
    if not profile:
        return Check(
            name="lag_sensitivity",
            verdict="warn",
            value=None,
            threshold=max_relative_drop_pct,
            explanation="no lead-lag profile available.",
        )
    by_lag = {p["lag"]: p["corr"] for p in profile if "lag" in p}
    headline = by_lag.get(best_lag)
    if headline is None or np.isnan(headline):
        return Check(
            name="lag_sensitivity",
            verdict="warn",
            value=None,
            threshold=max_relative_drop_pct,
            explanation=f"profile has no entry at lag {best_lag}.",
        )

    neighbours = [by_lag.get(best_lag - 1), by_lag.get(best_lag + 1)]
    neighbour_values = [v for v in neighbours if v is not None and not np.isnan(v)]
    if not neighbour_values:
        return Check(
            name="lag_sensitivity",
            verdict="warn",
            value=None,
            threshold=max_relative_drop_pct,
            explanation="no neighbouring lags in the profile to compare against.",
        )
    neighbour_avg = float(np.mean(neighbour_values))
    if headline == 0:
        relative_drop = 100.0 if neighbour_avg != 0 else 0.0
    else:
        relative_drop = float((abs(headline) - abs(neighbour_avg)) / abs(headline) * 100)
    relative_drop = round(relative_drop, 2)
    if relative_drop <= max_relative_drop_pct:
        verdict = "pass"
        explanation = (
            f"adjacent-lag correlation within {relative_drop:.1f}% of best; "
            "result is not riding on a single lag."
        )
    else:
        verdict = "warn"
        explanation = (
            f"adjacent-lag correlation drops {relative_drop:.1f}% from best (lag={best_lag}); "
            "result hinges on a single magical lag."
        )
    return Check(
        name="lag_sensitivity",
        verdict=verdict,
        value=relative_drop,
        threshold=max_relative_drop_pct,
        explanation=explanation,
    )


def check_outlier_sensitivity(
    predictor: pd.Series,
    target: pd.Series,
    headline_corr: float,
    *,
    drop_pct: float = 1.0,
    max_relative_drop_pct: float = 30.0,
) -> Check:
    """Drop the top ``drop_pct``% most extreme observations and re-correlate.

    A large drop in the headline correlation means the headline was the
    outliers. A small drop means the relationship is genuine.
    """
    joined = pd.concat([predictor.rename("p"), target.rename("t")], axis=1).dropna()
    n = len(joined)
    if n < 20 or np.isnan(headline_corr):
        return Check(
            name="outlier_sensitivity",
            verdict="warn",
            value=None,
            threshold=max_relative_drop_pct,
            explanation="too few observations or headline corr is NaN.",
        )

    # Identify the most extreme rows by |z(predictor)| + |z(target)|.
    z_p = (joined["p"] - joined["p"].mean()) / (joined["p"].std(ddof=0) or 1)
    z_t = (joined["t"] - joined["t"].mean()) / (joined["t"].std(ddof=0) or 1)
    extremity = z_p.abs() + z_t.abs()
    drop_n = max(1, int(round(n * (drop_pct / 100))))
    to_drop = extremity.nlargest(drop_n).index
    filtered = joined.drop(index=to_drop)

    if len(filtered) < 5:
        return Check(
            name="outlier_sensitivity",
            verdict="warn",
            value=None,
            threshold=max_relative_drop_pct,
            explanation="not enough surviving observations after drop.",
        )

    restated = float(filtered["p"].corr(filtered["t"]))
    if headline_corr == 0:
        relative_drop = 100.0 if restated != 0 else 0.0
    else:
        relative_drop = float((abs(headline_corr) - abs(restated)) / abs(headline_corr) * 100)
    relative_drop = round(relative_drop, 2)
    if relative_drop <= max_relative_drop_pct:
        verdict = "pass"
        explanation = (
            f"dropping top {drop_pct}% of extreme obs changes corr by {relative_drop:.1f}%; "
            "result is not driven by outliers."
        )
    else:
        verdict = "warn"
        explanation = (
            f"dropping top {drop_pct}% of extreme obs drops corr by {relative_drop:.1f}%; "
            "result is driven by a small number of extreme observations."
        )
    return Check(
        name="outlier_sensitivity",
        verdict=verdict,
        value=relative_drop,
        threshold=max_relative_drop_pct,
        explanation=explanation,
    )
