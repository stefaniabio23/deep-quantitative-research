---
name: statistical-validation
description: Prevent false confidence. Runs the full validation gate: sample size, missingness, outliers, autocorrelation, stationarity, spurious-trend, lookahead, survivorship, restatement, multiple-testing correction, walk-forward, regime split, lag sensitivity, transform sensitivity. Caps confidence and writes a validation report.
---

# statistical-validation

**Status:** scaffold. Content fill scheduled for Phase 3 of `BUILD_CHECKLIST.md` (section 7.8).

**Purpose:** the last gate before a result becomes a signal card. Confidence is capped to the lowest tier whose checks pass per `config/validation_thresholds.yaml`.

**Output:** `experiments/runs/<run>/validation-report.md`.
