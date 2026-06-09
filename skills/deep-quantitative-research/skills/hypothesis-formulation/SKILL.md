---
name: hypothesis-formulation
description: Convert a vague research idea into a specific, falsifiable hypothesis with target variable, candidate predictors, expected direction, expected lag, economic mechanism, and falsification criteria. Emits a Hypothesis YAML consumed by datasource-query and dataset-selection. Invoke when the user states a research idea or asks "what would we have to believe to call this true / false".
---

# hypothesis-formulation

## When to invoke

The user has a research idea (a vague claim, a "what if", a thesis pitch). Your job is to turn it into something testable.

You are not searching for data yet. You are not selecting datasets. You are forcing the idea to make a prediction sharp enough that a backtest can refute it.

## Inputs

- A short research idea, one or two sentences.
- Optional: domain (finance / biotech / macro / etc), suspected mechanism, target KPI or asset outcome, candidate predictor concepts, desired cadence, investment or research use case.

If anything below is missing, ask the user one question at a time. Do not assume.

## The seven questions

Work through these in order. The user's answers populate the hypothesis YAML.

1. What research question are we trying to answer? Force a single sentence.
2. What target variable do we need? A specific KPI, return series, or measurable outcome.
3. What observable proxy could predict it? Name the candidate, not the dataset.
4. What upstream variables could predict it? The earlier rungs of the causal chain.
5. What downstream effects might reveal it? Lagging confirmations.
6. What knock-on effects should be measurable? Second-order signals.
7. What would falsify the hypothesis? At least two concrete failure conditions.

A hypothesis without a falsification clause is not a hypothesis. Do not skip question 7.

## Procedure

1. Restate the user's idea in one sentence. Confirm before continuing.
2. Walk the seven questions above. Capture answers verbatim where possible.
3. Sketch the economic mechanism as a one-line causal chain (e.g. `search interest → patient demand → prescriptions → revenue`).
4. Estimate the expected lag window in target-cadence periods.
5. Draft falsification criteria. At minimum: out-of-sample failure, post-control disappearance, single-period dependence.
6. Emit the Hypothesis YAML (schema below) to `experiments/ideas/<slug>.yaml`. Use a kebab-case slug derived from the claim.
7. Suggest the next step: `/find-datasets --hypothesis experiments/ideas/<slug>.yaml`.

## Hard rules

- **Never invent dataset names here.** This step proposes *concepts*. Dataset selection comes later.
- **Avoid the "data mining because the dataset exists" failure mode.** If the user gestures at a dataset they happen to have, redirect to the predictor concept that dataset embodies.
- **Refuse to proceed without a falsification clause.** No falsification clause means no hypothesis.
- **One claim per hypothesis.** Compound claims (e.g. "X predicts Y AND Z") get split into one hypothesis per claim.

## Output schema

```yaml
hypothesis_id: HYP-2026-NNN              # auto-generated, monotonic
statement: <single-sentence claim>
domain: finance | biotech | macro | mixed
target_variable: <name as written, not dataset_id>
target_cadence: monthly | quarterly | annual
expected_direction: positive | negative | non-monotonic
expected_lag_periods: [0, 1, 2, 3]        # in target cadence
mechanism: <one-line causal chain>
candidate_predictors:
  - <concept 1>
  - <concept 2>
upstream_variables: []
downstream_effects: []
knock_on_effects: []
falsification:
  - <condition 1>
  - <condition 2>
created_at: <ISO datetime>
status: candidate
```

## Worked example

User: "I think Google searches for GLP-1 drugs predict Novo's obesity revenue."

```yaml
hypothesis_id: HYP-2026-001
statement: Google search interest for GLP-1 drugs leads Novo Nordisk obesity-segment revenue growth by one to three quarters.
domain: biotech
target_variable: Novo Nordisk obesity-segment revenue YoY growth
target_cadence: quarterly
expected_direction: positive
expected_lag_periods: [1, 2, 3]
mechanism: search interest → patient demand → prescriptions → reported revenue
candidate_predictors:
  - Google Trends interest in GLP-1 drug names
  - GLP-1 prescription volume
  - pharmacy fill data
upstream_variables: [media coverage, payer formulary inclusion]
downstream_effects: [Novo earnings call language, analyst consensus revisions]
knock_on_effects: [generic competitor stock moves, weight-loss adjacent category sales]
falsification:
  - signal does not lead revenue out-of-sample (2024 onward)
  - relationship disappears after controlling for overall pharma sector trend
  - effect only visible in a single quarter window
created_at: 2026-06-09T18:00:00Z
status: candidate
```

## Cross-references

- Next sub-skill: `datasource-query` (turn `candidate_predictors` into registry queries).
- Template: `templates/idea-template.md`.
- Spec: `BUILD_CHECKLIST.md` section 7.1.
