---
name: dataset-contract
description: Convert registry metadata into an experiment-specific data contract before any feature engineering or backtesting. Records fields, join keys, native and target cadence, variable type, aggregation rule, release lag, point-in-time safety, missingness policy, and known limitations.
---

# dataset-contract

**Status:** scaffold. Content fill scheduled for Phase 3 of `BUILD_CHECKLIST.md` (section 7.4).

**Purpose:** bridge abstract registry metadata to concrete experiment execution. Pulls from the registry, records `registry_commit`, fails fast on missing fields, warns on PIT-unsafe choices.

**Output:** `experiments/runs/<run>/dataset-contracts.yaml`.
