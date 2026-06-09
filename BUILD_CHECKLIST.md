# Deep Quantitative Research, Full Architecture Spec Checklist

Persistent, tickable plan for the v3 migration. Stephanie's comprehensive spec is the source of truth; this file is its enacted form. Pair with `ARCHITECTURE_LOG.md` for the OG inventory and rationale.

**How to use this file**

- Each section has checkboxes. Tick when done; do not delete.
- Decisions live in section 0 and stay locked unless explicitly revisited.
- New work that emerges goes into the same section as a new sub-bullet, not into a new file.

---

## 0. Phase 0 Decisions (locked 2026-06-09)

- [x] **Canonical name:** `deep-quantitative-research`. Rename the repo, skill folder, Python package, command, and CLI accordingly.
- [x] **`datasources` repo exists.** Lives at `~/Projects/datasources/` and on GitHub. Scaffolding tasks below are scoped to the gaps (DuckDB export, `join_key_graph.json`), not a full build.
- [x] **Retire `originality-scout`.** Drop from agent set and pipeline.
- [x] **Retire `knowledge-base-builder`.** Drop from agent set and pipeline.
- [x] **Adopt the canonical agent set** from section 7: `research-architect`, `dataset-scout`, `data-quality-auditor`, `feature-engineer`, `backtest-engine`, `causal-skeptic`, `findings-evaluator`, `dashboard-designer`.
- [x] **12 sub-skills, not 11.** Add `visual-display/` as a sub-skill alongside the original eleven.
- [x] **Branch strategy.** In-place rebuild on `main`; pre-v3 state preserved at git tag `pre-v3-2026-06-09` (decided 2026-06-09).
- [x] **Critique cluster: DROP.** Checklist-style validation folds into `statistical-validation`, `dataset-contract`, and `feature-engineering` sub-skills (decided 2026-06-09).
- [x] **`shared/critique-checklists/`: DROP** the directory; keep the idea of checklist-driven validation in the relevant sub-skills. Keep the elegant validator scripts (`validate_output.py`) and port to `src/deep_quantitative_research/validation/` (decided 2026-06-09).
- [x] **Bio-research:** parked in section 20.3 as post-v3 work (decided 2026-06-09).

---

## 1. Canonical Product Definition

### Objective

Build `deep-quantitative-research` as a Claude-native quantitative research operating system that converts vague research ideas into falsifiable, reproducible, dashboard-ready signal artifacts.

The system should turn:

```text
Idea → Hypothesis → Dataset Selection → Dataset Contract → Cadence Alignment → Feature Grid → Backtest → Statistical Validation → Signal Card → Dashboard
```

into a standardized workflow.

### Core Design Principle

The unit of work is a **signal**.

A signal contains:

- [ ] Hypothesis
- [ ] Target variable
- [ ] Predictor variables
- [ ] Dataset references
- [ ] Dataset contracts
- [ ] Join logic
- [ ] Cadence logic
- [ ] Feature grid
- [ ] Backtest results
- [ ] Statistical validation
- [ ] Causal interpretation
- [ ] Current read
- [ ] Confidence score
- [ ] Caveats
- [ ] Next iteration

### Separation of Responsibilities

```text
datasources repo = canonical public-data registry
deep-quantitative-research repo = research workflow engine
```

The `datasources` repo owns:

- [x] Public dataset metadata
- [x] Dataset schemas
- [x] Fields
- [x] Join keys
- [x] Entry kinds
- [x] Source URLs
- [x] Coverage
- [x] Cadence
- [x] Variable types
- [x] Access method
- [x] License
- [x] Point-in-time safety metadata

(Owned and largely populated in `~/Projects/datasources/`.)

The `deep-quantitative-research` repo owns:

- [ ] Hypotheses
- [ ] Research questions
- [ ] Dataset selection reasoning
- [ ] Signal specs
- [ ] Experiment specs
- [ ] Feature grids
- [ ] Backtests
- [ ] Validation reports
- [ ] Signal cards
- [ ] Dashboards
- [ ] Research ledger

---

## 2. Naming and Package Canonicalization

### 2.1 Canonical Names

```text
repo: deep-quantitative-research
skill folder: skills/deep-quantitative-research/
skill name: deep-quantitative-research
command: /deep-quantitative-research
python package: deep_quantitative_research
cli command: deep-quant
```

- [ ] Rename repo dir on disk (`mv ~/Projects/deep-quant-research ~/Projects/deep-quantitative-research`) and update the GitHub remote. **Deferred to after push.**
- [x] Rename installable skill path to `skills/deep-quantitative-research/`.
- [x] Update `SKILL.md` name and command.
- [x] Define CLI package as `deep_quantitative_research` in `pyproject.toml` (implementation in Phase 4).
- [x] Update README, QUICKSTART, CHANGELOG.
- [x] Remove old references to `deep-research` or `deep-quant-research` in core docs; deprecation note added to README and CONTRIBUTING.
- [ ] Update memory notes (`~/Desktop/second-brain/compounds/deep-quant-research.md`, `~/Desktop/Second Brain/work/deep-quant-research.md`, `PROJECTS.md`). **Deferred to after re-push.**
- [ ] Update `~/.claude/SKILLS.md` lookup table. **Deferred to after re-push.**
- [x] Migration note added to CHANGELOG.md under [3.0.0.dev0].

### 2.2 Deprecated Names

If older naming conventions remain in user-facing docs, add a compatibility note:

```md
Deprecated names:
- deep-research
- deep-quant-research

Canonical name:
- deep-quantitative-research
```

- [ ] Search entire repo for old names.
- [ ] Replace in README.
- [ ] Replace in SKILL.md.
- [ ] Replace in quickstart.
- [ ] Replace in changelog.
- [ ] Replace in examples.
- [ ] Replace in command files.
- [ ] Replace in tests.
- [ ] Add deprecation note if needed.

---

## 3. Repository Architecture

### 3.1 Target Repo Layout

