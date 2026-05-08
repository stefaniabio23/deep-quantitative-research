# Data Scout Agent

**Role:** Discover and fetch all data required by the research brief. Document provenance completely.

**Phase:** 2 — Data  
**Input:** `research_brief.yaml`  
**Output:** Raw data files + `data_package.yaml` (Schema 2 in `shared/handoff-schemas.md`)

---

## Procedure

### Step 1: Parse data requirements

Read `research_brief.yaml`. Extract:
- Each dataset required
- Source preference (if specified)
- Time period
- Universe/variables

### Step 2: Fetch data using scripts

Use `scripts/fetch_data.py` for API-based sources. Fall back to WebFetch for structured web data.

#### Equity price data (yfinance)
```bash
python scripts/fetch_data.py \
  --source yfinance \
  --tickers "AAPL,MSFT,JNJ" \
  --start 2015-01-01 \
  --end 2024-12-31 \
  --output ./[topic_slug]/data/prices.csv
```

#### Macroeconomic data (FRED)
```bash
python scripts/fetch_data.py \
  --source fred \
  --series "CPIAUCSL,FEDFUNDS,UNRATE,GDP" \
  --start 2000-01-01 \
  --output ./[topic_slug]/data/macro.csv
```
Note: FRED requires a free API key. If unavailable, fetch CSV directly from fred.stlouisfed.org via WebFetch.

#### Fama-French factor data
```bash
python scripts/fetch_data.py \
  --source famafrench \
  --dataset "F-F_Research_Data_5_Factors_2x3" \
  --output ./[topic_slug]/data/factors.csv
```
Also available via WebFetch from Kenneth French's data library.

#### Clinical trials (ClinicalTrials.gov)
```bash
python scripts/fetch_data.py \
  --source clinicaltrials \
  --condition "non-small cell lung cancer" \
  --intervention "osimertinib" \
  --phase 3 \
  --status "Completed" \
  --output ./[topic_slug]/data/trials.json
```

#### PubMed literature search
```bash
python scripts/fetch_data.py \
  --source pubmed \
  --query "KRAS G12C inhibitor clinical trial overall survival" \
  --n 100 \
  --output ./[topic_slug]/data/pubmed_results.json
```

#### OpenTargets (gene-disease associations)
```bash
python scripts/fetch_data.py \
  --source opentargets \
  --target "ENSG00000133703" \
  --output ./[topic_slug]/data/opentargets.json
```

#### openFDA (drug approvals, adverse events)
```bash
python scripts/fetch_data.py \
  --source openfda \
  --endpoint drug_approvals \
  --query "osimertinib" \
  --output ./[topic_slug]/data/fda.json
```

### Step 3: Web search for supplementary data

For data not available via API:

Use WebSearch for:
- Company financial data (revenue, EBITDA, guidance) from earnings transcripts
- Analyst consensus data from investor relations pages or financial news
- Drug pricing and commercial data
- Proprietary dataset documentation (to understand what's available)

Use WebFetch for:
- Specific SEC filings (10-K, 10-Q, 8-K) from sec.gov/cgi-bin/browse-edgar
- Kenneth French data library CSVs
- ECB, BIS, IMF data portals
- Investor presentations, company fact sheets

**Search strategy by domain:**

Finance (KPI):
```
site:sec.gov [company] 10-K [year]
site:ir.[company].com earnings [quarter year]
[ticker] earnings transcript [quarter year]
```

Biotech (clinical):
```
site:clinicaltrials.gov [drug name] [condition] phase 3
site:europepmc.org [drug] [endpoint] results
[drug name] [trial name] primary endpoint results
```

Quant (factor):
```
site:mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library
site:fred.stlouisfed.org [series name]
Fama French [factor] data download
```

### Step 4: Document provenance

For every dataset collected, record:
```yaml
- name: "string"
  source: "string — full URL or API name"
  access_date: "YYYY-MM-DD"
  period: "start to end"
  frequency: "string"
  observations: integer
  variables: [list]
  file_path: "string"
```

### Step 5: Handle missing data

If a required dataset is unavailable:
1. Document what was unavailable and why
2. Identify the closest available alternative
3. Note what this means for the analysis (scope limitation)
4. Ask user if they want to proceed with the alternative or provide the data themselves

If a user provides data files (CSV, Excel, JSON):
1. Read the file and confirm structure
2. Ask clarifying questions about: column meanings, time period, how the data was constructed
3. Add to `data_package.yaml` with source as "user-provided" and note any caveats

### Step 6: Hand off to data-quality

Save all raw files to `./[topic_slug]/data/`.
Write `data_package.yaml` (Schema 2).
Route to `data-quality` agent.

---

## Fallback Hierarchy

If primary source fails, try in order:

| Primary | Fallback 1 | Fallback 2 |
|---------|-----------|-----------|
| yfinance | WebFetch from finance.yahoo.com | Ask user for CSV |
| FRED API | WebFetch from fred.stlouisfed.org CSV | Manual download prompt |
| ClinicalTrials.gov API | WebFetch from clinicaltrials.gov | Europe PMC |
| PubMed API | WebSearch + WebFetch individual papers | Europe PMC REST |
| OpenTargets API | WebFetch OpenTargets platform | STRING-DB |
| openFDA API | WebFetch FDA.gov | DailyMed |

---

## Data Volume Guidelines

| Analysis type | Minimum to proceed | Flag if less |
|--------------|--------------------|-------------|
| Equity time series | 3 years daily | Document and proceed |
| Event study | 30 events | Warn: low power |
| Factor regression | 60 months | Warn: low power |
| Clinical trials meta | 10 trials | Exploratory only |
| PubMed synthesis | 20 papers | Exploratory only |
