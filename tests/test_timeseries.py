"""Tests for time series transformations and cadence rollup."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deep_quantitative_research.timeseries.alignment import apply_release_lag, period_index
from deep_quantitative_research.timeseries.cadence import (
    CADENCE_RANK,
    CadenceError,
    DEFAULT_AGGREGATION,
    finer_or_equal,
    rollup,
)
from deep_quantitative_research.timeseries.transformations import (
    AVAILABLE_TRANSFORMS,
    apply_transform,
    diff,
    lag,
    pct_change,
    rolling_mean,
    yoy_1y,
    zscore,
)


@pytest.fixture
def monthly_series() -> pd.Series:
    idx = pd.date_range("2020-01-31", periods=36, freq="ME")
    values = np.arange(1, 37, dtype=float)
    return pd.Series(values, index=idx, name="value")


# ---------------------------------------------------------------- transforms


def test_raw_and_diff(monthly_series):
    assert (apply_transform(monthly_series, "raw") == monthly_series).all()
    assert diff(monthly_series, periods=1).iloc[1:].iloc[0] == pytest.approx(1.0)


def test_pct_change(monthly_series):
    out = pct_change(monthly_series, periods=1)
    assert np.isnan(out.iloc[0])
    assert out.iloc[1] == pytest.approx(1.0)  # (2-1)/1


def test_yoy_1y_monthly(monthly_series):
    out = yoy_1y(monthly_series)
    # 12-period pct_change for monthly data: value at idx 12 = 13, base = 1, so 12.0
    assert out.iloc[12] == pytest.approx(12.0)


def test_rolling_mean(monthly_series):
    out = rolling_mean(monthly_series, window=3)
    # First two are NaN, third is (1+2+3)/3 = 2.0
    assert np.isnan(out.iloc[0])
    assert out.iloc[2] == pytest.approx(2.0)


def test_zscore_window(monthly_series):
    out = zscore(monthly_series, window=12)
    # First non-nan z should be 0 ± something; std > 0 means real number
    assert not np.isnan(out.iloc[11])


def test_lag_shifts_values(monthly_series):
    shifted = lag(monthly_series, periods=2)
    # value at idx 2 equals original at idx 0
    assert shifted.iloc[2] == monthly_series.iloc[0]


def test_apply_transform_rejects_unknown(monthly_series):
    with pytest.raises(KeyError):
        apply_transform(monthly_series, "no_such_transform")


def test_available_transforms_includes_canon():
    for name in ["raw", "diff", "yoy_1y", "rolling_mean_3", "zscore_12", "rolling_sum_12"]:
        assert name in AVAILABLE_TRANSFORMS


# ---------------------------------------------------------------- cadence


def test_cadence_rank_monotonic():
    assert CADENCE_RANK["daily"] < CADENCE_RANK["monthly"] < CADENCE_RANK["annual"]


def test_finer_or_equal():
    assert finer_or_equal("daily", "monthly")
    assert finer_or_equal("monthly", "monthly")
    assert not finer_or_equal("annual", "monthly")


def test_default_aggregation_table():
    assert DEFAULT_AGGREGATION["flow"] == "sum"
    assert DEFAULT_AGGREGATION["stock"] == "last"
    assert DEFAULT_AGGREGATION["price"] == "last"
    assert DEFAULT_AGGREGATION["sentiment"] == "mean"


def test_rollup_daily_to_monthly_flow():
    idx = pd.date_range("2024-01-01", periods=92, freq="D")  # 3 months
    s = pd.Series(np.ones(92), index=idx)
    rolled, audit = rollup(s, source_cadence="daily", target_cadence="monthly", variable_type="flow")
    assert audit["aggregation"] == "sum"
    # Jan has 31, Feb has 29 (2024 leap), then partial dropped for Mar
    assert rolled.iloc[0] == pytest.approx(31.0)
    assert audit["partial_periods_dropped"] in {0, 1}


def test_rollup_stock_uses_last():
    idx = pd.date_range("2024-01-01", periods=90, freq="D")
    s = pd.Series(np.arange(1, 91, dtype=float), index=idx)
    rolled, audit = rollup(s, source_cadence="daily", target_cadence="monthly", variable_type="stock")
    assert audit["aggregation"] == "last"
    assert rolled.iloc[0] == pytest.approx(31.0)  # last value in January


def test_rollup_refuses_to_sum_stock():
    idx = pd.date_range("2024-01-01", periods=90, freq="D")
    s = pd.Series(np.ones(90), index=idx)
    with pytest.raises(CadenceError):
        rollup(
            s,
            source_cadence="daily",
            target_cadence="monthly",
            variable_type="stock",
            aggregation="sum",
        )


def test_rollup_refuses_to_sum_price_unless_overridden():
    idx = pd.date_range("2024-01-01", periods=90, freq="D")
    s = pd.Series(np.ones(90), index=idx)
    with pytest.raises(CadenceError):
        rollup(s, source_cadence="daily", target_cadence="monthly", variable_type="price", aggregation="sum")
    # Override allowed
    rolled, _ = rollup(
        s,
        source_cadence="daily",
        target_cadence="monthly",
        variable_type="price",
        aggregation="sum",
        aggregation_overridden=True,
    )
    assert rolled.iloc[0] == pytest.approx(31.0)


def test_rollup_refuses_to_average_flow():
    idx = pd.date_range("2024-01-01", periods=90, freq="D")
    s = pd.Series(np.ones(90), index=idx)
    with pytest.raises(CadenceError):
        rollup(s, source_cadence="daily", target_cadence="monthly", variable_type="flow", aggregation="mean")


def test_rollup_refuses_to_roll_down():
    idx = pd.date_range("2024-01-31", periods=12, freq="ME")
    s = pd.Series(np.ones(12), index=idx)
    with pytest.raises(CadenceError):
        rollup(s, source_cadence="annual", target_cadence="monthly", variable_type="flow")


# ---------------------------------------------------------------- alignment


def test_apply_release_lag_shifts_index():
    idx = pd.date_range("2024-01-31", periods=3, freq="ME")
    s = pd.Series([1.0, 2.0, 3.0], index=idx)
    shifted = apply_release_lag(s, release_lag_days=30)
    assert shifted.index[0] == idx[0] + pd.Timedelta(days=30)
    assert (shifted.values == s.values).all()


def test_period_index_snaps_to_month_end():
    idx = pd.to_datetime(["2024-01-15", "2024-02-20"])
    s = pd.Series([1.0, 2.0], index=idx)
    snapped = period_index(s, cadence="monthly")
    assert snapped.index[0].day == 31  # Jan 31
    assert snapped.index[1].day == 29  # Feb 2024 leap