```text
deep-quantitative-research/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── CLAUDE.md
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── .mcp.json
│
├── config/
│   ├── datasources.yaml
│   ├── research_defaults.yaml
│   ├── scoring_weights.yaml
│   └── validation_thresholds.yaml
│
├── skills/
│   └── deep-quantitative-research/
│       ├── SKILL.md
│       ├── README.md
│       ├── commands/
│       ├── workflows/
│       ├── skills/
│       ├── agents/
│       ├── templates/
│       ├── references/
│       └── examples/
│
├── src/
│   └── deep_quantitative_research/
│       ├── registry/
│       ├── research/
│       ├── timeseries/
│       ├── features/
│       ├── backtest/
│       ├── validation/
│       ├── reporting/
│       ├── dashboard/
│       └── schemas/
│
├── scripts/
│   ├── fetch-data
│   ├── query-datasources
│   ├── validate-dataset
│   ├── cadence-roll-up
│   ├── build-feature-grid
│   ├── run-timeseries-backtest
│   ├── render-signal-card
│   └── render-dashboard
│
├── experiments/
│   ├── ideas/
│   ├── specs/
│   ├── runs/
│   └── outputs/
│
├── examples/
│   ├── 01-retail-sales-nowcast/
│   ├── 02-clinical-trials-biotech-signal/
│   ├── 03-macro-equity-signal/
│   └── 04-signal-dashboard/
│
├── docs/
│   ├── architecture.md
│   ├── research-workflow.md
│   ├── datasources-integration.md
│   ├── data-contracts.md
│   ├── cadence-roll-up.md
│   ├── feature-engineering.md
│   ├── validation.md
│   ├── dashboards.md
│   └── testing.md
│
└── tests/
    ├── fixtures/
    ├── test_registry_client.py
    ├── test_dataset_selection.py
    ├── test_dataset_contract.py
    ├── test_cadence_rollup.py
    ├── test_feature_grid.py
    ├── test_timeseries_backtest.py
    ├── test_validation.py
    ├── test_signal_card.py
    └── test_dashboard.py
```

- [ ] Keep `skills/deep-quantitative-research/` as the only canonical installable Claude skill.
- [ ] Keep Python execution logic in `src/deep_quantitative_research/`.
- [ ] Keep `scripts/` as thin CLI wrappers around the Python package.
- [ ] Keep `experiments/` as the research ledger.
- [ ] Keep `examples/` as runnable demonstrations.
- [ ] Keep `docs/` as architecture and development documentation.
- [ ] Do not duplicate agents at root and skill level.
- [ ] Do not duplicate dataset metadata from the `datasources` repo.

---

## 4. Datasources Registry Integration

### 4.1 Purpose

The `datasources` repo is the canonical source of truth for public datasets. `deep-quantitative-research` should reference it rather than duplicate it.

- [ ] Reference datasets by stable `dataset_id`.
- [ ] Reference fields by canonical field names from `datasources`.
- [ ] Reference join keys from `datasources`.
- [ ] Reference registry commit hash in every experiment.
- [ ] Never invent dataset metadata if it should come from the registry.
- [ ] Materialize dataset contracts for each experiment.
- [ ] Store registry snapshot metadata in every run.

### 4.2 Datasources Repo Gaps to Close

State as of 2026-06-09: schemas, entries (10 domain folders), `generated/datasets.csv`, `fields.csv`, `index.json`, `join-keys.csv`, `join-key-index.md`, `sources.csv`, plus `scripts/` and a working `skills/add-dataset-entry/` skill all present. Gaps:

- [ ] Add `generated/catalog.duckdb` export (preferred consumer format).
- [ ] Add `generated/join_key_graph.json` (graph-form, not just CSV/MD list).
- [ ] Confirm `index.json` matches the `catalog.json` shape expected by `config/datasources.yaml`, rename or add a symlink if needed.
- [ ] Add `generated/source_quality_scores.csv` (can stub initially).
- [ ] Verify schema files cover every field referenced in `config/datasources.yaml`.
- [ ] Confirm the GitHub remote and decide release cadence for the registry.

### 4.3 Datasources Config

Create `config/datasources.yaml`:

```yaml
datasources_repo:
  path: "../datasources"
  generated_catalog: "../datasources/generated/catalog.duckdb"
  generated_catalog_json: "../datasources/generated/catalog.json"
  generated_fields: "../datasources/generated/fields.csv"
  join_key_graph: "../datasources/generated/join_key_graph.json"

registry_mode: local

versioning:
  require_commit_hash: true
  lock_registry_snapshot: true

dataset_id_field: dataset_id
source_id_field: source_id
```

- [ ] Add `config/datasources.yaml`.
- [ ] Support relative local path to `datasources`.
- [ ] Support generated `catalog.duckdb`.
- [ ] Support generated `catalog.json`.
- [ ] Support generated `fields.csv`.
- [ ] Support generated `join_key_graph.json`.
- [ ] Require datasource registry commit hash for research runs.
- [ ] Fail gracefully if registry is unavailable.
- [ ] Add a `deep-quant query-datasources --healthcheck` command.

### 4.4 Registry Client

```text
src/deep_quantitative_research/registry/
├── client.py
├── index.py
├── search.py
├── contracts.py
├── join_graph.py
└── scoring.py
```

Registry client API:

```python
registry.search_datasets(query)
registry.get_dataset(dataset_id)
registry.get_fields(dataset_id)
registry.get_join_keys(dataset_id)
registry.find_compatible_sources(target_dataset_id)
registry.find_join_path(source_dataset_id, target_dataset_id)
registry.build_dataset_contract(dataset_id)
registry.score_dataset_fit(hypothesis, dataset_id)
registry.get_registry_commit()
```

- [ ] Implement local registry client.
- [ ] Load generated catalog.
- [ ] Load field metadata.
- [ ] Load join-key graph.
- [ ] Search datasets by keyword, domain, field, join key, cadence, and entry kind.
- [ ] Retrieve canonical dataset metadata by `dataset_id`.
- [ ] Retrieve fields by `dataset_id`.
- [ ] Retrieve join keys by `dataset_id`.
- [ ] Score dataset fit against a hypothesis.
- [ ] Build experiment-specific dataset contracts.
- [ ] Record registry commit hash.
- [ ] Add unit tests using a small fixture registry.

---

## 5. Canonical Skill Folder

### 5.1 Skill Layout

