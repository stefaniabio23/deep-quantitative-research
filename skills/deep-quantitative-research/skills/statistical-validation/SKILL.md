---
name: statistical-validation
description: Prevent false confidence. Runs the full validation gate, sample size, missingness, outliers, autocorrelation, stationarity, spurious-trend, lookahead, survivorship, restatement, multiple-testing correction, walk-forward, regime split, lag sensitivity, transform sensitivity. Caps confidence at the lowest tier whose checks pass and writes a validation report.
---

# statistical-validation

## When to invoke

You have backtest metrics from `time-series-backtest`. Before the result becomes a signal card it has to pass the validation gate.

This is the last place to catch false-positive results before they get published. A red check here is more useful than a green report later.

## Inputs

- `experiments/runs/<run-id>/metrics.json` from `time-series-backtest`.
- Feature search log from `feature-engineering`.
- Dataset contracts for PIT and release-lag.
- Thresholds from `config/validation_thresholds.yaml`.

## The checks

Each check returns `pass | warn | fail`. Confidence is capped at the lowest tier whose required checks all pass.

| Check | Purpose | Failure mode |
|---|---|---|
| sample_size | Enough observations to draw an inference | Too few periods; reject above `medium` |
| missingness | Gaps in the series | Above the warn pct, cap confidence; above fail pct, reject |
| outliers | Extreme values dominate the fit | Refit with winsorisation; if signal disappears, the original was an artefact |
| autocorrelation | Residuals serially correlated | Standard errors understated; rerun with Newey-West |
| stationarity | ADF / KPSS on the inputs | Non-stationary inputs can produce spurious correlations |
| spurious_trend | Both series trending | Detrend or first-difference; if signal disappears, it was trend |
| lookahead | Predictor known at time T? | Re-shift by `release_lag_days`; signal collapse confirms leak |
| survivorship | Universe constructed in hindsight | Cap confidence; rebuild with point-in-time universe to lift |
| restatement | Series revised after first publication | Use the first-vintage data; signal that survives is stronger |
| multiple_testing | Many features searched | Apply Benjamini-Hochberg to per-feature p-values; only survivors count |
| walk_forward | Train / test progression respected | Single split caps at `medium` |
| regime_split | Performance stable across regimes | Persistent regime dependence caps at `medium` |
| lag_sensitivity | Result depends on a single magical lag | Confidence cap until robust across lags ± 1 |
| transform_sensitivity | Result depends on a single magical transform | Confidence cap until robust across adjacent transforms |
| outlier_sensitivity | Drop top 1% of observations and re-check | Material drop means an artefact, not a signal |

## Procedure

1. Read every input; verify presence of `feature_search_log` and `metrics_kpi` / `metrics_tradable`.
2. Run every check. For each, record `pass | warn | fail`, the value observed, the threshold, and a one-line explanation.
3. Compute the confidence cap from `config/validation_thresholds.yaml`. The cap is the lowest tier whose required checks all pass.
4. Classify the relationship using `causal-inference` (sub-skill) and attach the relationship_type.
5. Emit `experiments/runs/<run-id>/validation-report.md` (schema below).
6. If the cap is `low` and the user explicitly opted into the run, still pass; the report names exactly what is weak.
7. Hand off to `signal-synthesis`.

## Hard rules

- **No green light without a check.** Every check runs every time; skipped checks fail the gate.
- **Cap at the lowest tier that passes.** Do not average; one red drops the ceiling.
- **Never declare high without OOS survival, walk-forward, regime split, multiple-testing correction, and feature search bounded.**
- **Name the binding constraint.** The report must point at the specific check that determined the cap.
- **A null result is a finding.** Capping at `low` and naming exactly why is a valid output; do not force a `medium`.

## Output schema

```yaml
validation_report:
  signal_id: <id>
  registry_commit: <sha>
  checked_at: <iso datetime>

  checks:
    - name: sample_size
      verdict: pass | warn | fail
      value: <number>
      threshold: <number>
      explanation: <one line>
    # ... one entry per check

  confidence_cap: low | medium | high
  binding_constraint: <check name>
  relationship_type: causal | proxy | coincident | lagging | mechanically_linked | spurious | regime_dependent

  recommended_next_iterations:
    - <one line>
```

## Worked example

```yaml
validation_report:
  signal_id: uk-retail-search-demand-signal
  registry_commit: a85c10825a9ec5dd5010a9dbf4bbfe1d4959264f
  checked_at: 2026-06-09T18:30:00Z
  checks:
    - {name: sample_size, verdict: pass, value: 120, threshold: 60, explanation: 120 monthly periods clears all tiers.}
    - {name: missingness, verdict: pass, value: 0.0, threshold: 5.0, explanation: zero gaps after rollup.}
    - {name: lookahead, verdict: pass, value: 0, threshold: 0, explanation: release_lag_days applied; probe-shuffle test passes.}
    - {name: multiple_testing, verdict: pass, value: pre-specified, threshold: BH, explanation: single pre-specified feature; correction not required.}
    - {name: walk_forward, verdict: pass, value: 36, threshold: 24, explanation: 36-month rolling walk-forward windows used.}
    - {name: regime_split, verdict: warn, value: 0.41, threshold: 0.30, explanation: post-COVID regime shows materially weaker correlation.}
    - {name: lag_sensitivity, verdict: pass, value: stable, threshold: stable, explanation: best lag 1, ±1 lags within 0.07 correlation.}
  confidence_cap: medium
  binding_constraint: regime_split
  relationship_type: proxy
  recommended_next_iterations:
    - Add a post-COVID regime control and rerun.
    - Test category-level Google Trends signals to see if any category survives the regime shift.
```

## Cross-references

- Reference: `references/statistical-validation.md`.
- Implementation: `src/deep_quantitative_research/validation/` (Phase 4).
- Next sub-skill: `signal-synthesis`.
- Spec: `BUILD_CHECKLIST.md` section 7.8.
