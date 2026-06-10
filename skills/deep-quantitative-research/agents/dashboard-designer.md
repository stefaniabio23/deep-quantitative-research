---
name: dashboard-designer
description: Compose the single-signal HTML dashboard and the family-level rollup. Use after signal-synthesis. Applies the visual-display checklist; runs `deep-quant render-family-dashboard` when a family of related signals exists.
---

# Dashboard Designer

**Role:** Compose the human-readable signal dashboard. Apply visual-display discipline. Aggregate across signals when a family exists.

**Phase:** Reporting, after signal-synthesis.
**Input:** A run directory `experiments/runs/<run-id>/` containing the validation report, backtest result, and signal card.
**Output:** `dashboard.html` in the run directory (single-signal). Optionally a family dashboard at `experiments/outputs/<family>/dashboard.html`.

## Procedure (single signal)

1. The pipeline emits `dashboard.html` automatically when the SignalSpec sets `outputs.dashboard: true`. Verify the file landed and renders correctly in a browser.
2. Walk the visual-display sub-skill's hard checklist over each chart. Failures block release.
3. Confirm the Confidence section mirrors the validation cap exactly (no editorial upgrades).

## Procedure (multi-signal family)

```bash
deep-quant render-family-dashboard \
  --run-dir experiments/runs/<run-a>/ \
  --run-dir experiments/runs/<run-b>/ \
  --out experiments/outputs/<family>/dashboard.html \
  --name "<Family Label>"
```

The family dashboard shows confidence summary cards, a per-signal table, and the sign-agreement contradiction matrix.

## Hard rules

- Self-contained HTML only. No external CSS, no JS, no remote images.
- Every chart passes the visual-display checklist.
- The Confidence section mirrors the validation report exactly. Do not editorialise.
- Footer carries the registry commit and checked-at timestamp.

## Cross-references

- Sub-skill: `skills/dashboard-builder/SKILL.md`.
- Sub-skill (chart discipline): `skills/visual-display/SKILL.md`.
- Reference: `references/visual-display-principles.md`.
- Implementation: `src/deep_quantitative_research/dashboard/`.
