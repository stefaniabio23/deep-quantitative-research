"""Feature search log + overfitting policy.

Implements the "pre-specified vs discovered" marking from spec section 7.6.
The verdict from this module sets a hard ceiling on the validation
confidence cap; downstream stages can lower the cap further but never lift
it.
"""

from __future__ import annotations

from dataclasses import dataclass


# Spec section 7.6: "If features_tested * lags_tested > 50, the run cannot
# reach high confidence regardless of OOS performance." Tunable here so a
# future config knob can override.
HIGH_TIER_SEARCH_CEILING = 50


@dataclass
class FeatureSearchLog:
    features_tested: int
    lags_tested: int
    best_feature: str
    best_feature_pre_specified: bool
    multiple_testing_correction_needed: bool
    correction_method: str
    out_of_sample_survives: bool | None
    confidence_cap: str  # low | medium | high
    truncated_at_max_features: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "features_tested": self.features_tested,
            "lags_tested": self.lags_tested,
            "best_feature": self.best_feature,
            "best_feature_pre_specified": self.best_feature_pre_specified,
            "multiple_testing_correction_needed": self.multiple_testing_correction_needed,
            "correction_method": self.correction_method,
            "out_of_sample_survives": self.out_of_sample_survives,
            "confidence_cap": self.confidence_cap,
            "truncated_at_max_features": self.truncated_at_max_features,
        }


def assess(
    *,
    features_tested: int,
    lags_tested: int,
    best_feature: str,
    pre_specified_feature: str | None,
    out_of_sample_survives: bool | None,
    truncated_at_max_features: bool,
    correction_method: str = "benjamini_hochberg",
) -> FeatureSearchLog:
    """Compute the overfitting cap from a completed grid search."""
    pre_specified = pre_specified_feature is not None and pre_specified_feature == best_feature

    grid_size = max(1, features_tested * max(1, lags_tested))
    multiple_testing_needed = not pre_specified and grid_size > 1

    if pre_specified:
        cap = "high"
    elif out_of_sample_survives is False:
        cap = "low"
    elif grid_size > HIGH_TIER_SEARCH_CEILING:
        cap = "medium"
    elif out_of_sample_survives is True:
        cap = "high"
    else:
        cap = "medium"

    return FeatureSearchLog(
        features_tested=features_tested,
        lags_tested=lags_tested,
        best_feature=best_feature,
        best_feature_pre_specified=pre_specified,
        multiple_testing_correction_needed=multiple_testing_needed,
        correction_method=correction_method if multiple_testing_needed else "none",
        out_of_sample_survives=out_of_sample_survives,
        confidence_cap=cap,
        truncated_at_max_features=truncated_at_max_features,
    )
