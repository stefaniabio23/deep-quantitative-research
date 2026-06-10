"""Tests for vintage CSV loading + first-vintage / as-of helpers + pipeline integration."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from deep_quantitative_research.timeseries.vintage import (
    as_of_series,
    first_vintage_series,
    load_vintage_csv,
)
from deep_quantitative_research.pipeline import run_signal_from_paths


# ---------------------------------------------------------------- module


def _write_vintage_csv(tmp_path: Path) -> Path:
    """A small vintage table: one observation gets revised, one doesn't."""
    df = pd.DataFrame([
        {"observation_date": "2024-01-31", "vintage_date": "2024-02-15", "value": 10.0},
        {"observation_date": "2024-01-31", "vintage_date": "2024-05-15", "value": 11.0},  # revised
        {"observation_date": "2024-02-29", "vintage_date": "2024-03-15", "value": 12.0},
        {"observation_date": "2024-03-31", "vintage_date": "2024-04-15", "value": 13.0},
        {"observation_date": "2024-03-31", "vintage_date": "2024-08-15", "value": 14.0},  # revised
    ])
    path = tmp_path / "vintage.csv"
    df.to_csv(path, index=False)
    return path


def test_load_vintage_csv_parses_dates(tmp_path: Path):
    path = _write_vintage_csv(tmp_path)
    df = load_vintage_csv(path)
    assert df["observation_date"].dtype.kind == "M"
    assert df["vintage_date"].dtype.kind == "M"
    assert df["value"].dtype == float
    # Sorted by (observation_date, vintage_date)
    assert df["observation_date"].is_monotonic_increasing


def test_load_vintage_csv_rejects_missing_column(tmp_path: Path):
    bad = tmp_path / "bad.csv"
    pd.DataFrame({"observation_date": ["2024-01-31"], "value": [10.0]}).to_csv(bad, index=False)
    with pytest.raises(KeyError):
        load_vintage_csv(bad)


def test_first_vintage_picks_earliest_publication(tmp_path: Path):
    path = _write_vintage_csv(tmp_path)
    df = load_vintage_csv(path)
    series = first_vintage_series(df)
    assert len(series) == 3
    # Jan obs first vintage was 10.0 (before the 11.0 revision)
    assert series.loc["2024-01-31"] == 10.0
    # Mar obs first vintage was 13.0 (before the 14.0 revision)
    assert series.loc["2024-03-31"] == 13.0


def test_first_vintage_empty_returns_empty():
    empty = pd.DataFrame(columns=["observation_date", "vintage_date", "value"])
    series = first_vintage_series(empty)
    assert series.empty


def test_as_of_series_returns_latest_visible_value(tmp_path: Path):
    path = _write_vintage_csv(tmp_path)
    df = load_vintage_csv(path)
    # As of 2024-03-01: only the Jan observation has been published (first
    # vintage 2024-02-15). Feb obs publishes 2024-03-15, after the as-of.
    as_of = as_of_series(df, pd.DatetimeIndex([pd.Timestamp("2024-03-01")]))
    assert as_of.iloc[0] == 10.0


def test_as_of_series_returns_feb_when_visible(tmp_path: Path):
    path = _write_vintage_csv(tmp_path)
    df = load_vintage_csv(path)
    # As of 2024-04-01: Jan and Feb both visible; Mar publishes 2024-04-15.
    # Most recent observation visible is Feb=12.0.
    as_of = as_of_series(df, pd.DatetimeIndex([pd.Timestamp("2024-04-01")]))
    assert as_of.iloc[0] == 12.0


def test_as_of_series_picks_post_revision_value(tmp_path: Path):
    path = _write_vintage_csv(tmp_path)
    df = load_vintage_csv(path)
    # As of 2024-06-01: Jan obs revised to 11.0; Feb still 12.0; Mar still 13.0.
    # Most recent observation visible is Mar=13.0.
    as_of = as_of_series(df, pd.DatetimeIndex([pd.Timestamp("2024-06-01")]))
    assert as_of.iloc[0] == 13.0


# ---------------------------------------------------------------- pipeline


def _write_spec(tmp_path: Path) -> Path:
    spec = {
        "signal_id": "vintage-test",
        "signal_name": "Vintage Test Signal",
        "hypothesis": {
            "statement": "x predicts y",
            "target_variable": "y",
            "expected_direction": "positive",
        },
        "target": {
            "dataset_id": "target-ds",
            "field": "y",
            "cadence": "monthly",
            "revisions_possible": True,
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
            "max_features": 6,
            "max_lags": 2,
            "multiple_testing_correction": True,
            "pre_specified_feature": "pred-ds::raw::lag_1",
        },
        "validation": {
            "train_period": "2008-03-31/2017-12-31",
            "test_period": "2018-03-31/2025-09-30",
            "walk_forward": True,
        },
        "outputs": {"signal_card": True},
    }
    p = tmp_path / "spec.yaml"
    p.write_text(yaml.safe_dump(spec))
    return p


