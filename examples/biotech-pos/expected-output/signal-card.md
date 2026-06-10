# Biotech PoS, Oncology Phase 3 Readout Density

## Hypothesis

Monthly Phase 3 oncology trial readout count leads quarterly biotech subindex returns by one quarter via re-rating of pipeline NPVs across the oncology-heavy subindex.

## Economic Mapping

Predictor concepts to xbi_quarterly_return via the mechanism declared in the hypothesis. Expected direction: positive.

## Data Inputs

- Target: `yfinance` (`xbi_quarterly_return`, quarterly).
- Predictor: `aact` (`phase3_onc_completions`, monthly, count, agg=sum).

## Time-Series

- `yfinance` rolled quarterly → quarterly by sum (periods=70, partial_dropped=0).
- `aact` rolled monthly → quarterly by sum (periods=71, partial_dropped=0).

Best feature: `aact::raw::lag_1`. Train window 2008-03-31/2017-12-31; test window 2018-03-31/2025-09-30.

## Model Logic

Single-feature linear specification. The test is whether the chosen feature leads the target with the expected sign, not how much can be curve-fit.

## Backtest Summary

| Metric | Train | Test |
| --- | ---: | ---: |
| Correlation | 0.57 | 0.33 |
| Directional accuracy | 0.36 | 0.55 |
| MAE | n/a | 32.80 |
| MAPE (%) | n/a | n/a |
| RMSE | n/a | 33.81 |
| Hit rate | n/a | 0.55 |

OOS degradation: 42.80%.
Sample size (test): 31.

## Current Read

Best feature: aact::raw::lag_1. Train r=0.57, test r=0.33. OOS degradation 42.8%.

## Related Signals

(none registered yet; populate as the signal library grows)

## Confidence

**Medium.** Binding constraint: `sample_size`.

## Caveats

- `sample_size`: 31 samples is enough for low only; medium requires 60.
- `stationarity_adf`: ADF p=0.069 >= 0.05; cannot reject unit root, consider differencing or detrending.
- `lag_sensitivity`: adjacent-lag correlation drops 58.1% from best (lag=0); result hinges on a single magical lag.
- `multiple_testing`: headline r=0.327 does NOT survive Bonferroni at m=3 (adjusted p=0.2185 >= 0.05). Deflated r=0.246. Result is plausibly a search artifact.

## Failure Modes

- OOS correlation falling more than 30% below train would invalidate the signal.
- Cadence rollup misclassification (sum vs mean) would silently corrupt the target.

## Next Iteration

- Address stationarity_adf: differencing or detrending may stabilise the result.

## Links

- SignalSpec: `experiments/specs/biotech-pos-onc-readout-density.yaml`
- Run artefacts: `experiments/runs/<run-id>/`
