# Dataset Contract YAML template

Materialised once per selected dataset per run. Path: `experiments/runs/<run-id>/dataset-contracts.yaml` (bundles all contracts for the run).

```yaml
dataset_contract:
  dataset_id: <id from datasources registry>
  role: target | predictor | context | benchmark
  registry_commit: <sha; required>

  fields:
    date_field: <field name from the registry schema>
    value_field: <field name>
    entity_fields: [<field>]

  join_keys:
    required: [<key>]      # keys this run needs
    available: [<key>]     # keys the dataset exposes per registry
    missing: [<key>]       # required minus available

  cadence:
    native_cadence: daily | weekly | monthly | quarterly | annual | irregular
    target_cadence: monthly | quarterly | annual
    aggregation: sum | mean | last | max | min | median

  variable:
    variable_type: flow | stock | rate | price | count | sentiment | event
    unit: <string, e.g. USD_millions, percent, normalised_index_0_100>
    transform_allowed: true

  timing:
    release_lag_days: <integer>
    point_in_time_safe: true | false
    revisions_possible: true | false

  quality:
    coverage_start: <YYYY-MM-DD>
    coverage_end: <YYYY-MM-DD or null for rolling>
    missingness_policy: error | drop | forward_fill | interpolate | flag
    known_limitations:
      - <one-line caveat>
```

## Required fields

`dataset_id`, `role`, `registry_commit`, `fields.date_field`, `fields.value_field`, `cadence.native_cadence`, `cadence.target_cadence`, `cadence.aggregation`, `variable.variable_type`, `timing.release_lag_days`, `timing.point_in_time_safe`, `quality.missingness_policy`.

## Refusal conditions

The pipeline refuses to backtest if any of these are true for a predictor:

- `timing.release_lag_days` is null
- `timing.point_in_time_safe` is null or false
- `variable.variable_type` is null
- `cadence.aggregation` contradicts the default for the `variable_type` without an `aggregation_overridden: true` flag and a stated reason
