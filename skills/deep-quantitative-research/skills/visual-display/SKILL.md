---
name: visual-display
description: Apply Tufte-style visual discipline to every chart the pipeline emits. Direct labels not legends. Honest scales. No chart junk. Uncertainty shown. Current read visually obvious. Raw vs transformed data distinguished. Sufficient historical context. Invoke when reviewing a chart produced by `signal-card.py` or `dashboard/charts.py`, or when designing a new chart for the pipeline.
---

# visual-display

## When to invoke

You are about to commit a chart that will land in a signal card, a dashboard, or a reference doc. Before it ships, run the chart through this skill's checklist.

The skill exists because charts in this project are read by the same person who funded the work. A chart that lies, even gently, costs more than a chart that says less.

## Inputs

- A draft chart (matplotlib figure, screenshot, or rendered HTML).
- The artefact it accompanies (signal-card, dashboard, validation report).
- The reference: `references/visual-display-principles.md`.

## Procedure

1. Read the draft. Decide what the chart is asking the reader to conclude.
2. Walk the checklist below. Each item is a hard pass / fail.
3. If any item fails, redraw before you commit. Do not annotate around a bad chart.
4. Keep style decisions consistent with `src/deep_quantitative_research/dashboard/charts.py` so the dashboard reads consistently across signals.

## The hard checklist

- [ ] **Signal vs target visible on one axis.** Either share an axis with z-scored series, or use two y-axes with clear scales declared.
- [ ] **Lag alignment shown.** Train / test boundary marked. If the chart claims a lead, show the lead explicitly with offset annotation.
- [ ] **Rolling correlation, if relevant, on a separate panel.** Do not overlay a slowly-moving rolling metric on a high-frequency price line.
- [ ] **Feature stability shown when claimed.** Show the per-window contribution, not just an aggregate.
- [ ] **Backtest performance on a non-zero baseline.** If the y-axis starts at zero only because the data does, leave the zero line; if it starts at a non-zero value to fit small wiggles, declare the bottom of the axis.
- [ ] **Drawdown panel for tradable signals.** Cumulative-return plots without drawdown lie about path risk.
- [ ] **Confidence and caveats visible somewhere in the rendered figure or its caption.** No chart should be shareable as an image without the confidence cap legible.
- [ ] **Direct labels where they fit.** A line labelled at its endpoint reads faster than a legend in a corner.
- [ ] **No 3D bars, no shadow effects, no pie charts for series of more than three categories.** Standard chart-junk refusal.
- [ ] **Honest scales.** Linear when the eye expects linear. Log only when the data span justifies it, and the axis says "log".
- [ ] **Uncertainty shown.** Where confidence intervals or standard errors exist, show them. Where they cannot be computed, say so.
- [ ] **Raw vs transformed declared.** Z-scored, year-over-year, rolling-mean: all label their transform on the axis or in the title.
- [ ] **Enough historical context.** At least the training window plus the test window. If the chart has only the test window, it cannot show OOS degradation.
- [ ] **Current read obvious.** The most recent observation is clear at a glance; not buried in the middle of a series.

## Output

A note attached to the artefact PR / commit naming which checklist items the chart passes and which were judged not applicable. Items that fail block merge.

## Cross-references

- Implementation: `src/deep_quantitative_research/dashboard/charts.py`.
- Reference: `references/visual-display-principles.md`.
- Sub-skill that consumes this discipline: `dashboard-builder`.
- Spec: `BUILD_CHECKLIST.md` section 7.11.
