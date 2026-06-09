# Architecture Log

Side-by-side log of what exists today (OG, v2.0.0) and what the new spec calls for. Sourced from:

- Current repo: `~/Projects/deep-quant-research/` (v2.0.0, 2026-06-08, git tag `pre-cleanup-2026-06-08`)
- Spec paste: `~/.claude/paste-cache/97c154776dd37555.txt` (1309 lines, pasted 2026-06-09 02:00)
- Memory: `[[project-ef-application]]`, `[[deep-quant-research]]` compounds note

Companion file: `BUILD_CHECKLIST.md` (the tickable plan).

---

## 0. Headline change in one sentence

Turn a single-skill multi-agent pipeline into a **registry-aware signal research engine** that consumes a separate `datasources` repo, materialises dataset contracts, runs controlled feature and backtest workflows, and emits reproducible signal cards and dashboards.

---

## 1. Naming and identity

Decided 2026-06-09.

| | OG (v2.0.0) | Target |
|---|---|---|
| Repo name | `deep-quant-research` | `deep-quantitative-research` |
| Top-level skill | `skills/deep-quant-research/` | `skills/deep-quantitative-research/` |
| Primary command | `/deep-quant-research` | `/deep-quantitative-research` plus per-stage commands |
| Python package | (none, loose scripts) | `deep_quantitative_research` |
| CLI command | (none) | `deep-quant` |
| Sibling repo | none | `~/Projects/datasources/` (exists, also on GitHub) |

---

## 2. Top-level repo layout

### OG (what is on disk now)

```
~/Projects/deep-quant-research/
├── README.md                        8.7K
├── QUICKSTART.md                    2.0K
├── CHANGELOG.md                     3.9K
├── CONTRIBUTING.md                  3.4K
├── LICENSE                          1.1K
├── requirements.txt                 0.7K
├── .gitignore
├── .github/
│   ├── workflows/validate-skill.yml
│   └── scripts/validate_skill.py
├── .claude/settings.json
├── examples/                        (3 subdirs, contents not enumerated in log)
├── tests/                           markdown only, NOT executable pytest
│   ├── functional-tests.md
│   └── trigger-tests.md
└── skills/
    └── deep-quant-research/
        ├── SKILL.md
        ├── agents/                  10 .md files
        │   ├── question-sharpener.md
        │   ├── originality-scout.md
        │   ├── knowledge-base-builder.md
        │   ├── research-architect.md
        │   ├── data-scout-quality.md
        │   ├── analysis-engine.md
        │   ├── backtest-engine.md
        │   ├── causal-inference.md
        │   ├── findings-evaluator.md
        │   └── report-compiler.md
        ├── shared/                  8 protocol files
        │   ├── critique-cluster.md
        │   ├── pipeline-monitor.md
        │   ├── statistical-standards.md
        │   ├── data-quality-protocol.md
        │   ├── interpretation-rubric.md
        │   ├── output-style-guide.md
        │   ├── chart-style-guide.md
        │   └── handoff-schemas.md
        ├── scripts/                 7 Python utilities
        │   ├── fetch_data.py
        │   ├── statistical_analysis.py
        │   ├── timeseries.py
        │   ├── backtest.py
        │   ├── data_quality.py
        │   ├── chart_theme.py
        │   └── validate_output.py
        └── references/
            ├── data-sources.md
            ├── mode-guide.md
            └── troubleshooting.md
```

Caveats: README mentions `shared/critique-checklists/` for the three critic checklists, but that directory was not in the file scan; either nested under `shared/` differently or missing. **Verify before refactor.**

### Target (per spec lines 511 to 687)

Two separate repos.

```
datasources/                         ← NEW REPO, canonical public-data ontology
├── README.md
├── SCHEMA.md
├── schema/
│   ├── source.schema.yaml
│   ├── dataset.schema.yaml
│   ├── field-schema.schema.yaml
│   └── entry.schema.yaml
├── entries/
│   ├── economics/
│   ├── finance/
│   ├── healthcare/
│   ├── clinical-trials/
│   ├── web/
│   ├── geospatial/
│   └── alternative-data/
├── join_keys/
│   ├── join_keys.yaml
│   ├── entity_types.yaml
│   └── join_key_compatibility.yaml
├── generated/                       ← machine index consumed by quant repo
│   ├── catalog.csv
│   ├── catalog.json
│   ├── catalog.duckdb               ← preferred consumer format
│   ├── fields.csv
│   ├── join_key_graph.json
│   └── source_quality_scores.csv
├── scripts/
│   ├── validate_catalog.py
│   ├── generate_catalog.py
│   ├── build_join_key_graph.py
│   └── export_duckdb.py
└── tests/
    ├── test_schema_validation.py
    ├── test_join_keys.py
    └── test_generated_catalog.py
```

