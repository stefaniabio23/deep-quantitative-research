---
name: cadence-roll-up
description: Align source series to the target KPI cadence safely. Encodes the daily / weekly / monthly / quarterly / annual ladder plus variable-type-aware aggregation (flow=sum, stock=last, rate=mean, price=last, count=sum, sentiment=mean, event=sum-or-max). Refuses to sum stock / rate / price by default.
---

# cadence-roll-up

**Status:** scaffold. Content fill scheduled for Phase 3 of `BUILD_CHECKLIST.md` (section 7.5).

**Purpose:** prevent silent cadence corruption. Every conversion is logged with periods created, partial periods dropped, missing periods, release lag applied, PIT safety verdict.

**Output:** `experiments/runs/<run>/cadence-rollup-audit.yaml`.
