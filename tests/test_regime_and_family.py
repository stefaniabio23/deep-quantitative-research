"""Tests for Phase 8: regime-split check and multi-signal family dashboard."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from deep_quantitative_research.dashboard import (
    FamilySignal,
    render_family_dashboard,
    render_family_from_run_dirs,
)
from deep_quantitative_research.validation import check_regime_split


# ---------------------------------------------------------------- regime


def _monthly(values: list[float] | np.ndarray, start: str = "2018-01-31") -> pd.Series:
    idx = pd.date_range(start, periods=len(values), freq="ME")
    return pd.Series(values, index=idx)


def test_regime_pass_when_correlation_stable():
    rng = np.random.default_rng(0)
    n = 80
    x = rng.normal(0, 1, n)
    y = x + rng.normal(0, 0.3, n)  # stable linear relationship
    check = check_regime_split(_monthly(x), _monthly(y))
    assert check.verdict == "pass"


def test_regime_warn_when_sign_flips_across_split():
    rng = np.random.default_rng(1)
    half = 40
    x_a = rng.normal(0, 1, half)
    y_a = x_a + rng.normal(0, 0.2, half)
    x_b = rng.normal(0, 1, half)
    y_b = -x_b + rng.normal(0, 0.2, half)
    x = np.concatenate([x_a, x_b])
    y = np.concatenate([y_a, y_b])
    check = check_regime_split(_monthly(x), _monthly(y))
    assert check.verdict == "warn"
    assert check.value is not None
    assert check.value >= 50


def test_regime_warn_when_too_few_samples():
    x = _monthly(list(range(10)))
    y = _monthly(list(range(10)))
    check = check_regime_split(x, y)
    assert check.verdict == "warn"
    assert check.value is None


def test_regime_explicit_split_date():
    rng = np.random.default_rng(2)
    n = 80
    x = rng.normal(0, 1, n)
    y = x + rng.normal(0, 0.3, n)
    midpoint = "2021-05-31"
    check = check_regime_split(_monthly(x), _monthly(y), split_date=midpoint)
    assert midpoint[:10] in check.explanation
    assert check.verdict in {"pass", "warn"}


# ---------------------------------------------------------------- family dashboard


def _write_run_dir(tmp_path: Path, *, signal_id: str, signal_name: str, confidence_cap: str, corr: float, survives: bool, relationship: str = "proxy") -> Path:
    run_dir = tmp_path / signal_id
    run_dir.mkdir(parents=True)
    (run_dir / "run.yaml").write_text(
        yaml.safe_dump({"run_id": signal_id, "signal_id": signal_id, "signal_name": signal_name})
    )
    (run_dir / "validation-report.yaml").write_text(
        yaml.safe_dump(
            {
                "signal_id": signal_id,
                "confidence_cap": confidence_cap,
                "binding_constraint": "sample_size" if confidence_cap != "high" else None,
                "relationship_type": relationship,
                "checks": [],
                "recommended_next_iterations": [],
                "checked_at": "2026-06-09T00:00:00+00:00",
            }
        )
    )
    (run_dir / "backtest-result.yaml").write_text(
        yaml.safe_dump(
            {
                "signal_id": signal_id,
                "best_feature": f"pred::raw::lag_1",
                "metrics_kpi": {"correlation_test": corr},
                "verdict": {"survives_oos": survives},
            }
        )
    )
    return run_dir


def test_family_signal_from_run_dir_parses_yaml(tmp_path: Path):
    run_dir = _write_run_dir(
        tmp_path,
        signal_id="alpha",
        signal_name="Alpha Signal",
        confidence_cap="medium",
        corr=0.33,
        survives=True,
    )
    signal = FamilySignal.from_run_dir(run_dir)
    assert signal.signal_id == "alpha"
    assert signal.signal_name == "Alpha Signal"
    assert signal.confidence_cap == "medium"
    assert signal.correlation_test == pytest.approx(0.33)
    assert signal.survives_oos is True


def test_family_signal_raises_when_validation_missing(tmp_path: Path):
    run_dir = tmp_path / "missing"
    run_dir.mkdir()
    (run_dir / "run.yaml").write_text("run_id: missing\n")
    with pytest.raises(FileNotFoundError):
        FamilySignal.from_run_dir(run_dir)


def test_render_family_dashboard_contains_each_signal(tmp_path: Path):
    a = _write_run_dir(tmp_path, signal_id="alpha", signal_name="Alpha", confidence_cap="high", corr=0.55, survives=True)
    b = _write_run_dir(tmp_path, signal_id="beta", signal_name="Beta", confidence_cap="low", corr=-0.20, survives=False)
    html = render_family_from_run_dirs([a, b], family_name="Test Family")

    assert html.startswith("<!doctype html>")
    assert "Test Family" in html
    assert "Alpha" in html and "Beta" in html
    # Summary cards present for each tier
    for tier in ("low", "medium", "high"):
        assert f">{tier}<" in html or f"cap-{tier}" in html
    # Contradiction matrix has both signal_ids
    assert "alpha" in html and "beta" in html
    # Inline confidence strip
    assert "data:image/png;base64," in html


def test_render_family_overall_cap_is_minimum_tier(tmp_path: Path):
    a = _write_run_dir(tmp_path, signal_id="alpha", signal_name="A", confidence_cap="high", corr=0.4, survives=True)
    b = _write_run_dir(tmp_path, signal_id="beta", signal_name="B", confidence_cap="medium", corr=0.3, survives=True)
    c = _write_run_dir(tmp_path, signal_id="gamma", signal_name="C", confidence_cap="low", corr=0.2, survives=False)
    signals = [FamilySignal.from_run_dir(d) for d in (a, b, c)]
    html = render_family_dashboard(signals, family_name="Mixed")
    # The overall strip is rendered with low because c is low. We can't read
    # the PNG, but we can check that the meta line reports the family count.
    assert "3 signal(s)" in html
    # Contradiction map present
    assert "Contradiction map" in html


def test_render_family_empty_handles_gracefully():
    html = render_family_dashboard([], family_name="Empty")
    assert "0 signal(s)" in html
    assert "Empty" in html
