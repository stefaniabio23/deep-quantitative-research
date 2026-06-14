# Preis-Moat-Stanley 2013 Replication

A pre-registered replication and 13-year out-of-sample extension of:

> Preis, T., Moat, H. S., & Stanley, H. E. (2013).
> *Quantifying trading behavior in financial markets using Google Trends.*
> Scientific Reports 3, 1684.

That paper claimed a strategy keyed on Google Trends search volume for
"debt" generated 326% returns trading the DJIA over 2004-2011. The
authors searched 98 keywords; "debt" was the headline survivor.
Multiple-testing was not corrected for.

This experiment uses the deep-quantitative-research pipeline to:

1. Replicate the in-sample claim with the pipeline's
   `pre_specified_feature` lane (their headline trial, no correction).
2. Extend out-of-sample to 2025-09-30, more than 13 years past the
   paper's data window.
3. Run a small family of related terms (5 to 10) through the same
   SignalSpec and apply Bonferroni correction. If the family-wide
   correction kills "debt" in-sample, the headline was selection
   bias from the start. If it survives, the OOS extension is the
   decisive test.

The publication-decay framing comes from McLean & Pontiff (2016) on
return-predictor decay after publication. The contribution here is
methods: an end-to-end audit with multiple-testing and OOS,
machine-checked by the validation gate.

## Data

- **Target**: DJIA weekly close-to-close return, fetched via
  `yfinance` (^DJI). Public, no auth.
- **Predictor**: Google Trends weekly search interest for "debt"
  (and a family of related terms), fetched via `pytrends`. Stitched
  across 5-year chunks because pytrends switches to monthly
  granularity above a 5-year window. Within-chunk normalization
  to 0-100 is per Google; the pipeline's zscore-12 transform
  absorbs per-chunk scale differences.

To refresh data:

```bash
python3 data/fetch_data.py
```

## SignalSpec

The pre-specified feature is `google-trends::zscore_12::lag_1`:
a 12-week trailing z-score applied to search interest, lagged by
one week. The original paper used a 3-week trailing deviation;
zscore-12 is the closest standard transform in our menu. Their
direction (negative — higher search interest predicts lower
DJIA returns) is encoded as `expected_direction: negative`.

Train window: 2004-01-04 to 2011-02-21 (matches the original
paper exactly).

Test window: 2011-02-28 to 2025-09-30. Note that 2011-present is
the genuine out-of-sample window: it covers the post-publication
era (paper came out 2013-04) plus the COVID regime shift.

## Run

```bash
./run.sh
```

`run.sh` calls `data/fetch_data.py` on first run, then
`deep-quant run-signal` end-to-end. Idempotent.

## What the verdict means

The validation gate produces a confidence cap with a binding
constraint. For this replication, the interesting outcomes are:

- **Cap = high, binding = none**. The signal survives even with
  the pipeline's strict gate. This would be evidence the original
  finding is robust at this sample size and lag.
- **Cap = medium, binding = sample_size or regime_split**. Honest
  but inconclusive at the weekly cadence.
- **Cap = low, binding = multiple_testing** or **out_of_sample**.
  The headline does not survive once trial count is properly
  accounted for, or the relationship died after publication.
  This is the documented null and the more likely outcome by
  the McLean-Pontiff pattern.

A documented null is a finding. The pipeline's tagline is
"refuses to certify what the data does not support"; this
experiment is the test of that tagline against a well-known
public claim.

## Expected output

After `./run.sh`, `expected-output/` contains:

```
run.yaml
cadence-rollup-audit.yaml
feature-grid.yaml
feature-search-log.yaml
backtest-result.yaml
validation-report.yaml
signal-card.md
dashboard.html
```

The signal card carries the headline verdict and binding
constraint; the validation report lists every check's value.

## Family-wide multiple-testing (post-headline)

`data/predictors_family.csv` contains the term family
(`debt, stocks, credit, unemployment, inflation, recession,
mortgage, savings, investment, bankruptcy`). To run the
family-wide test, re-run the pipeline per term and use
`deep-quant render-family-dashboard` to aggregate. If "debt"
clears alone but the family-wide Bonferroni kills it (with the
canonical 1 / m = 0.005 alpha for m=10 terms), the original
result was selection bias.

## Result (run 2026-06-10)

The pipeline produced **the documented null**.

| Field | Value |
|---|---|
| Confidence cap | **low** |
| Binding constraint | `multiple_testing` |
| Relationship type | `spurious` |
| Best feature | `google-trends::zscore_12::lag_2` |
| Train correlation | -0.09 (n = 313, weekly) |
| Test correlation | -0.06 (n = 561, weekly, fully OOS) |
| OOS degradation | 32.6% |
| Pre-specified feature wins? | No (the headline lag_1 lost to lag_2 by a sliver) |
| Bonferroni-adjusted p (m = 3 lags) | 0.45 |
| Deflated r | -0.04 |

The pipeline picked `lag_2` over the pre-specified `lag_1`, so the
pre-specification protection does not apply — Bonferroni runs.
Adjusted p = 0.45 means the result is statistically
indistinguishable from noise even at the single-keyword level.

The validation gate flagged three additional concerns:

- **Lag sensitivity warn.** Adjacent-lag correlation drops 96.4%
  from the best lag. The result hinges on a single magical lag, which
  is the signature of an overfit on a small effect.
- **Outlier sensitivity warn.** Dropping the top 1% of paired
  extremes drops the correlation by 68.5%. A handful of observations
  drive the headline.
- **Outliers warn.** Five observations exceed |z| > 4 on the test
  target.

The original 326% return claim almost certainly came from selection
bias across 98 keywords, but even the simpler predictive question
("does Google Trends 'debt' lead DJIA returns with the claimed sign?")
fails honest validation in a 561-week true out-of-sample window.

### Why this matters

This is what the pipeline's tagline means in practice. A famous, much-
cited result, fed through the same process biotech-pos and null-
control go through, gets classified `spurious` with a named binding
constraint. No editorial judgment, no narrative override.

A documented null is a finding. This one is also a methods
demonstration: when the discipline is mechanical and the trial count
is explicit, the false positives that fuel academic finance literature
get caught at the gate.

## Caveats

- Google Trends data is normalized per chunk and per query. Within
  a chunk it is a 0-100 index; absolute scale is meaningless.
  The pipeline's z-score transform is what matters here.
- pytrends rate-limits aggressively. The fetcher uses 1.5s sleeps
  between calls and retries on failure. A failed family fetch
  still leaves `target.csv` and `predictor_debt.csv` usable for
  the headline run.
- The original paper used a single-asset long/short PnL backtest.
  Our pipeline tests the underlying predictive relationship
  (correlation + significance with multiple-testing correction).
  The two questions are tightly coupled: if the predictive
  relationship doesn't survive, the PnL story falls with it.
