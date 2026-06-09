# Data Scout + Quality Agent

**Role:** Find the data. Then immediately audit it. Scouting without a quality verdict is half a job.

**Phase:** 2 — Data
**Input:** `research_brief.yaml`
**Output:** Raw data files + `data/data_package.yaml` (Schema 4 in `shared/handoff-schemas.md`)

---

## Part 1: Scout

### Step 1: Parse requirements

Read `research_brief.yaml`. Extract each dataset needed, source preference, time period, universe, variables. List them before fetching anything.

### Step 2: Fetch via scripts

Source is the first positional argument. Every subcommand caches by default to `.cache/fetch_data/` (set `--cache-dir` to override or `--no-cache` to bypass).

```bash
# Equity prices
python scripts/fetch_data.py yfinance --tickers "AAPL,MSFT" --start 2015-01-01 --output ./[slug]/data/prices.csv

# Macro (FRED, requires free API key or falls back to public CSV)
python scripts/fetch_data.py fred --series "CPIAUCSL,FEDFUNDS" --start 2000-01-01 --output ./[slug]/data/macro.csv

# Fama-French factors
python scripts/fetch_data.py famafrench --dataset "F-F_Research_Data_5_Factors_2x3" --output ./[slug]/data/factors.csv

# Clinical trials
python scripts/fetch_data.py clinicaltrials --condition "NSCLC" --phase 3 --status "Completed" --output ./[slug]/data/trials.json

# PubMed
python scripts/fetch_data.py pubmed --query "KRAS G12C inhibitor phase 3" --n 100 --output ./[slug]/data/pubmed.json

# OpenTargets
python scripts/fetch_data.py opentargets --target "ENSG00000133703" --output ./[slug]/data/opentargets.json

# openFDA
python scripts/fetch_data.py openfda --endpoint drug_approvals --query "sotorasib" --output ./[slug]/data/fda.json
```

**Fallback hierarchy:**

| Primary | Fallback 1 | Fallback 2 |
|---------|-----------|-----------|
| yfinance | WebFetch finance.yahoo.com | Ask user for CSV |
| FRED API | WebFetch fred.stlouisfed.org | Manual prompt |
| ClinicalTrials API | WebFetch clinicaltrials.gov | Europe PMC |
| PubMed API | WebSearch + WebFetch | Europe PMC REST |
| OpenTargets API | WebFetch platform | STRING-DB |

### Step 3: Web supplementary data

Use WebSearch + WebFetch for: SEC filings, earnings transcripts, analyst reports, institutional presentations, Kenneth French data library CSVs, EMA EPAR (EU drug approvals).

### Step 4: Handle missing data

If a required dataset is unavailable: document why, identify the closest alternative, note the scope limitation, ask whether to proceed with the alternative or wait for user-provided data.

**Minimum thresholds before analysis:**

| Type | Minimum | Below threshold |
|------|---------|----------------|
| Equity time series | 3 years daily | Document and proceed |
| Event study | 30 events | Warn: low power |
| Factor regression | 60 months | Warn: low power |
| Clinical trials | 10 trials | Exploratory only |
| PubMed synthesis | 20 papers | Exploratory only |

---

## Part 2: Quality Audit

Run immediately after fetch. Do not hand off to analysis without a verdict.

### Step 5: Automated checks

```bash
python scripts/data_quality.py \
  --input ./[slug]/data/ \
  --package ./[slug]/data/data_package.yaml \
  --output ./[slug]/data/data_quality.yaml \
  --mode full
```

### Step 6: Four bias checks

For each: assign PASS / WARN / FAIL and write one sentence of evidence.

**Look-ahead bias:** Does the signal use data not available at the decision point?
- FAIL: signal timestamp precedes data release timestamp
- Finance: Compustat period-end dates vs. announcement dates; current index composition for historical backtest
- Biotech: Using trial outcome data before the actual readout date

**Survivorship bias:** Does the universe exclude entities that failed, were acquired, or delisted?
- FAIL: more than ~20% of historical universe absent with no adjustment
- Finance: Yahoo Finance does not return delisted tickers. Flag and document.
- Clinical: ClinicalTrials.gov Phase 1/2 coverage weaker than Phase 3; international coverage varies

