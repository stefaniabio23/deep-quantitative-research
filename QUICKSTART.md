# Quick Start

Get running in under 5 minutes.

---

## Install

**Step 1:** Clone or download this repo

```bash
git clone https://github.com/[your-username]/deep-quant-research.git
```

**Step 2:** Copy the skill to your Claude Code skills directory

```bash
cp -r deep-quant-research/skills/deep-quant-research ~/.claude/commands/
```

**Step 3:** Install Python dependencies

```bash
pip install -r deep-quant-research/requirements.txt
```

**Step 4:** (Optional) Set FRED API key for macroeconomic data

```bash
export FRED_API_KEY=your_key_here
# Get a free key at: fred.stlouisfed.org/docs/api/api_key.html
```

---

## Run your first research

Open Claude Code in the directory where you want research output saved, then:

```
Research whether momentum is stronger during low-volatility regimes in European equities
```

Claude will:
1. Sharpen the hypothesis and ask you to confirm
2. Fetch factor and price data
3. Run the analysis
4. Score confidence and refine if needed
5. Produce a report

---

## Mode examples

```
# Full research loop
Research [your question]

# Test an existing hypothesis
/thesis-test: [state your hypothesis clearly]

# Quick brief (30 min target)
/quick: what drives EBITDA multiple expansion in European pharma

# You have a dataset
/data-first: [describe your dataset]

# Literature synthesis
/literature: KRAS G12C inhibitors — what does the clinical evidence show
```

---

## Troubleshooting

**Missing packages:** `pip install -r requirements.txt`

**yfinance errors:** Some tickers require the exchange suffix (e.g., `AZN.L` for AstraZeneca on LSE)

**ClinicalTrials.gov slow:** The API is public and occasionally slow. Retry after a minute.

**FRED data not fetching:** Set `FRED_API_KEY` or the script will attempt a direct CSV download as fallback.

**Confidence score stuck:** After 3 iterations, the system reports a null result. This is informative — see the report for what was ruled out and what additional data would resolve it.