```text
skills/deep-quantitative-research/
├── SKILL.md
├── README.md
├── commands/
│   ├── deep-quantitative-research.md
│   ├── formulate-hypothesis.md
│   ├── find-datasets.md
│   ├── design-signal.md
│   ├── backtest-signal.md
│   ├── validate-signal.md
│   └── build-dashboard.md
│
├── workflows/
│   ├── end-to-end-signal-research.md
│   ├── dataset-to-signal.md
│   ├── kpi-nowcast.md
│   ├── tradable-signal.md
│   ├── alt-data-equity-signal.md
│   └── bio-finance-signal.md
│
├── skills/
│   ├── hypothesis-formulation/
│   ├── datasource-query/
│   ├── dataset-selection/
│   ├── dataset-contract/
│   ├── cadence-roll-up/
│   ├── feature-engineering/
│   ├── time-series-backtest/
│   ├── statistical-validation/
│   ├── causal-inference/
│   ├── signal-synthesis/
│   ├── visual-display/
│   └── dashboard-builder/
│
├── agents/
│   ├── research-architect.md
│   ├── dataset-scout.md
│   ├── data-quality-auditor.md
│   ├── feature-engineer.md
│   ├── backtest-engine.md
│   ├── causal-skeptic.md
│   ├── findings-evaluator.md
│   └── dashboard-designer.md
│
├── templates/
│   ├── signal-template.md
│   ├── dataset-selection-template.md
│   ├── dataset-contract-template.md
│   ├── idea-template.md
│   ├── experiment-template.md
│   ├── model-template.md
│   ├── dashboard-template.md
│   └── validation-report-template.md
│
├── references/
│   ├── datasource-registry-interface.md
│   ├── cadence-roll-up.md
│   ├── feature-engineering-guardrails.md
│   ├── backtesting-pitfalls.md
│   ├── statistical-validation.md
│   ├── probability-foundations.md
│   ├── causal-inference-notes.md
│   ├── visual-display-principles.md
│   └── market-assumptions.md
│
└── examples/
    ├── retail-sales-nowcast/
    ├── clinical-trials-biotech-signal/
    ├── macro-equity-signal/
    └── dashboard-signal-pack/
```

- [ ] Create `skills/deep-quantitative-research/SKILL.md`.
- [ ] Add command docs.
- [ ] Add workflow docs.
- [ ] Add nested skill modules.
- [ ] Add canonical agents.
- [ ] Add output templates.
- [ ] Add references for progressive disclosure.
- [ ] Add examples.
- [ ] Remove root-level duplicate agents unless they are development scaffolding.
- [ ] Clearly label any non-canonical scaffolding.

---

## 6. SKILL.md Specification

### 6.1 Required Frontmatter

```yaml
---
name: deep-quantitative-research
description: Build falsifiable quantitative research signals using datasource registry search, dataset contracts, cadence alignment, feature grids, backtests, validation, and signal cards.
---
```

- [ ] Include canonical name.
- [ ] Include registry-aware description.
- [ ] Mention dataset contracts.
- [ ] Mention cadence alignment.
- [ ] Mention feature grids.
- [ ] Mention backtesting.
- [ ] Mention validation.
- [ ] Mention signal cards and dashboards.

### 6.2 Skill Behavior Rules

Add to `SKILL.md`:

```md
## Core Rules

1. Never invent dataset metadata if it should come from the `datasources` repo.
2. Always reference datasets by `dataset_id`.
3. Always record the datasource registry commit hash.
4. Always materialize a dataset contract before backtesting.
5. Always respect native cadence, variable type, default aggregation, and release lag.
6. Never sum stock, rate, or price variables unless explicitly overridden.
7. Always log the number of features and lags tested.
8. Always mark whether the best feature was pre-specified or discovered.
9. Always flag multiple-testing risk.
10. Never call a signal high-confidence unless it survives out-of-sample validation.
11. Always distinguish KPI prediction from tradable signal backtesting.
12. Always produce caveats, failure modes, and next iteration.
```

- [ ] Add hard research rules.
- [ ] Add anti-overfitting rules.
- [ ] Add dataset registry rules.
- [ ] Add point-in-time safety rules.
- [ ] Add signal confidence rules.

---

## 7. Workflow Modules

### 7.1 `hypothesis-formulation/`

Purpose: create a specific, falsifiable prediction about the relationship between variables. Converts vague ideas into testable research questions.

Inputs:

- [ ] Broad research idea
- [ ] Domain
- [ ] Suspected mechanism
- [ ] Target KPI or asset outcome
- [ ] Candidate predictor concepts
- [ ] Desired cadence
- [ ] Investment or research use case

Outputs:

- [ ] Research question
- [ ] Testable hypothesis
- [ ] Target variable
- [ ] Candidate predictors
- [ ] Expected direction
- [ ] Expected lag
- [ ] Economic mechanism
- [ ] Falsification criteria
- [ ] Dataset search prompts
- [ ] Candidate dataset requirements

Checklist:

- [ ] Ask: What research question are we trying to answer?
- [ ] Ask: What target variable do we need?
- [ ] Ask: What observable proxy could predict it?
- [ ] Ask: What upstream variables could predict it?
- [ ] Ask: What downstream effects might reveal it?
- [ ] Ask: What knock-on effects should be measurable?
- [ ] Ask: What would falsify the hypothesis?
- [ ] Link to `datasources` repo through `datasource-query`.
- [ ] Search for better public datasets or methods if the registry is insufficient.
- [ ] Avoid choosing datasets merely because they exist.

Example output:

```yaml
hypothesis_id: HYP-2026-001
statement: Search interest in a retail category predicts future UK retail sales growth.
target_variable: UK retail sales YoY growth
expected_direction: positive
expected_lag_periods: [0, 1, 2, 3]
mechanism: Search intent → consumer demand → purchases → reported retail sales
falsification:
  - relationship fails out-of-sample
  - signal only works after excessive feature search
  - relationship disappears after controlling for trend
```

### 7.2 `datasource-query/`

Purpose: query the `datasources` repo for relevant datasets, fields, join keys, coverage, cadence, and access constraints.

Inputs:

- [ ] Hypothesis
- [ ] Target variable concept
- [ ] Predictor concept
- [ ] Domain
- [ ] Required cadence
- [ ] Required history
- [ ] Required geography
- [ ] Required join keys

Outputs:

- [ ] Candidate target datasets
- [ ] Candidate predictor datasets
- [ ] Candidate context datasets
- [ ] Relevant fields
- [ ] Join keys
- [ ] Cadence compatibility
- [ ] Point-in-time safety
- [ ] Release-lag metadata
- [ ] Access constraints
- [ ] Registry references

Checklist:

- [ ] Search by dataset name.
- [ ] Search by domain.
- [ ] Search by field.
- [ ] Search by join key.
- [ ] Search by cadence.
- [ ] Search by entry kind.
- [ ] Return candidate target datasets.
- [ ] Return candidate predictor datasets.
- [ ] Return supporting / context datasets.
- [ ] Flag missing required variables.
- [ ] Flag weak proxies.
- [ ] Flag datasets with insufficient history.
- [ ] Flag point-in-time safety issues.
- [ ] Flag access or licensing constraints.

### 7.3 `dataset-selection/`

Purpose: choose datasets based on hypothesis fit, not availability.

Checklist:

