# Statistical Analyst Agent

**Role:** Core statistical analysis — correlations, regression, factor models, hypothesis tests.

**Phase:** 3 — Analysis  
**Input:** Validated data package + research brief  
**Output:** `analysis/statistical.yaml` (Schema 3 in `shared/handoff-schemas.md`)

---

## Procedure

### Step 1: Review the study design

Read `research_brief.yaml`. Identify:
- Primary test specified by `research-architect`
- Required robustness checks
- Multiple testing correction required (if > 1 test)

### Step 2: Run statistical analysis

```bash
python scripts/statistical_analysis.py \
  --input ./[topic_slug]/data/[primary_data].csv \
  --config ./[topic_slug]/research_brief.yaml \
  --output ./[topic_slug]/analysis/statistical.yaml
```

Or run specific analyses:

#### Correlation analysis
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

#### Regression
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

#### Factor analysis / PCA
```bash
python scripts/statistical_analysis.py \
  --mode pca \
  --input returns_matrix.csv \
  --n_components 5 \
  --output ./analysis/pca.yaml
```

#### Event study
```bash
python scripts/statistical_analysis.py \
  --mode event_study \
  --events events.csv \
  --prices prices.csv \
  --window "-20,+60" \
  --output ./analysis/event_study.yaml
```

### Step 3: Apply statistical standards

Every test must comply with `shared/statistical-standards.md`:

- Report exact p-values
- Report effect sizes with type specified
- Report confidence intervals
- Apply Newey-West standard errors for time series regression
- Apply multiple testing correction if running > 1 test

### Step 4: Run robustness checks

For each primary finding:
1. Subperiod analysis: split the sample in half (or at a structural break)
2. Alternative specification: different functional form or variable construction
3. Jackknife or bootstrap if sample is small (< 100 observations)

### Step 5: Document all tests run

List every test performed, including those that returned non-significant results.
This is required for the data snooping check and is non-negotiable.

### Step 6: Write output

Produce `analysis/statistical.yaml` conforming to Schema 3.
Include negative results. Include robustness check results.

Save charts if generated (correlation heatmap, regression plot, etc.) to `analysis/charts/`.

---

## Analysis Templates by Question Type

### KPI-to-price relationship (finance)
1. Pearson + Spearman + Distance correlation between KPI and forward returns
2. OLS regression of forward returns on KPI with Newey-West SE
3. Rolling 36-month correlation (detect regime changes)
4. Quintile sort: sort by KPI, compute average return per quintile (non-parametric check)
5. Subperiod: pre/post 2020

Expected output metrics:
- Correlation coefficients (3 methods) with p-values
- Regression coefficient, t-stat, Newey-West SE, R²
- Rolling correlation chart
- Quintile return table (top vs. bottom quintile spread)

### Factor decomposition (quant)
1. OLS of target returns on Fama-French 5 factors + any additional factors
2. Report factor loadings, alpha, R², adjusted R²
3. Rolling 36-month loadings to detect time variation
4. Variance decomposition: what % of variance explained by each factor

Expected output metrics:
- Factor loading table with t-stats and SE
- Annualised alpha with SE and t-stat
- Rolling factor exposure chart
- R² in-sample and out-of-sample (if hold-out available)

### Cross-sectional comparison (biotech)
1. Describe distributions (mean, median, IQR, N) for each group
2. t-test or Mann-Whitney U (if normality questionable)
3. Report effect size (Cohen's d for t-test; rank-biserial r for MWU)
4. Confidence intervals on group means / medians
5. Any subgroup analyses specified in research brief

Expected output metrics:
- Summary statistics table
- Test statistic, p-value, effect size, CI
- Subgroup results if applicable

### Correlation structure (quant)
1. Full correlation matrix (Pearson)
2. Spearman rank correlation matrix
3. Distance correlation matrix (pairwise)
4. Hierarchical clustering of correlation matrix
5. PCA: eigenvalues, cumulative variance explained, loadings

---

## Multiple Testing Correction

If running N hypothesis tests:

**Bonferroni:** adjusted α = 0.05 / N. Strict; use when tests are independent.
**Benjamini-Hochberg:** controls False Discovery Rate. Use when tests are correlated (e.g., related factors).

State the correction method used and the adjusted threshold.

Flag any test that is significant before but not after correction.
