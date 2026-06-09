---
name: dataset-contract
description: Convert registry metadata into an experiment-specific data contract before any feature engineering or backtesting. Records fields, join keys, native and target cadence, variable type, aggregation rule, release lag, point-in-time safety, missingness policy, and known limitations. Materialised once per selected dataset, per run.
---

# dataset-contract

## When to invoke

You have a selected target, predictors, and (optionally) context datasets from `dataset-selection`. Before you can roll up cadences or build a feature grid, every dataset must have an explicit, experiment-specific contract.

The contract is the bridge from "the registry says this dataset exists" to "this run will treat the dataset as follows". It freezes the operational assumptions so a later reader can reproduce the run.

## Inputs

- The `dataset_selection` block from `dataset-selection` (or the candidate set if running standalone).
- The Hypothesis YAML (for `target_cadence`).
- Registry access via `deep-quant build-dataset-contract`.

## Procedure

1. For each selected dataset_id, run:
   ```bash
   deep-quant build-dataset-contract <dataset_id> --role <target|predictor|context> --target-cadence <monthly|quarterly>
   ```
2. Inspect the emitted contract. The CLI fills as much as the registry knows; you must complete the rest:
   - `variable.unit`: the actual unit (the registry rarely carries this).
   - `timing.release_lag_days`: integer days from observation to publication.
   - `timing.point_in_time_safe`: boolean; true only if the value at time T was visible by T + release_lag_days.
   - `timing.revisions_possible`: true for any restated economic data, FRED series, government estimates.
   - `quality.coverage_start` / `coverage_end`: actual observed history.
   - `quality.missingness_policy`: `error | drop | forward_fill | interpolate | flag`.
   - `quality.known_limitations`: anything the registry caveats plus anything you know from manual inspection.
3. If any field is unavailable in the registry and unknowable from the source documentation, set the value to `null` and add an entry to `known_limitations` describing why.
4. Bundle every contract into `experiments/runs/<run-id>/dataset-contracts.yaml`.
5. Suggest the next step: `cadence-roll-up` operates on the contracts.

## Hard rules

- **Always materialise a contract before backtesting.** No exceptions.
- **Always record `registry_commit`.** The CLI does this automatically.
- **Refuse to proceed if `point_in_time_safe` is unknown for a predictor.** Predictor PIT failures invalidate the entire backtest.
- **Refuse to use a predictor whose `release_lag_days` is unknown.** Without lag, you cannot avoid lookahead.
- **`variable_type` must be set.** The default `flow` is a guess; verify and correct. The wrong `variable_type` drives the wrong aggregation, which silently corrupts cadence-rollup.

## Output schema

```yaml
dataset_contract:
  dataset_id: <id>
  role: target | predictor | context | benchmark
  registry_commit: <sha>

  fields:
    date_field: <field name>
    value_field: <field name>
    entity_fields: [<field>]

  join_keys:
    required: [<key>]
    available: [<key>]
    missing: [<key>]

  cadence:
    native_cadence: daily | weekly | monthly | quarterly | annual | irregular
    target_cadence: monthly | quarterly | annual
    aggregation: sum | mean | last | max | min | median

  variable:
    variable_type: flow | stock | rate | price | count | sentiment | event
    unit: <string>
    transform_allowed: true

  timing:
    release_lag_days: <integer>
    point_in_time_safe: true | false
    revisions_possible: true | false

  quality:
    coverage_start: <date>
    coverage_end: <date>
    missingness_policy: error | drop | forward_fill | interpolate | flag
    known_limitations:
      - <one-line caveat>
```

## Worked example

```yaml
dataset_contract:
  dataset_id: google-trends-retail-searches
  role: predictor
  registry_commit: a85c10825a9ec5dd5010a9dbf4bbfe1d4959264f
  fields:
    date_field: date
    value_field: search_interest
    entity_fields: [geo, category]
  join_keys:
    required: [date, ISO_3166_1]
    available: [date, ISO_3166_1, search_term]
    missing: []
  cadence:
    native_cadence: weekly
    target_cadence: monthly
    aggregation: mean      # sentiment → mean by default
  variable:
    variable_type: sentiment
    unit: normalised_index_0_100
    transform_allowed: true
  timing:
    release_lag_days: 1
    point_in_time_safe: false   # values can change between pulls
    revisions_possible: true
  quality:
    coverage_start: 2004-01-01
    coverage_end: null   # rolling
    missingness_policy: flag
    known_limitations:
      - Google Trends values are normalised indices, not absolute counts.
      - Sampling-driven; values may change between pulls.
      - Historical sampling stability is weaker pre-2010.
```

## Cross-references

- CLI: `deep-quant build-dataset-contract`.
- Template: `templates/dataset-contract-template.md`.
- Next sub-skill: `cadence-roll-up`.
- Spec: `BUILD_CHECKLIST.md` section 7.4.
