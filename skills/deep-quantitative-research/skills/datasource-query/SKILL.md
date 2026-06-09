---
name: datasource-query
description: Query the sibling datasources repo for datasets relevant to a hypothesis. Returns candidate target / predictor / context datasets with fields, join keys, cadence, point-in-time safety, release-lag metadata, and access constraints.
---

# datasource-query

**Status:** scaffold. Content fill scheduled for Phase 3 of `BUILD_CHECKLIST.md` (section 7.2).

**Purpose:** the bridge between a hypothesis and the registry. Wraps `deep_quantitative_research.registry` to answer: which datasets are relevant, which fields, which join keys, which cadence is compatible, what caveats.

**Output:** `experiments/specs/dataset-candidates.yaml`.
