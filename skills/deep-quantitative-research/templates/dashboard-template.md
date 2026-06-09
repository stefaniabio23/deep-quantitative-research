# Dashboard structural template

Spec for what a single-signal dashboard must contain. The canonical
emitter is `src/deep_quantitative_research/dashboard/html.py`; this
template documents the structure so a hand-authored or alternative
dashboard reads consistently.

Path: rendered output at `experiments/runs/<run-id>/dashboard.html`.

```text
HEADER
  Title:                 SignalSpec.signal_name
  Subtitle (meta):       signal_id, relationship_type
  Confidence strip:      visual horizontal strip (low | medium | high)
  Confidence statement:  "Confidence cap: <Tier>. Binding constraint: <check_name>."

SECTION: Hypothesis
  Body:                  SignalSpec.hypothesis.statement (verbatim)

SECTION: Predictor vs target
  Chart:                 standardised predictor and target on shared axis,
                         train/test boundary marked, endpoints directly labelled

SECTION: Lead-lag profile
  Chart:                 bar chart of correlation at lags 0..N,
                         numeric labels per bar, sign-coloured
  Caption:               best feature name and OOS degradation pct

SECTION: Backtest metrics
  Table:                 metric | train | test
                         Correlation, Rank correlation, Directional accuracy,
                         MAE, MAPE, RMSE, Hit rate, Sample size

SECTION: Validation checks
  Table:                 check name | verdict (pass/warn/fail, colour-coded)
                         | value | explanation
                         One row per Check in ValidationReport.checks

SECTION: Cadence rollup
  Bullet list:           one per source naming
                         dataset_id, source_cadence → target_cadence,
                         aggregation, periods_created, partial_periods_dropped

SECTION: Caveats
  Bullet list:           one per check with verdict ∈ {warn, fail},
                         carrying the check name and explanation

SECTION: Next iteration
  Bullet list:           ValidationReport.recommended_next_iterations

FOOTER
  Registry commit, checked-at timestamp, generator attribution
```

## Required properties

- **Self-contained.** No external CSS, no JavaScript, no remote images.
  Inline CSS and base64-embedded PNGs only.
- **Confidence mirrors validation.** The cap and binding constraint in the
  dashboard are exactly the values in `validation-report.yaml`.
- **All sections present.** Empty sections (e.g. no caveats) render an
  italic placeholder, never an absent block.
- **Tufte discipline.** Every chart passes the `visual-display` sub-skill's
  hard checklist.

## Optional properties (Phase 8)

- Related signals panel (confirming / contradicting list).
- Contradiction map (signal × signal heatmap across a family).
- Family-aggregate read ("2 supportive, 1 neutral, 1 contradictory").
