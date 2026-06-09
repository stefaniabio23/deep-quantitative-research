---
name: time-series-backtest
description: Evaluate whether predictors have useful relationship to target variables. Two modes, KPI prediction (rolling correlation, rank correlation, directionality, MAE / MAPE / RMSE, hit rate, lead-lag profile, OOS degradation) and tradable signal (CAGR, Sharpe, Sortino, max drawdown, turnover, transaction costs, benchmark alpha / beta, walk-forward).
---

# time-series-backtest

## When to invoke

You have a feature grid and the cadence-aligned target. Now run the backtest.

This sub-skill exists primarily to keep KPI prediction and tradable-signal backtests from getting mixed up. The metrics are different. The cost models are different. The interpretation is different. Pick one mode per run.

## Inputs

- Feature grid + feature search log from `feature-engineering`.
- Cadence-aligned target series.
- The SignalSpec's `validation` block (train / test split, walk-forward toggle, regime split).
- Dataset contracts for release-lag and PIT enforcement.

## The two modes

### Mode A, KPI prediction

`predictor → company KPI / economic variable`

The question: does the predictor lead the target with usable accuracy?

Metrics:

- rolling_correlation (Pearson and Spearman)
- rank_correlation
- directionality (sign agreement)
- directional_accuracy
- MAE
- MAPE
- RMSE
- hit_rate (top-decile or sign-correct)
- lead_lag_profile (correlation by lag, 0 to N)
- out_of_sample_degradation (train metric minus test metric)

### Mode B, tradable signal

`predictor → asset return / spread / factor`

The question: does the predictor produce a tradable PnL after costs?

Metrics:

- CAGR
- Sharpe
- Sortino
- maximum_drawdown
- hit_rate
- turnover
- transaction_costs (basis points modelled)
- benchmark_alpha
- benchmark_beta
- exposure
- walk-forward verdict
- capacity_caveat (rough $ size before signal degrades)

The same mechanic test (correlation) can produce a "good signal" in Mode A and an "unprofitable signal" in Mode B once costs apply. Always name the mode.

## Procedure

1. Read the SignalSpec; confirm the run mode (KPI prediction vs tradable).
2. Align target and predictor features to the same cadence and release-lag schedule.
3. Refuse to proceed if any predictor lacks `release_lag_days` or `point_in_time_safe` in its contract.
4. Split the data per `validation.train_period` / `validation.test_period`. Reserve test as untouched until train is locked.
5. Mode A: compute every metric in the KPI list, both train and test, plus the lead-lag profile.
   Mode B: simulate the backtest with realistic transaction costs, optional slippage, and walk-forward windows.
6. Compute `out_of_sample_degradation`. Anything > 30% relative drop is a flag.
7. Emit `experiments/runs/<run-id>/metrics.json` (the structured numbers) and `experiments/runs/<run-id>/backtest-summary.md` (the human-readable narrative).
8. Pass to `statistical-validation` for the gate.

## Hard rules

- **Pick one mode per run.** Mixing KPI and tradable metrics in one report is a category error.
- **Never let predictor data leak into the test window.** Apply release-lag everywhere; verify with a probe (shuffle the test window and assert the backtest score collapses).
- **Walk-forward where possible.** Single train / test split is acceptable but caps confidence at `medium`.
- **Report OOS degradation explicitly.** A train Sharpe of 2.5 and test Sharpe of 0.4 is not a successful backtest.
- **Costs are not optional in Mode B.** A pre-cost Sharpe means nothing; quote post-cost or do not run Mode B.

## Output schema

```yaml
backtest_result:
  mode: kpi_prediction | tradable_signal
  signal_id: <id>
  target: <field or composite>
  best_feature: <feature name>
  period:
    train: YYYY-MM-DD/YYYY-MM-DD
    test: YYYY-MM-DD/YYYY-MM-DD
  walk_forward: true | false
  regime_split: true | false

  # Mode A
  metrics_kpi:
    correlation_train: <number>
    correlation_test: <number>
    rank_correlation_test: <number>
    directional_accuracy_train: <number>
    directional_accuracy_test: <number>
    mae_test: <number>
    mape_test: <number>
    rmse_test: <number>
    hit_rate_test: <number>
    lead_lag_profile: [{lag: <int>, corr: <number>}]
    oos_degradation_pct: <number>

  # Mode B
  metrics_tradable:
    cagr: <number>
    sharpe: <number>
    sortino: <number>
    max_drawdown: <number>
    hit_rate: <number>
    turnover: <number>
    transaction_costs_bps: <number>
    benchmark_alpha: <number>
    benchmark_beta: <number>
    capacity_usd_estimate: <number>

  verdict:
    survives_oos: true | false
    confidence: low | medium | high
    notes: <one or two sentences>
```

## Worked example

```yaml
backtest_result:
  mode: kpi_prediction
  signal_id: uk-retail-search-demand-signal
  target: retail_sales_yoy
  best_feature: google_trends_yoy_1y_lag_1
  period:
    train: 2016-01-01/2021-12-31
    test: 2022-01-01/2025-12-31
  walk_forward: true
  regime_split: true
  metrics_kpi:
    correlation_train: 0.71
    correlation_test: 0.44
    rank_correlation_test: 0.49
    directional_accuracy_train: 0.69
    directional_accuracy_test: 0.61
    mae_test: 1.2
    mape_test: 8.4
    rmse_test: 1.6
    hit_rate_test: 0.62
    lead_lag_profile:
      - {lag: 0, corr: 0.31}
      - {lag: 1, corr: 0.44}
      - {lag: 2, corr: 0.41}
      - {lag: 3, corr: 0.28}
    oos_degradation_pct: 38
  verdict:
    survives_oos: true
    confidence: medium
    notes: OOS degradation 38% is at the edge; lead-lag confirms 1-period lead is the real signal.
```

## Cross-references

- Reference: `references/backtesting-pitfalls.md`.
- Implementation: `src/deep_quantitative_research/backtest/` (Phase 4).
- Next sub-skill: `statistical-validation`.
- Spec: `BUILD_CHECKLIST.md` section 7.7.
