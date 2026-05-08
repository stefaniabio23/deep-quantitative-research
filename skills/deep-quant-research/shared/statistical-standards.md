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
- Apply Bonferroni, Benjamini-Hochberg, or equivalent correction when running more than one test on the same dataset
- Report the number of tests considered, not just the ones that passed
- Flag any analysis that involved selecting the "best" specification post-hoc

### Threshold conventions by domain
| Domain | Primary standard | Notes |
|--------|-----------------|-------|
| Finance | p < 0.05, but Sharpe > 1.0 out-of-sample is more meaningful | Statistical significance is necessary but not sufficient |
| Biotech/clinical | p < 0.05 (Phase II), p < 0.01 (Phase III) | FDA standard; also check clinical significance |
| Quant/factor | p < 0.05 with Newey-West SE | Must account for autocorrelation |

---

## Time Series

### Stationarity
- Always test for stationarity before running regressions (ADF, KPSS)
- Non-stationary series: difference or cointegrate; do not regress levels directly
- Document the order of integration

### Autocorrelation
- Use Newey-West (HAC) standard errors for financial time series by default
- Report Durbin-Watson or Ljung-Box statistics
- ARIMA residuals must be white noise before accepting the model

### Look-ahead bias
This is the most common and damaging error in financial analysis. Mandatory checks:
- All signals must use only data available at the decision point
- Index constituents must be point-in-time (not current composition)
- Earnings data must use announcement dates, not period-end dates
- Analyst estimates must use vintage data where possible

### Survivorship bias
- Any analysis of a universe of stocks, funds, or drugs must account for survivorship
- Document whether the dataset includes delisted stocks, failed drugs, closed funds
- If survivorship-biased data is used, apply an explicit discount to results

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

---

## Backtesting

### Non-negotiable requirements
- Walk-forward or expanding window validation (not a single in-sample backtest)
- Transaction costs included (bid-ask spread + commission + market impact estimate)
- Slippage modelled for illiquid instruments
- Drawdown and maximum drawdown reported alongside returns
- Sharpe ratio computed with correct annualisation (√252 for daily, √52 for weekly)

### Red flags
- Sharpe ratio > 3 in-sample with no out-of-sample validation (overfit)
- No transaction costs
- Trading on close prices when signal is generated after close
- Strategy that requires perfect foresight in any period

---

## Correlation and Dependence

### Pearson correlation limitations
- Pearson measures linear dependence only
- Always supplement with Spearman (rank) correlation for non-linear relationships
- Report whether correlation is stable across subperiods (rolling correlation)

### Distance correlation (DC)
- DC = 0 implies statistical independence (Pearson = 0 does not)
- Use DC alongside Pearson/Spearman for a complete picture
- Especially important for fat-tailed financial data

### Spurious correlation
- High correlation between non-stationary series is meaningless without cointegration
- Check whether correlation is driven by a common third factor
- Report correlation over different subperiods as a stability check

---

## Causal Claims

Correlation is not causation. Causal language (`causes`, `drives`, `leads to`) requires:

| Method | Appropriate for |
|--------|----------------|
| Granger causality | Time series: does X help predict Y? (Not true causality, but useful) |
| Instrumental variables (IV) | Cross-sectional: isolate exogenous variation |
| Diff-in-differences (DiD) | Panel: treatment vs. control group changes |
| Regression discontinuity (RDD) | Threshold-based assignment |
| Natural experiment | Quasi-random variation in the real world |

Without one of these, use hedged language: `associated with`, `predictive of`, `correlated with`.

---

## Confidence Scoring Rubric

Used by `confidence-scorer` agent. Score the overall finding 1-10.

| Score | Interpretation | Action |
|-------|---------------|--------|
| 8-10 | Strong, replicable finding with out-of-sample validation | Proceed to skeptic review |
| 6-7 | Moderate evidence, in-sample with robustness checks | Proceed with caveats |
| 4-5 | Weak or single-sample evidence | Refine hypothesis, seek more data |
| 1-3 | Inconclusive or likely spurious | Do not report as finding; document as negative result |

Scoring factors:
- Data quality and provenance (+/-)
- Sample size (+)
- Out-of-sample validation (+)
- Robustness across subperiods (+)
- Look-ahead or survivorship bias (--)
- Number of unreported tests (--)
- Effect size relative to noise (+)
