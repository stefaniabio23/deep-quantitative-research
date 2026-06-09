# Cadence roll-up reference

Background and edge cases for the `cadence-roll-up` sub-skill.

## The ladder

```text
daily → weekly → monthly → quarterly → annual
```

Always upward. Never downward. If the source is coarser than the target, the source is wrong for the hypothesis.

## Default aggregation by variable type

| variable_type | default | rationale | counter-example |
|---|---|---|---|
| `flow` | `sum` | additive over periods | summing a flow already aggregated produces double-counting; check the source first |
| `stock` | `last` | snapshot value at period end | last day of month is usually fine; quarter-end book values are accounting-driven |
| `rate` | `mean` | bounded ratio averages cleanly | rates derived from flow / stock ratios may need numerator-and-denominator aggregation instead |
| `price` | `last` or `mean` | level series; never sum | mean = volume-unweighted; weighted average needs explicit volume data |
| `count` | `sum` | additive event counts | deduped counts (e.g. monthly active users) are stocks, not counts |
| `sentiment` | `mean` | bounded ratio | weighting by volume (mentions, articles) is often better than simple mean |
| `event` | `sum` or `max` | count occurrences (sum) or pick latest status (max) | event windows around earnings need a "did it happen" indicator, not a count |

## Edge cases

- **Partial current period.** Drop unless the SignalSpec opts in. A half-month rolled to monthly produces a value half its eventual size.
- **Missing observation.** Honour the dataset contract's `missingness_policy`. `flag` is safer than `forward_fill` for backtests.
- **Duplicate timestamps.** Deduplicate after aggregation, not before. The aggregation rule defines what "same period" means.
- **Release lag.** A value timestamped T is only observable at T + `release_lag_days`. Apply the shift before any cadence operation.
- **Fiscal vs calendar quarter.** SignalSpec must declare one. Mixing breaks the alignment silently.
- **Weekly to monthly.** Weeks straddle months. Two reasonable conventions: assign to the month containing the week's middle day (Wednesday or Thursday), or assign by week-end day. Pick one per SignalSpec; record in the audit.
- **Weekly to quarterly.** Same issue, more leverage. Use ISO-week-to-quarter mapping; document explicitly.
- **Daily to monthly with holidays.** Choose: business-day mean (ignore weekends), or calendar mean (zero-fill). Different across regimes; pick per region's convention.
- **Irregular cadence.** Aggregations like "trial readouts in a quarter" are valid but variance is huge; report the count alongside the value.

## Aggregation override convention

The default is the rule above. Overrides are allowed only with:

```yaml
cadence:
  aggregation: <override>
  aggregation_overridden: true
  override_reason: <one line>
```

A silent override is a bug. The audit must surface it.

## Probe test

Before declaring rollup correct: produce both the rolled-up series and the underlying high-frequency series. Plot one and the area-under-curve of the other side by side. Mismatches are visible immediately.