def _write_synthetic_csvs(tmp_path: Path):
    """Mirror the biotech-pos synthetic pattern at smaller scale."""
    rng = np.random.default_rng(42)
    months = pd.date_range("2008-01-31", "2025-09-30", freq="ME")
    predictor = rng.poisson(8, len(months))
    pred_df = pd.DataFrame({"date": months, "value": predictor})
    pred_df.to_csv(tmp_path / "predictor.csv", index=False)

    # Quarterly target with a planted lag-1 relationship to predictor.
    quarters = pd.date_range("2008-01-31", "2025-09-30", freq="QE")
    q_pred = pred_df.set_index("date")["value"].astype(float).resample("QE").sum()
    centered = (q_pred - q_pred.mean()) / q_pred.std()
    rng2 = np.random.default_rng(43)
    returns = 0.04 * centered.shift(1) + rng2.normal(0, 0.05, len(quarters))
    target_df = pd.DataFrame({"date": quarters, "value": returns.values}).dropna()
    target_df.to_csv(tmp_path / "target.csv", index=False)
    return tmp_path / "target.csv", tmp_path / "predictor.csv"


def _write_synthetic_vintage_csv(tmp_path: Path, final_target_csv: Path) -> Path:
    """Build a vintage CSV where first vintage equals final - small noise.

    Each observation gets a first-vintage publication 45 days later, plus a
    revision 12 months later that adjusts the value slightly. The pipeline
    should pick the first-vintage value.
    """
    final = pd.read_csv(final_target_csv)
    final["date"] = pd.to_datetime(final["date"])
    rng = np.random.default_rng(99)
    rows: list[dict[str, object]] = []
    for _, row in final.iterrows():
        obs_date = row["date"]
        first_vintage_date = obs_date + pd.Timedelta(days=45)
        revision_date = obs_date + pd.Timedelta(days=365)
        first_value = float(row["value"]) + float(rng.normal(0, 0.005))
        revised_value = float(row["value"])
        rows.append({"observation_date": obs_date.date(), "vintage_date": first_vintage_date.date(), "value": first_value})
        rows.append({"observation_date": obs_date.date(), "vintage_date": revision_date.date(), "value": revised_value})
    path = tmp_path / "target_vintage.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_pipeline_revisions_warning_when_no_vintage(tmp_path: Path):
    spec_path = _write_spec(tmp_path)
    target_csv, predictor_csv = _write_synthetic_csvs(tmp_path)
    run_dir = tmp_path / "run"
    run_signal_from_paths(
        spec_path=spec_path,
        target_csv=target_csv,
        predictor_csvs={"pred-ds": predictor_csv},
        run_dir=run_dir,
    )
    run_yaml = yaml.safe_load((run_dir / "run.yaml").read_text())
    validation = yaml.safe_load((run_dir / "validation-report.yaml").read_text())

    assert run_yaml["vintage_handled"] is False
    revisions = [c for c in validation["checks"] if c["name"] == "revisions"]
    assert len(revisions) == 1
    assert revisions[0]["verdict"] == "warn"


def test_pipeline_revisions_clears_when_vintage_provided(tmp_path: Path):
    spec_path = _write_spec(tmp_path)
    target_csv, predictor_csv = _write_synthetic_csvs(tmp_path)
    vintage_csv = _write_synthetic_vintage_csv(tmp_path, target_csv)
    run_dir = tmp_path / "run-vintage"
    run_signal_from_paths(
        spec_path=spec_path,
        target_vintage_csv=vintage_csv,
        predictor_csvs={"pred-ds": predictor_csv},
        run_dir=run_dir,
    )
    run_yaml = yaml.safe_load((run_dir / "run.yaml").read_text())
    validation = yaml.safe_load((run_dir / "validation-report.yaml").read_text())

    assert run_yaml["vintage_handled"] is True
    assert run_yaml["vintage_source"] is not None
    revisions = [c for c in validation["checks"] if c["name"] == "revisions"]
    assert len(revisions) == 1
    assert revisions[0]["verdict"] == "pass"


def test_pipeline_rejects_when_both_csvs_provided(tmp_path: Path):
    spec_path = _write_spec(tmp_path)
    target_csv, predictor_csv = _write_synthetic_csvs(tmp_path)
    vintage_csv = _write_synthetic_vintage_csv(tmp_path, target_csv)
    with pytest.raises(ValueError):
        run_signal_from_paths(
            spec_path=spec_path,
            target_csv=target_csv,
            target_vintage_csv=vintage_csv,
            predictor_csvs={"pred-ds": predictor_csv},
            run_dir=tmp_path / "run-bad",
        )


def test_pipeline_rejects_when_neither_csv_provided(tmp_path: Path):
    spec_path = _write_spec(tmp_path)
    _, predictor_csv = _write_synthetic_csvs(tmp_path)
    with pytest.raises(ValueError):
        run_signal_from_paths(
            spec_path=spec_path,
            predictor_csvs={"pred-ds": predictor_csv},
            run_dir=tmp_path / "run-bad",
        )
