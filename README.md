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
datasources/                  canonical public-data registry (sibling repo)
deep-quantitative-research/   research workflow engine (this repo)
```

The `datasources` repo owns dataset entries, schemas, fields, join keys, cadence, release lag, point-in-time safety. This repo owns hypotheses, dataset selection reasoning, signal specs, feature grids, backtests, validation, signal cards, and dashboards.

Layers:

```text
Layer 1  Registry         What data exists?         datasources
Layer 2  Semantics        What does it mean?        shared
Layer 3  Experiment       What are we testing?      this repo
Layer 4  Research output  What do we believe?       this repo
```

Compact form: `Data Registry → Signal Factory → Research Ledger → Dashboard`.

## Install

```bash
git clone https://github.com/stefaniabio23/deep-quantitative-research.git
cd deep-quantitative-research
pip install -e ".[dev]"
cp .env.example .env             # add FRED_API_KEY etc.
```

The sibling registry is expected at `../datasources/`. Override with `DATASOURCES_PATH` in `.env` if needed.

## Usage

Two worked demos are committed under `examples/`. Run either with one command:

```bash
./examples/biotech-pos/run.sh      # planted-signal demo; recovers a real lead-lag
./examples/null-control/run.sh     # negative control; pipeline returns a documented null
```

The shipped CLI subcommands:

```bash
deep-quant query-datasources --healthcheck
deep-quant query-datasources --query retail --domain finance-markets

deep-quant build-dataset-contract <dataset_id> --role predictor
deep-quant score-dataset <dataset_id> --hypothesis path/to/hypothesis.yaml
deep-quant assess-join <source_dataset> <target_dataset>

deep-quant run-signal \
  --spec experiments/specs/<signal>.yaml \
  --target-csv path/to/target.csv \
  --predictor-csv <dataset_id>=path/to/predictor.csv \
  --run-dir experiments/runs/<run-id>/

deep-quant render-family-dashboard \
  --run-dir experiments/runs/<run-a>/ \
  --run-dir experiments/runs/<run-b>/ \
  --out experiments/outputs/family.html
```

`run-signal` is the end-to-end command. It loads the SignalSpec, rolls cadences, builds the feature grid, runs the KPI backtest, applies the validation gate, and writes every artefact (including `dashboard.html` when `outputs.dashboard: true`) into the run directory.

Per-stage subcommands (`formulate-hypothesis`, `find-datasets`, `design-signal`, `validate-signal`, `render-signal-card`) are planned; see `BUILD_CHECKLIST.md`. Until they ship, drive each stage through the sub-skill specs under `skills/deep-quantitative-research/skills/`.

## Structure

```text
deep-quantitative-research/
├── README.md, QUICKSTART.md, CHANGELOG.md, CLAUDE.md, CONTRIBUTING.md
├── ARCHITECTURE_LOG.md, BUILD_CHECKLIST.md
├── pyproject.toml, .env.example, .mcp.json
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
│       ├── agents/                7 v2-carryover agents; v3 canonical rename pending
│       ├── templates/             signal-card, dataset-contract, dashboard, etc.
│       └── references/            registry interface, guardrails, Tufte, etc.
│
├── src/deep_quantitative_research/
│   ├── registry/                  bridge client to the datasources repo
│   ├── research/                  hypothesis, dataset selection, signal spec
│   ├── timeseries/                cadence, alignment, release lags, transforms
│   ├── features/                  grid, transforms, selection, overfitting
│   ├── backtest/                  KPI path, walk-forward, metrics
│   ├── validation/                data quality, statistical tests, robustness, selection bias
│   ├── reporting/                 signal card, charts, markdown
│   ├── dashboard/                 HTML emitter, multi-signal aggregator
│   └── schemas/                   YAML schemas for every artefact
│
├── examples/
│   ├── biotech-pos/               planted-signal demo (oncology readouts → biotech subindex)
│   └── null-control/              negative control demo (white noise → documented null)
│
└── tests/                         pytest suite (130 tests)
```

`experiments/` is the runtime research ledger; it's not committed, the pipeline writes into it.

## Status

**v3.0.0.dev0.** Migration from v2.0.0 complete; Phases 1 to 8 shipped. See `BUILD_CHECKLIST.md` for the live plan and `ARCHITECTURE_LOG.md` for the OG-vs-target gap analysis. Pre-v3 state preserved at git tag `pre-v3-2026-06-09`.

Deprecated names that may appear in old branches or external links: `deep-research`, `deep-quant-research`.

## License

MIT, see `LICENSE`.
