---
name: feature-engineering
description: Generate controlled feature grids (raw, diff, pct_change, mom, yoy, yo2y, rolling mean / sum, zscore, lags, seasonally adjusted) with hard caps from config. Records every feature and lag tested, flags multiple-testing risk, marks whether the winning feature was pre-specified or discovered, and caps confidence accordingly.
---

# feature-engineering

## When to invoke

You have cadence-aligned series for the target and predictors. Now you build the predictor features for the backtest.

The point of this sub-skill is to make feature search a logged, bounded experiment instead of a hidden over-fitting machine. Every transformation tried gets recorded. The winning feature is marked as either pre-specified (claimed before running) or discovered (found by search). The marking changes the confidence cap downstream.

## Inputs

- Cadence-aligned predictor series from `cadence-roll-up`.
- The SignalSpec's `feature_grid` block (max features, max lags, multiple-testing correction).
- The Hypothesis YAML (for the pre-specified feature, if any).
- Config defaults from `config/research_defaults.yaml`.

## The default controlled grid

These transforms are the menu. The SignalSpec selects which to enable; defaults below.

```yaml
features:
  - raw
  - diff
  - pct_change
  - mom_1p
  - mom_3p
  - yoy_1y
  - yo2y
  - rolling_mean_3
  - rolling_mean_6
  - rolling_sum_3
  - rolling_sum_12
  - zscore_12
  - zscore_24
  - lag_1
  - lag_2
  - lag_3
  - seasonally_adjusted_if_available
```

Each predictor's features are crossed with the lag set declared in the SignalSpec. `max_features` and `max_lags` cap the size of the grid.

## Procedure

1. Load the SignalSpec. Read `max_features`, `max_lags`, `multiple_testing_correction`, and any pre-specified feature.
2. Build the grid: for each predictor, for each enabled transform, for each lag, emit one feature column. Stop if `max_features` is hit; record the cut.
3. Compute every feature against the cadence-aligned target.
4. Optional: run feature-importance (ANOVA over time windows; see `feature-importance/` sub-component) to flag features whose explanatory power is unstable.
5. Record the feature search log (schema below).
6. Pass the grid + log to `time-series-backtest`.

## Hard rules

- **Record every feature tested.** Not just the winner. Future you needs the count for multiple-testing correction.
- **Mark pre-specified vs discovered.** The Hypothesis YAML names a pre-specified feature; anything not in that list that wins is `discovered`. A discovered winner caps confidence at `medium` unless OOS is decisive.
- **Apply multiple-testing correction when the grid is large.** Defaults to Benjamini-Hochberg per `config/research_defaults.yaml`. Skipping is allowed only when there is a single pre-specified feature.
- **Cap confidence on overfit risk.** If `features_tested * lags_tested > 50`, the run cannot reach `high` confidence regardless of OOS performance.
- **Never sneak in a transform mid-run.** All transforms are declared up front; expanding the grid mid-experiment counts as a new run.

## Output schema

```yaml
feature_grid:
  signal_id: <id>
  predictor_dataset_ids: [<id>]
  enabled_transforms: [<transform>]
  max_features: <integer>
  max_lags: <integer>
  lags: [0, 1, 2, 3]

  features_emitted: <integer>     # actual grid size after caps

feature_search_log:
  features_tested: <integer>
  lags_tested: <integer>
  best_feature: <feature name>
  best_feature_pre_specified: true | false
  multiple_testing_correction_needed: true | false
  correction_method: benjamini_hochberg | bonferroni | none
  out_of_sample_survives: true | false | unknown
  confidence_cap: low | medium | high
  truncated_at_max_features: true | false
```

## Worked example

```yaml
feature_grid:
  signal_id: uk-retail-search-demand-signal
  predictor_dataset_ids: [google-trends-retail-searches, boe-consumer-credit]
  enabled_transforms: [raw, yoy_1y, rolling_mean_3, zscore_12]
  max_features: 40
  max_lags: 3
  lags: [0, 1, 2, 3]
  features_emitted: 32

feature_search_log:
  features_tested: 32
  lags_tested: 3
  best_feature: google_trends_yoy_1y_lag_1
  best_feature_pre_specified: true   # SignalSpec named yoy_1y on Google Trends as pre-specified
  multiple_testing_correction_needed: false  # single pre-specified feature
  correction_method: none
  out_of_sample_survives: true
  confidence_cap: high
  truncated_at_max_features: false
```

## Cross-references

- Reference: `references/feature-engineering-guardrails.md`.
- Implementation: `src/deep_quantitative_research/features/` (Phase 4).
- Next sub-skill: `time-series-backtest`.
- Spec: `BUILD_CHECKLIST.md` section 7.6.
