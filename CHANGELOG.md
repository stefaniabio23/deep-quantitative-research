# Changelog

All notable changes to deep-quant-research are documented here.

Format: [version] — date — summary

---

## [1.0.0] — 2026-05-08

Initial release — includes blind critique cluster.

### Skill
- `deep-quant-research` orchestrator with 5 modes: full, quick, thesis-test, data-first, literature
- Research type auto-detection: biotech, finance, quant, mixed
- Iterative confidence-scored loop with up to 3 refinement cycles

### Agent team (12 agents)
- `findings-evaluator` — blind critique cluster reconciliation with PASS/REVISE/FAIL gates and human_review escalation

### Agent team (13 agents)
- `question-sharpener` — hypothesis formulation with success criteria
- `research-architect` — study design per research type
- `data-scout` — data discovery and fetching across 8+ sources
- `data-quality` — four-bias audit protocol
- `statistical-analyst` — correlation, regression, PCA, event study, Granger causality
- `timeseries-analyst` — stationarity, lag analysis, decomposition, DC, cointegration
- `backtest-engine` — walk-forward backtesting with transaction costs
- `causal-inference` — Granger, DiD, confound detection
- `interpret-agent` — domain-contextualised findings
- `confidence-scorer` — 1-10 scoring with loop/proceed decision
- `skeptic-agent` — adversarial review and alternative explanations
- `report-compiler` — multi-template output with writing quality check

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
