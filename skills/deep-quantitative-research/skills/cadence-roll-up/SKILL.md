---
name: cadence-roll-up
description: Align source series to the target KPI cadence safely. Encodes the daily / weekly / monthly / quarterly / annual ladder plus variable-type-aware aggregation (flow=sum, stock=last, rate=mean, price=last, count=sum, sentiment=mean, event=sum-or-max). Refuses to sum stock / rate / price by default. Emits a cadence-rollup-audit per source.
---

# cadence-roll-up

## When to invoke

You have a dataset_contract for every selected dataset and a target cadence on the hypothesis. Source cadences must now be aligned to the target without silently corrupting the data.

This step is invisible most of the time and catastrophic when it goes wrong. A monthly flow summed correctly looks identical to a monthly stock summed wrongly until the levels stop matching reality.

## Inputs

- `experiments/runs/<run-id>/dataset-contracts.yaml` from `dataset-contract`.
- The target cadence from the SignalSpec.

## The cadence ladder

```text
daily → weekly → monthly → quarterly → annual
```

Always roll up, never down. If a source is coarser than the target (annual to monthly), the source is wrong for this hypothesis; flag and refer to `dataset-selection`.

## Default aggregation by variable type

| variable_type | default_aggregation | rationale |
|---|---|---|
| `flow` | `sum` | revenue, sales, prescriptions: periods are additive |
| `stock` | `last` | inventory, subscribers: snapshot at period end |
| `rate` | `mean` | unemployment rate, conversion rate: bounded ratio |
| `price` | `last` or `mean` | share price, commodity price: never sum |
| `count` | `sum` | mentions, visits, events: additive |
| `sentiment` | `mean` | review sentiment, news sentiment: bounded ratio |
| `event` | `sum` or `max` | approvals, trial readouts: count occurrences, or use latest status |

Overrides are allowed in the SignalSpec but must be explicit and named. Silent overrides are a bug.

## Procedure

1. Read every contract. For each, confirm `variable_type` is set and the default aggregation matches.
2. For each source-target pair, build the cadence plan: source `native_cadence`, target_cadence from the SignalSpec, aggregation per the rule above (or explicit override).
3. Apply release-lag shift: the value for period T appears at T + release_lag_days. Backtests must respect this.
4. Apply the rollup. Handle:
   - **Partial current periods**: drop unless the SignalSpec explicitly allows partials.
   - **Missing periods**: handle per `missingness_policy` in the contract.
   - **Duplicate timestamps**: deduplicate after applying the aggregation rule.
   - **Fiscal vs calendar quarters**: never mix; the SignalSpec must declare which.
5. Emit `experiments/runs/<run-id>/cadence-rollup-audit.yaml` (schema below) for every source.
6. Suggest the next step: `feature-engineering` consumes the rolled-up series.

## Hard rules

- **Never sum stock, rate, or price variables unless explicitly overridden.** Pin this to the rule list in `CLAUDE.md` and check it on every run.
- **Never average flow variables unless explicitly overridden.** Same.
- **Roll up, never down.** If the source is coarser than the target, this signal is wrong; reject and re-select datasets.
- **Always apply release lag.** A value timestamped T was only knowable at T + release_lag_days. Using earlier violates point-in-time.
- **Always emit an audit.** No audit, no rollup. Future you needs to know exactly what happened.
- **Refuse to fabricate missing data.** Forward-fill and interpolation are allowed but must be explicit; `error` and `flag` are safer defaults.

## Output schema

```yaml
cadence_rollup_audit:
  dataset_id: <id>
  source_cadence: daily | weekly | monthly | quarterly | annual | irregular
  target_cadence: monthly | quarterly | annual
  variable_type: flow | stock | rate | price | count | sentiment | event
  aggregation: sum | mean | last | max | min | median
  aggregation_overridden: true | false
  override_reason: <string or null>

  periods_created: <integer>
  partial_periods_dropped: <integer>
  missing_periods: <integer>
  duplicate_timestamps_resolved: <integer>

  release_lag_applied_days: <integer>
  fiscal_calendar: calendar | fiscal | null

  point_in_time_safe: true | false
  warnings: [<one-liner>]
```

## Worked example

A weekly sentiment predictor rolled to monthly target:

```yaml
cadence_rollup_audit:
  dataset_id: google-trends-retail-searches
  source_cadence: weekly
  target_cadence: monthly
  variable_type: sentiment
  aggregation: mean
  aggregation_overridden: false
  override_reason: null
  periods_created: 96
  partial_periods_dropped: 1   # current month not yet complete
  missing_periods: 0
  duplicate_timestamps_resolved: 0
  release_lag_applied_days: 1
  fiscal_calendar: calendar
  point_in_time_safe: false
  warnings:
    - Google Trends values can change between pulls; this run uses a snapshot taken at 2026-06-09T12:00:00Z.
```

## Cross-references

- Reference: `references/cadence-roll-up.md` (rules table and edge cases).
- Implementation: `src/deep_quantitative_research/timeseries/cadence.py` (Phase 4).
- Next sub-skill: `feature-engineering`.
- Spec: `BUILD_CHECKLIST.md` section 7.5.
