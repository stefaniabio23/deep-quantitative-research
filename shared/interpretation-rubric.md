# Interpretation Rubric

Used by the `interpret-agent` to translate raw statistical output into findings.
The goal is domain-contextualised meaning, not a restatement of numbers.

---

## Core Obligation

A finding is not "the correlation is 0.43 (p = 0.002)".
A finding is "X is moderately predictive of Y, with the relationship strongest in [subperiod/subgroup], explaining roughly one-fifth of the variation."

The interpret-agent takes numbers and produces meaning. Every statistic must be contextualised against:
1. What magnitude is meaningful in this domain
2. How this compares to known benchmarks or prior research
3. What it implies for the original research question
4. What it does not say

---

## Finance: Interpreting Results

### Return prediction
| R² (in-sample) | Interpretation |
|---------------|----------------|
| > 0.50 | Exceptional; verify for look-ahead bias before trusting |
| 0.20-0.50 | Strong predictive signal |
| 0.05-0.20 | Modest but potentially tradeable |
| 0.01-0.05 | Weak; meaningful only at scale |
| < 0.01 | Economically negligible |

Out-of-sample R² degrades significantly from in-sample. A model with in-sample R² of 0.15 producing out-of-sample R² of 0.05 is performing normally, not poorly.

### Sharpe ratio benchmarks
| Sharpe (annualised) | Context |
|--------------------|---------|
| > 2.0 | Exceptional; rare in live trading; scrutinise for backtest bias |
| 1.0-2.0 | Strong; consistent with top-quartile hedge fund returns |
| 0.5-1.0 | Good; comparable to equity market long-run Sharpe |
| 0.0-0.5 | Marginal; may not survive transaction costs and slippage |
| < 0.0 | Loss-generating |

### Correlation in finance
- Pearson r > 0.5: strong for financial data (financial variables are noisy)
- Pearson r = 0.2-0.5: moderate; worth investigating
- Pearson r < 0.2: weak; may not be actionable unless the effect is consistent
- Always check rolling correlations; financial correlations are regime-dependent

### Factor analysis
- Report factor exposures (loadings) alongside return attribution
- A high loading on a known factor (Value, Momentum, Quality) is not alpha
- True alpha is return unexplained by standard factor models (Fama-French 5-factor minimum)
- Distinguish between strategy gross returns and factor-adjusted returns

### Lag analysis interpretation
- A statistically significant N-day lag relationship: describe the lead-lag in economic terms ("X tends to move N trading days before Y")
- Compute the implied trading window: how long is the predictive window, and is it actionable given execution constraints?
- Check whether the lag is stable across subperiods or concentrated in one regime

### KPI-to-price relationships
- Specify whether this is a level, change, or surprise relationship
- Distinguish between contemporaneous (same period) and predictive (leads price) relationships
- Report R² separately for different market regimes (bull/bear, high/low volatility)
- Flag whether the relationship is stronger among consensus-surprise observations

---

## Biotech/Clinical: Interpreting Results

### Clinical trial signal interpretation
| Endpoint | Meaningful threshold | Notes |
|----------|---------------------|-------|
| Overall survival (OS) | HR < 0.80 | 20%+ reduction in hazard |
| Progression-free survival (PFS) | HR < 0.75 | PFS does not always predict OS |
| ORR | Absolute improvement > 15-20pp | Context-dependent; compare vs. SoC |
| p-value | < 0.05 (Phase 2), < 0.01 (Phase 3) | One-sided vs. two-sided matters |

When interpreting trial data, always ask:
- What is the standard of care (SoC) comparator?
- Is this a biomarker-selected population (narrower applicability)?
- Are primary and secondary endpoints directionally consistent?
- What is the safety profile relative to efficacy signal?

### Drug-to-market signal interpretation
- Phase 2 to Phase 3 success rate (all oncology): ~40% historically; adjust by mechanism/target
- Phase 3 to approval: ~60% for oncology; higher for rare disease (expedited pathways)
- Regulatory timeline: typical 6-12 months FDA PDUFA review; EMA ~13 months
- Label breadth: narrow label (specific biomarker) vs. broad label (all-comers) has different commercial implications

### Genomic and molecular data
- Variant allele frequency (VAF): clinical significance depends on context and hotspot status
- Pathway enrichment (GSEA/ORA): report both statistical significance and effect size (NES for GSEA)
- Protein-protein interaction: network centrality of a target is evidence of biological importance, not therapeutic tractability
- Expression data: always report fold change alongside p-value; fold change of 1.5× is often biologically meaningful even if p > 0.05 at small N

---

## Quant/Macro: Interpreting Results

### Factor analysis
- PCA: report cumulative variance explained; first 3 factors typically explain 60-80% of cross-sectional variance in equity returns
- Factor loadings: distinguish between stable (structural) and time-varying (cyclical) loadings
- Eigenvalue > 1 rule: use as a starting point, not a hard rule; scree plot preferred

### Dependence structures
- Pearson + Spearman + Distance Correlation should broadly agree if the relationship is linear; divergence suggests non-linearity
- Tail dependence (copula): financial crises drive correlation spikes; lower-tail dependence is more relevant than upper-tail for risk management
- Regime-conditioning: report whether correlations change materially in high-volatility or stress regimes

### Macro relationships
- Granger causality: a significant Granger F-test means X contains information that helps predict Y; it does not mean X causes Y in a structural sense
- Cointegration: long-run equilibrium relationship; deviations are mean-reverting; the speed of adjustment (α in VECM) matters for timing
- Structural breaks: macro relationships often break around major regime changes (2008, 2020, major policy shifts); test for breaks before trusting long-sample results

---

## Negative Results

A negative result (no significant relationship found) is a finding. Report it as:
- "We found no evidence of [X relationship] in this dataset, period, and specification"
- Distinguish between "no effect" and "insufficient power to detect an effect"
- Report the minimum effect size that the analysis would have been powered to detect
- A well-powered null result is informative; a low-powered null result is not

---

## Language for Different Confidence Levels

| Confidence score | Appropriate language |
|-----------------|---------------------|
| 8-10 | "The data shows...", "X predicts Y...", "There is strong evidence that..." |
| 6-7 | "The data suggests...", "There is moderate evidence...", "X appears to predict Y..." |
| 4-5 | "There is tentative evidence...", "Preliminary analysis suggests...", "This warrants further investigation" |
| 1-3 | "The analysis is inconclusive", "No reliable signal detected", "Results are consistent with noise" |

Never use high-confidence language for a score below 6. Never use low-confidence language for a score above 7.