```
deep-quant-research/                 ← THIS REPO, research execution engine
├── README.md
├── CLAUDE.md                        ← NEW, hard rules per spec section 17
├── pyproject.toml                   ← NEW, pinned deps
├── requirements.txt
├── .env.example                     ← NEW
│
├── config/                          ← NEW
│   ├── datasources.yaml
│   ├── research_defaults.yaml
│   └── scoring_weights.yaml
│
├── skills/
│   └── deep-quantitative-research/  ← renamed
│       ├── SKILL.md
│       ├── commands/                ← NEW, per-stage slash commands
│       │   ├── deep-quant-research.md
│       │   ├── formulate-hypothesis.md
│       │   ├── find-datasets.md
│       │   ├── design-signal.md
│       │   ├── backtest-signal.md
│       │   ├── validate-signal.md
│       │   └── build-dashboard.md
│       │
│       ├── skills/                  ← NEW, eleven sub-skills replace agents/
│       │   ├── hypothesis-formulation/
│       │   ├── datasource-query/
│       │   ├── dataset-selection/
│       │   ├── dataset-contract/
│       │   ├── cadence-roll-up/
│       │   ├── feature-engineering/
│       │   ├── time-series-backtest/
│       │   ├── statistical-validation/
│       │   ├── causal-inference/
│       │   ├── signal-synthesis/
│       │   └── dashboard-builder/
│       │
│       ├── templates/               ← NEW
│       │   ├── signal-template.md
│       │   ├── dataset-selection-template.md
│       │   ├── experiment-template.md
│       │   ├── model-template.md
│       │   ├── dashboard-template.md
│       │   └── validation-template.md
│       │
│       ├── references/
│       │   ├── datasource-registry-interface.md
│       │   ├── cadence-roll-up.md
│       │   ├── feature-engineering-guardrails.md
│       │   ├── backtesting-pitfalls.md
│       │   ├── statistical-validation.md
│       │   └── visual-display-principles.md
│       │
│       └── examples/
│           ├── retail-sales-nowcast/
│           ├── clinical-trials-biotech-signal/
│           └── macro-equity-signal/
│
├── src/
│   └── deep_quant_research/         ← NEW, real Python package
│       ├── registry/
│       │   ├── client.py
│       │   ├── index.py
│       │   ├── search.py
│       │   ├── join_graph.py
│       │   └── contracts.py
│       ├── research/
│       │   ├── hypothesis.py
│       │   ├── dataset_selection.py
│       │   ├── signal_spec.py
│       │   └── experiment_spec.py
│       ├── timeseries/
│       │   ├── cadence.py
│       │   ├── alignment.py
│       │   ├── release_lags.py
│       │   └── transformations.py
│       ├── features/
│       │   ├── grid.py
│       │   ├── transforms.py
│       │   ├── selection.py
│       │   └── overfitting.py
│       ├── backtest/
│       │   ├── kpi_backtest.py
│       │   ├── trading_backtest.py
│       │   ├── walk_forward.py
│       │   └── metrics.py
│       ├── validation/
│       │   ├── data_quality.py
│       │   ├── statistical_tests.py
│       │   ├── multiple_testing.py
│       │   ├── robustness.py
│       │   └── causal_checks.py
│       ├── reporting/
│       │   ├── signal_card.py
│       │   ├── dashboard.py
│       │   ├── charts.py
│       │   └── markdown.py
│       └── schemas/
│           ├── signal.schema.yaml
│           ├── experiment.schema.yaml
│           ├── feature-grid.schema.yaml
│           ├── backtest-result.schema.yaml
│           └── signal-card.schema.yaml
│
├── experiments/                     ← NEW, research ledger
│   ├── ideas/
│   ├── specs/
│   ├── runs/                        ← one folder per run, with registry-lock.yaml
│   └── outputs/
│
├── examples/
│   ├── 01-retail-sales-nowcast/
│   ├── 02-clinical-trials-signal/
│   └── 03-macro-regime-signal/
│
└── tests/                           ← NEW, real pytest suite
    ├── fixtures/
    │   ├── prices.csv
    │   ├── signal.csv
    │   └── clinical_trials_sample.json
    ├── test_registry_client.py
    ├── test_dataset_selection.py
    ├── test_cadence_rollup.py
    ├── test_feature_grid.py
    ├── test_backtest.py
    └── test_signal_card.py
```

---

## 3. Mental model layers (per spec section 14)

