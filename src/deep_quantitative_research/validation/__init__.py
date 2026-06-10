"""Validation gate: data-quality + stationarity + autocorrelation + robustness
+ causal classification + multiple-testing correction + verdict assembly.
"""

from .causal_checks import classify_relationship
from .data_quality import (
    Check,
    check_missingness,
    check_outliers,
    check_sample_size,
)
from .effective_sample_size import (
    autocorrelations,
    bartlett_effective_n,
    check_effective_sample_size,
)
from .gate import ValidationReport, assemble
from .multiple_testing import benjamini_hochberg
from .regime import check_regime_split
from .robustness import check_lag_sensitivity, check_outlier_sensitivity
from .selection_bias import (
    bonferroni,
    check_selection_bias,
    correlation_p_value,
    deflated_correlation,
)
from .statistical_tests import (
    check_autocorrelation,
    check_stationarity_adf,
    check_stationarity_kpss,
)

__all__ = [
    "Check",
    "check_missingness",
    "check_outliers",
    "check_sample_size",
    "check_stationarity_adf",
    "check_stationarity_kpss",
    "check_autocorrelation",
    "check_lag_sensitivity",
    "check_outlier_sensitivity",
    "check_regime_split",
    "check_selection_bias",
    "check_effective_sample_size",
    "autocorrelations",
    "bartlett_effective_n",
    "classify_relationship",
    "ValidationReport",
    "assemble",
    "benjamini_hochberg",
    "bonferroni",
    "correlation_p_value",
    "deflated_correlation",
]
