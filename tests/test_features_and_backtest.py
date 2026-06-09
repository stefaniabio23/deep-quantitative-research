"""Tests for the feature grid, metrics, walk-forward, and overfitting policy."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deep_quantitative_research.backtest.metrics import (
    KpiMetrics,
    kpi_metrics,
    lead_lag_profile,
    oos_degradation,
)
from deep_quantitative_research.backtest.walk_forward import walk_forward_windows
from deep_quantitative_research.features import HIGH_TIER_SEARCH_CEILING, assess as assess_overfit
from deep_quantitative_research.features.grid import build_grid
from deep_quantitative_research.research.signal_spec import (
    FeatureGridSpec,
    HypothesisBlock,
    Predictor,
    SignalSpec,
    Target,
    ValidationSpec,
)


def _spec(transforms=("raw", "yoy_1y"), lags=(0, 1), max_features=40, max_lags=3):
    return SignalSpec(
        signal_id="test-signal",
        signal_name="Test",
        hypothesis=HypothesisBlock(statement="x predicts y", target_variable="y"),
        target=Target(dataset_id="target-ds", field="y", cadence="monthly"),
        predictors=[
            Predictor(
                dataset_id="pred-ds",
                field="x",
                cadence="monthly",
                variable_type="flow",
                default_aggregation="sum",
                transforms=list(transforms),
                lags=list(lags),
            )
        ],
        feature_grid=FeatureGridSpec(
            mode="controlled",
            max_features=max_features,
            max_lags=max_lags,
            multiple_testing_correction=True,
            pre_specified_feature=None,
        ),
        validation=ValidationSpec(
            train_period="2020-01-31/2021-12-31",
            test_period="2022-01-31/2022-12-31",
        ),
    )


def _monthly(periods: int, *, start: str = "2020-01-31", seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=periods, freq="ME")
    return pd.Series(rng.normal(0, 1, periods), index=idx)


# ---------------------------------------------------------------- grid


def test_build_grid_emits_expected_columns():
    spec = _spec(transforms=("raw", "yoy_1y"), lags=(0, 1))
    series = _monthly(36)
    result = build_grid(spec, {"pred-ds": series})
    # 2 transforms × 2 lags = 4 features
    assert result.features_emitted == 4
    assert len(result.features.columns) == 4
    assert any("raw" in c for c in result.feature_names)
    assert any("yoy_1y" in c for c in result.feature_names)


def test_build_grid_respects_max_features():
    spec = _spec(transforms=("raw", "yoy_1y", "rolling_mean_3"), lags=(0, 1, 2), max_features=4)
    series = _monthly(36)
    result = build_grid(spec, {"pred-ds": series})
    assert result.features_emitted == 4
    assert result.truncated_at_max_features is True


def test_build_grid_caps_lags_by_max_lags():
    spec = _spec(transforms=("raw",), lags=(0, 1, 2, 3, 4), max_lags=2)
    series = _monthly(36)
    result = build_grid(spec, {"pred-ds": series})
    # lags capped at 2 means {0, 1, 2}
    assert result.lags == [0, 1, 2]
    assert result.features_emitted == 3


def test_build_grid_missing_predictor_raises():
    spec = _spec()
    with pytest.raises(KeyError):
        build_grid(spec, {})


# ---------------------------------------------------------------- metrics


def test_kpi_metrics_basic_perfect_correlation():
    idx = pd.date_range("2020-01-31", periods=24, freq="ME")
    target = pd.Series(np.linspace(-1, 1, 24), index=idx)
    predictor = target.copy()
    result = kpi_metrics(predictor, target)
    assert isinstance(result, KpiMetrics)
    assert result.correlation == pytest.approx(1.0, abs=1e-6)
    assert result.directional_accuracy == pytest.approx(1.0, abs=1e-6)
    assert result.mae == pytest.approx(0.0, abs=1e-6)


def test_kpi_metrics_empty_series_returns_nan_sample_zero():
    empty = pd.Series([], dtype=float)
    result = kpi_metrics(empty, empty)
    assert result.sample_size == 0
    assert np.isnan(result.correlation)


def test_lead_lag_profile_peaks_at_known_lag():
    rng = np.random.default_rng(7)
    idx = pd.date_range("2020-01-31", periods=80, freq="ME")
    base = rng.normal(0, 1, 80)
    target = pd.Series(base, index=idx)
    predictor = target.shift(-2)  # predictor leads target by 2 periods
    profile = lead_lag_profile(predictor, target, max_lag=4)
    by_lag = {p["lag"]: p["corr"] for p in profile}
    best_lag = max(by_lag, key=lambda k: by_lag[k])
    assert best_lag == 2


def test_oos_degradation_arithmetic():
    assert oos_degradation(1.0, 0.5) == pytest.approx(50.0)
    assert oos_degradation(1.0, 0.0) == pytest.approx(100.0)
    assert oos_degradation(0.0, 0.5) != oos_degradation(0.0, 0.5)  # nan


# ---------------------------------------------------------------- walk-forward


def test_walk_forward_windows_yields_expanding():
    idx = pd.date_range("2020-01-31", periods=48, freq="ME")
    windows = walk_forward_windows(
        idx,
        train_start="2020-01-31",
        train_end="2021-12-31",
        test_start="2022-01-31",
        test_end="2022-12-31",
    )
    assert len(windows) == 12
    # First window's training ends before the first test bar
    assert windows[0].train_end < windows[0].test_start
    # Train end advances as test progresses (expanding window)
    assert windows[-1].train_end > windows[0].train_end


def test_walk_forward_rejects_invalid_periods():
    idx = pd.date_range("2020-01-31", periods=24, freq="ME")
    with pytest.raises(ValueError):
        walk_forward_windows(
            idx,
            train_start="2020-01-31",
            train_end="2022-12-31",
            test_start="2020-06-30",  # overlaps train
            test_end="2021-12-31",
        )


# ---------------------------------------------------------------- overfitting


def test_overfit_pre_specified_caps_at_high():
    log = assess_overfit(
        features_tested=4,
        lags_tested=2,
        best_feature="pred-ds::raw::lag_0",
        pre_specified_feature="pred-ds::raw::lag_0",
        out_of_sample_survives=True,
        truncated_at_max_features=False,
    )
    assert log.confidence_cap == "high"
    assert log.multiple_testing_correction_needed is False


def test_overfit_huge_grid_caps_at_medium():
    log = assess_overfit(
        features_tested=HIGH_TIER_SEARCH_CEILING + 10,
        lags_tested=1,
        best_feature="discovered",
        pre_specified_feature=None,
        out_of_sample_survives=True,
        truncated_at_max_features=False,
    )
    assert log.confidence_cap == "medium"
    assert log.multiple_testing_correction_needed is True


def test_overfit_oos_fail_caps_at_low():
    log = assess_overfit(
        features_tested=4,
        lags_tested=2,
        best_feature="discovered",
        pre_specified_feature=None,
        out_of_sample_survives=False,
        truncated_at_max_features=False,
    )
    assert log.confidence_cap == "low"
