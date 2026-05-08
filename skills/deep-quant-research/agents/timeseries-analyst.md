# Time Series Analyst Agent

**Role:** Time-series specific analysis — stationarity, lag structure, decomposition, cointegration, distance correlation over time.

**Phase:** 3 — Analysis  
**Input:** Validated data package + research brief  
**Output:** `analysis/timeseries.yaml` (Schema 3 in `shared/handoff-schemas.md`)

---

## Procedure

### Step 1: Run time series analysis

```bash
python scripts/timeseries.py \
  --input ./[topic_slug]/data/[timeseries_data].csv \
  --target close \
  --config ./[topic_slug]/research_brief.yaml \
  --output ./[topic_slug]/analysis/timeseries.yaml
```

Or run individual components:

#### Stationarity testing
```bash
python scripts/timeseries.py \
  --mode stationarity \
  --input prices.csv \
  --columns "price,volume,signal" \
  --output ./analysis/stationarity.yaml
```

#### Lag analysis
```bash
python scripts/timeseries.py \
  --mode lag \
  --input data.csv \
  --x signal_col \
  --y returns_col \
  --lags "1,2,5,10,20,60" \
  --rolling_window 252 \
  --output ./analysis/lag_analysis.yaml
```

#### Decomposition
```bash
python scripts/timeseries.py \
  --mode decompose \
  --input prices.csv \
  --column close \
  --model additive \
  --period 252 \
  --output ./analysis/decomposition.yaml
```

#### Distance correlation over rolling windows
```bash
python scripts/timeseries.py \
  --mode distance_correlation \
  --input data.csv \
  --x col1 \
  --y col2 \
  --rolling 60 \
  --output ./analysis/dc_rolling.yaml
```

#### Cointegration
```bash
python scripts/timeseries.py \
  --mode cointegration \
  --input prices.csv \
  --columns "series1,series2" \
  --output ./analysis/cointegration.yaml
```

---

## Analysis Sequence (standard)

### 1. Stationarity first

Before any regression or correlation on time series, test for stationarity.

**Augmented Dickey-Fuller (ADF):**
- H0: series has a unit root (non-stationary)
- Reject H0 (p < 0.05) → stationary
- Fail to reject → likely non-stationary; difference before analysis

**KPSS test:**
- H0: series is stationary
- Reject H0 → non-stationary
- Use both ADF and KPSS: they test opposite nulls; agreement is stronger evidence

**Decision tree:**
```
ADF: reject H0, KPSS: fail to reject → Stationary → proceed
ADF: fail to reject, KPSS: reject → Non-stationary → difference
ADF: reject, KPSS: reject → Trend-stationary → detrend
ADF: fail to reject, KPSS: fail to reject → Inconclusive → use first differences and note
```

### 2. Lag analysis

Testing whether X at time t-k predicts Y at time t.

**Standard lags to test:** 1, 2, 5, 10, 20, 60 days (or equivalent in data frequency)

For each lag k:
- Pearson correlation between X(t-k) and Y(t)
- t-statistic with Newey-West standard errors
- Rolling 252-day correlation at lag k (stability check)

Report as a table:
```
Lag | Pearson r | Spearman r | DC   | t-stat | p-value | Rolling stability
1   | 0.12      | 0.11       | 0.14 | 2.1    | 0.038   | Stable
5   | 0.21      | 0.19       | 0.23 | 3.8    | 0.000   | Stable
10  | 0.18      | 0.17       | 0.20 | 3.1    | 0.002   | Moderate
20  | 0.08      | 0.07       | 0.09 | 1.4    | 0.162   | Unstable
60  | 0.03      | 0.02       | 0.04 | 0.5    | 0.618   | Unstable
```

**Key interpretation:** The lag with the highest stable correlation is the primary signal lag. "Stable" means the rolling correlation maintains the same sign > 80% of the time.

### 3. Decomposition (if trend/seasonal analysis needed)

Decompose into trend, seasonal, and residual components using STL (Seasonal-Trend decomposition using LOESS) or classical decomposition.

Report:
- Trend component plot
- Seasonal pattern (if present)
- Residual autocorrelation (ACF/PACF)

### 4. Distance correlation (DC)

DC captures linear and non-linear dependence. DC = 0 implies independence.

Run rolling DC alongside Pearson to detect:
- Periods where non-linear dependence is present (DC >> |Pearson|)
- Regime changes in the dependence structure
- Tail dependence (compute DC on tail observations: top/bottom 20%)

Report:
- Overall DC vs. Pearson comparison
- Rolling DC chart
- Tail DC vs. middle-sample DC

### 5. Cointegration (if long-run relationship hypothesis)

Engle-Granger two-step test for pairs:
1. Regress Y on X; test residuals for stationarity
2. If residuals are I(0): cointegrated

Johansen test for multiple series:
- Reports trace statistic and max eigenvalue statistic
- Number of cointegrating vectors

If cointegrated: fit VECM (Vector Error Correction Model)
- Report speed of adjustment (α)
- Mean reversion half-life = -ln(2) / ln(1 + α)

### 6. Autocorrelation and ARCH effects

For residuals of any model:
- Ljung-Box test for autocorrelation (H0: no autocorrelation)
- ARCH-LM test for conditional heteroskedasticity (H0: no ARCH effects)

If autocorrelation is present: use HAC (Newey-West) standard errors.
If ARCH effects present: note for any volatility-related analysis.

---

## Output Schema

`analysis/timeseries.yaml` must include:

```yaml
analyst: timeseries

stationarity:
  [series_name]:
    adf_statistic: float
    adf_pvalue: float
    kpss_statistic: float
    kpss_pvalue: float
    verdict: "stationary | non-stationary | trend-stationary"
    transformation_applied: "none | first-difference | log | log-difference"

lag_analysis:
  optimal_lag: integer
  lag_table: [see format above]
  rolling_stability: "stable | moderate | unstable"
  
decomposition:
  trend: "description"
  seasonality: "present | absent | period: X"
  residual_autocorrelation: "present | absent"

distance_correlation:
  overall_dc: float
  vs_pearson: "higher | similar | lower"
  rolling_interpretation: "string"
  tail_dc: float

cointegration:
  tested: true/false
  result: "cointegrated | not-cointegrated | not-applicable"
  half_life_days: float  # if cointegrated

findings: [list conforming to Schema 3]
negative_results: [list]
scripts_used: [list]
output_files: [list]
```
