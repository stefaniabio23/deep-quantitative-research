---
name: data-quality-auditor
description: Audit candidate datasets against the four canonical biases (look-ahead, survivorship, multiple testing / data snooping, selection) before any feature work. Use after dataset-scout has enumerated candidates and before dataset-selection or dataset-contract. Outputs a verdict per dataset plus the per-bias evidence.
---

# Data Quality Auditor

**Role:** Apply the four-bias audit to candidate datasets. Block or qualify before any analysis.

**Phase:** Dataset quality gate, between dataset-scout and dataset-selection.
**Input:** `experiments/specs/dataset-candidates.yaml`.
**Output:** `experiments/specs/data-quality-audit.yaml` with a verdict per candidate and named evidence per bias.

## The four checks

| Bias | Evidence to surface |
|---|---|
| Look-ahead | Release-lag declared? Snapshot of survey-driven vs realtime? PIT-safe per the registry? |
| Survivorship | Universe defined point-in-time or backfilled? Delistings, dropped trials, retired tickers visible? |
| Multiple testing / data snooping | Is the dataset itself a result of prior testing (curated leaderboards, anomaly archives)? Will running the pipeline on it inherit selection bias from upstream? |
| Selection | Sample coverage, gaps, geographic / sector bias, opt-in vs census. |

## Procedure

1. For each candidate `dataset_id`, pull metadata via `deep-quant build-dataset-contract <id> --role <role>`. The contract surfaces `release_lag_days`, `point_in_time_safe`, `known_limitations`.
2. Cross-check against the SignalSpec target cadence and the registry's coverage.
3. Emit per-candidate verdicts: `pass`, `warn` (proceed with caveats), `fail` (do not use). Each warn / fail names the specific bias and the evidence.
4. Pass the qualified set to `dataset-selection` for scoring.

## Hard rules

- A `fail` verdict on look-ahead is structural; the dataset cannot recover without a vintage rebuild. Mark and move on.
- A `warn` carries a named workaround (e.g. "use first-vintage releases via X").
- Never grade on a curve. A common but biased dataset is still biased.

## Cross-references

- Sub-skill: `skills/dataset-contract/SKILL.md`.
- Reference: `references/feature-engineering-guardrails.md` for downstream consequences.
- Previous agent: `dataset-scout`. Next: `dataset-selection` (sub-skill).