- [ ] Define target variable needed for the hypothesis.
- [ ] Define predictor variable needed for the hypothesis.
- [ ] Define context variables that may help interpretation.
- [ ] Identify upstream variables.
- [ ] Identify downstream variables.
- [ ] Identify observable proxies.
- [ ] Search `datasources` for candidate datasets.
- [ ] Search externally for better datasets if needed.
- [ ] Score each dataset for hypothesis fit.
- [ ] Select target dataset.
- [ ] Select predictor dataset or datasets.
- [ ] Select context datasets.
- [ ] Reject weak or tempting but irrelevant datasets.
- [ ] Explain why selected datasets are appropriate.
- [ ] Explain what is missing.
- [ ] Explain what would improve the dataset layer.

Dataset fit score:

```yaml
dataset_fit_score:
  economic_proximity: 0-10
  coverage: 0-10
  cadence_fit: 0-10
  release_lag_clarity: 0-10
  point_in_time_safety: 0-10
  survivorship_bias_risk: 0-10
  api_scriptability: 0-10
  cost_access_practicality: 0-10
  total_score: 0-10
```

Dataset-selection output:

```md
## Selected Datasets

### Target

- Dataset ID:
- Field:
- Cadence:
- Why this is the target:
- Limitations:

### Predictors

- Dataset ID:
- Field:
- Expected relationship:
- Expected lag:
- Limitations:

### Context

- Dataset ID:
- Field:
- Why it helps interpretation:

### Rejected Datasets

| Dataset | Reason rejected |
|---|---|
|  |  |
```

### 7.4 `dataset-contract/`

Purpose: convert registry metadata into an experiment-specific contract. Every signal must materialize a dataset contract before feature engineering or backtesting.

Required contract:

```yaml
dataset_contract:
  dataset_id: string
  role: target | predictor | context | benchmark
  registry_commit: string

  fields:
    date_field: string
    value_field: string
    entity_fields: []

  join_keys:
    required: []
    available: []
    missing: []

  cadence:
    native_cadence: daily | weekly | monthly | quarterly | annual | irregular
    target_cadence: monthly | quarterly | annual
    aggregation: sum | mean | last | max | min | median

  variable:
    variable_type: flow | stock | rate | price | count | sentiment | event
    unit: string
    transform_allowed: true

  timing:
    release_lag_days: integer
    point_in_time_safe: true | false
    revisions_possible: true | false

  quality:
    coverage_start: date
    coverage_end: date
    missingness_policy: error | drop | forward_fill | interpolate | flag
    known_limitations: []
```

Checklist:

- [ ] Create dataset contract for target.
- [ ] Create dataset contract for each predictor.
- [ ] Create dataset contract for each context dataset.
- [ ] Pull metadata from registry.
- [ ] Record registry commit hash.
- [ ] Record field choices.
- [ ] Record join keys.
- [ ] Record native cadence.
- [ ] Record target cadence.
- [ ] Record variable type.
- [ ] Record default aggregation.
- [ ] Record release lag.
- [ ] Record point-in-time safety.
- [ ] Record missing-data policy.
- [ ] Record known limitations.
- [ ] Fail if required fields are unavailable.
- [ ] Warn if point-in-time safety is false.
- [ ] Warn if join keys require manual semantic mapping.

### 7.5 `cadence-roll-up/`

Purpose: align source series to the target KPI cadence safely. Essential for KPI prediction and time-series backtesting.

Required fields:

```yaml
variable_type: flow | stock | rate | price | count | sentiment | event
default_aggregation: sum | mean | last | max | min | median
release_lag_days: integer
point_in_time_safe: true | false
```

Default aggregation rules:

| Variable Type | Default Aggregation | Example |
| --- | --- | --- |
| `flow` | `sum` | revenue, sales, prescriptions |
| `stock` | `last` | inventory, subscribers |
| `rate` | `mean` | unemployment rate, conversion rate |
| `price` | `last` or `mean` | share price, commodity price |
| `count` | `sum` | mentions, visits, events |
| `sentiment` | `mean` | review sentiment, news sentiment |
| `event` | `sum` or `max` | approvals, trial readouts |

Checklist:

- [ ] Support daily to weekly.
- [ ] Support daily to monthly.
- [ ] Support daily to quarterly.
- [ ] Support weekly to monthly.
- [ ] Support weekly to quarterly.
- [ ] Support monthly to quarterly.
- [ ] Support monthly to annual.
- [ ] Support quarterly to annual.
- [ ] Support fiscal quarters.
- [ ] Support calendar quarters.
- [ ] Handle partial current periods.
- [ ] Handle missing observations.
- [ ] Handle duplicate timestamps.
- [ ] Handle release lags.
- [ ] Handle point-in-time availability dates.
- [ ] Prevent summing stock variables by default.
- [ ] Prevent averaging flow variables by default unless explicitly overridden.
- [ ] Produce cadence audit output.

Cadence audit output:

```yaml
cadence_rollup_audit:
  source_dataset_id: string
  source_cadence: daily
  target_cadence: quarterly
  variable_type: flow
  aggregation: sum
  periods_created: 24
  partial_periods_dropped: 1
  missing_periods: 0
  release_lag_applied_days: 7
  point_in_time_safe: true
  warnings: []
```

### 7.6 `feature-engineering/`

Purpose: generate controlled feature grids without uncontrolled data mining.

Default feature grid:

```yaml
features:
  - raw
  - diff
  - pct_change
  - mom_1p
  - mom_3p
  - yoy_1y
  - yo2y
  - rolling_mean_3
  - rolling_mean_6
  - rolling_sum_3
  - rolling_sum_12
  - zscore_12
  - zscore_24
  - lag_1
  - lag_2
  - lag_3
  - seasonally_adjusted_if_available
```

Checklist:

- [ ] Generate controlled feature grid.
- [ ] Support raw values.
- [ ] Support differences.
- [ ] Support percent change.
- [ ] Support momentum.
- [ ] Support YoY.
- [ ] Support Yo2Y.
- [ ] Support rolling mean.
- [ ] Support rolling sum.
- [ ] Support z-score normalization.
- [ ] Support lags.
- [ ] Support seasonal-adjusted version if available.
- [ ] Limit number of features by config.
- [ ] Limit number of lags by config.
- [ ] Record all tested features.
- [ ] Record all tested lags.
- [ ] Mark whether best feature was pre-specified.
- [ ] Mark whether best feature was discovered.
- [ ] Trigger multiple-testing warning if feature grid is large.
- [ ] Require out-of-sample survival for confidence upgrade.
- [ ] Save feature grid to run directory.
- [ ] Sub-skill `feature-importance/` (ANOVA over feature-importance to decide how much of that feature to include over time).

Feature search log:

