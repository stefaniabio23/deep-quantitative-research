# Biotech PoS, Oncology Phase 3 Readout Density

A worked end-to-end demo of the deep-quantitative-research pipeline.

## The hypothesis

Monthly Phase 3 oncology trial readout count leads quarterly biotech subindex returns by one quarter. Mechanism: clusters of Phase 3 readouts reset analyst expectations and pipeline NPVs across the oncology-heavy biotech subindex, with the price impact concentrated in the quarter following the readout cluster.

This is a stylised version of the indication × MOA Probability-of-Success setup, narrowed to a single registry-shaped feature so the demo runs cleanly.

## What this demo shows

1. The SignalSpec references real `dataset_id`s from the sibling `datasources` registry (`aact`, `yfinance`).
2. The predictor data is monthly, the target is quarterly: the pipeline rolls cadence with `variable_type: count → aggregation: sum`.
3. The pre-specified feature is `aact::raw::lag_1` (the planted lead-lag); the pipeline confirms it survives the train/test split.
4. The validation gate runs every Phase 4b check: sample size, missingness, outliers, ADF, KPSS, Ljung-Box, lag sensitivity, outlier sensitivity, plus relationship classification.
5. All run artefacts land in `expected-output/`, version-controlled so a reader can diff against their own run.

## Data

The demo uses **synthetic data** with a planted relationship. Real biotech PoS analysis would feed actual ClinicalTrials.gov readout dates and biotech ETF prices into the same SignalSpec without changing any code. The synthetic generator is deterministic (seeded), so the artefacts in `expected-output/` reproduce exactly with `./run.sh`.

- `data/predictor.csv`: monthly count of Phase 3 oncology trial completions, with a 2022 regime shift (loosely echoing the post-COVID approval acceleration).
- `data/target.csv`: quarterly biotech subindex returns, constructed so the predictor at lag 1 quarter has a real coefficient plus realistic noise.

To regenerate: `python3 data/generate.py`.

## Run

```bash
./run.sh
```

The script regenerates the CSVs, runs `deep-quant run-signal`, and writes every artefact into `expected-output/`. Idempotent: rerun without cleaning up first.

## Expected output

After `./run.sh`, `expected-output/` should contain:

```
run.yaml                       run metadata and registry commit
cadence-rollup-audit.yaml      one entry per source: rollup decisions made
feature-grid.yaml              feature names emitted + caps applied
feature-search-log.yaml        pre-specified vs discovered, multiple-testing flag, confidence cap
backtest-result.yaml           full KPI metric panel + lead-lag profile + OOS degradation
validation-report.yaml         every check verdict + binding constraint + relationship_type
signal-card.md                 the human-readable signal card
```

## What the demo proves

- The pre-specified feature wins (no overfitting from a wide grid search).
- Test correlation stays positive at the planted lag.
- The validation gate caps confidence honestly when the underlying data has limited history.
- Cadence rollup respects the `count → sum` rule.
- The signal card renders with every canonical section populated.

## Caveats and next iterations

- The data is synthetic. Wire the same SignalSpec against real ClinicalTrials.gov / yfinance fetches to get a real result. The pipeline does not change.
- The Phase 3 readout count is treated as an undirected event count. A sharper feature would separate positive vs negative readouts, which requires structured outcome data the registry does not currently carry.
- No regime split is applied; the 2022 shift is a single regime change that a regime-split check would flag in a richer SignalSpec.
