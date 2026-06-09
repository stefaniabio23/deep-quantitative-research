"""Pure time series transformations used by the feature grid.

Every transform takes a pandas Series indexed by date, returns a same-length
Series with NaN where the transform is undefined (the early periods, mostly).
"""

from __future__ import annotations

import pandas as pd


# Periods used by yoy / yo2y, keyed by inferred frequency. Falls back to
# 12 (months) when the series frequency is unknown.
_YOY_PERIODS = {"D": 365, "W": 52, "M": 12, "MS": 12, "Q": 4, "QS": 4, "A": 1, "Y": 1, "AS": 1}


def _infer_yoy(series: pd.Series) -> int:
    freq = pd.infer_freq(series.index)
    if freq is None:
        return 12
    return _YOY_PERIODS.get(freq.split("-")[0].upper(), 12)


def raw(series: pd.Series) -> pd.Series:
    return series.copy()


def diff(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.diff(periods=periods)


def pct_change(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.pct_change(periods=periods)


def mom_1p(series: pd.Series) -> pd.Series:
    return series.pct_change(periods=1)


def mom_3p(series: pd.Series) -> pd.Series:
    return series.pct_change(periods=3)


def yoy_1y(series: pd.Series) -> pd.Series:
    return series.pct_change(periods=_infer_yoy(series))


def yo2y(series: pd.Series) -> pd.Series:
    return series.pct_change(periods=_infer_yoy(series) * 2)


def rolling_mean(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def rolling_sum(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).sum()


def zscore(series: pd.Series, window: int) -> pd.Series:
    rolling = series.rolling(window=window, min_periods=window)
    mean = rolling.mean()
    std = rolling.std(ddof=0)
    return (series - mean) / std


def lag(series: pd.Series, periods: int) -> pd.Series:
    return series.shift(periods=periods)


# ---------------------------------------------------------------- registry

# Each entry: name -> callable(series) -> series. Parameterised transforms
# expose canonical names ("rolling_mean_3" rather than rolling_mean(3)).
def _builder() -> dict[str, callable]:
    out: dict[str, callable] = {
        "raw": raw,
        "diff": diff,
        "pct_change": pct_change,
        "mom_1p": mom_1p,
        "mom_3p": mom_3p,
        "yoy_1y": yoy_1y,
        "yo2y": yo2y,
    }
    for w in (3, 6):
        out[f"rolling_mean_{w}"] = lambda s, _w=w: rolling_mean(s, _w)
    for w in (3, 12):
        out[f"rolling_sum_{w}"] = lambda s, _w=w: rolling_sum(s, _w)
    for w in (12, 24):
        out[f"zscore_{w}"] = lambda s, _w=w: zscore(s, _w)
    return out


AVAILABLE_TRANSFORMS: dict[str, callable] = _builder()


def apply_transform(series: pd.Series, name: str) -> pd.Series:
    """Apply the named transform. Raises KeyError on unknown names."""
    if name not in AVAILABLE_TRANSFORMS:
        raise KeyError(
            f"unknown transform: {name!r}. Available: {sorted(AVAILABLE_TRANSFORMS)}"
        )
    return AVAILABLE_TRANSFORMS[name](series)
