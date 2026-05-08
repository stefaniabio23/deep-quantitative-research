# Functional Tests

Concrete test cases to verify end-to-end workflow quality.

---

## Test 1: Finance — KPI backtest (quick mode)

**Input:**
```
/quick: is revenue growth predictive of 3-month forward returns in European pharma?
```

**Expected output:**
- Hypothesis confirmed in Phase 1 (revenue growth → 3m forward returns, EU pharma, specific period)
- Data fetched: price data from yfinance (EU pharma tickers), revenue growth from web/user
- Correlation analysis run (Pearson + Spearman + DC)
- Lag analysis: 1, 2, 3-month lags tested
- Report: Research Brief format (Key Finding, Evidence, Caveats, Method)
- No backtest run (quick mode)

**Pass criteria:**
- Report produced in < 15 tool calls
- Statistics embedded in prose (not table-dumped)
- Caveats include survivorship bias of yfinance data
- Confidence score reported

---

## Test 2: Biotech — Literature synthesis

**Input:**
```
/literature: KRAS G12C inhibitors — what does the clinical evidence show for overall survival
```

**Expected output:**
- PubMed search: `KRAS G12C inhibitor overall survival clinical trial`
- ClinicalTrials.gov search: KRAS G12C Phase 2/3
- Literature Synthesis report format
- Key studies table with: drug, trial, design, N, endpoint, HR/ORR, limitations
- Discussion of biomarker selection, comparison to SoC
- Gaps section: what has not been established

**Pass criteria:**
- At least 10 papers/trials referenced
- Distinguishes Phase 2 from Phase 3 evidence
- Hazard ratios reported with CIs, not just p-values
- No false citations (all papers cited should be findable)

---

## Test 3: Quant — Factor analysis (full mode)

**Input:**
```
Research whether the Value factor (Fama-French HML) performs differently during high vs low inflation regimes over 1970-2024
```

**Expected output:**
- Phase 1: hypothesis sharpened (HML return in high CPI vs low CPI months, defined threshold)
- Data: Fama-French monthly factors + FRED CPI
- statistical-analyst: regression of HML on inflation regime dummy + rolling correlation
- timeseries-analyst: stationarity check, regime breakdown
- Confidence scoring with out-of-sample validation attempt (pre/post 2000 subperiods)
- Skeptic: challenges data snooping (how many factor/regime combinations were pre-specified?)
- Full Report format

**Pass criteria:**
- Regime defined explicitly (e.g., CPI YoY > X%)
- Both in-sample and subperiod results reported
- Skeptic challenge on regime definition included
- Writing passes anti-AI checklist

---

## Test 4: Data quality — Look-ahead bias detection

**Setup:** Provide a CSV where a signal column uses period-end dates rather than announcement dates.

**Input:**
```
/data-first: [attach CSV with end-of-quarter signal and stock returns]
```

**Expected output:**
- data-quality agent flags the potential look-ahead bias
- WARN or FAIL verdict depending on whether the issue can be assessed from the data structure
- User asked to confirm before proceeding

**Pass criteria:**
- Look-ahead bias explicitly mentioned in the data quality report
- Analysis does not proceed without user acknowledgement

---

## Test 5: Confidence scoring and loop

**Input:**
```
Research whether analyst consensus changes predict stock returns in EU healthcare (use 2023 data only)
```

**Expected output:**
- Phase 1-3 run normally
- Confidence score: likely 3-5 (2023 only = 12 months, low N)
- confidence-scorer recommends REFINE
- question-sharpener proposes extending to 2018-2023
- User asked to confirm before re-running
- Second iteration: N increases, confidence score should improve

**Pass criteria:**
- Loop triggered (not just a single pass)
- Specific gap identified in refinement suggestion (sample size)
- Second iteration produces higher confidence score

---

## Test 6: Null result handling

**Input:**
```
Research whether full moon cycles predict stock market returns
```

**Expected output:**
- Hypothesis formed and tested
- Statistical analysis: correlation and regression
- Confidence score: 1-3
- Null result report produced (not a positive finding)
- Report explicitly states: "no reliable relationship detected"
- Power analysis: minimum detectable effect at this sample size

**Pass criteria:**
- No positive finding reported
- Null result framed as informative, not as failure
- Proper statistical framing (what would have been detectable)

---

## Script tests

Run these directly to verify scripts work:

```bash
# Test data fetching
python scripts/fetch_data.py --source yfinance --tickers AZN.L --start 2020-01-01 --output /tmp/test_prices.csv

# Test statistical analysis
python scripts/statistical_analysis.py --mode correlation --input /tmp/test_prices.csv --x Close --y Volume --output /tmp/test_corr.yaml

# Test time series
python scripts/timeseries.py --mode stationarity --input /tmp/test_prices.csv --columns Close,Volume --output /tmp/test_ts.yaml

# Test data quality
python scripts/data_quality.py --input /tmp/test_prices.csv --output /tmp/test_dq.yaml --mode full

# Test PubMed
python scripts/fetch_data.py --source pubmed --query "osimertinib overall survival" --n 10 --output /tmp/test_pubmed.json

# Test ClinicalTrials
python scripts/fetch_data.py --source clinicaltrials --condition "non-small cell lung cancer" --phase 3 --n 20 --output /tmp/test_trials.json
```

All should exit with code 0 and produce output files.
