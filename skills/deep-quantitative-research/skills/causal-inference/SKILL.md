---
name: causal-inference
description: Classify the relationship as causal, proxy, coincident, lagging, mechanically linked, spurious, or regime-dependent. Identifies confounders, upstream / downstream candidates, reverse causality, third-variable risk, and trend-driven artefacts. Blocks causal language unless evidence justifies it.
---

# causal-inference

**Status:** scaffold. Content fill scheduled for Phase 3 of `BUILD_CHECKLIST.md` (section 7.9).

**Purpose:** keep interpretation honest. A signal that survives backtesting is still usually a proxy, not a cause.

**Output:** relationship classification block fed into `signal-synthesis`.
