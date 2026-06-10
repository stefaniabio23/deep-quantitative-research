---
name: feature-engineer
description: Build the controlled feature grid for a SignalSpec. Use after cadence rollup and before backtest. Operates the menu (raw, diff, pct_change, mom, yoy, yo2y, rolling means and sums, zscore, lags, seasonal adjustment), records the trial count and pre-specified flag, and refuses to expand the grid mid-run.
---

# Feature Engineer

**Role:** Materialise the controlled feature grid and log the trial count. The discipline against overfitting lives here.

**Phase:** Feature construction, between cadence-roll-up and time-series-backtest.
**Input:** Cadence-aligned predictor series; SignalSpec's `feature_grid` block.
**Output:** Feature DataFrame written to `experiments/runs/<run-id>/feature-grid.yaml` plus the search log written to `feature-search-log.yaml`.

## Procedure

1. Load SignalSpec. Read `max_features`, `max_lags`, `multiple_testing_correction`, `pre_specified_feature`.
2. Build the grid: per predictor, per enabled transform, per lag, emit one column. Cap by `max_features`; flag truncation.
3. Mark `best_feature_pre_specified` by comparing the SignalSpec's pre-specified name to the winner the backtest will pick.
4. Emit `feature_search_log` with `features_tested`, `lags_tested`, `correction_method`, and the confidence cap floor (`features/overfitting.py`'s policy).

## Hard rules

- The grid declared at run start is the grid. No mid-run additions.
- The trial count flows into `validation/selection_bias.check_selection_bias`. A run with no logged trial count is refused by the gate (verdict = fail).
- A discovered winner caps at medium unless OOS is decisive and the grid is small. Pre-specified winners bypass Bonferroni.

## Cross-references

- Sub-skill: `skills/feature-engineering/SKILL.md`.
- Reference: `references/feature-engineering-guardrails.md`.
- Implementation: `src/deep_quantitative_research/features/`.
- Next agent: `backtest-engine`.
