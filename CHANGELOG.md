# Changelog

All notable changes to deep-quant-research are documented here.

Format: [version], date, summary

---

## [2.0.0], 2026-06-08

Repo canonicalisation and agent consolidation. The installable skill is now self-contained inside `skills/deep-quant-research/`; the duplicated root-level `agents/`, `shared/`, and `scripts/` trees have been removed. Pre-cleanup state preserved at git tag `pre-cleanup-2026-06-08`.

### Agent team (10 named agents + critique cluster)
- `question-sharpener`, `originality-scout`, `knowledge-base-builder`, `research-architect`, `data-scout-quality`, `analysis-engine`, `backtest-engine`, `causal-inference`, `findings-evaluator`, `report-compiler`
- Critique cluster: `methods-critic`, `data-critic`, `logic-critic` defined by checklists in `shared/critique-checklists/`, orchestrated by `shared/critique-cluster.md`

### Migration from 1.0
- `data-scout` + `data-quality` consolidated into `data-scout-quality` (fetch and audit in one agent so look-ahead bias is caught before analysis)
- `statistical-analyst` + `timeseries-analyst` consolidated into `analysis-engine`
- `interpret-agent` + `confidence-scorer` + `skeptic-agent` folded into `findings-evaluator` with PASS/REVISE/FAIL gates
- Added `originality-scout` (prior-work survey, novelty score)
- Added `knowledge-base-builder` (durable topic entry: consensus, disputes, datasets, open questions)
- Critique-cluster checklists moved into the skill folder so install is one `cp -r`

### Scripts
- Added `chart_theme.py` (shared matplotlib theme) and `validate_output.py` (pipeline-monitor validation)

---

## [1.0.0], 2026-05-08

Initial release. Includes blind critique cluster.

### Skill
- `deep-quant-research` orchestrator with 5 modes: full, quick, thesis-test, data-first, literature
- Research type auto-detection: biotech, finance, quant, mixed
- Iterative confidence-scored loop with up to 3 refinement cycles

### Agent team (13 agents)
- `question-sharpener`, `research-architect`, `data-scout`, `data-quality`, `statistical-analyst`, `timeseries-analyst`, `backtest-engine`, `causal-inference`, `interpret-agent`, `confidence-scorer`, `skeptic-agent`, `findings-evaluator`, `report-compiler`

### Blind critique cluster
- `critique-cluster.md` — protocol: isolated critics, PASS/REVISE/FAIL schema, retry policy, escalation rules
- `critique-checklists/methods-checklist.md` — 19 items across test appropriateness, validation, estimation, backtest, stationarity
- `critique-checklists/data-checklist.md` — 14 items across provenance, look-ahead, survivorship, completeness
- `critique-checklists/logic-checklist.md` — 16 items across hypothesis alignment, causal language, scope, data snooping
- `critique-checklists/interpretation-checklist.md` — 14 items across domain calibration, hedging, scope, skeptic quality
- `critique-checklists/report-checklist.md` — 19 items across structure, faithfulness, AI filler, writing quality
- `pipeline-monitor.md` — session state tracker; triggers critique at Phases 3, 4, 6

### Shared protocols
- `statistical-standards.md` — evidence hierarchy and analysis standards
- `data-quality-protocol.md` — four-bias protocol with verdicts
- `interpretation-rubric.md` — domain-specific benchmarks
- `output-style-guide.md` — writing standards and anti-AI checklist
- `handoff-schemas.md` — agent-to-agent data contracts

### Python scripts
- `fetch_data.py` — yfinance, FRED, Fama-French, ClinicalTrials.gov, PubMed, OpenTargets, openFDA
- `statistical_analysis.py` — correlation (Pearson, Spearman, DC), regression, PCA, event study, Granger
- `timeseries.py` — stationarity (ADF, KPSS), lag analysis, STL decomposition, rolling DC, cointegration
- `backtest.py` — walk-forward backtesting, transaction costs, drawdown, benchmark comparison
- `data_quality.py` — outlier detection, missing data audit