```yaml
feature_search_log:
  features_tested: 42
  lags_tested: 3
  best_feature: yoy_1y_lag_2
  best_feature_pre_specified: false
  multiple_testing_correction_needed: true
  correction_method: benjamini_hochberg
  out_of_sample_survives: true
  confidence_cap: medium
```

### 7.7 `time-series-backtest/`

Purpose: evaluate whether predictors have useful relationship to target variables. The skill must distinguish two modes:

```text
1. KPI prediction
   predictor → company KPI / economic variable

2. Tradable signal
   predictor → asset return / spread / factor
```

KPI prediction metrics:

- [ ] Rolling correlation
- [ ] Rank correlation
- [ ] Directionality
- [ ] Directional correctness
- [ ] MAE
- [ ] MAPE
- [ ] RMSE
- [ ] Hit rate
- [ ] Lead-lag profile
- [ ] Out-of-sample degradation

Tradable signal metrics:

- [ ] CAGR
- [ ] Sharpe
- [ ] Sortino
- [ ] Maximum drawdown
- [ ] Hit rate
- [ ] Turnover
- [ ] Transaction costs
- [ ] Benchmark alpha
- [ ] Benchmark beta
- [ ] Exposure
- [ ] Walk-forward validation
- [ ] Capacity caveat

Checklist:

- [ ] Support KPI prediction mode.
- [ ] Support tradable signal mode.
- [ ] Align target and predictor cadences.
- [ ] Respect release lags.
- [ ] Prevent lookahead leakage.
- [ ] Support raw signal tests.
- [ ] Support YoY signal tests.
- [ ] Support rolling correlation.
- [ ] Support lead-lag analysis.
- [ ] Support walk-forward validation.
- [ ] Support train / test split.
- [ ] Support regime split.
- [ ] Report out-of-sample degradation.
- [ ] Save backtest results to JSON.
- [ ] Save human-readable summary to markdown.

Backtest output:

```yaml
backtest_result:
  mode: kpi_prediction
  target: retail_sales_yoy
  best_feature: google_trends_yoy_lag_1
  period:
    train: 2016-01-01/2021-12-31
    test: 2022-01-01/2025-12-31
  metrics:
    correlation_train: 0.71
    correlation_test: 0.44
    directional_accuracy_train: 0.69
    directional_accuracy_test: 0.61
    mae_test: 1.2
    mape_test: 8.4
  verdict:
    survives_oos: true
    confidence: medium
```

### 7.8 `statistical-validation/`

Purpose: prevent false confidence.

Checklist:

- [ ] Check sample size.
- [ ] Check missingness.
- [ ] Check outliers.
- [ ] Check autocorrelation.
- [ ] Check stationarity.
- [ ] Check spurious trend risk.
- [ ] Check lookahead bias.
- [ ] Check survivorship bias.
- [ ] Check restatement / revision risk.
- [ ] Check multiple testing.
- [ ] Apply multiple-testing correction when needed.
- [ ] Run train / test split.
- [ ] Run walk-forward validation.
- [ ] Run regime split.
- [ ] Run lag sensitivity test.
- [ ] Run feature-family sensitivity test.
- [ ] Run robustness to transform choice.
- [ ] Run outlier sensitivity.
- [ ] Cap confidence if validation is weak.
- [ ] Produce validation report.

Validation report sections:

```md
# Validation Report

## Data Quality
## Sample Size
## Missingness
## Point-in-Time Safety
## Lookahead Risk
## Feature Search Risk
## Multiple Testing
## Out-of-Sample Survival
## Regime Robustness
## Lag Sensitivity
## Transform Sensitivity
## Final Confidence Cap
```

### 7.9 `causal-inference/`

Purpose: classify the relationship rather than overstating causality.

Relationship types:

```yaml
relationship_type:
  - causal
  - proxy
  - coincident
  - lagging
  - mechanically_linked
  - spurious
  - regime_dependent
```

Checklist:

- [ ] State whether relationship is causal, proxy, coincident, lagging, mechanical, spurious, or regime-dependent.
- [ ] Identify possible confounders.
- [ ] Identify whether predictor is upstream or downstream.
- [ ] Identify whether target could influence predictor.
- [ ] Identify whether both are driven by a third variable.
- [ ] Identify whether relationship is just trend.
- [ ] Identify whether relationship is regime-specific.
- [ ] Explain what causal evidence would be needed.
- [ ] Prevent causal language unless justified.

Example:

```md
Google Trends does not cause retail sales. It may proxy consumer demand, media intensity, or category awareness. The relationship should be treated as a proxy signal unless validated against stronger demand-side data.
```

### 7.10 `signal-synthesis/`

Purpose: turn experiment outputs into a signal card.

Checklist:

- [ ] Summarize hypothesis.
- [ ] Summarize datasets used.
- [ ] Summarize economic mapping.
- [ ] Summarize backtest results.
- [ ] Summarize current read.
- [ ] Summarize related signals.
- [ ] State confidence.
- [ ] State caveats.
- [ ] State failure modes.
- [ ] State next iteration.
- [ ] Link to datasets.
- [ ] Link to model.
- [ ] Link to experiment.
- [ ] Link to dashboard.

### 7.11 `visual-display/`

Purpose: apply Tufte-style visual discipline to quantitative outputs.

Checklist:

- [ ] Show signal vs target.
- [ ] Show lag alignment clearly.
- [ ] Show rolling correlation.
- [ ] Show feature stability.
- [ ] Show backtest performance.
- [ ] Show drawdown if tradable.
- [ ] Show confidence and caveats.
- [ ] Avoid decorative chart junk.
- [ ] Label directly where possible.
- [ ] Preserve honest scales.
- [ ] Show uncertainty.
- [ ] Show enough historical context.
- [ ] Distinguish raw data from transformed data.
- [ ] Make current read visually obvious.

### 7.12 `dashboard-builder/`

Purpose: show the state of the signal system.

Dashboard sections:

- [ ] Signal overview
- [ ] Current read
- [ ] Related signals
- [ ] Confidence
- [ ] Backtest metrics
- [ ] Feature stability
- [ ] Data quality warnings
- [ ] Caveats
- [ ] Next iteration

Dashboard schema:

```yaml
dashboard_id: retail-demand-dashboard
signals:
  - uk-retail-search-demand-signal
  - consumer-credit-retail-signal
  - card-spend-retail-signal

views:
  - current_read
  - signal_vs_target
  - rolling_correlation
  - feature_stability
  - confidence_matrix
  - contradiction_map
```

Checklist:

- [ ] Build single-signal dashboard.
- [ ] Build multi-signal dashboard.
- [ ] Show current read.
- [ ] Show whether related signals confirm or contradict.
- [ ] Show confidence matrix.
- [ ] Show data quality warnings.
- [ ] Show caveats.
- [ ] Show next iteration.
- [ ] Export dashboard as HTML.
- [ ] Save dashboard in run directory.

