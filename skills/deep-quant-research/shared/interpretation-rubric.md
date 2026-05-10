# Interpretation Rubric

Used by the `findings-evaluator` to translate raw statistical output into findings.
The goal is domain-contextualised meaning, not a restatement of numbers.

---

## Core Obligation

A finding is not "the correlation is 0.43 (p = 0.002)".
A finding is "X is moderately predictive of Y, with the relationship strongest in [subperiod/subgroup], explaining roughly one-fifth of the variation."

Every statistic must be contextualised against:
1. What magnitude is meaningful in this domain
2. How this compares to known benchmarks or prior research
3. What it implies for the original research question
4. What it does not say

### Bad vs. good interpretation (calibration reference)

**Bad (just restates numbers):**
> "The Spearman correlation between days-to-filing and 30-day returns is 0.31 (p = 0.003). This is statistically significant."

**Good (produces meaning):**
> "Regulatory filing speed is a moderate predictor of post-approval equity returns among European oncology companies (Spearman r = 0.31, p = 0.003, n = 47). In an equity signal context, r = 0.31 places this in the upper quartile of documented event-study predictors for this universe size — comparable to, for example, documented analyst upgrade effects in small-cap healthcare. The relationship is economically modest: a one-standard-deviation faster filing predicts roughly 3.4 percentage points of additional 30-day return. This suggests filing speed is a partial proxy for something else — likely drug quality — rather than an independent signal. The finding does not imply that filing speed is tradeable without additional evidence on what is driving it."

**Bad (overclaims from biotech data):**
> "Biomarker-selected trials succeed more. Companies should use biomarker selection."

**Good:**
> "Biomarker-selected Phase 2 oncology trials achieved Phase 2→3 transition at 41% versus 27% for unselected trials in this dataset (OR 1.88, 95% CI 1.24–2.85, p = 0.003, n = 312 trials, 2010–2024). The 14-percentage-point gap is consistent with the directional finding in Sargent et al. (2013) but is larger, which may reflect the post-2015 maturation of precision oncology selection practices. This does not establish whether the improvement stems from patient matching itself or from the tendency to apply biomarker strategies to more biologically validated targets — a partially confounded comparison."

---

## Finance: Interpreting Results

### Return prediction

| R² (in-sample) | Interpretation |
|---------------|----------------|
| > 0.50 | Exceptional; verify for look-ahead bias before trusting |
| 0.20–0.50 | Strong predictive signal |
| 0.05–0.20 | Modest but potentially tradeable |
| 0.01–0.05 | Weak; meaningful only at scale |
| < 0.01 | Economically negligible |

Out-of-sample R² degrades significantly from in-sample. A model with in-sample R² of 0.15 producing out-of-sample R² of 0.05 is performing normally. If out-of-sample R² turns negative, the model is overfitted to noise.

### Sharpe ratio benchmarks

| Sharpe (annualised, net of costs) | Context |
|----------------------------------|---------|
| > 2.0 | Exceptional; rare in live trading; scrutinise for backtest artefacts |
| 1.0–2.0 | Strong; consistent with top-quartile systematic strategy |
| 0.5–1.0 | Good; comparable to equity market long-run Sharpe |
| 0.2–0.5 | Marginal; may not survive full transaction costs and slippage |
| < 0.2 | Effectively zero net of realistic costs |

For EU small-cap healthcare: apply at least 80 bps round-trip transaction cost assumption before reporting Sharpe. A gross Sharpe of 0.7 routinely becomes 0.2-0.3 net in this universe.

### Correlation in finance

- Spearman r > 0.30: strong for financial cross-sectional data; worth investigating
- Spearman r = 0.10–0.30: moderate; potentially informative; check stability
- Spearman r < 0.10: weak; not actionable; consistent with noise
- Always report both Pearson and Spearman. If Pearson > Spearman by more than 0.10, the Pearson is being pulled by outliers — use Spearman as the primary result.
- Rolling correlations are essential: a correlation that is 0.30 on average but alternates between 0.60 and -0.10 in alternate years is not a stable signal.

### Factor analysis

- Report factor exposures (loadings) alongside return attribution
- A high loading on a known factor (Value, Momentum, Quality) is not alpha
- True alpha is return unexplained by standard factor models (Fama-French 5-factor minimum in equities)
- Distinguish gross and factor-adjusted returns explicitly

### Lag analysis

- A statistically significant N-day lag: describe the economic interpretation ("X tends to lead Y by N trading days")
- Compute the implied trading window: is the predictive window long enough to be actionable given execution constraints and trading frequency?
- Check lag stability across subperiods — a lag that shifts from 5 days to 30 days between halves of the sample is not a reliable trading signal

### KPI-to-price relationships

- Specify whether this is a level, change, or surprise relationship (surprise vs. consensus is usually the most informative)
- Distinguish contemporaneous (same period) from predictive (leads price by 1+ period) relationships
- Report R² separately for different market regimes where feasible
- "Statistical significance" in a KPI-to-price regression with 5+ years of quarterly data is a low bar — 20 observations is barely enough to detect r > 0.40

---

## Biotech/Clinical: Interpreting Results

### Hazard ratio interpretation

Always report the CI alongside the HR. A HR of 0.75 with 95% CI [0.55, 1.02] crosses 1.0 — the trial does not establish OS benefit regardless of the point estimate.

CI width guidance:
- CI width > 0.5 on the log-HR scale (roughly, upper/lower ratio > 1.6): the estimate is imprecise; describe as "consistent with benefit but inconclusive"
- CI that excludes 1.0 on both sides at p < 0.01: strong evidence of effect
- CI that includes 1.0 with upper bound close to 1.0 (e.g., [0.82, 0.98]): significant but marginal; clinical relevance depends on indication

