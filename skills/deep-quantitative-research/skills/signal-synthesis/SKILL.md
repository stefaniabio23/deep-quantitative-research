---
name: signal-synthesis
description: Turn experiment outputs into a signal card. Pulls hypothesis, datasets, economic mapping, backtest results, current read, related signals, confidence, caveats, failure modes, next iteration, and links into the canonical signal-template.md.
---

# signal-synthesis

**Status:** scaffold. Content fill scheduled for Phase 3 of `BUILD_CHECKLIST.md` (section 7.10).

**Purpose:** the synthesis step that produces the human-readable artefact. Renders `templates/signal-template.md` against the run's artefacts.

**Output:** `experiments/runs/<run>/signal-card.md`.