---

## 8. Agent Architecture

### 8.1 Canonical Agents

```text
skills/deep-quantitative-research/agents/
├── research-architect.md
├── dataset-scout.md
├── data-quality-auditor.md
├── feature-engineer.md
├── backtest-engine.md
├── causal-skeptic.md
├── findings-evaluator.md
└── dashboard-designer.md
```

- [ ] Remove duplicate root-level agent architecture.
- [ ] Move all canonical agents into skill folder.
- [ ] Rename old experimental agents.
- [ ] Update changelog with rename map.
- [ ] Ensure each agent has a clear purpose.
- [ ] Ensure agents do not duplicate skill module responsibilities.

Rename map:

```text
data-scout              → dataset-scout
data-quality            → data-quality-auditor
interpret-agent         → findings-evaluator
confidence-scorer       → findings-evaluator
skeptic-agent           → causal-skeptic
analysis-engine         → backtest-engine or statistical-validation
causal-inference        → causal-skeptic
research-architect      → keep
originality-scout       → RETIRE (decision 2026-06-09)
knowledge-base-builder  → RETIRE (decision 2026-06-09)
question-sharpener      → fold into hypothesis-formulation sub-skill
data-scout-quality      → split into dataset-scout + data-quality-auditor
report-compiler         → split into signal-synthesis + dashboard-designer
```

---

## 9. Templates

### 9.1 Required Templates

```text
templates/
├── signal-template.md
├── dataset-selection-template.md
├── dataset-contract-template.md
├── idea-template.md
├── experiment-template.md
├── model-template.md
├── dashboard-template.md
└── validation-report-template.md
```

