"""Time series primitives: transformations, cadence rollup, alignment.

Every transform is a pure function on a pandas Series. Series convention:
DatetimeIndex named ``date``, numeric values, sorted ascending. NaNs are
allowed but must round-trip through the transform.
"""

from .alignment import apply_release_lag, period_index
from .cadence import (
    DEFAULT_AGGREGATION,
    CADENCE_RANK,
    finer_or_equal,
    rollup,
)
from .transformations import (
    AVAILABLE_TRANSFORMS,
    apply_transform,
    diff,
    lag,
    mom_3p,
    pct_change,
    rolling_mean,
    rolling_sum,
    yo2y,
    yoy_1y,
    zscore,
)
from .vintage import (
    REQUIRED_COLUMNS,
    as_of_series,
    final_vintage_series,
    first_revisions,
    first_vintage_series,
    load_vintage_csv,
)

__all__ = [
    "apply_release_lag",
    "period_index",
    "DEFAULT_AGGREGATION",
    "CADENCE_RANK",
    "finer_or_equal",
    "rollup",
    "AVAILABLE_TRANSFORMS",
    "apply_transform",
    "diff",
    "lag",
    "mom_3p",
    "pct_change",
    "rolling_mean",
    "rolling_sum",
    "yo2y",
    "yoy_1y",
    "zscore",
    "REQUIRED_COLUMNS",
    "as_of_series",
    "final_vintage_series",
    "first_revisions",
    "first_vintage_series",
    "load_vintage_csv",
]
