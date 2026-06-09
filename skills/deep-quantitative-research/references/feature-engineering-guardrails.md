# Feature engineering guardrails

Background for the `feature-engineering` sub-skill. The transforms are well known; the danger is in how many you try.

## The grid you actually want

A controlled grid is the menu of transforms plus the lag set, capped by `max_features` and `max_lags` from the SignalSpec. The default menu:

```text
raw, diff, pct_change,
mom_1p, mom_3p,
yoy_1y, yo2y,
rolling_mean_3, rolling_mean_6,
rolling_sum_3, rolling_sum_12,
zscore_12, zscore_24,
lag_1, lag_2, lag_3,
seasonally_adjusted_if_available
```

Each is justified by a separate intuition (level, change, year-over-year, momentum, normalisation, displacement). None is justified by "we tried everything else".

## The grid you should refuse to build

- Every polynomial transform.
- Every interaction term across predictors with no economic story.
- Every rolling window across an arbitrary range (3, 4, 5, ..., 24).
- Every Box-Cox parameter.

Those produce "found" features that do not survive OOS.

## Pre-specified vs discovered

Mark every winning feature one of two ways:

- **Pre-specified.** Named in the Hypothesis YAML before any data was looked at.
- **Discovered.** Surfaced by the grid search.

A discovered winner caps confidence at `medium` regardless of OOS performance, unless the grid was small (under 10 features), the winner is statistically separated from the runner-up, and OOS degradation is under 20%.

## Multiple-testing correction

When the feature grid is large, p-values understate false-positive risk. Default: Benjamini-Hochberg per `config/research_defaults.yaml`. Bonferroni is acceptable when the number of features is small and the cost of a false negative is high.

Correction is optional only when:

- The Hypothesis YAML pre-specified a single feature, AND
- The grid was used only to verify the pre-specified feature is best.

## ANOVA over time (the `feature-importance/` sub-component)

The single-period regression "best feature" is not informative if its explanatory power swings over time. Run ANOVA on per-window R² across the training set; flag features whose contribution is concentrated in fewer than half the windows. These are regime-dependent and should be downweighted.

## Counts to record

Every run logs:

- `features_tested`: actual grid size after caps.
- `lags_tested`: distinct lag count.
- `best_feature_pre_specified`: bool.
- `multiple_testing_correction_needed`: bool.
- `correction_method`: name.
- `out_of_sample_survives`: bool.
- `confidence_cap`: tier.

Without these, the run cannot reach `high` confidence.
