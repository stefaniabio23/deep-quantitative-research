# Statistical Standards

Standards for what constitutes credible quantitative analysis across all research types.
All agents performing or interpreting analysis must reference this document.

---

## Evidence Hierarchy

| Level | Description | Weight |
|-------|-------------|--------|
| 1 | Replicated finding with out-of-sample validation | Highest |
| 2 | Walk-forward or cross-validated result | High |
| 3 | In-sample with robust robustness checks | Moderate |
| 4 | Single-period in-sample only | Low |
| 5 | Curve-fitted or data-mined result | Suspect |

A finding should not be presented as strong evidence below Level 3 without explicit caveats.

---

## Hypothesis Testing

### Minimum requirements
- State the null hypothesis before running any test
- Pre-register the test statistic and significance threshold before seeing results
- Report exact p-values, not "p < 0.05"
- Report effect sizes alongside p-values (Cohen's d, R², partial η²)
- Report confidence intervals, not just point estimates

### Multiple testing

Apply Bonferroni, Benjamini-Hochberg (BH), or equivalent correction when running more than one test on the same dataset.

**When to use which:**
- **Bonferroni:** tests are independent (or close to it). α_adj = 0.05 / N. Conservative; use when a single false positive is very costly.
- **Benjamini-Hochberg:** tests are correlated (common in factor analysis, genomics, or any screen across many related variables). Controls false discovery rate (FDR), not familywise error rate. Preferable when N > 10 tests.

**Worked example:**
> You test 12 combinations of factor × holding period. Two pass at p < 0.05. Without correction: expected false discoveries at this rate = 12 × 0.05 = 0.6 — plausibly both "findings" are noise. After Bonferroni, threshold is p < 0.004; neither survives. After BH at FDR = 0.10, the threshold for the two lowest p-values is p < 0.0083; whether they survive depends on the exact values. Report all 12 results, state the correction applied, and flag the pre-correction survivors explicitly.

Report the number of tests considered, not just those that passed. Flag any analysis that selected the "best" specification post-hoc.

### Threshold conventions by domain

| Domain | Primary standard | Notes |
|--------|-----------------|-------|
| Finance | p < 0.05; but Sharpe > 1.0 out-of-sample is more meaningful | Statistical significance is necessary but not sufficient |
| Biotech/clinical | p < 0.05 (Phase 2), p < 0.01 (Phase 3) | FDA standard; check clinical significance separately |
| Quant/factor | p < 0.05 with Newey-West SE | Must account for autocorrelation |

---

## Effect Size Thresholds by Domain

Statistical significance says the effect is probably not zero. Effect size says whether it is worth caring about. Always report both.

### Finance

| Measure | Weak | Moderate | Strong |
|---------|------|----------|--------|
| Spearman r (signal vs. returns) | < 0.10 | 0.10–0.25 | > 0.25 |
| R² (factor model) | < 0.02 | 0.02–0.10 | > 0.10 |
| Sharpe ratio (out-of-sample) | < 0.4 | 0.4–0.8 | > 0.8 |
| IC (information coefficient) | < 0.03 | 0.03–0.07 | > 0.07 |

Context: financial markets are noisy. An r = 0.15 on a signal vs. monthly returns is modest but potentially tradeable at scale. An r = 0.40 should be viewed with suspicion unless the data quality is impeccable.

### Biotech/clinical

| Measure | Meaningful threshold | Notes |
|---------|---------------------|-------|
| Hazard ratio (OS) | HR < 0.80 | 20%+ reduction in event hazard |
| Hazard ratio (PFS) | HR < 0.75 | PFS benefit does not reliably predict OS benefit |
| Odds ratio (Phase transition) | OR > 1.5 | Practically meaningful for pipeline analysis |
| Absolute risk difference | > 10 percentage points | OR alone is misleading at low base rates |
| ORR absolute improvement | > 15–20pp vs. SoC | Context-dependent; lower bar in refractory settings |

### Quant/macro

| Measure | Weak | Moderate | Strong |
|---------|------|----------|--------|
| Granger F-statistic | p < 0.10 | p < 0.05 | p < 0.01, stable lag |
| Cointegration (ADF on residuals) | p < 0.10 | p < 0.05 | p < 0.01 |
| PCA variance explained (factor 1) | < 20% | 20–40% | > 40% |

---

## Time Series

### Stationarity
- Always test for stationarity before running regressions (ADF, KPSS)
- Non-stationary series: difference or cointegrate; do not regress levels directly
- Document the order of integration
- If two non-stationary I(1) series are regressed without a cointegration test, the regression is likely spurious regardless of the reported R² or p-value

### Autocorrelation
- Use Newey-West (HAC) standard errors for financial time series by default
- Report Durbin-Watson or Ljung-Box statistics
- ARIMA residuals must be white noise before accepting the model

### Look-ahead bias

The most common and damaging error in financial analysis.

**Finance — mandatory checks:**
- All signals must use only data available at the decision point
- **Index composition:** Using current S&P 500 or STOXX 600 constituents as the historical universe applies survivorship + look-ahead simultaneously — ~50% of 2004 constituents are not in the current index. Use point-in-time constituent files.
- **Compustat / accounting data:** Fiscal period ends (e.g., 31 Dec) do not equal announcement dates. Earnings are typically announced 30-60 days after period end. Using fiscal-period values before the announcement date is look-ahead biased.
- **Analyst estimates:** Consensus files must use vintage (date-stamped) estimates, not current consensus applied retroactively.
- **Corporate actions:** Splits and dividends must be adjusted as of the date they occurred, not pre-adjusted throughout history.

**Biotech — mandatory checks:**
- Trial outcomes must not enter analysis before the trial readout date (primary completion date in ClinicalTrials.gov)
- Regulatory decisions (FDA approval, rejection) must use the PDUFA date or action date, not the announcement date on press releases (which can precede the regulatory letter by hours)
- Publication dates: a result published in NEJM in 2022 from a trial that completed in 2020 must be dated to the completion date if it is being used as an outcome in a predictive model

### Survivorship bias

Any analysis of a universe of stocks, funds, or drugs must account for survivorship.

**Finance:**
- Yahoo Finance and most free equity APIs do not return delisted tickers. A backtest using only currently-listed stocks is survivorship biased for any lookback period > 5 years.
- Bias direction: positive. Strategies built on surviving stocks appear better than they would have been, because the universe excluded the losers.
- Approximate magnitude in US equities: ~30-40 failures per year from S&P 500 over a 20-year period. Not negligible.

**Biotech/clinical:**
- ClinicalTrials.gov mandatory registration (US): 2007. Pre-2007 data is incomplete and skewed toward registered (typically positive or commercially significant) trials.
- Phase 1/2 registration is less consistent than Phase 3. Termination rates for Phase 1/2 are likely underestimated in registry-based analyses.
- Published literature overrepresents positive results. Any literature-based synthesis must weight by evidence quality (RCT > observational; NEJM > low-impact journal) and note publication bias explicitly.

---

## Regression

### Required diagnostics
- Heteroskedasticity (Breusch-Pagan or White test)
- Multicollinearity (VIF > 10 is a red flag)
- Influential observations (Cook's distance)
- Residual normality (for inference, not prediction)

### Overfitting
- Number of parameters vs. observations: minimum 10:1 ratio recommended
- Out-of-sample R² must be reported alongside in-sample R²
- Prefer parsimony: a simple model that generalises beats a complex model that fits
- Biotech: Phase 2 sample sizes averaging n < 50 with > 4 estimated parameters produce unreliable estimates — flag and widen CIs explicitly

---

## Backtesting

### Non-negotiable requirements
- Walk-forward or expanding window validation (not a single in-sample backtest)
- Transaction costs included: bid-ask spread + commission + market impact estimate
- Slippage modelled for illiquid instruments
- Drawdown and maximum drawdown reported alongside returns
- Sharpe ratio computed with correct annualisation (√252 for daily, √52 for weekly)

### Transaction cost benchmarks

| Universe | Typical round-trip cost | Notes |
|----------|------------------------|-------|
| US large-cap (S&P 500) | 5–15 bps | Highly liquid; institutional impact varies |
| EU large-cap (STOXX 50) | 10–20 bps | Slightly wider than US |
| EU mid-cap | 20–50 bps | MiFID II fragmentation; spreads vary by venue |
| EU small-cap (< €500M) | 50–150 bps | Material; can eliminate a modest momentum signal |
| Biotech small-cap | 80–200 bps | Event-driven volatility; spreads widen around catalysts |

For any strategy in EU small-cap healthcare: model at least 80 bps round-trip. A gross Sharpe of 0.6 will likely fall to < 0.3 net. Document this explicitly.

### Red flags
- Sharpe ratio > 3 in-sample with no out-of-sample validation: almost certainly overfit
- No transaction costs
- Trading on close prices when signal is generated after close
- Strategy that requires perfect foresight in any period

---

## Correlation and Dependence

### Pearson vs. Spearman

Pearson correlation assumes approximately linear relationships and is sensitive to outliers. In financial data:
- **Use Pearson** when both series are approximately normally distributed with no extreme outliers
- **Use Spearman** for equity returns (fat-tailed), factor rankings, biotech event returns, or any data with outliers. Spearman is robust to the outlier structure of financial data.
- Report both when the domain is finance or biotech. If Pearson >> Spearman, the Pearson result is being driven by outliers — report Spearman as primary.

### Distance correlation (DC)
- DC = 0 implies statistical independence (Pearson = 0 does not)
- Use DC alongside Pearson/Spearman for a complete picture
- Especially important for fat-tailed financial data and non-linear biomarker relationships

### Spurious correlation
- High correlation between non-stationary series is meaningless without cointegration
- Check whether correlation is driven by a common third factor
- Report correlation over different subperiods as a stability check

---

## Causal Claims

Correlation is not causation. Causal language (`causes`, `drives`, `leads to`) requires:

| Method | Appropriate for | Biotech example | Finance example |
|--------|----------------|-----------------|----------------|
| Granger causality | Time series lead-lag | Sentiment leads Phase 3 starts | CPI Granger-causes yield curve slope |
| Instrumental variables (IV) | Cross-sectional endogeneity | Random trial assignment as IV for treatment intensity | Plausibly exogenous regulatory shock |
| Diff-in-differences (DiD) | Panel with treatment/control | Drug approval in one indication vs. adjacent indication not yet approved | Policy change affecting one sector |
| Regression discontinuity (RDD) | Threshold-based assignment | Phase 2 HR just above/below conventional approval threshold | Index inclusion cutoff |
| Natural experiment | Quasi-random variation | Patent cliff date as exogenous shock to pipeline investment | Fed announcement surprise |

Without one of these, use hedged language: `associated with`, `predictive of`, `correlated with`.

Note on Granger causality: a significant Granger F-test means X contains information that helps predict Y in a linear VAR framework. It does not establish structural causation. If X Granger-causes Y, check whether the reverse is also true; bidirectional Granger causality is common and makes causal language inappropriate for either direction.

---

## Confidence Scoring Rubric

Used by `findings-evaluator` agent. Score the overall finding 1-10.

| Score | Interpretation | Action |
|-------|---------------|--------|
| 9-10 | Replicated, out-of-sample validated, large effect, clean data | PROCEED |
| 7-8 | Strong evidence; out-of-sample or walk-forward confirmed | PROCEED |
| 5-6 | Moderate evidence; in-sample with robustness checks | PROCEED with caveats |
| 3-4 | Weak; single-sample, marginal effect, or unresolved confounds | REFINE if iteration < 3 |
| 1-2 | Inconclusive or likely spurious | TERMINATE_WITH_NULL |

Scoring factors:
- Data quality and provenance (+/-)
- Sample size relative to model complexity (+)
- Out-of-sample or walk-forward validation (+2)
- Robustness across subperiods and specifications (+1)
- Look-ahead or survivorship bias: WARN -2, FAIL -4
- Number of unreported tests / data snooping (-1 to -2)
- Effect size relative to domain benchmarks (+/-)
- FATAL critique challenge unresolved: -2
