"""SignalSpec YAML loader, validator, and typed view."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ..schemas import validate


@dataclass
class Target:
    dataset_id: str
    field: str
    cadence: str
    transform: str | None = None
    # Provenance / vintage handling (PIT discipline). Unknown when None.
    revisions_possible: bool | None = None
    point_in_time_safe: bool | None = None


@dataclass
class Predictor:
    dataset_id: str
    field: str
    cadence: str
    variable_type: str | None = None
    default_aggregation: str | None = None
    transforms: list[str] = field(default_factory=list)
    lags: list[int] = field(default_factory=list)


@dataclass
class FeatureGridSpec:
    mode: str = "controlled"
    max_features: int = 40
    max_lags: int = 3
    multiple_testing_correction: bool = True
    pre_specified_feature: str | None = None


@dataclass
class ValidationSpec:
    train_period: str
    test_period: str
    walk_forward: bool = True
    regime_split: bool = False


@dataclass
class HypothesisBlock:
    statement: str
    target_variable: str
    expected_direction: str = "positive"
    expected_lag_periods: list[int] = field(default_factory=list)


@dataclass
class SignalSpec:
    signal_id: str
    signal_name: str
    hypothesis: HypothesisBlock
    target: Target
    predictors: list[Predictor]
    feature_grid: FeatureGridSpec
    validation: ValidationSpec
    join_logic: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


def _period_bounds(period: str) -> tuple[str, str]:
    if "/" not in period:
        raise ValueError(f"period must be 'YYYY-MM-DD/YYYY-MM-DD', got {period!r}")
    start, end = period.split("/", 1)
    return start.strip(), end.strip()


def load_signal_spec(path: Path | str) -> SignalSpec:
    """Load + schema-validate a SignalSpec YAML."""
    path = Path(path)
    raw = yaml.safe_load(path.read_text()) or {}
    validate("signal", raw)

    h = raw["hypothesis"]
    hypothesis = HypothesisBlock(
        statement=h["statement"],
        target_variable=h["target_variable"],
        expected_direction=h.get("expected_direction", "positive"),
        expected_lag_periods=list(h.get("expected_lag_periods") or []),
    )

    t = raw["target"]
    target = Target(
        dataset_id=t["dataset_id"],
        field=t["field"],
        cadence=t["cadence"],
        transform=t.get("transform"),
        revisions_possible=t.get("revisions_possible"),
        point_in_time_safe=t.get("point_in_time_safe"),
    )

    predictors = [
        Predictor(
            dataset_id=p["dataset_id"],
            field=p["field"],
            cadence=p["cadence"],
            variable_type=p.get("variable_type"),
            default_aggregation=p.get("default_aggregation"),
            transforms=list(p.get("transforms") or []),
            lags=list(p.get("lags") or []),
        )
        for p in raw["predictors"]
    ]

    fg = raw["feature_grid"]
    feature_grid = FeatureGridSpec(
        mode=fg.get("mode", "controlled"),
        max_features=int(fg["max_features"]),
        max_lags=int(fg["max_lags"]),
        multiple_testing_correction=bool(fg.get("multiple_testing_correction", True)),
        pre_specified_feature=fg.get("pre_specified_feature"),
    )

    v = raw["validation"]
    _period_bounds(v["train_period"])  # raise early on malformed periods
    _period_bounds(v["test_period"])
    validation = ValidationSpec(
        train_period=v["train_period"],
        test_period=v["test_period"],
        walk_forward=bool(v.get("walk_forward", True)),
        regime_split=bool(v.get("regime_split", False)),
    )

    return SignalSpec(
        signal_id=raw["signal_id"],
        signal_name=raw["signal_name"],
        hypothesis=hypothesis,
        target=target,
        predictors=predictors,
        feature_grid=feature_grid,
        validation=validation,
        join_logic=dict(raw.get("join_logic") or {}),
        outputs=dict(raw.get("outputs") or {}),
        raw=raw,
    )