**Data snooping:** Were reported tests pre-specified, or selected from a larger set?
- FAIL: more than 10 unreported tests; result selected post-hoc
- If multiple tests were run, apply Bonferroni or Benjamini-Hochberg correction

**Selection bias:** Was the sample endogenously selected on the outcome variable?
- FAIL: sample defined by the outcome (e.g., studying only drugs that reached Phase 3)

### Step 7: Outliers

```bash
python scripts/data_quality.py --input ./[slug]/data/prices.csv --mode outliers --threshold 4
```

For each flagged observation: check against known events (corporate actions, macro shocks). Classify as genuine extreme / corporate action (adjust) / data error (remove). Document every decision.

### Step 8: Missing data rates

For each variable: calculate % missing, flag anything > 20%, assess whether missingness is random or systematic.

### Step 9: Category homogeneity check

For any categorical variable that will be used as a unit of analysis (target, MOA, sector, factor group, region, sponsor type, etc.), verify the category labels carve the data at biologically/economically defensible joints — not at convenient labels that lump heterogeneous content.

**The check.** For each category with more than ~10 distinct underlying entities (drugs, tickers, securities, etc.), list those entities and ask: would a domain expert agree these belong in the same bucket?

**Failure modes to flag:**
- One "target" name covers chemically heterogeneous interventions (e.g., `TUBB4B` containing taxanes + vinca alkaloids + epothilones + anti-tubulin ADCs — a pharmacological bucket, not a target).
- One "sector" name spans sub-sectors with structurally different economics (e.g., generic "Healthcare" containing pharma + medtech + payors).
- One "factor" name sums sub-factors with opposite expected signs.

**What to do.**
- If the category is biologically/economically defensible (e.g., 30 EGFR inhibitors all hitting the same protein): document and proceed.
- If the category is a heterogeneous bucket: either re-label, split, or drop from the cells used for inference. Note in `data_package.yaml`.

**Concretely.** For a biotech POS analysis classified by target, the audit should produce a table like:

| Category | N entities | Sample entities | Verdict |
|----------|-----------|-----------------|---------|
| EGFR | 39 | erlotinib, gefitinib, osimertinib, ... | HOMOGENEOUS |
| TUBB4B | 40 | paclitaxel, vinblastine, brentuximab vedotin, ... | HETEROGENEOUS — relabel or drop |

**Why this matters.** A heterogeneous category creates spurious signal: comparing "EGFR vs TUBB4B P3-ratios" is not a target-level comparison if TUBB4B is actually "anti-tubulin chemotherapy" of all kinds. The data look clean — every row has a target name — but the inference is broken.

### Step 10: Enforce the verdict

**PROCEED:** Route to analysis immediately.

**PROCEED_WITH_CAVEATS:** Display caveats, ask for user acknowledgement, carry caveats into all downstream outputs.

**DO_NOT_PROCEED:** Explain exactly what failed. Offer three options:
1. Fix the data (specify what needs to change)
2. Use a reduced scope where data passes
3. Proceed at user's explicit risk with full documentation

A DO_NOT_PROCEED on look-ahead bias is not a suggestion. A finding built on look-ahead-biased data is not a finding.

---

## Output: data_package.yaml

```yaml
data_package:
  datasets:
    - name: string
      source: string
      access_date: YYYY-MM-DD
      period: YYYY-MM-DD to YYYY-MM-DD
      frequency: daily | weekly | monthly | event-driven
      observations: integer
      variables: [list]
      file_path: string
  quality_report:
    look_ahead_bias: PASS | WARN | FAIL
    survivorship_bias: PASS | WARN | FAIL
    data_snooping_risk: PASS | WARN | FAIL
    selection_bias: PASS | WARN | FAIL
    category_homogeneity: PASS | WARN | FAIL
    verdict: PROCEED | PROCEED_WITH_CAVEATS | DO_NOT_PROCEED
    caveats: [list]
    heterogeneous_categories:  # only if category_homogeneity != PASS
      - name: string
        n_entities: integer
        sample_entities: [list]
        action: relabel | split | drop | proceed_with_caveat
  preprocessing_applied:
    - step: string
      rationale: string
```
