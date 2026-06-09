# {{Signal Name}}

The canonical signal-card layout. Every signal that ships uses this structure. Path: `experiments/runs/<run-id>/signal-card.md`.

## Hypothesis

{{Single-sentence claim. What real-world variable does this predict? Include subject, predictor concept, target, direction.}}

## Economic Mapping

{{Data → KPI → Financial outcome. One-line causal chain.}}

## Data Inputs

- Target: `{{target_dataset_id}}` ({{cadence}}, {{source notes}}).
- Predictor: `{{predictor_dataset_id}}` ({{cadence}}, {{variable_type}}, {{aggregation}}).
- Context: `{{context_dataset_id}}` ({{purpose}}).

## Time-Series

{{Aligned cadence, period covered, release-lag applied. Best feature name and its lag. One paragraph.}}

## Model Logic

{{Explain simply, no code. What does the model do, why is the specification this and not something more complex.}}

## Backtest Summary

KPI prediction mode:

| Metric | Train | Test |
|---|---:|---:|
| Correlation | {{train_corr}} | {{test_corr}} |
| Directional accuracy | {{train_dir}} | {{test_dir}} |
| MAE | | {{mae}} |
| Hit rate | | {{hit_rate}} |
| OOS degradation | | {{oos_deg}}% |

(Tradable mode uses the alternative metric panel from `time-series-backtest`.)

## Current Read

{{What is the signal saying right now? Most recent prediction plus look-through to today. Two or three sentences.}}

## Related Signals

- `{{related_signal_id}}`: confirming | contradicting | neutral. {{One-line rationale.}}

## Confidence

**{{Low | Medium | High}}.** Binding constraint: `{{check_name}}`.

(The confidence statement mirrors the `validation_report.confidence_cap` field exactly. No editorial upgrades.)

## Caveats

- {{Caveat 1, sourced from dataset contracts and validation report.}}
- {{Caveat 2.}}

## Failure Modes

- {{When did this signal historically break? News, regime shift, structural change.}}
- {{What would visibly tell us it has broken again?}}

## Next Iteration

- {{One concrete experiment that would lift the confidence cap.}}
- {{Another.}}

## Links

- Hypothesis: `experiments/ideas/{{slug}}.yaml`
- SignalSpec: `experiments/specs/{{slug}}.yaml`
- Dataset contracts: `experiments/runs/{{run_id}}/dataset-contracts.yaml`
- Cadence audit: `experiments/runs/{{run_id}}/cadence-rollup-audit.yaml`
- Feature grid: `experiments/runs/{{run_id}}/feature-grid.yaml`
- Backtest: `experiments/runs/{{run_id}}/metrics.json`
- Validation: `experiments/runs/{{run_id}}/validation-report.md`
- Dashboard: `experiments/runs/{{run_id}}/dashboard.html`
