---
name: dashboard-builder
description: "Aggregate signal cards into an HTML dashboard. Shows current read, related signals (confirming or contradicting), confidence matrix, backtest metrics, feature stability, data quality warnings, caveats, and next iteration. Single-signal and multi-signal modes. Invoke after signal-synthesis or when the SignalSpec opts in via outputs.dashboard true. Uses dashboard/charts.py for Tufte-styled matplotlib panels and emits a self-contained HTML file."
---

# dashboard-builder

## When to invoke

The signal card is the human-readable summary; the dashboard is the operational view. Invoke when:

- A run finishes and the SignalSpec has `outputs.dashboard: true`.
- A signal-library reader asks "what does this signal say right now".
- A family of related signals exists and the question is what they say together (multi-signal mode, future phase).

The pipeline already does this automatically when the SignalSpec opts in. The skill is the spec for what the rendered dashboard must contain, regardless of whether the renderer is Python or hand-authored.

## Inputs

- The SignalSpec (for `signal_name`, predictors, target).
- `backtest-result.yaml` (for metrics + lead-lag profile + best feature + OOS).
- `validation-report.yaml` (for the cap + binding constraint + relationship type).
- The cadence rollup audits.
- The cadence-aligned target Series and the best-feature Series (for the time-series chart).

## Procedure (single signal)

1. Header block. Signal name, signal_id, relationship_type, confidence cap (the visual strip from `confidence_strip()`), binding constraint.
2. Hypothesis paragraph. Verbatim from the SignalSpec.
3. Predictor vs target chart. Standardised both, train/test boundary marked, endpoints directly labelled.
4. Lead-lag profile chart. Bars; positive correlations one colour, negative another; numeric label above each bar.
5. Backtest metrics table. Train and test columns. MAE / MAPE / RMSE only when the target is strictly positive.
6. Validation checks table. Each check name, verdict (colour-coded), value, explanation.
7. Cadence rollup audits. One bullet per source naming source cadence, target cadence, aggregation, periods created, partial periods dropped.
8. Caveats. Pulled from warn / fail checks; each carries the check name as a code tag plus the explanation.
9. Next iteration. From `validation.recommended_next_iterations`.
10. Footer. Registry commit, checked-at timestamp.

All sections required. A missing section is a render failure, not a layout choice.

## Procedure (multi-signal, future)

Deferred to Phase 8. The dashboard module will grow:

- `aggregator.py` that reads multiple `signal-card.md` / `validation-report.yaml` from `experiments/runs/` and produces a "current read" rollup.
- A contradiction map: matrix of signal × signal showing agreement / disagreement of current reads.
- A family-level dashboard.html.

## Hard rules

- **Self-contained HTML.** No external assets, no JavaScript. Inline CSS, base64-embedded images. A reader can email it or commit it.
- **Confidence cap mirrors the validation report.** No editorial upgrades.
- **Caveats are mandatory.** A dashboard without flagged caveats means every validation check passed; double-check that the gate ran.
- **Tufte discipline applies to every chart.** Run `visual-display` over each chart before commit.
- **Footer carries the registry commit.** Without it the dashboard is not reproducible.

## Output

`experiments/runs/<run-id>/dashboard.html` for a single signal. Future multi-signal output will land at `experiments/outputs/<family>/dashboard.html`.

## Cross-references

- Implementation: `src/deep_quantitative_research/dashboard/html.py`, `dashboard/charts.py`.
- Template: `templates/dashboard-template.md`.
- Required discipline: `visual-display`.
- Spec: `BUILD_CHECKLIST.md` section 7.12.
