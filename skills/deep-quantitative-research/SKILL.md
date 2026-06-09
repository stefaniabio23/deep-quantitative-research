---
name: deep-quantitative-research
description: Build falsifiable quantitative research signals using datasource registry search, dataset contracts, cadence alignment, controlled feature grids, walk-forward backtests, statistical validation, and signal cards. Replaces ad-hoc analysis with a registry-aware, reproducible signal factory across finance, biotech, and macro domains.
license: MIT
compatibility: "Claude Code with Python 3.10+. Requires the sibling datasources repo at ../datasources/. Run pip install -e . from the repo root."
allowed-tools: "Bash(python:*) Bash(deep-quant:*) WebSearch WebFetch Read Write Task"
metadata:
  version: "3.0.0.dev0"
  category: quantitative-research
  tags: [finance, biotech, macro, research, backtesting, time-series, dataset-registry, signal-cards]
---

# deep-quantitative-research

A registry-aware signal research engine. Consumes the `datasources` repo, materialises dataset contracts, runs cadence-safe and point-in-time-aware feature and backtest workflows, validates against overfitting and leakage, and emits reproducible signal cards and dashboards.

The unit of work is a **signal**, not a model.

## Workflow

```text
Idea → Hypothesis → Dataset Selection → Dataset Contract → Cadence Alignment
     → Feature Grid → Backtest → Statistical Validation → Signal Card → Dashboard
```

## Commands

```text
/deep-quantitative-research "<question>"   end-to-end pipeline
/formulate-hypothesis                       idea → testable hypothesis
/find-datasets                              hypothesis → candidate datasets from registry
/design-signal                              candidates → SignalSpec
/backtest-signal                            run cadence rollup, feature grid, backtest
/validate-signal                            apply the statistical-validation gate
/build-dashboard                            render signal cards into a dashboard
```

Per-stage commands live in `commands/`. End-to-end and domain workflows live in `workflows/`.

## Sub-skills

Each sub-skill owns one stage. Specs live under `skills/`.

| # | Sub-skill | Owns |
|---|---|---|
| 1 | `hypothesis-formulation/` | Vague idea to falsifiable hypothesis |
| 2 | `datasource-query/` | Query the `datasources` registry |
| 3 | `dataset-selection/` | Score and pick datasets by hypothesis fit |
| 4 | `dataset-contract/` | Materialise per-experiment data contract |
| 5 | `cadence-roll-up/` | Align source cadences to target safely |
| 6 | `feature-engineering/` | Controlled feature grid with overfitting guards |
| 7 | `time-series-backtest/` | KPI-prediction and tradable-signal backtests |
| 8 | `statistical-validation/` | Multi-bias and OOS gate |
| 9 | `causal-inference/` | Classify relationship type |
| 10 | `signal-synthesis/` | Render the signal card |
| 11 | `visual-display/` | Tufte-aware chart discipline |
| 12 | `dashboard-builder/` | Aggregate signals into a dashboard |

## Agents

Higher-level orchestrators that invoke sub-skills:

`research-architect`, `dataset-scout`, `data-quality-auditor`, `feature-engineer`, `backtest-engine`, `causal-skeptic`, `findings-evaluator`, `dashboard-designer`.

## Core rules

1. Never invent dataset metadata if it should come from the `datasources` repo.
2. Always reference datasets by `dataset_id`.
3. Always record the datasource registry commit hash.
4. Always materialise a dataset contract before backtesting.
5. Always respect native cadence, variable type, default aggregation, and release lag.
6. Never sum stock, rate, or price variables unless explicitly overridden.
7. Always log the number of features and lags tested.
8. Always mark whether the best feature was pre-specified or discovered.
9. Always flag multiple-testing risk.
10. Never call a signal high-confidence unless it survives out-of-sample validation.
11. Always distinguish KPI prediction from tradable signal backtesting.
12. Always produce caveats, failure modes, and next iteration.

## Output structure

Every run lands in `experiments/runs/<run-id>/`:

```text
run.yaml
registry-lock.yaml
signal-spec.yaml
dataset-contracts.yaml
cadence-rollup-audit.yaml
feature-grid.yaml
metrics.json
validation-report.md
signal-card.md
dashboard.html
```

Traceability: `claim → dataset_id → field → join_key → cadence transform → feature → backtest → validation → confidence → current read`.

## Status

v3.0.0.dev0. Migration from v2.0.0 in progress. See `BUILD_CHECKLIST.md` at repo root.
