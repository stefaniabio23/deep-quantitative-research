# Hypothesis YAML template

Canonical artefact produced by `hypothesis-formulation` and consumed by every later stage. One file per hypothesis. Path: `experiments/ideas/<kebab-slug>.yaml`.

```yaml
hypothesis_id: HYP-2026-NNN
statement: <single-sentence claim with subject, predictor, target, and direction>
domain: finance | biotech | macro | mixed

target_variable: <name as written, NOT a dataset_id>
target_cadence: monthly | quarterly | annual

expected_direction: positive | negative | non-monotonic
expected_lag_periods: [0, 1, 2, 3]   # in target cadence

mechanism: <one-line causal chain, A -> B -> C -> target>

candidate_predictors:
  - <concept 1>
  - <concept 2>

upstream_variables: []
downstream_effects: []
knock_on_effects: []

falsification:
  - <condition 1, e.g. "signal does not lead out-of-sample">
  - <condition 2, e.g. "relationship disappears after controlling for trend">
  - <condition 3, e.g. "signal only works in one cherry-picked period">

created_at: <ISO datetime>
status: candidate | refined | locked | retired
notes: ""
```

## Required fields

`hypothesis_id`, `statement`, `target_variable`, `target_cadence`, `expected_direction`, `mechanism`, `candidate_predictors` (at least one), `falsification` (at least two clauses), `created_at`, `status`.

Anything else is optional but recommended.

## Lifecycle

- `candidate`: drafted, not yet selected for a run.
- `refined`: revised after a clarification loop or after an early run produced a failure mode.
- `locked`: tied to a SignalSpec; do not edit without bumping the SignalSpec version.
- `retired`: tested, refuted, archived. Keep the file; the rejection is a finding.
