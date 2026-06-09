---
name: dataset-selection
description: Score and select datasets by hypothesis fit, not availability. Applies the dataset_fit_score rubric (economic proximity, coverage, cadence fit, release-lag clarity, point-in-time safety, survivorship-bias risk, API scriptability, cost) and returns target, predictor, context, and rejected datasets with reasoning. Invoke after datasource-query.
---

# dataset-selection

## When to invoke

You have a candidate set from `datasource-query` and need to commit to a target, predictors, and context datasets for a SignalSpec. This is the step that prevents "we used X because we had it" research.

## Inputs

- `experiments/specs/dataset-candidates.yaml` from `datasource-query`.
- The original hypothesis at `experiments/ideas/<slug>.yaml`.
- Weights at `config/scoring_weights.yaml` (defaults are sensible; override per domain only when justified).

## Procedure

1. Read the hypothesis and candidate set.
2. For each candidate, run `deep-quant score-dataset <dataset_id> --hypothesis <path>`. Capture all 8 axes plus `total_score`.
3. Apply the rubric below to assign roles: `target`, `predictor`, `context`, or `rejected`.
4. For every rejection, record a one-line reason. A reason like "low score" is not acceptable; name the axis (e.g. "rejected: cadence_fit=3, native annual but hypothesis wants monthly").
5. Emit the `dataset-selection` block (schema below) and append it to the in-flight SignalSpec, or write it to `experiments/specs/<slug>-selection.md` if no SignalSpec exists yet.
6. Suggest the next step: `/design-signal` to consolidate into a full SignalSpec.

## The dataset_fit_score rubric

Each axis is 0 to 10. Weighted mean produces `total_score` (also 0 to 10).

| Axis | What it captures | Default weight |
|---|---|---|
| economic_proximity | How close in the causal chain to the target variable | 1.5 |
| coverage | Geography, time span, entity universe | 1.0 |
| cadence_fit | Native vs target cadence; rollup-feasible vs forced | 1.2 |
| release_lag_clarity | Is the publication lag known and stable? | 1.0 |
| point_in_time_safety | Was the value observable when it claims to be? | 1.3 |
| survivorship_bias_risk | Lower score = higher risk (equity universes especially) | 1.1 |
| api_scriptability | REST / bulk vs scrape / manual | 0.8 |
| cost_access_practicality | Free + no key > free + key > freemium > paid | 0.6 |

Decision thresholds (from `config/scoring_weights.yaml`):

- `total_score < 4.0` → reject.
- `4.0 ≤ total_score < 6.0` → flag for review, do not auto-include.
- `total_score ≥ 6.0` → eligible.
- `total_score ≥ 8.0` → high-fit; prefer over lower-scoring alternatives for the same role.

## Role assignment

- **Target**: the dataset that carries the variable named in `target_variable`. Usually one. Multiple targets only when the hypothesis explicitly tests cross-target consistency.
- **Predictor**: the dataset whose values you regress / correlate against the target. One or more, but the count of predictors plus the count of features-per-predictor controls overfitting risk; fewer is safer.
- **Context**: not regressed directly; used for interpretation, regime tagging, or robustness checks (e.g. macro indicators for a sector signal).
- **Rejected**: scored and dismissed. Recording these is mandatory so the next iteration knows what was already considered.

## Hard rules

- **Score every candidate.** Skipping a score because the dataset "obviously fits" hides bias.
- **Record rejections with a named axis.** Future you needs to know what was tried.
- **Choose by score, not availability.** If the best-scoring target is paid or hard to access, name the trade-off explicitly.
- **One target unless the hypothesis is explicitly multi-target.**

## Output schema

```yaml
dataset_selection:
  hypothesis_id: HYP-2026-NNN
  registry_commit: <sha>
  scoring_weights_path: config/scoring_weights.yaml
  target:
    dataset_id: <id>
    field_of_interest: <field>
    score: <0-10>
    rationale: <one sentence>
  predictors:
    - dataset_id: <id>
      predictor_concept: <which hypothesis predictor>
      field_of_interest: <field>
      score: <0-10>
      expected_lag_periods: [0, 1, 2, 3]
      rationale: <one sentence>
  context:
    - dataset_id: <id>
      role_in_interpretation: <one sentence>
  rejected:
    - dataset_id: <id>
      score: <0-10>
      reason: <one sentence naming the worst axis>
```

## Worked example

Markdown summary written alongside the YAML:

```md
## Selected Datasets

### Target
- `ons-retail-sales-index` (score 9.1). Monthly, official, point-in-time-safe.

### Predictors
- `google-trends-retail-searches` (score 7.4). Closest to demand intent. Caveat: normalised index, values can change between pulls.
- `boe-consumer-credit` (score 6.8). Provides consumer-liquidity context.

### Rejected
| Dataset | Score | Reason |
|---|---:|---|
| `barclays-consumer-spending` | 5.2 | cost_access_practicality=3 (institutional access only) |
| `random-twitter-mentions` | 3.1 | economic_proximity=2 (predictor not in causal chain) |
```

## Cross-references

- Scoring: `src/deep_quantitative_research/registry/scoring.py`.
- Template: `templates/dataset-selection-template.md`.
- Next sub-skill: `dataset-contract`.
- Spec: `BUILD_CHECKLIST.md` section 7.3.