```
Layer 1  Registry       What data exists?         datasources repo
Layer 2  Semantics      What does it mean?        shared by both
Layer 3  Experiment     What relationship?         deep-quant
Layer 4  Research output What do we believe?       deep-quant
```

Compact form: `Data Registry → Signal Factory → Research Ledger → Dashboard`.

---

## 4. Pipeline / workflow

### OG pipeline (linear, 11 phases, agent-per-phase)

```
question-sharpener → originality-scout → knowledge-base-builder
→ research-architect → data-scout-quality → analysis-engine
→ backtest-engine → causal-inference
→ [critique cluster: methods, data, logic, parallel]
→ findings-evaluator → report-compiler
```

Mode-gated (quick / full / thesis-test / data-first / literature / thorough). 3-iteration confidence loop, score ≥ 6 to pass.

### Target workflow (spec section 10)

```
Hypothesis → Dataset Search → Dataset Contract → Feature Grid
→ Backtest → Validation → Signal Card → Dashboard
```

Each step is its own sub-skill and slash command:

```
/formulate-hypothesis  → writes experiments/ideas/<slug>.yaml
/find-datasets         → reads registry, writes dataset-candidates.yaml
/design-signal         → writes experiments/specs/<signal-id>.yaml (SignalSpec)
/backtest-signal       → runs full feature-grid backtest
/validate-signal       → applies the statistical-validation gate
/build-dashboard       → emits dashboard.html
/deep-quant-research   → wraps the whole chain end-to-end
```

The critique cluster and findings-evaluator are NOT explicitly retired in the spec. **Decision needed:** keep them as an adversarial overlay on the new pipeline, or replace with the new validation/causal sub-skills. Recommendation: keep critique cluster, since its blind-review pattern is independent of the registry refactor.

---

## 5. Agent / skill mapping (gap matrix)

Decisions: originality-scout and knowledge-base-builder retired (2026-06-09). Canonical agent set is the 8 from spec section 7. Twelve sub-skills (added `visual-display/`).

| OG agent | Target | Action |
|---|---|---|
| question-sharpener | folded into `hypothesis-formulation` sub-skill | **retire as agent** |
| originality-scout | none | **retire** |
| knowledge-base-builder | none | **retire** |
| research-architect | `research-architect` agent (kept) | **keep** |
| data-scout-quality | split: `dataset-scout` agent + `data-quality-auditor` agent | **split** |
| analysis-engine | `backtest-engine` agent + `statistical-validation` sub-skill | **split** |
| backtest-engine | `backtest-engine` agent | **keep, scope to trading mode** |
| causal-inference | `causal-skeptic` agent + `causal-inference` sub-skill | **rename + extract** |
| findings-evaluator | `findings-evaluator` agent (kept) | **keep** |
| report-compiler | `signal-synthesis` sub-skill + `dashboard-designer` agent | **split** |
| methods-critic checklist | TBD (Phase 0 decision pending) | conditional |
| data-critic checklist | TBD (Phase 0 decision pending) | conditional |
| logic-critic checklist | TBD (Phase 0 decision pending) | conditional |
| (new) | `feature-engineer` agent | **new** |
| (new) | `cadence-roll-up/` sub-skill | **new** |
| (new) | `feature-engineering/` sub-skill | **new** |
| (new) | `visual-display/` sub-skill | **new (12th)** |
| (new) | `dashboard-builder/` sub-skill + `dashboard-designer` agent | **new** |

---

## 6. New artefacts and schemas

| Artefact | Where it lives | Purpose |
|---|---|---|
| `SignalSpec` YAML | `experiments/specs/<signal-id>.yaml` | Connects hypothesis, datasets, features, model. Spec sections 9 and 357 to 408. |
| `dataset_contract` YAML | materialised per run | Bridges registry metadata and execution. Records release lag, PIT safety, cadence target, known limits. |
| `registry-lock.yaml` | `experiments/runs/<run>/` | Records datasources commit hash and catalog version per run. Reproducibility. |
| `run.yaml` | `experiments/runs/<run>/` | Run ledger: inputs, outputs, verdict, confidence, next iteration. |
| `feature-grid.csv` | `experiments/runs/<run>/` | Controlled grid output. Counts features and lags tested. |
| `signal-card.md` | `experiments/runs/<run>/` | The Stephanie-canon template (hypothesis, economic mapping, backtest, current read, failure modes, confidence, next iteration, links). |
| `dashboard.html` | `experiments/runs/<run>/` | State-of-signals view; aggregates supportive / neutral / contradictory across a family. |

Vocabularies (closed enums, spec lines 66 to 69, 109 to 117):

- `variable_type` ∈ {flow, stock, rate, price, count, sentiment, event}
- `default_aggregation` ∈ {sum, mean, last, max, min, median}
- `relationship_type` ∈ {causal, proxy, coincident, lagging, mechanically-linked, spurious, regime-dependent}

