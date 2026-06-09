"""Tests for the validation gate, data-quality checks, BH correction, and schema loaders."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from deep_quantitative_research.research.hypothesis import load_hypothesis
from deep_quantitative_research.research.signal_spec import load_signal_spec
from deep_quantitative_research.schemas import SchemaError, schema_names, validate
from deep_quantitative_research.validation import (
    Check,
    benjamini_hochberg,
    check_missingness,
    check_outliers,
    check_sample_size,
)
from deep_quantitative_research.validation.gate import assemble


# ---------------------------------------------------------------- data quality


def test_sample_size_pass():
    c = check_sample_size(200)
    assert c.verdict == "pass"


def test_sample_size_warn():
    c = check_sample_size(80)
    assert c.verdict == "warn"


def test_sample_size_fail():
    c = check_sample_size(5)
    assert c.verdict == "fail"


def test_missingness_pass():
    idx = pd.date_range("2020-01-31", periods=24, freq="ME")
    s = pd.Series(np.ones(24), index=idx)
    assert check_missingness(s).verdict == "pass"


def test_missingness_warn_and_fail():
    idx = pd.date_range("2020-01-31", periods=20, freq="ME")
    s = pd.Series(np.ones(20), index=idx)
    s.iloc[:2] = np.nan  # 10%
    assert check_missingness(s).verdict == "warn"
    s.iloc[:10] = np.nan  # 50%
    assert check_missingness(s).verdict == "fail"


def test_outliers_pass_on_constant_series():
    s = pd.Series(np.zeros(100), index=pd.date_range("2020-01-31", periods=100, freq="ME"))
    c = check_outliers(s)
    assert c.verdict == "pass"


def test_outliers_flags_extremes():
    rng = np.random.default_rng(0)
    s = pd.Series(rng.normal(0, 1, 200), index=pd.date_range("2020-01-31", periods=200, freq="ME"))
    s.iloc[10] = 100.0
    s.iloc[20] = -100.0
    c = check_outliers(s)
    assert c.verdict in {"warn", "fail"}
    assert c.value >= 2


# ---------------------------------------------------------------- BH


def test_bh_all_significant():
    # When every p is tiny, every hypothesis should pass at fdr 0.05
    out = benjamini_hochberg([0.001, 0.002, 0.003, 0.004], fdr=0.05)
    assert all(out)


def test_bh_all_null():
    # When every p is large, every hypothesis fails
    out = benjamini_hochberg([0.9, 0.8, 0.7], fdr=0.05)
    assert not any(out)


def test_bh_preserves_input_order():
    out = benjamini_hochberg([0.5, 0.001, 0.6, 0.002], fdr=0.05)
    # Indices 1 and 3 have small p-values
    assert out[1] is True
    assert out[3] is True


# ---------------------------------------------------------------- gate assembly


def _good_checks() -> list[Check]:
    return [
        Check(name="sample_size", verdict="pass", value=200, threshold={}, explanation="ok"),
        Check(name="missingness", verdict="pass", value=0.0, threshold={}, explanation="ok"),
        Check(name="outliers", verdict="pass", value=0, threshold=4.0, explanation="ok"),
    ]


def test_gate_caps_to_minimum_constraint():
    checks = _good_checks()
    # Feature search caps at medium; nothing else gives less
    report = assemble(
        signal_id="x",
        checks=checks,
        feature_search_cap="medium",
        survives_oos=True,
        walk_forward=True,
    )
    assert report.confidence_cap == "medium"
    assert report.binding_constraint == "feature_search"


def test_gate_low_on_oos_failure():
    report = assemble(
        signal_id="x",
        checks=_good_checks(),
        feature_search_cap="high",
        survives_oos=False,
        walk_forward=True,
    )
    assert report.confidence_cap == "low"
    assert report.binding_constraint == "out_of_sample"


def test_gate_walk_forward_off_caps_medium():
    report = assemble(
        signal_id="x",
        checks=_good_checks(),
        feature_search_cap="high",
        survives_oos=True,
        walk_forward=False,
    )
    assert report.confidence_cap == "medium"


# ---------------------------------------------------------------- schemas


def test_schema_names_contain_signal():
    assert "signal" in schema_names()
    assert "hypothesis" in schema_names()


def test_validate_minimal_hypothesis():
    payload = {
        "hypothesis_id": "HYP-2026-001",
        "statement": "Search interest predicts retail sales.",
        "target_variable": "UK retail sales YoY",
        "target_cadence": "monthly",
        "expected_direction": "positive",
        "mechanism": "search → demand → sales reporting",
        "candidate_predictors": ["Google Trends"],
        "falsification": ["fails out of sample", "disappears after trend control"],
    }
    validate("hypothesis", payload)  # raises on failure


def test_validate_rejects_missing_required():
    with pytest.raises(SchemaError):
        validate("hypothesis", {"statement": "incomplete"})


# ---------------------------------------------------------------- loaders


def test_load_signal_spec_round_trip(tmp_path: Path):
    spec_yaml = {
        "signal_id": "test-signal",
        "signal_name": "Test Signal",
        "hypothesis": {
            "statement": "x predicts y",
            "target_variable": "y",
            "expected_direction": "positive",
            "expected_lag_periods": [0, 1],
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
                "transforms": ["raw", "yoy_1y"],
                "lags": [0, 1],
            }
        ],
        "feature_grid": {
            "mode": "controlled",
            "max_features": 20,
            "max_lags": 3,
            "multiple_testing_correction": True,
        },
        "validation": {
            "train_period": "2020-01-31/2021-12-31",
            "test_period": "2022-01-31/2022-12-31",
            "walk_forward": False,
        },
        "outputs": {"signal_card": True},
    }
    path = tmp_path / "sig.yaml"
    import yaml

    path.write_text(yaml.safe_dump(spec_yaml))
    spec = load_signal_spec(path)
    assert spec.signal_id == "test-signal"
    assert spec.predictors[0].dataset_id == "pred-ds"
    assert spec.feature_grid.max_features == 20


def test_load_hypothesis_validates(tmp_path: Path):
    payload = {
        "hypothesis_id": "HYP-2026-002",
        "statement": "Search interest predicts retail sales.",
        "target_variable": "UK retail sales YoY",
        "target_cadence": "monthly",
        "expected_direction": "positive",
        "mechanism": "search → demand → sales reporting",
        "candidate_predictors": ["Google Trends"],
        "falsification": ["fails out of sample", "disappears after trend control"],
    }
    path = tmp_path / "h.yaml"
    import yaml

    path.write_text(yaml.safe_dump(payload))
    h = load_hypothesis(path)
    assert h.hypothesis_id == "HYP-2026-002"
    assert len(h.falsification) == 2
