"""KPI-prediction backtest orchestrator.

Takes a feature DataFrame, a target Series, and a validation block; picks the
best feature on the train window by correlation, evaluates on the test
window, computes the full metric panel + lead-lag profile + OOS degradation,
and returns a verdict block.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from ..research.signal_spec import SignalSpec
from .metrics import KpiMetrics, kpi_metrics, lead_lag_profile, oos_degradation


@dataclass
class KpiBacktestResult:
    mode: str
    signal_id: str
    target: str
    best_feature: str
    train_period: str
    test_period: str
    metrics_train: KpiMetrics
    metrics_test: KpiMetrics
    lead_lag: list[dict[str, float | int]]
    oos_degradation_pct: float
    survives_oos: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "signal_id": self.signal_id,
            "target": self.target,
            "best_feature": self.best_feature,
            "period": {"train": self.train_period, "test": self.test_period},
            "walk_forward": False,
            "regime_split": False,
            "metrics_kpi": {
                "correlation_train": self.metrics_train.correlation,
                "correlation_test": self.metrics_test.correlation,
                "rank_correlation_test": self.metrics_test.rank_correlation,
                "directional_accuracy_train": self.metrics_train.directional_accuracy,
                "directional_accuracy_test": self.metrics_test.directional_accuracy,
                "mae_test": self.metrics_test.mae,
                "mape_test": self.metrics_test.mape,
                "rmse_test": self.metrics_test.rmse,
                "hit_rate_test": self.metrics_test.hit_rate,
                "lead_lag_profile": self.lead_lag,
                "oos_degradation_pct": self.oos_degradation_pct,
            },
            "verdict": {
                "survives_oos": self.survives_oos,
                "confidence": "medium" if self.survives_oos else "low",
                "notes": self.notes,
            },
        }


def _period_bounds(period: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    start, end = period.split("/")
    return pd.Timestamp(start.strip()), pd.Timestamp(end.strip())


def _slice(df: pd.DataFrame | pd.Series, start: pd.Timestamp, end: pd.Timestamp):
    return df[(df.index >= start) & (df.index <= end)]


def run_kpi_backtest(
    spec: SignalSpec,
    features: pd.DataFrame,
    target: pd.Series,
    *,
    oos_degradation_threshold_pct: float = 50.0,
) -> KpiBacktestResult:
    """Run a single-split KPI backtest. Walk-forward variant lives in
    walk_forward.py; this is the basic case used by validation.

    Survives-OOS rule: test correlation must be at least 50% of the train
    correlation in absolute terms AND match the expected sign.
    """
    if features.empty or target.empty:
        raise ValueError("features and target must be non-empty")

    train_start, train_end = _period_bounds(spec.validation.train_period)
    test_start, test_end = _period_bounds(spec.validation.test_period)

    features_train = _slice(features, train_start, train_end)
    target_train = _slice(target, train_start, train_end)
    features_test = _slice(features, test_start, test_end)
    target_test = _slice(target, test_start, test_end)

    if features_train.empty or target_train.empty:
        raise ValueError("train window is empty after slicing; check periods vs. data coverage")

    # Pick the best feature on the train window by absolute correlation.
    best_feature: str | None = None
    best_train_corr = -np.inf
    for column in features_train.columns:
        corr = features_train[column].corr(target_train)
        if not np.isnan(corr) and abs(corr) > best_train_corr:
            best_train_corr = abs(corr)
            best_feature = column

    if best_feature is None:
        raise ValueError(
            "could not pick a best feature: every feature/target correlation was NaN. "
            "Check input data and transform definitions."
        )

    predictor_train = features_train[best_feature]
    predictor_test = features_test[best_feature]

    metrics_train = kpi_metrics(predictor_train, target_train)
    metrics_test = kpi_metrics(predictor_test, target_test)

    lead_lag = lead_lag_profile(predictor_test, target_test, max_lag=6)
    oos = oos_degradation(metrics_train.correlation, metrics_test.correlation)

    survives = bool(
        not np.isnan(metrics_test.correlation)
        and abs(metrics_test.correlation) >= 0.1
        and (
            np.sign(metrics_test.correlation) == np.sign(metrics_train.correlation)
            or metrics_train.correlation == 0
        )
        and (np.isnan(oos) or oos <= oos_degradation_threshold_pct)
    )

    notes = (
        f"Best feature: {best_feature}. "
        f"Train r={metrics_train.correlation:.2f}, test r={metrics_test.correlation:.2f}. "
        f"OOS degradation {oos:.1f}%." if not np.isnan(oos) else
        f"Best feature: {best_feature}. Train r={metrics_train.correlation:.2f}, "
        f"test r={metrics_test.correlation:.2f}."
    )

    return KpiBacktestResult(
        mode="kpi_prediction",
        signal_id=spec.signal_id,
        target=spec.target.field,
        best_feature=best_feature,
        train_period=spec.validation.train_period,
        test_period=spec.validation.test_period,
        metrics_train=metrics_train,
        metrics_test=metrics_test,
        lead_lag=lead_lag,
        oos_degradation_pct=oos,
        survives_oos=survives,
        notes=notes,
    )
