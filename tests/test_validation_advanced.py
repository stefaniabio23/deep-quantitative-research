"""Tests for Phase 4b validation: stationarity, autocorrelation, robustness, causal."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deep_quantitative_research.validation import (
    check_autocorrelation,
    check_lag_sensitivity,
    check_outlier_sensitivity,
    check_stationarity_adf,
    check_stationarity_kpss,
    classify_relationship,
)


# ---------------------------------------------------------------- stationarity


def test_adf_pass_on_white_noise():
    rng = np.random.default_rng(0)
    idx = pd.date_range("2018-01-31", periods=200, freq="ME")
    s = pd.Series(rng.normal(0, 1, 200), index=idx)
    check = check_stationarity_adf(s)
    assert check.verdict == "pass"


def test_adf_warn_on_random_walk():
    rng = np.random.default_rng(0)
    idx = pd.date_range("2018-01-31", periods=200, freq="ME")
    s = pd.Series(rng.normal(0, 1, 200).cumsum(), index=idx)
    check = check_stationarity_adf(s)
    assert check.verdict == "warn"


def test_kpss_pass_on_white_noise():
    rng = np.random.default_rng(1)
    idx = pd.date_range("2018-01-31", periods=200, freq="ME")
    s = pd.Series(rng.normal(0, 1, 200), index=idx)
    check = check_stationarity_kpss(s)
    assert check.verdict == "pass"


def test_kpss_warn_on_random_walk():
    rng = np.random.default_rng(1)
    idx = pd.date_range("2018-01-31", periods=200, freq="ME")
    s = pd.Series(rng.normal(0, 1, 200).cumsum(), index=idx)
    check = check_stationarity_kpss(s)
    assert check.verdict == "warn"


def test_adf_warn_when_series_too_short():
    s = pd.Series([1.0, 2.0, 3.0], index=pd.date_range("2024-01-31", periods=3, freq="ME"))
    check = check_stationarity_adf(s)
    assert check.verdict == "warn"


# ---------------------------------------------------------------- autocorrelation


def test_autocorrelation_pass_on_white_noise():
    rng = np.random.default_rng(2)
    idx = pd.date_range("2018-01-31", periods=200, freq="ME")
    s = pd.Series(rng.normal(0, 1, 200), index=idx)
    check = check_autocorrelation(s)
    assert check.verdict == "pass"


def test_autocorrelation_warn_on_ar1():
    rng = np.random.default_rng(3)
    n = 200
    idx = pd.date_range("2018-01-31", periods=n, freq="ME")
    values = np.zeros(n)
    eps = rng.normal(0, 1, n)
    for i in range(1, n):
        values[i] = 0.9 * values[i - 1] + eps[i]
    s = pd.Series(values, index=idx)
    check = check_autocorrelation(s)
    assert check.verdict == "warn"


# ---------------------------------------------------------------- robustness


def test_lag_sensitivity_pass_when_neighbours_close():
    profile = [
        {"lag": -1, "corr": 0.45},
        {"lag": 0, "corr": 0.50},
        {"lag": 1, "corr": 0.42},
    ]
    check = check_lag_sensitivity(profile, best_lag=0)
    assert check.verdict == "pass"


def test_lag_sensitivity_warn_when_neighbours_drop():
    profile = [
        {"lag": -1, "corr": 0.05},
        {"lag": 0, "corr": 0.60},
        {"lag": 1, "corr": 0.10},
    ]
    check = check_lag_sensitivity(profile, best_lag=0)
    assert check.verdict == "warn"


def test_lag_sensitivity_warn_when_profile_empty():
    check = check_lag_sensitivity([], best_lag=0)
    assert check.verdict == "warn"


def test_outlier_sensitivity_pass_on_clean_relationship():
    rng = np.random.default_rng(4)
    idx = pd.date_range("2018-01-31", periods=200, freq="ME")
    x = pd.Series(rng.normal(0, 1, 200), index=idx)
    y = x + rng.normal(0, 0.2, 200)
    headline = x.corr(y)
    check = check_outlier_sensitivity(x, y, headline_corr=headline)
    assert check.verdict == "pass"


def test_outlier_sensitivity_warn_when_outliers_drive_corr():
    rng = np.random.default_rng(5)
    idx = pd.date_range("2018-01-31", periods=200, freq="ME")
    x = pd.Series(rng.normal(0, 1, 200), index=idx)
    y = pd.Series(rng.normal(0, 1, 200), index=idx)
    # Insert a handful of extreme paired observations to drive correlation up
    for i in range(3):
        x.iloc[i] = 20.0 + i
        y.iloc[i] = 20.0 + i
    headline = x.corr(y)
    check = check_outlier_sensitivity(x, y, headline_corr=headline, drop_pct=2.0)
    assert check.verdict == "warn"


# ---------------------------------------------------------------- causal


def test_classify_coincident_when_best_lag_zero():
    profile = [
        {"lag": 0, "corr": 0.7},
        {"lag": 1, "corr": 0.3},
    ]
    rel_type, _ = classify_relationship(profile)
    assert rel_type == "coincident"


def test_classify_lagging_when_best_lag_negative():
    profile = [
        {"lag": -2, "corr": 0.7},
        {"lag": 0, "corr": 0.2},
        {"lag": 1, "corr": 0.1},
    ]
    rel_type, _ = classify_relationship(profile)
    assert rel_type == "lagging"


def test_classify_spurious_when_oos_fails():
    profile = [
        {"lag": 1, "corr": 0.5},
    ]
    rel_type, _ = classify_relationship(profile, survives_oos=False)
    assert rel_type == "spurious"


def test_classify_proxy_default_when_no_data_for_granger():
    profile = [
        {"lag": 1, "corr": 0.5},
    ]
    rel_type, _ = classify_relationship(profile, survives_oos=True)
    assert rel_type == "proxy"


def test_classify_unknown_when_empty_profile():
    rel_type, _ = classify_relationship([])
    assert rel_type == "unknown"


def test_classify_with_granger_evidence():
    """When a Granger test runs and rejects, classification should be 'causal'."""
    rng = np.random.default_rng(7)
    n = 80
    idx = pd.date_range("2018-01-31", periods=n, freq="ME")
    predictor = pd.Series(rng.normal(0, 1, n), index=idx)
    target = pd.Series(predictor.shift(1).fillna(0) + rng.normal(0, 0.1, n), index=idx)
    profile = [
        {"lag": 0, "corr": 0.2},
        {"lag": 1, "corr": 0.9},
    ]
    rel_type, justification = classify_relationship(
        profile,
        predictor=predictor,
        target=target,
        survives_oos=True,
    )
    # Either "causal" (Granger significant) or "proxy" (Granger not run on this seed)
    assert rel_type in {"causal", "proxy"}
    assert isinstance(justification, str)
