# deep-research

A structured, iterative quantitative research skill for Claude Code. Runs an 11-agent pipeline plus a three-critic adversarial cluster across finance, biotech, and quant domains, with a confidence-scored loop that refines hypotheses until the evidence is strong enough to report or returns an honest null.

---

## What it does

Give it a research question. It formulates a testable hypothesis, finds and validates data, runs statistical analysis, sends the result through three blind adversarial critics (methods, data, logic), reconciles their verdicts, and produces a research report. Every phase carries explicit confidence scoring and falsification criteria.

If the evidence is weak, it surfaces why and refines the hypothesis. If after three iterations there is still no reliable signal, it reports that as a null result.

**Research types supported:**
- **Finance:** KPI-to-price analysis, factor decomposition, backtesting, lag analysis, earnings quality, event studies
- **Biotech:** Clinical trial signal extraction, drug pipeline analysis, genomic data interpretation, literature synthesis
- **Quantitative signals explored:** Factor models, macro relationships, dependence structures (including distance correlation), regime analysis

---

## The research loop

```
Question
  → Hypothesis formulation (testable, with falsification criteria)
  → Originality check + knowledge-base entry
  → Study design (method choice, evidence threshold)
  → Data discovery + immediate quality audit (4-bias check)
  → Analysis: stats, time-series, optional backtest + causal
  → Critique cluster (methods + data + logic critics, parallel, blind)
  → Findings reconciliation, interpretation, scoring (1-10)
       ↓ FAIL: revise affected phase, max 3 loops
       ↓ score < 6: refine hypothesis, max 3 iterations
       ↓ score ≥ 6: pass to report
  → Final report with writing quality check
```

---

## Install

```bash
# 1. Copy skill to Claude Code skills directory
cp -r skills/deep-research ~/.claude/commands/

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Optional: FRED API key for macro data
export FRED_API_KEY=your_key_here
```

See [QUICKSTART.md](QUICKSTART.md) for the 5-minute guide.

---

## Usage

```
/deep-research "<your question>" [--mode <mode>]
```

Modes:

| Mode | Use case |
|------|----------|
| `full` (default) | Standard research question, full pipeline, critique cluster on |
| `quick` | Fast scoping, sanity check, no backtest or causal |
| `thesis-test` | Stress-test an investment or research thesis, all critics required |
| `data-first` | You have data, find the story |
| `literature` | Prior work synthesis, gap analysis, no analysis-engine |
| `thorough` | Publication-quality, all critics required, up to 2 revision rounds |


---

## Structure

The installable skill is self-contained inside `skills/deep-research/`. Copy that one folder to `~/.claude/commands/` to install.

```
skills/deep-research/    ← the installable skill
  SKILL.md                     ← orchestrator: modes, pipeline, routing
  agents/                      ← 10 core agents + findings-evaluator
    question-sharpener.md
    originality-scout.md
    knowledge-base-builder.md
    research-architect.md
    data-scout-quality.md
    analysis-engine.md
    backtest-engine.md
    causal-inference.md
    findings-evaluator.md
    report-compiler.md
  shared/                      ← protocols referenced by all agents
    critique-cluster.md        ← blind critique protocol (methods + data + logic critics)
    pipeline-monitor.md        ← session state, abort conditions, revision tracking
    statistical-standards.md   ← evidence hierarchy, test requirements, confidence rubric
    data-quality-protocol.md   ← four-bias audit: look-ahead, survivorship, snooping, selection
    interpretation-rubric.md   ← domain benchmarks for finance, biotech, quant
    output-style-guide.md      ← writing standards and anti-AI checklist
    chart-style-guide.md       ← chart conventions and diagnostic charts
    handoff-schemas.md         ← data contracts between agents
  scripts/                     ← Python utilities
    fetch_data.py              ← yfinance, FRED, Fama-French, ClinicalTrials.gov, PubMed, OpenTargets, openFDA
    statistical_analysis.py    ← correlation, regression (Newey-West), PCA, event study, Granger
    timeseries.py              ← ADF/KPSS, lag analysis, STL decomposition, distance correlation, cointegration
    backtest.py                ← walk-forward backtesting with transaction costs and drawdown
    data_quality.py            ← outlier detection, missing data audit
    chart_theme.py             ← shared matplotlib theme
    validate_output.py         ← pipeline-monitor validation
  references/                  ← background docs
    data-sources.md            ← all APIs and their limitations
    mode-guide.md              ← when to use each mode
    troubleshooting.md         ← common failure modes
```

