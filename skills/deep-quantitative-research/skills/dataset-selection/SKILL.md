---
name: dataset-selection
description: Score and select datasets by hypothesis fit, not availability. Applies the dataset_fit_score rubric (economic proximity, coverage, cadence fit, release-lag clarity, point-in-time safety, survivorship-bias risk, API scriptability, cost) and returns target, predictor, context, and rejected datasets with reasoning.
---

# dataset-selection

**Status:** scaffold. Content fill scheduled for Phase 3 of `BUILD_CHECKLIST.md` (section 7.3).

**Purpose:** force discipline at the point most quant work goes wrong. Weights come from `config/scoring_weights.yaml`. Rejection reasons are mandatory so the next iteration knows what to look for.

**Output:** dataset-selection block in the SignalSpec.
