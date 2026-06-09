---
name: feature-engineering
description: Generate controlled feature grids (raw, diff, pct_change, mom, yoy, yo2y, rolling mean / sum, zscore, lags, seasonally adjusted) with hard caps from config. Records every feature and lag tested, flags multiple-testing risk, marks whether the winning feature was pre-specified or discovered, and caps confidence accordingly.
---

# feature-engineering

**Status:** scaffold. Content fill scheduled for Phase 3 of `BUILD_CHECKLIST.md` (section 7.6).

**Purpose:** turn feature search from a temptation into a logged, bounded experiment. Houses the `feature-importance/` sub-component (ANOVA over time).

**Output:** `experiments/runs/<run>/feature-grid.yaml` plus a `feature_search_log` block.