---

## 7. Hard rules to encode (spec section 17)

To be written into `CLAUDE.md` and surfaced in `SKILL.md`:

1. Never invent dataset metadata if it should come from `datasources`.
2. Always reference datasets by `dataset_id`.
3. Always record `datasources` repo commit hash per run.
4. Always materialise a dataset contract before backtesting.
5. Always respect native cadence, `variable_type`, `default_aggregation`, `release_lag_days`.
6. Never sum stock / rate / price variables unless explicitly overridden.
7. Always log number of features and lags tested.
8. Always mark whether the winning feature was pre-specified or discovered.
9. Always produce caveats and failure modes.
10. Never call a signal high-confidence unless it survives out-of-sample validation.

---

## 8. Scripts hardening (spec lines 1247 to 1267)

Move from MVP utilities to a tested package:

- Add CLI arg validation (e.g. `--source yfinance` requires `--tickers`, fail fast with clear message).
- Restructure CLI: `fetch-data yfinance --tickers AAPL,MSFT --start 2020-01-01` style sub-commands.
- Pin dependency versions in `pyproject.toml`.
- Add fixture data under `tests/fixtures/` (small CSV / JSON samples).
- Add caching, API pagination, rate-limit handling, retries with backoff.
- Replace markdown `tests/*.md` with executable pytest suite + smoke compile (`python -m py_compile`).
- Add a working end-to-end demo run committed to the repo.

---

## 9. References and external skills to fold in

| Source | What | Status |
|---|---|---|
| Anthropic data plugin | sql-queries, data-exploration, data-visualization, statistical-analysis, data-validation, interactive-dashboard-builder | Reference, mine for patterns |
| Anthropic financial-data-analyst quickstart | Chart picker, viz code patterns | Reference |
| Anthropic bio-research plugin | scientific-problem-selection skill | Already downloaded at `~/Downloads/SKILL.md` — out-of-scope for this migration, separate plugin |
| Wentzel, *Applied problems in probability theory* | Probability skill (statistical-validation reference) | Future skill |
| Tufte, *Visual display of quantitative information* | `visual-display-principles.md` reference + chart-style-guide refresh | Reference examples: `gnurio/tufte-vdqi-plugin`, `aparente/e48c353755958621b3c0004593105a90` |
| MCPs to consider | Snowflake / Databricks / BigQuery, Looker / Tableau, Jupyter / Hex, Google Sheets, Airflow / dbt / Dagster, Fivetran / Airbyte / Stitch | Optional Phase 15 |
| Bio-research MCPs | PubMed, bioRxiv / medRxiv, Consensus, Wiley, Sage Bionetworks, deepsense chemical DB, OpenTargets, ClinicalTrials.gov, BioRender, Owkin, Benchling | Out-of-scope for quant, but list for bio-research plugin spinoff |

---

## 10. Open decisions

Resolved 2026-06-09:

1. ✅ Final repo name = `deep-quantitative-research`.
2. ✅ Retire `originality-scout` and `knowledge-base-builder`.
3. ✅ `datasources` repo already exists at `~/Projects/datasources/` and on GitHub. Schemas, 10 domain folders, generated CSV/JSON catalog, and `add-dataset-entry` skill all in place. Gaps: `catalog.duckdb`, `join_key_graph.json`.

Still open:

4. **Branch strategy for v3.** Migrate `main` in-place, or work on `v3-registry-aware` and merge at v3.0.0 tag?
5. **Critique cluster fate.** Keep methods/data/logic critics as an adversarial overlay on the new pipeline, or trust `statistical-validation` + `causal-skeptic` alone? If kept, decide trigger points (after backtest? after synthesis?).
6. **`shared/critique-checklists/` directory.** Referenced in old README but not in the file scan. Find it or recreate before any agent refactor.
7. **Bio-research plugin.** Spin out as separate repo (`~/Projects/bio-research/`) or stay inside deep-quant. Currently parked under section 20.3 of `BUILD_CHECKLIST.md` as post-v3 work.

---

## 11. Source links

- Spec: `~/.claude/paste-cache/97c154776dd37555.txt`
- Compound note: `~/Desktop/second-brain/compounds/deep-quant-research.md`
- Project ref: `~/Desktop/Second Brain/work/deep-quant-research.md`
- Memory: `[[project-ef-application]]` (relevant: building public projects to show edge)
- Pre-cleanup git tag: `pre-cleanup-2026-06-08`
- Old SKILL.md to compare against: `skills/deep-quant-research/SKILL.md`

Last updated: 2026-06-09.
