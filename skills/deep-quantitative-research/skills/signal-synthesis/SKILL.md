---
name: signal-synthesis
description: Turn experiment outputs into a signal card. Pulls hypothesis, datasets, economic mapping, backtest results, current read, related signals, confidence, caveats, failure modes, next iteration, and links into the canonical signal-template.md. The signal card is the human-readable artefact a reader sees first.
---

# signal-synthesis

## When to invoke

The validation gate has run. Every artefact for the signal exists. Now compose the signal card.

The signal card is the deliverable. A reader who lands on the card cold should be able to understand what was claimed, what was tested, what survived, what failed, and what to do next, without opening any other file.

## Inputs

- The Hypothesis YAML.
- The SignalSpec.
- Dataset contracts.
- Cadence rollup audit.
- Feature grid + feature search log.
- Backtest metrics.
- Validation report (this drives the confidence statement).

## Procedure

1. Read every artefact in the run directory. If anything is missing, stop and report which sub-skill needs to run.
2. Compose the signal card by populating `templates/signal-template.md`. Section order is fixed.
3. The Confidence section copies the validation cap. Never upgrade the cap here.
4. The Current Read section answers "what does this signal say right now?". Use the most recent in-sample period plus any look-through to today.
5. The Failure Modes section lists when the signal historically broke and why. Pull from `validation_report.checks` with `warn` or `fail` plus any narrative from the backtest summary.
6. The Next Iteration section names one to three concrete experiments that would lift the confidence cap. Pull from `validation_report.recommended_next_iterations`.
7. Cross-link to the run directory artefacts and to any related signals already in the library.
8. Emit `experiments/runs/<run-id>/signal-card.md`.
9. If the SignalSpec opts into dashboard rendering, hand off to `dashboard-builder`.

## Hard rules

- **The Confidence section mirrors the validation cap.** No editorial upgrades.
- **Every section in the template is required.** A blank section is a flag, not an option.
- **Failure Modes are mandatory.** A signal card without named failure modes is incomplete.
- **Name the related-signal contradictions explicitly.** If three signals say "up" and one says "down", surface the contradictor; do not hide it.
- **Link, do not duplicate.** The signal card points at run artefacts; it does not paste them.

## Output schema

The signal card is markdown; the canonical sections (also in `templates/signal-template.md`):

```md
# <Signal Name>

## Hypothesis
## Economic Mapping
## Data Inputs
## Time-Series
## Model Logic
## Backtest Summary
## Current Read
## Related Signals
## Confidence
## Caveats
## Failure Modes
## Next Iteration
## Links
```

## Worked example

```md
# UK Retail Search Demand Signal

## Hypothesis
Google search interest for retail categories leads UK retail sales YoY growth by one to two months.

## Economic Mapping
Search intent → category demand → store traffic → reported retail sales.

## Data Inputs
- Target: `ons-retail-sales-index` (monthly, official).
- Predictor: `google-trends-retail-searches` (weekly, sentiment, rolled to monthly mean).
- Context: `boe-consumer-credit` (monthly, used for regime tagging).

## Time-Series
Aligned monthly, 2016-01 to 2025-12. Release lag 1 day applied. Best feature: `google_trends_yoy_1y_lag_1`.

## Model Logic
The best feature predicts the next month's UK retail sales YoY growth with a positive sign. No model fitting beyond a single-feature linear specification; the test is whether the relationship survives, not how much we can curve-fit.

## Backtest Summary
- Period: train 2016-01 to 2021-12, test 2022-01 to 2025-12.
- Test correlation: 0.44 (Pearson), 0.49 (rank).
- Directional accuracy: 0.61.
- OOS degradation: 38%.
- Hit rate: 0.62.

## Current Read
As of 2026-06: predictor running 8% YoY above its 3-year mean; signal says retail sales growth should accelerate one to two months out. Confidence capped by post-COVID regime shift; treat as supportive, not decisive.

## Related Signals
- `consumer-credit-retail-signal`: confirming (also supportive).
- `card-spend-retail-signal`: not yet built; high priority next.

## Confidence
**Medium.** Binding constraint: regime_split (post-COVID correlation 0.41 vs pre-COVID 0.58).

## Caveats
- Google Trends values are normalised indices and can change between pulls.
- Sentiment series; aggregation is mean, not sum.
- Single pre-specified feature; not yet tested across category-level Google Trends.

## Failure Modes
- Signal weakened materially during 2020-2021 (COVID demand shock).
- Single magical lag (1 month) is the headline; lag 0 and lag 2 are within 0.07 correlation but the result depends on lag 1 holding.

## Next Iteration
- Add a post-COVID regime control and rerun.
- Test category-level Google Trends signals.
- Add card-spend data when available; test the three-way ensemble.

## Links
- Hypothesis: `experiments/ideas/uk-retail-demand.yaml`
- SignalSpec: `experiments/specs/uk-retail-search-demand-signal.yaml`
- Backtest: `experiments/runs/2026-06-09-uk-retail-search-demand/metrics.json`
- Validation: `experiments/runs/2026-06-09-uk-retail-search-demand/validation-report.md`
- Dashboard: `experiments/runs/2026-06-09-uk-retail-search-demand/dashboard.html`
```

## Cross-references

- Template: `templates/signal-template.md`.
- Implementation: `src/deep_quantitative_research/reporting/signal_card.py` (Phase 4).
- Next sub-skill: `dashboard-builder` (when SignalSpec opts in).
- Spec: `BUILD_CHECKLIST.md` section 7.10.
