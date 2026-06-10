# Null Control, Phase 3 Oncology Readout Density

## Hypothesis

Monthly Phase 3 oncology readout counts lead quarterly biotech subindex returns by one quarter. (Asserted hypothesis; the data has no such relationship and the pipeline should reject it.)

## Economic Mapping

Predictor concepts to xbi_quarterly_return via the mechanism declared in the hypothesis. Expected direction: positive.

## Data Inputs

- Target: `yfinance` (`xbi_quarterly_return`, quarterly).
- Predictor: `aact` (`phase3_onc_completions`, monthly, count, agg=sum).

## Time-Series

- `yfinance` rolled quarterly → quarterly by sum (periods=71, partial_dropped=0).
- `aact` rolled monthly → quarterly by sum (periods=71, partial_dropped=0).

Best feature: `aact::raw::lag_1`. Train window 2008-03-31/2017-12-31; test window 2018-03-31/2025-09-30.

## Model Logic

Single-feature linear specification. The test is whether the chosen feature leads the target with the expected sign, not how much can be curve-fit.

## Backtest Summary

| Metric | Train | Test |
| --- | ---: | ---: |
| Correlation | 0.09 | 0.17 |
| Directional accuracy | 0.56 | 0.65 |
| MAE | n/a | 25.44 |
| MAPE (%) | n/a | n/a |
| RMSE | n/a | 25.72 |
| Hit rate | n/a | 0.65 |

OOS degradation: -77.23%.
Sample size (test): 31.

## Current Read

Best feature: aact::raw::lag_1. Train r=0.09, test r=0.17. OOS degradation -77.2%.

## Related Signals

(none registered yet; populate as the signal library grows)

## Confidence

**Low.** Binding constraint: `multiple_testing`.

## Caveats

- `sample_size`: 31 samples is enough for low only; medium requires 60.
- `multiple_testing`: headline r=0.167 does NOT survive Bonferroni at m=3 (adjusted p=1.0000 >= 0.05). Deflated r=0.086. Result is plausibly a search artifact.

## Failure Modes

- OOS correlation falling more than 30% below train would invalidate the signal.
- Cadence rollup misclassification (sum vs mean) would silently corrupt the target.

## Next Iteration

- Relationship classified spurious: headline relationship did not survive out-of-sample.
- Investigate why OOS correlation drops. Probe a regime split and check release_lag handling.

## Links

- SignalSpec: `experiments/specs/null-control-onc-readout-density.yaml`
- Run artefacts: `experiments/runs/<run-id>/`
