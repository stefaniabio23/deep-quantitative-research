"""Tests for the multiple-testing enforcement (Bonferroni + deflated correlation)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from deep_quantitative_research.validation import (
    bonferroni,
    check_selection_bias,
    correlation_p_value,
    deflated_correlation,
)


# ---------------------------------------------------------------- bonferroni


def test_bonferroni_all_below_threshold():
    out = bonferroni([0.001, 0.002, 0.003], alpha=0.05)
    # 0.05 / 3 = 0.0167; every p below threshold
    assert all(out)


def test_bonferroni_none_below_threshold():
    out = bonferroni([0.5, 0.6, 0.7], alpha=0.05)
    assert not any(out)


def test_bonferroni_partial():
    out = bonferroni([0.001, 0.5, 0.0005, 0.9], alpha=0.05)
    # 0.05 / 4 = 0.0125; 0.001 and 0.0005 survive
    assert out == [True, False, True, False]


def test_bonferroni_empty_returns_empty():
    assert bonferroni([], alpha=0.05) == []


# ---------------------------------------------------------------- correlation p-value


def test_correlation_p_value_perfect_correlation_is_zero():
    assert correlation_p_value(1.0, 30) == 0.0


def test_correlation_p_value_zero_correlation_is_one():
    p = correlation_p_value(0.0, 30)
    assert p == pytest.approx(1.0, abs=1e-6)


def test_correlation_p_value_decreases_with_correlation():
    assert correlation_p_value(0.5, 30) < correlation_p_value(0.2, 30)


def test_correlation_p_value_decreases_with_sample_size():
    # For the same r, larger n means more confidence that it's not chance
    assert correlation_p_value(0.4, 100) < correlation_p_value(0.4, 30)


def test_correlation_p_value_tiny_sample_returns_nan():
    assert math.isnan(correlation_p_value(0.5, 2))


# ---------------------------------------------------------------- deflated correlation


def test_deflated_correlation_one_trial_is_passthrough():
    assert deflated_correlation(0.5, 100, n_trials=1) == pytest.approx(0.5)


def test_deflated_correlation_many_trials_shrinks_headline():
    # Many trials → expected null max is large → deflated r < headline
    headline = 0.5
    deflated = deflated_correlation(headline, 60, n_trials=100)
    assert deflated < headline
    assert deflated >= 0  # never crosses sign


def test_deflated_correlation_preserves_sign_when_above_correction():
    assert deflated_correlation(-0.6, 80, n_trials=10) < 0


def test_deflated_correlation_floors_at_zero():
    # A tiny headline with huge n_trials should deflate to ~zero
    deflated = deflated_correlation(0.05, 60, n_trials=500)
    assert deflated >= 0
    assert deflated <= 0.05


# ---------------------------------------------------------------- check_selection_bias


def test_selection_bias_refuses_without_features_tested():
    check = check_selection_bias(headline_corr=0.5, sample_size=60, n_features_tested=None)
    assert check.verdict == "fail"
    assert "features_tested not logged" in check.explanation


def test_selection_bias_refuses_with_zero_features_tested():
    check = check_selection_bias(headline_corr=0.5, sample_size=60, n_features_tested=0)
    assert check.verdict == "fail"


def test_selection_bias_pre_specified_single_feature_passes():
    check = check_selection_bias(
        headline_corr=0.4, sample_size=60, n_features_tested=1, pre_specified=True,
    )
    assert check.verdict == "pass"
    assert "pre-specified" in check.explanation


def test_selection_bias_pass_when_bonferroni_clears():
    # Strong correlation + small grid + decent sample = should clear
    check = check_selection_bias(
        headline_corr=0.6, sample_size=100, n_features_tested=4,
    )
    assert check.verdict == "pass"
    assert check.value is not None
    assert check.value["deflated_r"] > 0


def test_selection_bias_warn_when_bonferroni_fails():
    # Weak correlation + large grid = should not clear
    check = check_selection_bias(
        headline_corr=0.2, sample_size=30, n_features_tested=50,
    )
    assert check.verdict == "warn"
    assert "does NOT survive Bonferroni" in check.explanation


def test_selection_bias_check_value_includes_deflated_r():
    check = check_selection_bias(
        headline_corr=0.4, sample_size=80, n_features_tested=10,
    )
    assert isinstance(check.value, dict)
    assert "deflated_r" in check.value
    assert "p" in check.value
    assert "adjusted_p" in check.value


def test_selection_bias_handles_nan_correlation():
    check = check_selection_bias(
        headline_corr=float("nan"), sample_size=60, n_features_tested=5,
    )
    assert check.verdict == "warn"
    assert "NaN" in check.explanation
