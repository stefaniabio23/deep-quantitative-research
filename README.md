# deep-quant-research

A structured, iterative quantitative research skill for Claude Code. Runs a 12-agent pipeline across finance, biotech, and quant domains with a confidence-scored loop that refines hypotheses until the evidence is strong enough to report.

---

## What it does

Give it a research question. It formulates a testable hypothesis, finds and validates data, runs statistical analysis, interprets the results in domain context, stress-tests the findings, and produces a research report — all with explicit confidence scoring at each stage.

If the evidence is weak, it surfaces why and refines the hypothesis. If after three iterations there is still no reliable signal, it reports that as a null result.

**Research types supported:**
- **Finance:** KPI-to-price analysis, factor decomposition, backtesting, lag analysis, earnings quality, event studies
- **Biotech:** Clinical trial signal extraction, drug pipeline analysis, genomic data interpretation, literature synthesis
- **Quant:** Factor models, macro relationships, dependence structures (including distance correlation), regime analysis

---

## The research loop

```
Question
  → Hypothesis formulation + study design
  → Data discovery and quality audit
  → Statistical analysis (correlation, regression, time series, backtest, causal)
  → Plain-language interpretation with domain benchmarks
  → Confidence score (1-10)
       ↓ < 6: refine hypothesis and loop (max 3 iterations)
       ↓ ≥ 6: adversarial review by skeptic agent
  → Final report with writing quality check
```

---

## Install

```bash
# 1. Copy skill to Claude Code skills directory
cp -r skills/deep-quant-research ~/.claude/commands/

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Optional: FRED API key for macro data
export FRED_API_KEY=your_key_here
```

See [QUICKSTART.md](QUICKSTART.md) for the 5-minute guide.

---

## Usage

```
# Full research
Research [your question]
Deep research on [topic]

# Modes
/thesis-test: [hypothesis to test]
/quick: [question for a fast brief]
/data-first: [describe your dataset]
/literature: [topic to synthesise]
```

---

## Structure

```
skills/
  deep-quant-research/      ← the installable skill (copy this to ~/.claude/commands/)
    SKILL.md                ← orchestrator: modes, loop, routing
    references/
      data-sources.md       ← all APIs and their limitations

agents/                     ← 12 agent definitions
  question-sharpener.md
  research-architect.md
  data-scout.md
  data-quality.md
  statistical-analyst.md
  timeseries-analyst.md
  backtest-engine.md
  causal-inference.md
  interpret-agent.md
  confidence-scorer.md
  skeptic-agent.md
  report-compiler.md

shared/                     ← protocols referenced by all agents
  statistical-standards.md  ← evidence hierarchy, test requirements, confidence rubric
  data-quality-protocol.md  ← four-bias audit: look-ahead, survivorship, snooping, selection
  interpretation-rubric.md  ← domain benchmarks: what a result means in finance vs. biotech vs. quant
  output-style-guide.md     ← writing standards and anti-AI writing checklist
  handoff-schemas.md        ← data contracts between agents

scripts/                    ← Python utilities
  fetch_data.py             ← yfinance, FRED, Fama-French, ClinicalTrials.gov, PubMed, OpenTargets, openFDA
  statistical_analysis.py   ← correlation, regression (Newey-West), PCA, event study, Granger causality
  timeseries.py             ← ADF/KPSS, lag analysis, STL decomposition, distance correlation, cointegration
  backtest.py               ← walk-forward backtesting with transaction costs and drawdown
  data_quality.py           ← outlier detection, missing data audit
```

---

## The agent team

| Agent | Role |
|-------|------|
| `question-sharpener` | Converts vague questions into testable hypotheses with explicit success criteria |
| `research-architect` | Designs the study: analyses, data requirements, validation approach |
| `data-scout` | Fetches data from 8+ free APIs and web sources with provenance documentation |
| `data-quality` | Audits for look-ahead bias, survivorship bias, data snooping, and selection bias |
| `statistical-analyst` | Correlations (Pearson, Spearman, distance), regression, PCA, event study |
| `timeseries-analyst` | Stationarity, lag analysis, decomposition, rolling distance correlation, cointegration |
| `backtest-engine` | Walk-forward backtesting with transaction costs, drawdown, benchmark comparison |
| `causal-inference` | Granger causality, difference-in-differences, confound detection |
| `interpret-agent` | Plain-language findings with domain context and appropriate hedging |
| `confidence-scorer` | Scores 1-10 per statistical standards; routes to refine or proceed |
| `skeptic-agent` | Adversarial review: alternative explanations, methodology challenges, generalisability |
| `report-compiler` | Final output with style guide and anti-AI writing check |

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

**Add a new agent:** Create a file in `agents/` following the template in [CONTRIBUTING.md](CONTRIBUTING.md).

**Add domain context:** Create a domain context skill (e.g., `oncology-genomics-context/`) in the repo root. The orchestrator detects loaded context skills and incorporates them into the research design phase.

**Add a data source:** Extend `scripts/fetch_data.py` and document in `skills/deep-quant-research/references/data-sources.md`.

---

## Requirements

- Python 3.10+
- Claude Code with `Bash(python:*)`, `WebSearch`, `WebFetch` permissions
- See [requirements.txt](requirements.txt) for Python packages

---

## License

MIT — see [LICENSE](LICENSE)
