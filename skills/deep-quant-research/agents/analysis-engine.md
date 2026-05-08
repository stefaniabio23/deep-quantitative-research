# Analysis Engine Agent

**Role:** Run all statistical and time series analysis for the current research question. Produces the primary evidence base before critique and interpretation.

**Phase:** 6 — Analysis  
**Input:** `data_package.yaml` + `research_brief.yaml`  
**Output:** `analysis/statistical.yaml`, `analysis/timeseries.yaml`

---

## What this phase covers

The analysis engine runs two complementary workstreams, then consolidates:

1. **Statistical analysis** — correlations, regressions, factor models, hypothesis tests, event studies, PCA
2. **Time series analysis** — stationarity, lag structures, decomposition, rolling dependence, cointegration

Which analyses run depends on the study design in `research_brief.yaml`. Do not run every analysis by default. Run what the `research-architect` specified, plus the robustness checks it prescribed.

---

## Procedure

### Step 1: Read the study design

From `research_brief.yaml`, extract:
- Primary analysis method(s) specified
- Required robustness checks
- Multiple testing correction required (if > 1 test)
- Outcome variables and predictors
- Sample period and any subperiod splits

### Step 2: Run statistical analysis

```bash
python scripts/statistical_analysis.py \
  --input ./[topic_slug]/data/[primary_data].csv \
  --config ./[topic_slug]/research_brief.yaml \
  --output ./[topic_slug]/analysis/statistical.yaml
```

Run specific analyses as needed:

**Correlation:**
```bash
python scripts/statistical_analysis.py \
  --mode correlation \
  --input data.csv \
  --x signal_column \
  --y target_column \
  --method pearson,spearman,distance \
  --rolling 60 \
  --output ./analysis/correlation.yaml
```

**Regression (Newey-West SE):**
```bash
python scripts/statistical_analysis.py \
  --mode regression \
  --input data.csv \
  --target returns \
  --features "momentum,value,quality,size" \
  --se_type newey_west \
  --lags 12 \
  --output ./analysis/regression.yaml
```

**PCA / factor structure:**
```bash
python scripts/statistical_analysis.py \
  --mode pca \
  --input returns_matrix.csv \
  --n_components 5 \
  --output ./analysis/pca.yaml
```

**Event study:**
```bash
python scripts/statistical_analysis.py \
  --mode event_study \
  --events events.csv \
  --prices prices.csv \
  --window "-20,+60" \
  --output ./analysis/event_study.yaml
```

### Step 3: Run time series analysis

**Stationarity (run before any time series regression):**
```bash
python scripts/timeseries.py \
  --mode stationarity \
  --input data.csv \
  --columns "var1,var2" \
  --output ./analysis/stationarity.yaml
```

**Lag analysis:**
```bash
python scripts/timeseries.py \
  --mode lag \
  --input data.csv \
  --x lead_variable \
  --y target_variable \
  --max_lag 60 \
  --output ./analysis/lag.yaml
```

**Decomposition:**
```bash
python scripts/timeseries.py \
  --mode decompose \
  --input data.csv \
  --column series_name \
  --period 12 \
  --output ./analysis/decomposition.yaml
```

**Distance correlation (non-linear dependence):**
```bash
python scripts/timeseries.py \
  --mode distance_correlation \
  --input data.csv \
  --x var1 \
  --y var2 \
  --rolling 60 \
  --output ./analysis/dc.yaml
```

**Cointegration:**
```bash
python scripts/timeseries.py \
  --mode cointegration \
  --input data.csv \
  --output ./analysis/cointegration.yaml
```

### Step 4: Apply statistical standards

Every test must comply with `shared/statistical-standards.md`:

- Report exact p-values. Never "p < 0.05".
- Report effect sizes with type specified (Cohen's d, r, f², partial η²)
- Report confidence intervals on all point estimates
- Apply Newey-West HAC standard errors for all time series regressions
- Apply multiple testing correction when running > 1 test; state correction method

### Step 5: Run robustness checks

For each primary finding:
1. Subperiod split (halve the sample or split at a structural break)
2. Alternative specification (different functional form or variable construction)
3. Bootstrap CIs if sample N < 100

If robustness checks contradict the primary finding, report that explicitly.

### Step 6: Document all tests run

List every test performed — including those with non-significant results. This is mandatory for the data snooping check in the critique phase. Omitting failed tests is a protocol violation.

### Step 7: Write outputs

Produce:
- `analysis/statistical.yaml` — Schema 3 from `shared/handoff-schemas.md`
- `analysis/timeseries.yaml` — Schema 3 extension
- `analysis/charts/` — any charts generated

Include negative results. Include robustness check results.

---

## Analysis Templates by Question Type

### KPI-to-price relationship (finance)
1. Pearson + Spearman + Distance correlation, KPI vs. forward returns
2. OLS regression: forward returns on KPI, Newey-West SE
3. Rolling 36-month correlation (detect regime changes)
4. Quintile sort on KPI; average return per quintile
5. Stationarity of both series before regression
6. Lag analysis: which lag of KPI is most predictive
7. Subperiod: pre/post a relevant structural break (e.g., 2020, 2008)

### Factor decomposition (quant)
1. OLS: target returns on Fama-French 5 factors + any additional factors
2. Factor loadings, alpha, R², adjusted R²
3. Rolling 36-month loadings
4. Variance decomposition by factor
5. Stationarity check

### Clinical/biotech cross-sectional comparison
1. Describe distributions (mean, median, IQR, N) per group
2. t-test or Mann-Whitney U depending on normality
3. Effect size (Cohen's d or rank-biserial r)
4. CIs on group means/medians
5. Subgroup analyses specified in research brief

### Dependence structure (quant)
1. Full Pearson correlation matrix
2. Spearman rank correlation matrix
3. Pairwise distance correlation matrix
4. Hierarchical clustering on correlation matrix
5. PCA: eigenvalues, cumulative variance, loadings
6. Tail DC: lower/upper 20th percentile DC to detect asymmetric dependence

---

## Multiple Testing

If running N hypothesis tests:

**Bonferroni:** α_adj = 0.05 / N. Use when tests are independent.  
**Benjamini-Hochberg:** controls FDR. Use when tests are correlated.

State the correction method. Flag any test that is significant before correction but not after.
