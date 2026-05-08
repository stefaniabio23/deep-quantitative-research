---
name: deep-quant-research
description: "Structured multi-agent quantitative research pipeline. 10 core agents + adversarial critique cluster + pipeline monitor. Turns a vague research question into a rigorous finding — or an honest null result. Domains: biotech (clinical trials, drug pipelines, target analysis), finance (equity, factors, KPIs), quant (macro, time series, dependence structures). Modes: quick, full, thesis-test, data-first, literature, thorough."
license: MIT
compatibility: "Claude Code with Python 3.10+. Requires: pandas, numpy, scipy, statsmodels, yfinance, requests, pyyaml, matplotlib. Run pip install -r requirements.txt."
allowed-tools: "Bash(python:*) WebSearch WebFetch Read Write Task"
metadata:
  version: "2.0.0"
  category: quantitative-research
  tags: [finance, biotech, quant, research, backtesting, time-series, causal-inference]
---

# deep-quant-research

A structured multi-agent research pipeline. Rigour over speed. Honest null results over forced conclusions.

---

## Invocation

```
/deep-quant-research "<question>" [--mode <mode>]
```

Default mode: `full`

---

## Modes and critique policy

```yaml
modes:
  quick:
    agents: [question-sharpener, research-architect, data-scout-quality, analysis-engine, findings-evaluator, report-compiler]
    run_critique_cluster: false
    use_case: Fast scoping, sanity check

  full:
    agents: all
    run_critique_cluster: true
    require_all_critics: false
    allow_revision_loop: false
    use_case: Standard research question

  thesis-test:
    agents: all
    run_critique_cluster: true
    require_all_critics: true
    allow_revision_loop: false
    use_case: Stress-testing an investment or research thesis

  data-first:
    agents: [question-sharpener, data-scout-quality, knowledge-base-builder, research-architect, analysis-engine, backtest-engine, causal-inference, findings-evaluator, report-compiler]
    run_critique_cluster: true
    require_all_critics: false
    use_case: You have data, find the story

  literature:
    agents: [question-sharpener, originality-scout, knowledge-base-builder, research-architect, findings-evaluator, report-compiler]
    run_critique_cluster: true
    require_all_critics: false
    use_case: Prior work synthesis, gap analysis

  thorough:
    agents: all
    run_critique_cluster: true
    require_all_critics: true
    allow_revision_loop: true
    max_revision_rounds: 2
    use_case: Publication-quality, high-stakes decision
```

---

## Pipeline

```
[1]  question-sharpener       Vague idea → testable hypothesis with explicit success criteria
[2]  originality-scout        Prior work → novelty assessment → differentiation angle
[3]  knowledge-base-builder   Reusable topic entry: consensus, disputes, datasets, open questions
[4]  research-architect       Study design: method choice, evidence threshold, falsification criteria
[5]  data-scout-quality       Find data + immediately audit for the four critical biases

[6]  analysis-engine          Descriptive stats, correlations, regressions, time-series
[7]  backtest-engine          Walk-forward validation, benchmark, transaction costs (skip in quick/literature)
[8]  causal-inference         Confounders, Granger candidates, DiD/IV feasibility (skip in quick/literature)

     ── if run_critique_cluster: true ──────────────────────────────
     [9a] methods-critic  ┐
     [9b] data-critic     ├── parallel, independent, adversarial
     [9c] logic-critic    ┘
     ── outputs fed into findings-evaluator ────────────────────────

[10] findings-evaluator       Interpret + score + challenge. Reconciles critique outputs.
[11] report-compiler          Final report with charts, reproducibility notes, next questions.
```

Each phase is validated by the pipeline monitor (`scripts/validate_output.py`) before passing downstream. See `shared/pipeline-monitor.md`.

---

## Agent team

| # | Agent | Role |
|---|-------|------|
| 1 | question-sharpener | Testable hypothesis, success criteria, scope |
| 2 | originality-scout | Prior work, novelty level, differentiation angle |
| 3 | knowledge-base-builder | Durable topic entry: consensus, disputes, open questions |
| 4 | research-architect | Study design, method choice, falsification criteria |
| 5 | data-scout-quality | Data discovery + immediate quality audit |
| 6 | analysis-engine | Stats, correlations, regressions, time-series |
| 7 | backtest-engine | Walk-forward validation |
| 8 | causal-inference | Causality, confounders, Granger |
| 9 | [critique cluster] | methods-critic, data-critic, logic-critic — parallel, adversarial |
| 10 | findings-evaluator | Interpret + score + adversarial challenge |
| 11 | report-compiler | Final report |

The critique cluster is not counted as core agents. It is a parallel adversarial review phase. See `shared/critique-cluster.md`.

---

## Shared protocols

| File | Purpose |
|------|---------|
| `shared/critique-cluster.md` | Critique phase: three parallel adversarial critics |
| `shared/pipeline-monitor.md` | Validation, retry, degraded-output handling |
| `shared/handoff-schemas.md` | Input/output contracts between agents |
| `shared/statistical-standards.md` | Required statistical practices |
| `shared/data-quality-protocol.md` | Four bias checks: look-ahead, survivorship, snooping, selection |
| `shared/interpretation-rubric.md` | Domain benchmarks for scoring findings |
| `shared/chart-style-guide.md` | Visual standards (use scripts/chart_theme.py) |
| `shared/output-style-guide.md` | Writing standards for reports |

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/validate_output.py` | Pipeline monitor validation |
| `scripts/chart_theme.py` | Shared matplotlib theme |
| `scripts/fetch_data.py` | Data fetching: yfinance, FRED, ClinicalTrials, PubMed, OpenTargets |
| `scripts/statistical_analysis.py` | Regression, correlation, effect sizes |
| `scripts/timeseries.py` | Stationarity, decomposition, lag analysis |
| `scripts/backtest.py` | Walk-forward backtesting framework |

---

## Output structure

```
[topic_slug]/
├── pipeline_status.yaml          # pipeline monitor state
├── research_brief.yaml
├── originality_assessment.yaml
├── knowledge_base/
│   └── [topic_slug].yaml
├── data/
│   ├── data_package.yaml
│   ├── data_quality.yaml
│   └── [raw data files]
├── analysis/
│   ├── statistical.yaml
│   ├── timeseries.yaml
│   └── backtest.yaml
├── critique/
│   ├── methods.yaml
│   ├── data.yaml
│   └── logic.yaml
├── synthesis/
│   └── evaluation.yaml
└── report.md
```

---

## Principles

- A null result documented honestly is a finding. Report it.
- Do not skip the data quality audit. One look-ahead bias failure invalidates everything downstream.
- The critique cluster is adversarial by design. A finding that survives it is stronger.
- After 3 refinement iterations without a score ≥ 6, terminate with a null result. Do not force a conclusion.