| Endpoint | Meaningful threshold | Notes |
|----------|---------------------|-------|
| Overall survival (OS) | HR < 0.80 | 20%+ reduction in hazard |
| Progression-free survival (PFS) | HR < 0.75 | PFS does not reliably predict OS benefit |
| ORR | Absolute improvement > 15–20pp vs. SoC | Context-dependent; lower bar in refractory/late-line settings |
| p-value | < 0.05 (Phase 2), < 0.01 (Phase 3) | One-sided vs. two-sided matters; specify |

### Phase transition benchmarks by indication

Use these as the reference class when interpreting Phase 2→3 or Phase 3→approval results.

| Indication | Ph2→Ph3 (overall) | Notes |
|------------|-------------------|-------|
| Oncology (all) | ~35–40% | BIO 2016; Hay et al. 2014 |
| Haematology | ~45% | Higher; often biomarker-selected |
| Solid tumour (unselected) | ~25–30% | Lower; harder target biology |
| Rare/orphan disease | ~55–60% | Expedited pathways; smaller trials |
| CNS | ~15–20% | Notoriously low; translation failure |
| Infectious disease | ~55–65% | Higher; established endpoints |

A Phase 2→3 rate below 25% in oncology warrants scrutiny — either a difficult indication, an early-stage pipeline, or a dataset with incomplete coverage.

### Drug-to-market signal

- Phase 3 to approval: ~60% oncology; higher (~75–80%) for rare disease with breakthrough/orphan designation
- Regulatory timeline: FDA PDUFA review 6–12 months; EMA ~13 months standard, faster with PRIME designation
- Label breadth: narrow (specific biomarker subgroup) vs. broad (all-comers) has large commercial implication beyond the statistical result

### Publication bias adjustment

Literature-based analyses must account for publication bias explicitly. Positive results publish at ~3× the rate of negative results in high-impact oncology journals.

Adjustments to apply:
- Down-weight single-arm Phase 2 results with no comparator arm (no way to estimate true effect vs. SoC)
- Weight by evidence hierarchy: RCT > well-controlled observational > single-arm
- Weight by publication venue: NEJM/Lancet/JCO > lower-impact journals, particularly for positive claims
- For meta-analyses: report funnel plot asymmetry and Egger's test; a p < 0.05 on Egger's suggests meaningful publication bias

When a literature synthesis produces a strong positive result without accounting for publication bias, label it as potentially overstated.

### Genomic and molecular data

- VAF (variant allele frequency): clinical significance depends on context, hotspot status, and tumor fraction — do not interpret in isolation
- Pathway enrichment (GSEA/ORA): report NES (normalised enrichment score) alongside p-value; NES > 1.5 is typically considered meaningful for GSEA
- Network centrality: a highly connected target in STRING-DB is evidence of biological importance, not therapeutic tractability — the two are weakly correlated in oncology
- Expression: always report fold change alongside p-value; 1.5× fold change can be biologically meaningful even if p > 0.05 at small N; conversely, 1.1× fold change with p < 0.001 in a large dataset is usually not clinically relevant

---

## Quant/Macro: Interpreting Results

### Factor analysis

- PCA: report cumulative variance explained; first 3 factors typically explain 60–80% of cross-sectional variance in equity returns
- Factor loadings: distinguish stable (structural) from time-varying (cyclical) loadings using rolling windows
- Eigenvalue > 1 rule: use as a starting point, not a hard rule; scree plot preferred

### Dependence structures

- Pearson + Spearman + Distance Correlation should broadly agree if the relationship is linear; divergence suggests non-linearity — investigate the form before modelling
- Tail dependence: financial crises drive correlation spikes; lower-tail dependence is more relevant than upper-tail for risk management
- Regime-conditioning: correlations that change materially in high-volatility regimes are unreliable as structural features — report regime-conditional values

### Macro relationships

- Granger causality: significant Granger F-test means X contains predictive information about Y in a linear model; it does not mean X causes Y structurally. Bidirectional Granger causality makes directional claims inappropriate.
- Cointegration: long-run equilibrium relationship; the speed of adjustment (α in VECM) matters for timing claims
- Structural breaks: macro relationships frequently break around major regime changes (2008, 2020, major policy shifts). Test for breaks (Chow test or CUSUM) before trusting long-sample relationships. A 1970–2024 result for inflation regimes may be driven by 1973–1982 alone.

---

## Negative Results

A negative result is a finding. Report it explicitly with:
- "We found no reliable evidence of [X relationship] in this dataset, period, and specification"
- The distinction between "no effect" and "insufficient power to detect an effect" — different interpretations with different implications
- The minimum detectable effect at current sample size (power calculation)
- A well-powered null is informative; a low-powered null is not

**Example:**
> "No association was found between PD-L1 expression level (continuous) and ORR in this cohort (Spearman r = 0.09, p = 0.41, n = 88 patients, 95% CI: -0.12 to 0.29). The analysis had 80% power to detect r ≥ 0.22. The null is informative at r ≥ 0.22 but cannot rule out smaller effects. Given that PD-L1 is an approved biomarker in this indication, the absence of a detectable continuous relationship may reflect threshold effects (binary high/low cut-off performs better than continuous score) rather than absence of a biological relationship."

---

## Language for Different Confidence Levels

| Confidence score | Appropriate language |
|-----------------|---------------------|
| 8-10 | "The data shows...", "X predicts Y...", "There is strong evidence that...", "Robust across..." |
| 6-7 | "The data suggests...", "Moderate evidence...", "X appears to predict Y..." |
| 4-5 | "Preliminary evidence...", "The pattern warrants further investigation", "Consistent with..." |
| 1-3 | "Inconclusive", "No reliable signal detected", "Results are consistent with noise" |

Never use high-confidence language (score < 6). Never use low-confidence language (score > 7).
