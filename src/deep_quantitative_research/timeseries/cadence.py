"""Cadence rollup with variable-type-aware aggregation.

Implements the spec section 7.5 ladder (daily → annual) and refuses to sum
stock / rate / price variables without an explicit override. Every rollup
produces an audit dict that the run pipeline writes to
``cadence-rollup-audit.yaml``.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


# Variable type → default aggregation function name. Spec section 7.5.
DEFAULT_AGGREGATION: dict[str, str] = {
    "flow": "sum",
    "stock": "last",
    "rate": "mean",
    "price": "last",
    "count": "sum",
    "sentiment": "mean",
    "event": "sum",
}


# Cadence rank (lower = finer). Used to refuse rolling DOWN (target finer
# than source) which is the typical sign of a misclassified source.
CADENCE_RANK: dict[str, int] = {
    "daily": 0,
    "weekly": 1,
    "monthly": 2,
    "quarterly": 3,
    "annual": 4,
    "irregular": 5,
}


# Pandas resample rule per target cadence. Period-end ("E") variants give
# us right-edge timestamps so monthly bars land on month-end dates.
_RESAMPLE_RULE: dict[str, str] = {
    "weekly": "W",
    "monthly": "ME",
    "quarterly": "QE",
    "annual": "YE",
}


_REFUSED_SUMS = {"stock", "rate", "price"}
_REFUSED_MEANS = {"flow"}


class CadenceError(ValueError):
    """Raised when a rollup is unsafe and not explicitly overridden."""


def finer_or_equal(source_cadence: str, target_cadence: str) -> bool:
    """True when the source is at least as fine as the target."""
    return CADENCE_RANK[source_cadence] <= CADENCE_RANK[target_cadence]


def _validate_aggregation(
    *,
    variable_type: str,
    aggregation: str,
    overridden: bool,
) -> None:
    if overridden:
        return
    if aggregation == "sum" and variable_type in _REFUSED_SUMS:
        raise CadenceError(
            f"refusing to sum {variable_type!r} without an explicit aggregation "
            "override. Spec section 7.5 hard rule."
        )
    if aggregation == "mean" and variable_type in _REFUSED_MEANS:
        raise CadenceError(
            f"refusing to mean {variable_type!r} without an explicit aggregation "
            "override. Spec section 7.5 hard rule."
        )


def rollup(
    series: pd.Series,
    *,
    source_cadence: str,
    target_cadence: str,
    variable_type: str,
    aggregation: str | None = None,
    aggregation_overridden: bool = False,
    drop_partial: bool = True,
) -> tuple[pd.Series, dict[str, Any]]:
    """Roll a series up the cadence ladder.

    Returns ``(rolled_series, audit_dict)``. The audit captures everything a
    later reader needs to verify the operation.
    """
    if source_cadence not in CADENCE_RANK or target_cadence not in CADENCE_RANK:
        raise CadenceError(
            f"unknown cadence(s): source={source_cadence!r} target={target_cadence!r}"
        )
    if not finer_or_equal(source_cadence, target_cadence):
        raise CadenceError(
            f"refusing to roll DOWN: source {source_cadence!r} is coarser than "
            f"target {target_cadence!r}. The source is wrong for this hypothesis."
        )

    if variable_type not in DEFAULT_AGGREGATION:
        raise CadenceError(f"unknown variable_type: {variable_type!r}")

    if aggregation is None:
        aggregation = DEFAULT_AGGREGATION[variable_type]

    _validate_aggregation(
        variable_type=variable_type,
        aggregation=aggregation,
        overridden=aggregation_overridden,
    )

    if source_cadence == target_cadence:
        rolled = series.copy()
        partial_dropped = 0
    else:
        rule = _RESAMPLE_RULE[target_cadence]
        resampler = series.resample(rule)
        if not hasattr(resampler, aggregation):
            raise CadenceError(
                f"pandas resample has no aggregation method {aggregation!r}"
            )
        rolled = getattr(resampler, aggregation)()
        partial_dropped = 0
        if drop_partial and len(rolled) > 0:
            # If the last source point sits inside (not on) the last target
            # period, treat that target period as partial.
            last_source = series.index.max()
            last_target = rolled.index.max()
            if last_source < last_target:
                rolled = rolled.iloc[:-1]
                partial_dropped = 1

    missing_periods = int(rolled.isna().sum())

    audit: dict[str, Any] = {
        "source_cadence": source_cadence,
        "target_cadence": target_cadence,
        "variable_type": variable_type,
        "aggregation": aggregation,
        "aggregation_overridden": aggregation_overridden,
        "periods_created": int(len(rolled)),
        "partial_periods_dropped": partial_dropped,
        "missing_periods": missing_periods,
        "duplicate_timestamps_resolved": 0,
    }
    return rolled, audit
