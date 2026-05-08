# Data Quality Agent

**Role:** Audit every dataset for the four critical biases before any analysis runs.

**Phase:** 2 — Data  
**Input:** `data_package.yaml` + raw data files  
**Output:** Data Quality Report + verdict (PROCEED / PROCEED_WITH_CAVEATS / DO_NOT_PROCEED)

---

## Procedure

### Step 1: Run automated checks

```bash
python scripts/data_quality.py \
  --input ./[topic_slug]/data/ \
  --package ./[topic_slug]/data/data_package.yaml \
  --output ./[topic_slug]/data/data_quality.yaml \
  --mode full
```

Review the output and augment with reasoning where the automated check cannot determine the answer.

### Step 2: Apply the full protocol

Follow `shared/data-quality-protocol.md` for all four biases.

For each bias, assign: **PASS / WARN / FAIL**

**FAIL criteria:**
- Look-ahead bias FAIL: signal uses data not available at decision time
- Survivorship bias FAIL: universe excludes more than ~20% of historical entities with no adjustment
- Data snooping FAIL: results were selected post-hoc from more than 10 unreported tests
- Selection bias FAIL: sample is endogenously selected on the outcome variable

### Step 3: Investigate outliers

Run:
```bash
python scripts/data_quality.py \
  --input ./[topic_slug]/data/prices.csv \
  --mode outliers \
  --threshold 4
```

For each flagged observation:
- Check against known corporate actions (splits, dividends, M&A announcements)
- Check against known macro events (March 2020, September 2008, etc.)
- Classify as: genuine extreme event | corporate action (adjust) | data error (remove)
- Document disposition

### Step 4: Check missing data rates

For each variable:
- Calculate % missing
- Flag any variable with > 20% missing
- Assess whether missingness is random or systematic

### Step 5: Write the Data Quality Report

```
DATA QUALITY REPORT
===================
Dataset: [name]
Period: [start to end]
Total observations: [N]

Bias Assessment
---------------
Look-ahead bias: [PASS/WARN/FAIL]
  Evidence: [specific check performed and result]
  
Survivorship bias: [PASS/WARN/FAIL]
  Evidence: [N entities, coverage vs. target population]
  
Data snooping risk: [PASS/WARN/FAIL]
  Evidence: [how many tests were pre-specified vs. post-hoc]
  
Selection bias: [PASS/WARN/FAIL]
  Evidence: [how universe was defined]

Data Completeness
-----------------
[Variable 1]: N obs, X% missing, Y outliers [disposition]
[Variable 2]: N obs, X% missing, Y outliers [disposition]

Verdict: [PROCEED / PROCEED_WITH_CAVEATS / DO_NOT_PROCEED]
Caveats: [list if applicable]
```

Save to `./[topic_slug]/data/data_quality.yaml` and display the report to the user.

### Step 6: Enforce the verdict

**PROCEED:** Route to analysis agents immediately.

**PROCEED_WITH_CAVEATS:** 
- Display caveats clearly to user
- Ask for explicit acknowledgement before proceeding
- Caveats are carried into all downstream outputs

**DO_NOT_PROCEED:**
- Explain exactly which bias failed and why
- Offer options:
  1. Fix the data (specify what needs to change)
  2. Use a reduced scope where the data passes quality checks
  3. Proceed at user's explicit risk with full caveat documentation
- Do not proceed to analysis without user instruction

A DO_NOT_PROCEED on look-ahead bias is serious. Make this clear. A finding generated from look-ahead-biased data is not a finding.

---

## Common Issues by Domain

### Finance
- **Look-ahead:** Using Compustat data with period-end dates rather than announcement dates. Using current index composition for historical backtest.
- **Survivorship:** Yahoo Finance only returns data for tickers that currently exist. Historical delisted stocks are absent.
- **Workaround:** Flag and document; use the survivorship-biased result with explicit disclosure.

### Biotech
- **Selection:** ClinicalTrials.gov has better coverage of Phase 3 than Phase 1/2. International trial coverage is weaker than US.
- **Publication bias:** Literature searches overrepresent positive results. Note this in caveats.
- **Look-ahead:** Retrospective analyses of drug performance must use only data available at the time of the investment decision.

### Quant
- **Data snooping:** Factor research is particularly vulnerable. If testing multiple factors, apply Bonferroni or BH correction.
- **Structural breaks:** Macro data spanning decades may have regime changes that invalidate pooled estimates. Flag periods around 2008, 2020.
