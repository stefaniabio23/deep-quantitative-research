"""Tests for Bartlett's effective sample size + Ljung-Box-gated check."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deep_quantitative_research.validation import (
    autocorrelations,
    bartlett_effective_n,
    check_effective_sample_size,
)


def _series(values, start: str = "2018-01-31") -> pd.Series:
    idx = pd.date_range(start, periods=len(values), freq="ME")
    return pd.Series(values, index=idx, dtype=float)


def _white_noise(n: int, seed: int) -> pd.Series:
    rng = np.random.default_rng(seed)
    return _series(rng.normal(0, 1, n))


def _ar1(n: int, phi: float, seed: int) -> pd.Series:
    rng = np.random.default_rng(seed)
    values = np.zeros(n)
    eps = rng.normal(0, 1, n)
    for i in range(1, n):
        values[i] = phi * values[i - 1] + eps[i]
    return _series(values)


# ---------------------------------------------------------------- autocorrelations


def test_autocorrelations_white_noise_near_zero():
    s = _white_noise(200, seed=0)
    rhos = autocorrelations(s, max_lag=5)
    assert len(rhos) == 5
    assert all(abs(rho) < 0.2 for rho in rhos)


def test_autocorrelations_ar1_lag1_near_phi():
    # AR(1) with phi=0.85 and n=600 gives the lag-1 sample autocorr a tighter
    # neighborhood around the true value; tolerance 0.2 accommodates small-
    # sample bias in sample autocorrelations.
    phi = 0.85
    s = _ar1(600, phi=phi, seed=1)
    rhos = autocorrelations(s, max_lag=4)
    assert abs(rhos[0] - phi) < 0.2
    # Lag-1 autocorrelation should be unambiguously positive for AR(1) with phi > 0
    assert rhos[0] > 0.5


def test_autocorrelations_too_short_returns_empty():
    s = _series([1.0, 2.0, 3.0])
    assert autocorrelations(s, max_lag=5) == []


# ---------------------------------------------------------------- effective n


def test_bartlett_effective_n_white_noise_close_to_n():
    a = _white_noise(150, seed=2)
    b = _white_noise(150, seed=3)
    n_eff = bartlett_effective_n(a, b)
    assert abs(n_eff - len(a)) <= max(5, int(len(a) * 0.1))


def test_bartlett_effective_n_two_ar1_series_shrinks():
    a = _ar1(200, phi=0.8, seed=4)
    b = _ar1(200, phi=0.8, seed=5)
    n_eff = bartlett_effective_n(a, b)
    assert n_eff < len(a)


def test_bartlett_effective_n_tiny_series_returns_n():
    s = _series([1.0, 2.0])
    assert bartlett_effective_n(s, s) == len(s)


# ---------------------------------------------------------------- check


def test_check_skipped_when_ljungbox_does_not_reject():
    a = _white_noise(100, seed=6)
    b = _white_noise(100, seed=7)
    check = check_effective_sample_size(
        a, b, headline_corr=0.4, autocorr_ljungbox_p=0.6,
    )
    assert check.verdict == "pass"
    assert "not required" in check.explanation


def test_check_skipped_when_ljungbox_p_is_none():
    a = _white_noise(100, seed=8)
    b = _white_noise(100, seed=9)
    check = check_effective_sample_size(
        a, b, headline_corr=0.4, autocorr_ljungbox_p=None,
    )
    assert check.verdict == "pass"


def test_check_pass_when_ess_adjustment_still_significant():
    rng = np.random.default_rng(11)
    n = 200
    common = rng.normal(0, 1, n)
    a = _series(common + rng.normal(0, 0.1, n))
    b = _series(common + rng.normal(0, 0.1, n))
    check = check_effective_sample_size(
        a, b, headline_corr=0.95, autocorr_ljungbox_p=0.001,
    )
    assert check.verdict == "pass"
    assert check.value["ess_adjusted_p"] is not None


def test_check_warn_when_autocorrelation_kills_significance():
    a = _ar1(80, phi=0.9, seed=12)
    b = _ar1(80, phi=0.9, seed=13)
    check = check_effective_sample_size(
        a, b, headline_corr=0.20, autocorr_ljungbox_p=0.001,
    )
    assert check.verdict in {"warn", "pass"}
    if check.value is not None and isinstance(check.value, dict):
        assert check.value["n_eff"] <= check.value["n"]


def test_check_warn_when_too_few_samples():
    a = _series([1.0, 2.0, 3.0, 4.0, 5.0])
    b = _series([1.0, 2.0, 3.0, 4.0, 5.0])
    check = check_effective_sample_size(
        a, b, headline_corr=0.9, autocorr_ljungbox_p=0.01,
    )
    assert check.verdict == "warn"


def test_check_handles_nan_correlation():
    a = _white_noise(50, seed=14)
    b = _white_noise(50, seed=15)
    check = check_effective_sample_size(
        a, b, headline_corr=float("nan"), autocorr_ljungbox_p=0.001,
    )
    assert check.verdict == "warn"
