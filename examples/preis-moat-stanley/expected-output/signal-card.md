# Preis-Moat-Stanley 2013 Replication: Google Trends "debt" vs DJIA

## Hypothesis

Weekly Google Trends search interest in the term "debt" predicts the following week's DJIA return with a negative sign: when search interest rises above trend, DJIA returns the next week are lower. Pre-registered headline claim from Preis, Moat, Stanley (2013, Scientific Reports), with their 2004-2011 window as train and 2011 onward as the genuine out-of-sample extension.

## Economic Mapping

Predictor concepts to djia_weekly_return via the mechanism declared in the hypothesis. Expected direction: negative.

## Data Inputs

- Target: `yfinance` (`djia_weekly_return`, weekly).
- Predictor: `google-trends` (`debt_interest`, weekly, sentiment, agg=mean).

## Time-Series

- `yfinance` rolled weekly → weekly by sum (periods=1134, partial_dropped=0).
- `google-trends` rolled weekly → weekly by mean (periods=879, partial_dropped=0).

Best feature: `google-trends::zscore_12::lag_2`. Train window 2008-12-07/2014-12-31; test window 2015-01-04/2025-09-28.

## Model Logic

Single-feature linear specification. The test is whether the chosen feature leads the target with the expected sign, not how much can be curve-fit.

## Backtest Summary

| Metric | Train | Test |
| --- | ---: | ---: |
| Correlation | -0.09 | -0.06 |
| Directional accuracy | 0.44 | 0.50 |
| MAE | n/a | 0.93 |
| MAPE (%) | n/a | n/a |
| RMSE | n/a | 1.17 |
| Hit rate | n/a | 0.50 |

OOS degradation: 32.58%.
Sample size (test): 561.

## Current Read

Best feature: google-trends::zscore_12::lag_2. Train r=-0.09, test r=-0.06. OOS degradation 32.6%.

## Related Signals

(none registered yet; populate as the signal library grows)

## Confidence

**Low.** Binding constraint: `multiple_testing`. Tier semantics: see `skills/deep-quantitative-research/references/confidence-tiers.md`.

## Caveats

- `outliers`: 5 observations exceed |z| > 4.0.
- `lag_sensitivity`: adjacent-lag correlation drops 96.4% from best (lag=0); result hinges on a single magical lag.
- `outlier_sensitivity`: dropping top 1.0% of extreme obs drops corr by 68.5%; result is driven by a small number of extreme observations.
- `multiple_testing`: headline r=-0.061 does NOT survive Bonferroni at m=3 (adjusted p=0.4531 >= 0.05). Deflated r=-0.042. Result is plausibly a search artifact.

## Failure Modes

- OOS correlation falling more than 30% below train would invalidate the signal.
- Cadence rollup misclassification (sum vs mean) would silently corrupt the target.

## Next Iteration

- Relationship classified spurious: headline relationship did not survive out-of-sample.
- Pre-specify the feature in SignalSpec.feature_grid.pre_specified_feature; current best (google-trends::zscore_12::lag_2) was discovered.
- Investigate why OOS correlation drops. Probe a regime split and check release_lag handling.

## Links

- SignalSpec: `experiments/specs/preis-moat-stanley-debt-djia.yaml`
- Run artefacts: `experiments/runs/<run-id>/`
