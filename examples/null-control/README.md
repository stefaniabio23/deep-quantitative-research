# Null-Control Demo

A negative control for the deep-quantitative-research pipeline. The
biotech-pos demo proves the pipeline can recover a planted signal; this
demo proves it refuses to manufacture one out of noise.

## The setup

- **Predictor.** Monthly Poisson-distributed counts. White noise. No
  trend, no regime shift, no relationship to anything.
- **Target.** Quarterly Gaussian returns from a completely independent
  random stream. By construction, the predictor cannot lead, lag, or
  co-move with the target beyond random luck.
- **SignalSpec.** Asserts the same one-quarter-lead hypothesis as
  biotech-pos. The hypothesis is false here on purpose.

If a correctly tuned pipeline finds a meaningful relationship in this
dataset, that is a regression. The expected behaviour is:

1. Best-feature correlation drifts near zero.
2. `multiple_testing` check warns or fails (Bonferroni-adjusted p-value
   well above alpha).
3. Validation gate caps confidence at `low`.
4. Signal card and dashboard both report a defensible null with the
   binding constraint named.

## Why this matters

The repo's tagline is "honest null results." That claim requires both:

- a planted-signal test (biotech-pos), and
- a planted-nothing test (this demo).

A pipeline that passes only the first is one that finds what it's
looking for. A pipeline that passes both is one that says no when no is
the right answer. That second property is the actual differentiator.

## Run

```bash
./run.sh
```

The script regenerates the CSVs from a fixed seed, runs the pipeline,
and writes every artefact into `expected-output/`. Idempotent.

## Expected output

After `./run.sh`, `expected-output/` should contain the same artefact
set as biotech-pos:

```
run.yaml                       run metadata and registry commit
cadence-rollup-audit.yaml      rollup decisions
feature-grid.yaml              feature names emitted + caps applied
feature-search-log.yaml        trial count + pre-specified flag + cap
backtest-result.yaml           KPI metric panel + lead-lag + OOS
validation-report.yaml         every check verdict + binding constraint
signal-card.md                 the human-readable signal card
dashboard.html                 self-contained HTML dashboard
```

The headline difference from biotech-pos: the `verdict.confidence` and
`validation.confidence_cap` should both be `low`, and the
`multiple_testing` check should fire (since the SignalSpec deliberately
does not pre-specify a feature, forcing Bonferroni onto the three
lag-shifted variants).

If a future commit silently turns this run into a "medium" or "high"
verdict, that's a bug — open an issue rather than ratifying the
regression.
