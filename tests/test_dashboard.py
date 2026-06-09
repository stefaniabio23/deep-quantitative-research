"""Tests for the Phase 7 dashboard module."""

from __future__ import annotations

import base64
import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from deep_quantitative_research.backtest.kpi_backtest import KpiBacktestResult
from deep_quantitative_research.backtest.metrics import KpiMetrics
from deep_quantitative_research.dashboard import (
    confidence_strip,
    lead_lag_chart,
    render_dashboard,
    signal_vs_target_chart,
)
from deep_quantitative_research.research.signal_spec import (
    FeatureGridSpec,
    HypothesisBlock,
    Predictor,
    SignalSpec,
    Target,
    ValidationSpec,
)
from deep_quantitative_research.validation.data_quality import Check
from deep_quantitative_research.validation.gate import ValidationReport


# ---------------------------------------------------------------- charts


def _monthly_series(periods: int = 60, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-31", periods=periods, freq="ME")
    return pd.Series(rng.normal(0, 1, periods).cumsum(), index=idx)


def _is_base64_png(value: str) -> bool:
    try:
        raw = base64.b64decode(value)
    except (ValueError, TypeError):
        return False
    return raw.startswith(b"\x89PNG")


def test_signal_vs_target_chart_returns_base64_png():
    a = _monthly_series(seed=1)
    b = _monthly_series(seed=2)
    encoded = signal_vs_target_chart(a, b)
    assert _is_base64_png(encoded)


def test_signal_vs_target_chart_with_train_boundary():
    a = _monthly_series(seed=1)
    b = _monthly_series(seed=2)
    encoded = signal_vs_target_chart(a, b, train_end=pd.Timestamp("2020-12-31"))
    assert _is_base64_png(encoded)


def test_signal_vs_target_chart_handles_empty():
    empty = pd.Series([], dtype=float)
    encoded = signal_vs_target_chart(empty, empty)
    assert _is_base64_png(encoded)


def test_lead_lag_chart_bars_match_profile_length():
    profile = [{"lag": k, "corr": 0.1 * k - 0.3} for k in range(-3, 4)]
    encoded = lead_lag_chart(profile)
    assert _is_base64_png(encoded)


def test_lead_lag_chart_empty_profile_renders_placeholder():
    encoded = lead_lag_chart([])
    assert _is_base64_png(encoded)


@pytest.mark.parametrize("tier", ["low", "medium", "high"])
def test_confidence_strip_each_tier(tier):
    encoded = confidence_strip(tier)
    assert _is_base64_png(encoded)


def test_confidence_strip_unknown_tier_defaults_to_low():
    encoded = confidence_strip("nope")
    assert _is_base64_png(encoded)


# ---------------------------------------------------------------- dashboard


def _signal_spec() -> SignalSpec:
    return SignalSpec(
        signal_id="dash-test",
        signal_name="Dashboard Test Signal",
        hypothesis=HypothesisBlock(
            statement="Predictor leads target by one quarter.",
            target_variable="y",
            expected_direction="positive",
            expected_lag_periods=[1],
        ),
        target=Target(dataset_id="target-ds", field="y", cadence="quarterly"),
        predictors=[
            Predictor(
                dataset_id="pred-ds",
                field="x",
                cadence="quarterly",
                variable_type="count",
                default_aggregation="sum",
                transforms=["raw"],
                lags=[0, 1],
            )
        ],
        feature_grid=FeatureGridSpec(
            mode="controlled",
            max_features=4,
            max_lags=2,
            multiple_testing_correction=True,
            pre_specified_feature="pred-ds::raw::lag_1",
        ),
        validation=ValidationSpec(
            train_period="2018-03-31/2021-12-31",
            test_period="2022-03-31/2025-09-30",
            walk_forward=True,
        ),
        outputs={"signal_card": True, "dashboard": True},
    )


def _backtest_result(spec: SignalSpec) -> KpiBacktestResult:
    train = KpiMetrics(
        correlation=0.55,
        rank_correlation=0.5,
        directional_accuracy=0.7,
        mae=12.0,
        mape=float("nan"),
        rmse=14.0,
        hit_rate=0.7,
        sample_size=16,
    )
    test = KpiMetrics(
        correlation=0.33,
        rank_correlation=0.31,
        directional_accuracy=0.6,
        mae=15.0,
        mape=float("nan"),
        rmse=18.0,
        hit_rate=0.6,
        sample_size=14,
    )
    return KpiBacktestResult(
        mode="kpi_prediction",
        signal_id=spec.signal_id,
        target="y",
        best_feature="pred-ds::raw::lag_1",
        train_period=spec.validation.train_period,
        test_period=spec.validation.test_period,
        metrics_train=train,
        metrics_test=test,
        lead_lag=[{"lag": 0, "corr": 0.33}, {"lag": 1, "corr": 0.15}, {"lag": 2, "corr": 0.05}],
        oos_degradation_pct=40.0,
        survives_oos=True,
        notes="Recovered planted lag.",
    )


def _validation_report(spec: SignalSpec) -> ValidationReport:
    return ValidationReport(
        signal_id=spec.signal_id,
        checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        checks=[
            Check(name="sample_size", verdict="warn", value=14, threshold={}, explanation="14 is enough for low only."),
            Check(name="missingness", verdict="pass", value=0.0, threshold={}, explanation="no NaNs."),
            Check(name="lag_sensitivity", verdict="warn", value=42.0, threshold=30.0, explanation="adjacent lag drops 42%."),
        ],
        confidence_cap="medium",
        binding_constraint="sample_size",
        relationship_type="proxy",
        recommended_next_iterations=["Extend training history.", "Add a regime split."],
        registry_commit="abc123def",
    )


def test_render_dashboard_returns_self_contained_html():
    spec = _signal_spec()
    backtest = _backtest_result(spec)
    validation = _validation_report(spec)
    target = _monthly_series(seed=3)
    predictor = _monthly_series(seed=4)
    html = render_dashboard(
        spec,
        backtest,
        validation,
        target_series=target,
        predictor_series=predictor,
        cadence_audits=[
            {"dataset_id": "target-ds", "source_cadence": "quarterly", "target_cadence": "quarterly", "aggregation": "sum", "periods_created": 30, "partial_periods_dropped": 0},
            {"dataset_id": "pred-ds", "source_cadence": "monthly", "target_cadence": "quarterly", "aggregation": "sum", "periods_created": 30, "partial_periods_dropped": 0},
        ],
    )

    assert html.startswith("<!doctype html>")
    assert "<style>" in html
    assert "data:image/png;base64," in html  # charts embedded inline
    assert "dash-test" in html
    assert "Dashboard Test Signal" in html
    assert "Confidence cap: Medium" in html
    assert "Binding constraint: sample_size" in html
    assert "pred-ds::raw::lag_1" in html
    assert "Extend training history." in html
    # All five canonical sections present
    for h2 in ["Hypothesis", "Predictor vs target", "Lead-lag profile", "Backtest metrics", "Validation checks", "Cadence rollup", "Caveats", "Next iteration"]:
        assert f"<h2>{h2}</h2>" in html or h2 in html


def test_render_dashboard_no_caveats_renders_placeholder():
    spec = _signal_spec()
    backtest = _backtest_result(spec)
    validation = ValidationReport(
        signal_id=spec.signal_id,
        checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        checks=[Check(name="sample_size", verdict="pass", value=200, threshold={}, explanation="ok.")],
        confidence_cap="high",
        binding_constraint=None,
        relationship_type="proxy",
        recommended_next_iterations=[],
    )
    target = _monthly_series(seed=5)
    predictor = _monthly_series(seed=6)
    html = render_dashboard(
        spec, backtest, validation,
        target_series=target, predictor_series=predictor,
    )
    assert "no caveats flagged" in html
    assert "no next iteration recorded" in html


def test_render_dashboard_xss_escape_in_signal_name():
    spec = _signal_spec()
    spec.signal_name = "<script>alert(1)</script>"
    backtest = _backtest_result(spec)
    validation = _validation_report(spec)
    target = _monthly_series(seed=7)
    predictor = _monthly_series(seed=8)
    html = render_dashboard(
        spec, backtest, validation,
        target_series=target, predictor_series=predictor,
    )
    assert "<script>alert" not in html
    assert "&lt;script&gt;alert" in html
