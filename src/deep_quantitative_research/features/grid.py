"""Controlled feature grid builder.

Reads a SignalSpec's ``feature_grid`` block and a dict of cadence-aligned
predictor Series; emits a DataFrame whose columns are crossed transforms ×
lags, capped by ``max_features`` and ``max_lags``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import pandas as pd

from ..research.signal_spec import Predictor, SignalSpec
from ..timeseries.transformations import AVAILABLE_TRANSFORMS, apply_transform, lag

# Default controlled menu when a predictor leaves ``transforms`` empty in the
# SignalSpec. Spec section 7.6.
DEFAULT_TRANSFORMS: tuple[str, ...] = (
    "raw",
    "yoy_1y",
    "mom_3p",
    "rolling_mean_3",
    "zscore_12",
)


@dataclass
class FeatureGridResult:
    """The materialised grid plus the metadata needed for the audit log."""

    features: pd.DataFrame
    signal_id: str
    predictor_dataset_ids: list[str]
    enabled_transforms: list[str]
    lags: list[int]
    max_features: int
    max_lags: int
    features_emitted: int
    truncated_at_max_features: bool
    feature_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "signal_id": self.signal_id,
            "predictor_dataset_ids": list(self.predictor_dataset_ids),
            "enabled_transforms": list(self.enabled_transforms),
            "lags": list(self.lags),
            "max_features": self.max_features,
            "max_lags": self.max_lags,
            "features_emitted": self.features_emitted,
            "truncated_at_max_features": self.truncated_at_max_features,
            "feature_names": list(self.feature_names),
        }


def _expand_transforms(spec_transforms: Iterable[str]) -> list[str]:
    out: list[str] = []
    for name in spec_transforms or DEFAULT_TRANSFORMS:
        if name not in AVAILABLE_TRANSFORMS:
            raise KeyError(
                f"unknown transform in SignalSpec: {name!r}. "
                f"Known: {sorted(AVAILABLE_TRANSFORMS)}"
            )
        out.append(name)
    return out


def build_grid(
    spec: SignalSpec,
    predictor_series: dict[str, pd.Series],
) -> FeatureGridResult:
    """Build the controlled feature grid for ``spec`` against the given series.

    ``predictor_series`` keys must match the SignalSpec's predictor
    ``dataset_id`` values. Missing predictors raise ``KeyError`` rather
    than silently producing a smaller grid.
    """
    fg = spec.feature_grid
    enabled_transforms = sorted(
        {t for p in spec.predictors for t in (p.transforms or DEFAULT_TRANSFORMS)},
        key=lambda s: s.lower(),
    )
    enabled_transforms = [t for t in enabled_transforms if t in AVAILABLE_TRANSFORMS]

    # If no predictor declares transforms, fall back to defaults.
    if not enabled_transforms:
        enabled_transforms = list(DEFAULT_TRANSFORMS)

    # Aggregate the lag set across predictors, capped by max_lags.
    declared_lags: list[int] = sorted({l for p in spec.predictors for l in (p.lags or [0])})
    if not declared_lags:
        declared_lags = [0]
    capped_lags = [l for l in declared_lags if l <= fg.max_lags]

    columns: list[pd.Series] = []
    feature_names: list[str] = []
    truncated = False

    for predictor in spec.predictors:
        if predictor.dataset_id not in predictor_series:
            raise KeyError(
                f"predictor series missing for {predictor.dataset_id!r}; "
                "pass a Series under that dataset_id key."
            )
        series = predictor_series[predictor.dataset_id]
        transforms = _expand_transforms(predictor.transforms)
        lags_to_use = capped_lags
        for transform_name in transforms:
            base = apply_transform(series, transform_name)
            base.name = f"{predictor.dataset_id}::{transform_name}"
            for lag_periods in lags_to_use:
                if len(columns) >= fg.max_features:
                    truncated = True
                    break
                shifted = lag(base, periods=lag_periods)
                column_name = f"{predictor.dataset_id}::{transform_name}::lag_{lag_periods}"
                shifted.name = column_name
                columns.append(shifted)
                feature_names.append(column_name)
            if truncated:
                break
        if truncated:
            break

    if not columns:
        features = pd.DataFrame()
    else:
        features = pd.concat(columns, axis=1)

    return FeatureGridResult(
        features=features,
        signal_id=spec.signal_id,
        predictor_dataset_ids=[p.dataset_id for p in spec.predictors],
        enabled_transforms=enabled_transforms,
        lags=capped_lags,
        max_features=fg.max_features,
        max_lags=fg.max_lags,
        features_emitted=len(feature_names),
        truncated_at_max_features=truncated,
        feature_names=feature_names,
    )
