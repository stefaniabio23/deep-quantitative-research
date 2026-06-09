# Validation Report

Path: `experiments/runs/<run-id>/validation-report.md`. Machine-readable counterpart is `validation_report.yaml`.

## Run

- Signal: `{{signal_id}}`
- Registry commit: `{{commit_hash}}`
- Checked at: `{{iso_datetime}}`

## Checks

Each check returns `pass`, `warn`, or `fail`. Confidence is capped at the lowest tier whose required checks pass.

| Check | Verdict | Value | Threshold | Explanation |
|---|---|---:|---:|---|
| sample_size | | | | |
| missingness | | | | |
| outliers | | | | |
| autocorrelation | | | | |
| stationarity | | | | |
| spurious_trend | | | | |
| lookahead | | | | |
| survivorship | | | | |
| restatement | | | | |
| multiple_testing | | | | |
| walk_forward | | | | |
| regime_split | | | | |
| lag_sensitivity | | | | |
| transform_sensitivity | | | | |
| outlier_sensitivity | | | | |

## Confidence cap

**{{Low | Medium | High}}.**

Binding constraint: `{{check_name}}`.

## Relationship classification

`{{causal | proxy | coincident | lagging | mechanically_linked | spurious | regime_dependent}}`.

Justification: {{one or two sentences from causal-inference}}.

## Recommended next iterations

1. {{One concrete experiment that would lift the cap.}}
2. {{Another.}}

## Notes

{{Anything that did not fit the table. Edge cases, contested judgements, manual overrides.}}