The critique cluster's three critics (methods, data, logic) are defined by their checklists in `shared/critique-checklists/` rather than as separate agent files; the cluster protocol in `shared/critique-cluster.md` orchestrates them. That is why the agent table below shows 10 named agents plus the cluster.

---

## The agent team

| # | Agent | Role |
|---|-------|------|
| 1 | `question-sharpener` | Converts vague questions into testable hypotheses with explicit falsification criteria |
| 2 | `originality-scout` | Maps prior work, scores novelty, identifies the differentiation angle |
| 3 | `knowledge-base-builder` | Builds a durable topic entry: consensus, disputes, datasets, open questions |
| 4 | `research-architect` | Designs the study: method choice, evidence threshold, validation approach |
| 5 | `data-scout-quality` | Fetches data from 8+ free APIs and immediately runs the four-bias audit |
| 6 | `analysis-engine` | Correlations (Pearson, Spearman, distance), regression, PCA, event study, time-series |
| 7 | `backtest-engine` | Walk-forward backtesting with transaction costs, drawdown, benchmark comparison |
| 8 | `causal-inference` | Granger causality, difference-in-differences, confound detection |
| 9 | **critique cluster** | `methods-critic` + `data-critic` + `logic-critic`. Parallel, blind, adversarial. |
| 10 | `findings-evaluator` | Reconciles critic verdicts; routes to revision, proceed, or human review |
| 11 | `report-compiler` | Final output with style guide and anti-AI writing check |

The critique cluster runs at three points in the pipeline (after analysis, after synthesis, after the report draft). Each critic sees only the work it is reviewing plus its checklist, never the other critics' verdicts or the producing agent's reasoning. That isolation is the point: it forces independent challenges from three angles and surfaces failure modes that a single reviewer would miss.

---

## Data sources (all free)

| Source | Domain | Access |
|--------|--------|--------|
| yfinance | Equity prices, global | `scripts/fetch_data.py` |
| FRED | Macro (800k+ series) | `scripts/fetch_data.py` (free API key) |
| Fama-French | Factor returns 1926+ | `scripts/fetch_data.py` |
| ClinicalTrials.gov | Clinical trials registry | `scripts/fetch_data.py` |
| PubMed / NCBI | Biomedical literature | `scripts/fetch_data.py` |
| OpenTargets | Gene-disease associations | `scripts/fetch_data.py` |
| openFDA | Drug approvals, adverse events | `scripts/fetch_data.py` |
| WebSearch + WebFetch | General web, filings, reports | Built-in Claude tools |

---

## Extending the system

**Add a new agent:** Create a file in `skills/deep-research/agents/` following the template in [CONTRIBUTING.md](CONTRIBUTING.md). Reference it from the relevant mode block in `SKILL.md`.

**Add a critic:** Add a checklist to `skills/deep-research/shared/critique-checklists/` and register the trigger point in `shared/critique-cluster.md`. New critics inherit the blind-review protocol automatically.

**Add domain context:** Create a domain context skill (e.g., `oncology-genomics-context/`) in the repo root. The orchestrator detects loaded context skills and incorporates them into the research design phase.

**Add a data source:** Extend `skills/deep-research/scripts/fetch_data.py` and document in `skills/deep-research/references/data-sources.md`.

---

## Requirements

- Python 3.10+
- Claude Code with `Bash(python:*)`, `WebSearch`, `WebFetch` permissions
- See [requirements.txt](requirements.txt) for Python packages

---

## License

MIT, see [LICENSE](LICENSE)
