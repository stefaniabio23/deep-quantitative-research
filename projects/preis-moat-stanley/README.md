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

## Family-wide multiple-testing (the McLean-Pontiff frame)

`data/predictors_family.csv` carries the 10-term family
(`debt, stocks, credit, unemployment, inflation, recession,
mortgage, savings, investment, bankruptcy`). With 3 lags per term,
the family is **m = 30 trials**. To run:

```bash
python3 run_family.py
```

The script reuses the pipeline's `zscore_12` transform and
`correlation_p_value` primitive; the SignalSpec window split (train
2008-12 to 2014-12, test 2015-01 to 2025-09) applies per trial.

### Result (run 2026-06-14)

**0 of 30 trials survive Bonferroni in-sample (alpha = 0.05).**
**1 of 30 trials survives Bonferroni out-of-sample.**

The single OOS survivor is `recession` at lag 1
(test r = -0.141, raw p = 0.001, Bonferroni-adjusted p = 0.024). Under
Bonferroni at m = 30 we expect 5% chance of any one trial firing
under the null; getting 1 of 30 is within noise rather than evidence.

Headline interpretation:

- Even **before** any multiple-testing correction, no term-lag
  combination has a significant in-sample correlation at alpha = 0.05.
  The smallest in-sample raw p-value across 30 trials is 0.088 (for
  `investment` at lag 2). The famous 326% PnL number cannot have
  come from a predictive relationship of the strength implied; it
  came from picking the strategy that happened to win after the fact
  across 98 keywords and a parameter grid.
- For `debt` specifically — the paper's headline term — the
  publication-decay pattern is visible. Train r = -0.074 at lag 1
  decays to test r = +0.003. Lag 2 holds train r = -0.090 but test
  r = -0.061 (also non-significant). Lag 3 train r = -0.046 decays
  to test r = +0.003.

See `expected-output/family-results.csv` for the full 30-row table
and `expected-output/family-summary.md` for the rendered markdown.

### Methodological note

The original paper tested 98 keywords and reported the top performer.
With m = 98 and the canonical alpha = 0.05, the per-trial Bonferroni
threshold is 0.00051. A correlation of |r| ≈ 0.20 with n ≈ 500 has
p ≈ 1e-6 — that **would** clear the bar. But the actual paper's
data (2004-2011, ~365 weekly obs) suggests an even higher r needed.
Even with 365 obs, hitting Bonferroni at m = 98 requires |r| > 0.21.
The original paper's headline correlation between "debt"
search-volume deviation and DJIA return was on the order of 0.06-
0.10 (consistent with what we measure here). It was the PnL through
a long/short trading rule that produced the 326% number, not the
underlying predictive correlation.

This is the McLean-Pontiff finding generalised: when you apply the
multiple-testing correction the original methodology hid, the
return predictor is gone. When you extend the period out-of-sample,
the predictor that was already gone stays gone.

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
