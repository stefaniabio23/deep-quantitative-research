"""Validation gate: data-quality checks + multiple-testing + verdict assembly.

Phase 4 ships the MVP: sample_size, missingness, outliers, BH correction,
gate assembly. Phase 4b adds stationarity (ADF/KPSS), autocorrelation,
robustness sensitivity, causal_checks.
"""

from .data_quality import (
    Check,
    check_missingness,
    check_outliers,
    check_sample_size,
)
from .gate import ValidationReport, assemble
from .multiple_testing import benjamini_hochberg

__all__ = [
    "Check",
    "check_missingness",
    "check_outliers",
    "check_sample_size",
    "ValidationReport",
    "assemble",
    "benjamini_hochberg",
]