- [ ] Add signal template.
- [ ] Add dataset-selection template.
- [ ] Add dataset-contract template.
- [ ] Add idea template.
- [ ] Add experiment template.
- [ ] Add model template.
- [ ] Add dashboard template.
- [ ] Add validation report template.
- [ ] Add insight template (from Stephanie's canon, spec lines 308 to 319).

### 9.2 Signal Template Sections

Signal card must include:

- [ ] Signal name
- [ ] Hypothesis
- [ ] Real-world variable predicted
- [ ] Economic mapping
- [ ] Data inputs
- [ ] Dataset IDs
- [ ] Fields used
- [ ] Join keys
- [ ] Cadence alignment
- [ ] Feature grid
- [ ] Backtest summary
- [ ] Current read
- [ ] Related signals
- [ ] Confidence level
- [ ] Caveats
- [ ] Failure modes
- [ ] Next iteration
- [ ] Links to dataset, model, experiment, dashboard

---

## 10. Python CLI and Scripts

### 10.1 CLI Structure

```bash
deep-quant query-datasources --query "retail sales"

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

deep-quant render-signal-card \
  --run experiments/runs/2026-06-09-uk-retail-search-demand/

deep-quant render-dashboard \
  --run experiments/runs/2026-06-09-uk-retail-search-demand/
```

Checklist:

- [ ] Implement `deep-quant` CLI.
- [ ] Add subcommands.
- [ ] Validate required arguments before execution.
- [ ] Provide clear error messages.
- [ ] Add `--help` for every command.
- [ ] Add examples to help output.
- [ ] Fail early if source-specific arguments are missing.
- [ ] Fail early if datasource registry is missing.
- [ ] Fail early if required dataset fields are unavailable.
- [ ] Add caching layer (`~/.cache/deep-quantitative-research/`).
- [ ] Add pagination handling for ClinicalTrials.gov and PubMed.
- [ ] Add rate-limit handling with exponential backoff.
- [ ] Add retries on transient HTTP errors.

Example validation:

```text
Error: --source yfinance requires --tickers.

Example:
  deep-quant fetch-data yfinance --tickers AAPL,MSFT --start 2020-01-01
```

---

## 11. Schemas

### 11.1 Required Schemas

```text
src/deep_quantitative_research/schemas/
├── hypothesis.schema.yaml
├── dataset-contract.schema.yaml
├── signal.schema.yaml
├── experiment.schema.yaml
├── feature-grid.schema.yaml
├── backtest-result.schema.yaml
├── validation-report.schema.yaml
├── signal-card.schema.yaml
└── dashboard.schema.yaml
```

- [ ] Add hypothesis schema.
- [ ] Add dataset contract schema.
- [ ] Add signal spec schema.
- [ ] Add experiment schema.
- [ ] Add feature grid schema.
- [ ] Add backtest result schema.
- [ ] Add validation report schema.
- [ ] Add signal card schema.
- [ ] Add dashboard schema.
- [ ] Validate all generated outputs against schemas.

---

## 12. Research Ledger

### 12.1 Run Directory Structure

Every run must be logged.

```text
experiments/runs/
└── 2026-06-09-uk-retail-search-demand/
    ├── run.yaml
    ├── registry-lock.yaml
    ├── signal-spec.yaml
    ├── dataset-contracts.yaml
    ├── cadence-rollup-audit.yaml
    ├── feature-grid.yaml
    ├── metrics.json
    ├── validation-report.md
    ├── signal-card.md
    └── dashboard.html
```

- [ ] Create unique run directory.
- [ ] Save run metadata.
- [ ] Save registry lock.
- [ ] Save signal spec.
- [ ] Save dataset contracts.
- [ ] Save cadence roll-up audit.
- [ ] Save feature grid.
- [ ] Save backtest metrics.
- [ ] Save validation report.
- [ ] Save signal card.
- [ ] Save dashboard.
- [ ] Save final verdict.
- [ ] Save next iteration.

Example `run.yaml`:

```yaml
run_id: 2026-06-09-uk-retail-search-demand
signal_id: uk-retail-search-demand-signal
created_at: 2026-06-09T12:00:00Z
registry_commit: 8f42c91
code_commit: 2af812e
status: completed

inputs:
  signal_spec: experiments/specs/uk-retail-search-demand-signal.yaml
  registry: ../datasources

outputs:
  signal_card: signal-card.md
  dashboard: dashboard.html
  metrics: metrics.json

verdict:
  confidence: medium
  current_read: supportive
  next_iteration: Add card-spend data and test category-level mapping.
```

---

## 13. Tests

### 13.1 Test Structure

```text
tests/
├── fixtures/
│   ├── registry_catalog_sample.yaml
│   ├── fields_sample.csv
│   ├── join_key_graph_sample.json
│   ├── prices.csv
│   ├── signal_daily.csv
│   ├── signal_monthly.csv
│   ├── kpi_quarterly.csv
│   ├── macro_monthly.csv
│   └── clinical_trials_sample.json
│
├── test_registry_client.py
├── test_dataset_selection.py
├── test_dataset_contract.py
├── test_cadence_rollup.py
├── test_feature_grid.py
├── test_timeseries_backtest.py
├── test_validation.py
├── test_signal_card.py
└── test_dashboard.py
```

- [ ] Add fixture registry.
- [ ] Add fixture datasets.
- [ ] Add unit tests for registry client.
- [ ] Add tests for dataset scoring.
- [ ] Add tests for dataset contracts.
- [ ] Add tests for cadence roll-up.
- [ ] Add tests for feature grid.
- [ ] Add tests for backtest metrics.
- [ ] Add tests for validation warnings.
- [ ] Add tests for template rendering.
- [ ] Add tests for dashboard output.
- [ ] Add py_compile check.
- [ ] Add pytest command.
- [ ] Add CI workflow.

Required commands:

```bash
python -m py_compile src/deep_quantitative_research/**/*.py
pytest
deep-quant --help
deep-quant query-datasources --healthcheck
```

Important test cases:

- [ ] Flow variables sum correctly.
- [ ] Stock variables use last value.
- [ ] Rate variables average correctly.
- [ ] Price variables are not accidentally summed.
- [ ] Release lag shifts availability date.
- [ ] Partial periods are flagged.
- [ ] Missing observations are handled according to policy.
- [ ] Feature grid records tested features.
- [ ] Best discovered feature triggers overfitting warning.
- [ ] Walk-forward split prevents leakage.
- [ ] Signal card renders without unresolved placeholders.
- [ ] Dashboard exports successfully.

---

## 14. MCP and External Connectors

### 14.1 Local-First Connectors

- [ ] Local CSV.
- [ ] Local Excel.
- [ ] Local YAML catalog.
- [ ] Local JSON catalog.
- [ ] Local DuckDB catalog.
- [ ] Local SQLite.
- [ ] Local markdown signal notes.

### 14.2 Data Warehouse / Analytics

- [ ] Snowflake
- [ ] Databricks
- [ ] BigQuery
- [ ] DuckDB
- [ ] Google Sheets
- [ ] Excel
- [ ] Jupyter
- [ ] Hex
- [ ] Looker
- [ ] Tableau
- [ ] dbt
- [ ] Dagster
- [ ] Prefect
- [ ] Airflow
- [ ] Fivetran
- [ ] Airbyte

### 14.3 Finance / Macro

- [ ] FRED
- [ ] yfinance
- [ ] SEC EDGAR
- [ ] Companies House
- [ ] Nasdaq Data Link
- [ ] Alpha Vantage
- [ ] Polygon
- [ ] OpenBB

### 14.4 Bio / Science

- [ ] PubMed
- [ ] Europe PMC
- [ ] bioRxiv
- [ ] medRxiv
- [ ] ClinicalTrials.gov
- [ ] OpenTargets
- [ ] Crossref
- [ ] Semantic Scholar
- [ ] ChEMBL
- [ ] DrugBank (if accessible)
- [ ] BioRender (if needed for figures)

---

## 15. Example MVP Workflow

### 15.1 First Demo

Build one complete demo before expanding.

Recommended first demo:

```text
Search interest / public web proxy → quarterly or monthly KPI
```

Example:

```text
Google Trends-style signal → ONS Retail Sales Index
```

Demo folder:

```text
examples/01-retail-sales-nowcast/
├── README.md
├── data/
│   ├── signal_daily.csv
│   └── kpi_quarterly.csv
├── signal-spec.yaml
├── run.sh
└── expected-output/
    ├── registry-lock.yaml
    ├── dataset-contracts.yaml
    ├── cadence-rollup-audit.yaml
    ├── feature-grid.yaml
    ├── metrics.json
    ├── validation-report.md
    ├── signal-card.md
    └── dashboard.html
```

- [ ] Create fixture dataset.
- [ ] Create fixture registry entry.
- [ ] Create signal spec.
- [ ] Run cadence roll-up.
- [ ] Run feature grid.
- [ ] Run KPI backtest.
- [ ] Produce validation report.
- [ ] Produce signal card.
- [ ] Produce dashboard.
- [ ] Add `run.sh`.
- [ ] Add expected outputs.
- [ ] Add test that demo runs end-to-end.

---

## 16. Best-Practice Rules for CLAUDE.md

Add to root `CLAUDE.md`:

```md
# Deep Quantitative Research Rules

## Data Registry

- Use the `datasources` repo as the canonical source for dataset metadata.
- Never invent dataset metadata that should come from the registry.
- Reference datasets by `dataset_id`.
- Record the datasource registry commit hash in every experiment.
- Materialize dataset contracts before feature engineering or backtesting.

## Time Series

- Respect native cadence.
- Respect release lag.
- Respect point-in-time safety.
- Never sum stock, rate, or price variables unless explicitly overridden.
- Never average flow variables unless explicitly overridden.
- Always produce a cadence roll-up audit.

## Feature Engineering

- Generate controlled feature grids.
- Record number of features tested.
- Record number of lags tested.
- Mark whether the best feature was pre-specified or discovered.
- Flag multiple-testing risk.
- Cap confidence when the best feature is discovered through a large search.

## Backtesting

- Distinguish KPI prediction from tradable signal backtesting.
- Use walk-forward validation where possible.
- Report out-of-sample degradation.
- Never call a signal high-confidence unless it survives out-of-sample.

## Reporting

- Every signal card must include hypothesis, economic mapping, data inputs, backtest summary, current read, confidence, caveats, and next iteration.
- Every run must be saved to the research ledger.
- Every dashboard must show current read, confidence, related signals, and data quality warnings.
```

- [ ] Add registry rules.
- [ ] Add time-series rules.
- [ ] Add feature engineering rules.
- [ ] Add backtesting rules.
- [ ] Add reporting rules.
- [ ] Keep root `CLAUDE.md` concise.
- [ ] Move long references into docs or skill references.

---

## 17. Migration Plan

### Phase 1, Canonicalize ✅ COMPLETED 2026-06-09

- [x] Rename to `deep-quantitative-research` (skill folder + all internal refs; repo dir rename deferred to after re-push).
- [x] Standardize skill folder path → `skills/deep-quantitative-research/`.
- [x] Standardize command name → `/deep-quantitative-research`.
- [x] Standardize Python package name → `deep_quantitative_research` (declared in pyproject.toml).
- [x] Remove duplicate / obsolete root-level architecture (originality-scout, kb-builder, question-sharpener, critique-cluster, pipeline-monitor, handoff-schemas, mode-guide).
- [x] Update README.
- [x] Update quickstart.
- [x] Update changelog.
- [x] Add CLAUDE.md with 19 hard rules.
- [x] Add pyproject.toml, .env.example, .mcp.json scaffold.
- [x] Add config/{datasources,research_defaults,scoring_weights,validation_thresholds}.yaml.
- [x] Scaffold src/deep_quantitative_research/ package skeleton (9 subpackages with __init__.py).
- [x] Scaffold experiments/{ideas,specs,runs,outputs}/ and docs/ and tests/fixtures/.
- [x] Scaffold 12 sub-skill folders with placeholder SKILL.mds.
- [x] Rename agents/causal-inference.md → agents/causal-skeptic.md.
- [x] Update CONTRIBUTING.md for the new layout.

### Phase 2, Datasources Integration

- [ ] Add `config/datasources.yaml`.
- [ ] Add registry client.
- [ ] Add registry healthcheck.
- [ ] Add dataset search command.
- [ ] Add dataset contract generation.
- [ ] Add registry lockfile.
- [ ] Generate `catalog.duckdb` in datasources repo.
- [ ] Generate `join_key_graph.json` in datasources repo.

### Phase 3, Core Research Workflow

- [ ] Add hypothesis formulation skill.
- [ ] Add dataset selection skill.
- [ ] Add dataset contract skill.
- [ ] Add cadence roll-up skill.
- [ ] Add feature engineering skill.
- [ ] Add time-series backtest skill.
- [ ] Add statistical validation skill.
- [ ] Add signal synthesis skill.

### Phase 4, Python Engine

- [ ] Move script logic into `src/`.
- [ ] Add CLI.
- [ ] Add argument validation.
- [ ] Add clear errors.
- [ ] Add schemas.
- [ ] Add output writers.

### Phase 5, Tests

- [ ] Add fixture registry.
- [ ] Add fixture datasets.
- [ ] Add unit tests.
- [ ] Add demo test.
- [ ] Add CI.

### Phase 6, Outputs

- [ ] Add signal template.
- [ ] Add dataset contract template.
- [ ] Add experiment template.
- [ ] Add validation template.
- [ ] Add dashboard template.
- [ ] Build first end-to-end demo.

### Phase 7, Advanced Research Layer

- [ ] Add multiple-testing correction.
- [ ] Add feature-family ANOVA.
- [ ] Add regime split.
- [ ] Add causal-inference checks.
- [ ] Add visual-display review.
- [ ] Add multi-signal dashboard.

---

## 18. Acceptance Criteria

The architecture is complete when:

- [ ] The repo has one canonical name.
- [ ] The skill has one canonical installable path.
- [ ] The README and SKILL.md agree.
- [ ] The root and skill folders no longer compete.
- [ ] `datasources` is referenced, not duplicated.
- [ ] Dataset IDs are used in signal specs.
- [ ] Every run records datasource registry commit.
- [ ] Dataset contracts are generated before backtests.
- [ ] Cadence roll-up handles variable types correctly.
- [ ] Feature grids are controlled and logged.
- [ ] Backtests distinguish KPI prediction from tradable signal testing.
- [ ] Validation flags overfitting, leakage, and weak PIT safety.
- [ ] Signal cards include confidence, caveats, and current read.
- [ ] Dashboards show signal state, not just charts.
- [ ] Tests run with `pytest`.
- [ ] Demo runs end-to-end.
- [ ] Outputs are reproducible from the research ledger.

---

## 19. Final Target State

The final system should feel like this:

```text
datasources gives the system a map of public data.

deep-quantitative-research turns that map into testable research.

experiments/runs records what was tried, what worked, what failed, and what the signal says now.

dashboards show the current state of the signal library.
```

Final architecture statement:

```text
Build `deep-quantitative-research` as a registry-aware signal research engine that consumes the `datasources` repo, materializes dataset contracts, runs cadence-safe and point-in-time-aware feature/backtest workflows, validates against overfitting and leakage, and emits reproducible signal cards and dashboards.
```

Final traceability requirement:

```text
Every research output must be traceable from:

claim → dataset_id → field → join_key → cadence transform → feature → backtest → validation → confidence → current read
```

---

## 20. Post-v3 extensions (out-of-scope until v3.0.0 ships)

### 20.1 Reference plugins to mine

- [ ] Anthropic `data` plugin: sql-queries, data-exploration, data-visualization, statistical-analysis, data-validation, interactive-dashboard-builder.
- [ ] Anthropic `financial-data-analyst` quickstart for chart picker logic.
- [ ] Anthropic `bio-research` plugin (`scientific-problem-selection`) already downloaded at `~/Downloads/SKILL.md`.

### 20.2 Standalone book-derived skills

- [ ] `~/Projects/applied-probability/` from Wentzel, *Applied problems in probability theory* (feeds `references/probability-foundations.md`).
- [ ] `~/Projects/visual-display/` from Tufte, *The visual display of quantitative information* (feeds `references/visual-display-principles.md` and `reporting/charts.py`). Inspect `gnurio/tufte-vdqi-plugin` and `aparente/e48c353755958621b3c0004593105a90` for prior art.

### 20.3 Bio-research plugin

- [ ] Spin out `~/Projects/bio-research/` (or sub-folder) using the canonical `scientific-problem-selection` skill plus the bio-domain MCPs from section 14.4 and the literature / journal / chemical / drug-target / clinical-trial / scientific-illustration categories.

---

## 21. Decisions log (append-only)

- 2026-06-09: Canonical name = `deep-quantitative-research`. Rename approved.
- 2026-06-09: Datasources repo exists at `~/Projects/datasources/` and on GitHub. No re-scaffold, only gap-fill (DuckDB, join-key graph).
- 2026-06-09: Retire `originality-scout` and `knowledge-base-builder`.
- 2026-06-09: Adopt 8-agent canonical set per section 8.1.
- 2026-06-09: Adopt 12 sub-skills (added `visual-display/`).
- 2026-06-09: In-place rebuild on `main`; pre-v3 state preserved at git tag `pre-v3-2026-06-09`.
- 2026-06-09: Drop critique cluster. Keep the checklist idea inside sub-skills; keep elegant validator scripts and port to `src/deep_quantitative_research/validation/`.
- 2026-06-09: Bio-research deferred to post-v3 (section 20.3).
- 2026-06-09: Phase 1 (Canonicalize) completed. Re-push to GitHub, then update external references (memory notes, `~/.claude/SKILLS.md`).

---

Last updated: 2026-06-09. Source of truth for v3 migration. Pair with `ARCHITECTURE_LOG.md`.
