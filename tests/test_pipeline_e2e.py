"""End-to-end test of the run-signal pipeline against synthetic data.

The fixture generates a target series with a known one-period-ahead
relationship to the predictor plus noise; the pipeline should recover the
relationship and write a coherent signal card.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from deep_quantitative_research.pipeline import run_signal_from_paths
from deep_quantitative_research.research.signal_spec import load_signal_spec


def _make_dataset(tmp_path: Path, *, noise_sigma: float = 0.3, seed: int = 42) -> tuple[Path, Path, Path]:
    """Generate target.csv, predictor.csv, and signal-spec.yaml.

    Construction: predictor is white noise; target[t] = predictor[t-1] + noise.
    So the predictor LEADS the target by one period. The feature
    ``pred-ds::raw::lag_1`` (predictor at t-1, viewed from t) should produce
    the highest correlation.
    """
    rng = np.random.default_rng(seed)
    n = 96  # 8 years of monthly data
    idx = pd.date_range("2018-01-31", periods=n, freq="ME")

    predictor = rng.normal(0, 1, n)
    noise = rng.normal(0, noise_sigma, n)
    target = np.full(n, np.nan)
    target[1:] = predictor[:-1] + noise[1:]

    target_df = pd.DataFrame({"date": idx, "value": target}).dropna()
    predictor_df = pd.DataFrame({"date": idx, "value": predictor})

    target_csv = tmp_path / "target.csv"
    predictor_csv = tmp_path / "predictor.csv"
    target_df.to_csv(target_csv, index=False)
    predictor_df.to_csv(predictor_csv, index=False)

    spec = {
        "signal_id": "e2e-signal",
        "signal_name": "E2E Test Signal",
        "hypothesis": {
            "statement": "Predictor leads target by one month.",
            "target_variable": "y",
            "expected_direction": "positive",
            "expected_lag_periods": [1],
        },
        "target": {
            "dataset_id": "target-ds",
            "field": "y",
            "cadence": "monthly",
            "transform": None,
        },
        "predictors": [
            {
                "dataset_id": "pred-ds",
                "field": "x",
                "cadence": "monthly",
                "variable_type": "flow",
                "default_aggregation": "sum",
                "transforms": ["raw"],
                "lags": [0, 1, 2],
            }
        ],
        "feature_grid": {
            "mode": "controlled",
            "max_features": 10,
            "max_lags": 2,
            "multiple_testing_correction": True,
            "pre_specified_feature": "pred-ds::raw::lag_1",
        },
        "validation": {
            "train_period": "2018-01-31/2022-12-31",
            "test_period": "2023-01-31/2025-09-30",
            "walk_forward": True,
        },
        "outputs": {"signal_card": True},
    }
    spec_path = tmp_path / "signal-spec.yaml"
    spec_path.write_text(yaml.safe_dump(spec))

    return spec_path, target_csv, predictor_csv


def test_pipeline_e2e_writes_all_artefacts(tmp_path: Path):
    spec_path, target_csv, predictor_csv = _make_dataset(tmp_path)
    run_dir = tmp_path / "run"

    summary = run_signal_from_paths(
        spec_path=spec_path,
        target_csv=target_csv,
        predictor_csvs={"pred-ds": predictor_csv},
        run_dir=run_dir,
    )

    # Summary fields populated
    assert summary.signal_id == "e2e-signal"
    assert summary.confidence_cap in {"low", "medium", "high"}
    # The pre-specified feature should be picked since correlation should be highest at lag_1
    assert "lag_1" in summary.best_feature

    # Artefacts on disk
    for filename in [
        "run.yaml",
        "cadence-rollup-audit.yaml",
        "feature-grid.yaml",
        "feature-search-log.yaml",
        "backtest-result.yaml",
        "validation-report.yaml",
        "signal-card.md",
    ]:
        assert (run_dir / filename).exists(), f"missing artefact: {filename}"

    # Signal card has the canonical sections
    card = (run_dir / "signal-card.md").read_text()
    for section in [
        "## Hypothesis",
        "## Economic Mapping",
        "## Data Inputs",
        "## Time-Series",
        "## Backtest Summary",
        "## Current Read",
        "## Confidence",
        "## Caveats",
        "## Failure Modes",
        "## Next Iteration",
        "## Links",
    ]:
        assert section in card, f"signal card missing section: {section}"


def test_pipeline_picks_lag_1_with_strong_signal(tmp_path: Path):
    """Stronger signal version: noise reduced, expect lag_1 wins and survives OOS."""
    spec_path, target_csv, predictor_csv = _make_dataset(tmp_path, noise_sigma=0.05, seed=123)

    run_dir = tmp_path / "run-strong"
    summary = run_signal_from_paths(
        spec_path=spec_path,
        target_csv=target_csv,
        predictor_csvs={"pred-ds": predictor_csv},
        run_dir=run_dir,
    )

    backtest = yaml.safe_load((run_dir / "backtest-result.yaml").read_text())
    assert backtest["verdict"]["survives_oos"] is True
    assert "lag_1" in backtest["best_feature"]
    # Test correlation should be strongly positive with clean signal
    assert backtest["metrics_kpi"]["correlation_test"] > 0.5
