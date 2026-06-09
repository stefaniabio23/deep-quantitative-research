# Statistical validation reference

Background for the `statistical-validation` sub-skill. What each check is, why it exists, and when it caps confidence.

## The check catalogue

| Check | What | Failure mode | Cap if failed |
|---|---|---|---|
| sample_size | Enough observations to draw inference | Too few periods; estimates unstable | medium |
| missingness | Gaps in the series | Selection bias; imputed values masquerade as data | medium (warn) / low (fail) |
| outliers | Extreme values dominate the fit | A single observation drives the regression | medium |
| autocorrelation | Residuals serially correlated | Standard errors understated; significance overstated | medium |
| stationarity | ADF / KPSS on the inputs | Non-stationary → spurious correlation | medium |
| spurious_trend | Both series trending | Trend-driven correlation, not signal | medium |
| lookahead | Predictor known at time T? | Leakage; backtest is a fiction | low |
| survivorship | Universe built in hindsight | Past returns are not past returns | medium |
| restatement | Series revised after first publication | First-vintage predictor and final-vintage target is leakage | medium |
| multiple_testing | Many features searched | Reported p-value understates false-positive risk | medium |
| walk_forward | Train / test progression respected | Single split; no robustness across windows | medium |
| regime_split | Performance stable across regimes | Signal is regime-dependent | medium |
| lag_sensitivity | Result holds at adjacent lags | Single magical lag; brittle | medium |
| transform_sensitivity | Result holds across adjacent transforms | Single magical transform; brittle | medium |
| outlier_sensitivity | Drop top 1% and re-check | Result was the outlier | medium |

A `low` cap on any check propagates to the overall cap. The overall cap is the minimum of all check tiers.

## Confidence tier requirements

From `config/validation_thresholds.yaml`:

- **Low**: sample_size ≥ 30. Anything else can be warn.
- **Medium**: sample_size ≥ 60, walk_forward and OOS survival required.
- **High**: sample_size ≥ 120, walk_forward, regime_split, multiple_testing correction (or pre-specified single feature), feature search bounded under the cap, OOS degradation < 30%.

The cap is the *highest* tier whose required checks all pass. A signal can score well on metrics and still cap at `low` because of an unfixable check (e.g. lookahead risk that cannot be ruled out).

## Newey-West and friends

When autocorrelation is detected:

- Use Newey-West standard errors with a lag length based on the autocorrelation structure.
- Or, prewhiten the residuals.

Do not just report the un-corrected p-value as if the correction were unnecessary.

## Stationarity

ADF (Augmented Dickey-Fuller) and KPSS test different nulls. ADF tests for unit root (null: non-stationary). KPSS tests for stationarity (null: stationary). Run both:

- Both reject their null → ambiguous; the series may be near-integrated.
- ADF rejects, KPSS does not reject → likely stationary.
- ADF does not reject, KPSS rejects → likely non-stationary; difference or detrend.

## Relationship classification

Every validated signal carries a `relationship_type`:

- **causal**: predictor mechanistically drives target.
- **proxy**: predictor co-moves because both reflect a common observable cause.
- **coincident**: same-period co-movement, no lead-lag.
- **lagging**: target leads predictor (relationship is real but the predictor is downstream).
- **mechanically_linked**: definitional or accounting tie (revenue → units sold × price).
- **spurious**: correlated by chance, regime, or shared trend.
- **regime_dependent**: real in one regime, absent in another.

The classification is rarely "causal" outside an experimental setting. "Proxy" is the honest default for most observational signals.

## What a passing report looks like

Every check has a verdict, a value, a threshold, and an explanation. The confidence cap is named with its binding constraint. The recommended next iterations are concrete and would, if successful, lift the cap.

A report with no warnings is suspicious. Real signals usually have at least one yellow.
