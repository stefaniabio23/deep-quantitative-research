# deep-quantitative-research

A registry-aware quantitative research engine. Turns a vague research idea into a falsifiable, reproducible, dashboard-ready signal artifact.

The unit of work is a **signal**, not a model. A signal carries its hypothesis, datasets, contracts, features, backtest, validation, causal read, confidence, caveats, and next iteration in one folder.

```text
Idea → Hypothesis → Dataset Selection → Dataset Contract → Cadence Alignment
     → Feature Grid → Backtest → Statistical Validation → Signal Card → Dashboard
```

## What it does

Give it a research question. The pipeline formulates a testable hypothesis, queries the sibling `datasources` registry, scores candidate datasets by hypothesis fit, materialises an experiment-specific dataset contract, aligns cadences safely, generates a controlled feature grid, runs walk-forward backtests in either KPI-prediction or tradable-signal mode, validates against leakage and overfitting, and emits a signal card plus a dashboard.

If the evidence is weak it caps confidence and returns a documented null. A null result with the right caveats is a finding.

**Domains:**

- **Finance.** KPI-to-price analysis, factor decomposition, backtesting, lag analysis, event studies.
- **Biotech.** Clinical trial signal extraction, drug pipeline analysis, openFDA / OpenTargets feeds.
- **Macro / quant.** Factor models, macro relationships, dependence structures, regime analysis.

## Architecture

Two repos, clean separation:

```text
~/Projects/datasources/                 canonical public-data registry
~/Projects/deep-quant-research/         research workflow engine (this repo)
```

The `datasources` repo owns dataset entries, schemas, fields, join keys, cadence, release lag, point-in-time safety. This repo owns hypotheses, dataset selection reasoning, signal specs, feature grids, backtests, validation, signal cards, and dashboards.

Layers:

```text
Layer 1  Registry         What data exists?         datasources
Layer 2  Semantics        What does it mean?        shared
Layer 3  Experiment       What are we testing?      deep-quant
Layer 4  Research output  What do we believe?       deep-quant
```

Compact form: `Data Registry → Signal Factory → Research Ledger → Dashboard`.

## Install

```bash
git clone https://github.com/stephbeccag/deep-quantitative-research.git
cd deep-quantitative-research
pip install -e ".[dev]"
cp .env.example .env             # add FRED_API_KEY etc.
```

The sibling registry is expected at `../datasources/`. Override with `DATASOURCES_PATH` in `.env` if needed.

## Usage

Per-stage commands (recommended):

```bash
deep-quant formulate-hypothesis \
  --idea "Search interest predicts UK retail sales" \
  --out experiments/ideas/uk-retail-demand.yaml

deep-quant find-datasets \
  --hypothesis experiments/ideas/uk-retail-demand.yaml \
  --out experiments/specs/dataset-candidates.yaml

deep-quant design-signal \
  --target ons-retail-sales-index \
  --predictors google-trends-retail-searches,boe-consumer-credit \
  --out experiments/specs/uk-retail-search-demand-signal.yaml

deep-quant run-signal \
  --spec experiments/specs/uk-retail-search-demand-signal.yaml

deep-quant render-dashboard \
  --run experiments/runs/2026-06-09-uk-retail-search-demand/
```

End-to-end Claude skill:

```text
/deep-quantitative-research "Does Google Trends interest in GLP-1 drugs predict next-quarter Novo obesity revenue?"
```

## Structure

```text
deep-quantitative-research/
├── README.md, QUICKSTART.md, CHANGELOG.md, CLAUDE.md
├── ARCHITECTURE_LOG.md, BUILD_CHECKLIST.md
├── pyproject.toml, requirements.txt, .env.example, .mcp.json
│
├── config/
│   ├── datasources.yaml           bridge to ../datasources
│   ├── research_defaults.yaml     default knobs for feature grids, validation, etc.
│   ├── scoring_weights.yaml       dataset_fit_score weights
│   └── validation_thresholds.yaml confidence-cap thresholds
│
├── skills/
│   └── deep-quantitative-research/
│       ├── SKILL.md
│       ├── commands/              one slash command per pipeline stage
│       ├── workflows/             end-to-end and domain-specific recipes
│       ├── skills/                12 sub-skills, one per pipeline stage
│       ├── agents/                8 canonical agents that orchestrate sub-skills
│       ├── templates/             signal-card, dataset-contract, dashboard, etc.
│       ├── references/            registry interface, guardrails, Tufte, etc.
│       └── examples/
│
├── src/deep_quantitative_research/
│   ├── registry/                  bridge client to the datasources repo
│   ├── research/                  hypothesis, dataset selection, signal spec
│   ├── timeseries/                cadence, alignment, release lags, transforms
│   ├── features/                  grid, transforms, selection, overfitting
│   ├── backtest/                  KPI and trading paths, walk-forward, metrics
│   ├── validation/                data quality, statistical tests, robustness
│   ├── reporting/                 signal card, charts, markdown
│   ├── dashboard/                 HTML emitter, multi-signal aggregator
│   └── schemas/                   YAML schemas for every artefact
│
├── scripts/                       thin CLI wrappers around the Python package
├── experiments/                   research ledger: ideas/ specs/ runs/ outputs/
├── examples/                      runnable demos with expected outputs
├── docs/                          architecture, workflow, validation, testing
└── tests/                         pytest suite with fixtures
```

## Agents

| Agent | Role |
|---|---|
| `research-architect` | Designs the study, sets evidence threshold |
| `dataset-scout` | Searches the registry for candidate datasets |
| `data-quality-auditor` | Runs four-bias audit on every dataset |
| `feature-engineer` | Builds controlled feature grids |
| `backtest-engine` | Walk-forward KPI / tradable backtests |
| `causal-skeptic` | Classifies relationship type, blocks unjustified causal language |
| `findings-evaluator` | Reconciles results, scores confidence, gates the report |
| `dashboard-designer` | Composes multi-signal dashboard with current read |

## Status

**v3.0.0.dev0.** Migration from v2.0.0 in progress. See `BUILD_CHECKLIST.md` for the live plan and `ARCHITECTURE_LOG.md` for the OG-vs-target gap analysis. Pre-v3 state preserved at git tag `pre-v3-2026-06-09`.

Deprecated names that may appear in old branches or external links: `deep-research`, `deep-quant-research`.

## License

MIT, see `LICENSE`.
