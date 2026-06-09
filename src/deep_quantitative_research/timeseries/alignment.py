"""Release lag application and period-aware alignment helpers."""

from __future__ import annotations

import pandas as pd


def apply_release_lag(series: pd.Series, release_lag_days: int) -> pd.Series:
    """Shift each observation forward by ``release_lag_days`` days.

    A value timestamped T was only observable at T + release_lag_days. The
    shift moves the index, not the values; the resulting series is aligned
    to "first-knowable" dates and is safe to join against a target series
    without lookahead.
    """
    if release_lag_days < 0:
        raise ValueError("release_lag_days must be non-negative")
    if release_lag_days == 0:
        return series.copy()
    shifted = series.copy()
    shifted.index = shifted.index + pd.Timedelta(days=release_lag_days)
    return shifted


def period_index(series: pd.Series, cadence: str) -> pd.Series:
    """Snap the index to the period-end timestamp for the given cadence.

    Used after release-lag shift to re-align observations to the cadence
    grid so they join cleanly against rolled-up target series.
    """
    # Period frequency aliases (no E suffix); distinct from resample aliases.
    period_rule = {
        "weekly": "W",
        "monthly": "M",
        "quarterly": "Q",
        "annual": "Y",
    }.get(cadence)
    if period_rule is None:
        return series.copy()
    snapped = series.copy()
    snapped.index = snapped.index.to_period(period_rule).to_timestamp(how="end").normalize()
    return snapped
