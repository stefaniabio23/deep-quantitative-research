# CLAUDE.md, deep-quantitative-research

Repo-scoped rules for the v3 architecture. Pair with the global rules in `~/CLAUDE.md`.

## Identity

- Repo: `deep-quantitative-research`
- Skill: `skills/deep-quantitative-research/`
- Command: `/deep-quantitative-research`
- Python package: `deep_quantitative_research`
- CLI: `deep-quant`

Deprecated aliases (do not introduce in new code): `deep-research`, `deep-quant-research`.

## Sibling repos

- `~/Projects/datasources/` is the canonical public-data registry. This repo consumes it through `src/deep_quantitative_research/registry/`. Never duplicate dataset metadata here.

## Core rules

### Data registry

1. Use the `datasources` repo as the canonical source for dataset metadata.
2. Never invent dataset metadata that should come from the registry.
3. Reference datasets by `dataset_id`.
4. Record the datasource registry commit hash in every experiment.
5. Materialize dataset contracts before feature engineering or backtesting.

### Time series

6. Respect native cadence, release lag, and point-in-time safety.
7. Never sum stock, rate, or price variables unless explicitly overridden.
8. Never average flow variables unless explicitly overridden.
9. Always produce a cadence roll-up audit.

### Feature engineering

10. Generate controlled feature grids.
11. Record number of features tested, number of lags tested, and whether the best feature was pre-specified or discovered.
12. Flag multiple-testing risk; cap confidence when the best feature was discovered through a large search.

### Backtesting

13. Distinguish KPI prediction from tradable signal backtesting.
14. Use walk-forward validation where possible.
15. Report out-of-sample degradation.
16. Never call a signal high-confidence unless it survives out-of-sample.

### Reporting

17. Every signal card must include hypothesis, economic mapping, data inputs, backtest summary, current read, confidence, caveats, and next iteration.
18. Every run must be saved to the research ledger at `experiments/runs/<run-id>/`.
19. Every dashboard must show current read, confidence, related signals, and data quality warnings.

## Working files

- `ARCHITECTURE_LOG.md`, structured OG-vs-target log.
- `BUILD_CHECKLIST.md`, persistent build plan; source of truth for migration progress.

## Projects vs examples

When the pipeline is deployed against a real research question, the work lives in a dedicated project folder. One folder per project. Convention:

```text
projects/<project-slug>/
├── README.md             one-paragraph claim + verdict table + caveats
├── signal-spec.yaml      pre-registered SignalSpec
├── data/                 fetch scripts + CSVs (network-fetched; gitignored if large)
├── run.sh                idempotent end-to-end runner
├── run_family.py         optional: family-wide multiple-testing follow-on
└── expected-output/      committed reference artefacts (signal-card, validation-report, dashboard)
```

Folder ownership:

- `examples/` holds canonical pipeline demos with synthetic data (`biotech-pos`, `null-control`). These prove the pipeline behaves correctly: planted signal recovers, planted nothing rejects. Run in CI.
- `projects/` holds real research applications: replications, audits, original investigations against live data. **Not** run in CI because they hit external networks (yfinance, pytrends, etc.) which are flaky and rate-limited.

When a new research question comes in, scaffold `projects/<slug>/` from the same skeleton as `projects/preis-moat-stanley/`. Pre-register the hypothesis in `signal-spec.yaml` BEFORE running anything. Commit the verdict as `expected-output/` so a later reader can diff against their own re-run.

## Things that are NOT part of v3 (do not re-add)

- Mode-based pipeline routing (`quick`, `full`, `thesis-test`, `data-first`, `literature`, `thorough`). Replaced by per-stage commands.
- Critique cluster (`methods-critic`, `data-critic`, `logic-critic`). Dropped 2026-06-09; checklist-style validation is folded into the relevant sub-skills (`statistical-validation`, `dataset-contract`, `feature-engineering`).
- Agents: `originality-scout`, `knowledge-base-builder`, `question-sharpener` (folded into `hypothesis-formulation` sub-skill).
