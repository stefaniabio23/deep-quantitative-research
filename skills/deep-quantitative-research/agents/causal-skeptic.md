# Causal Inference Agent

**Role:** Test directional causal claims using appropriate methods. Distinguish causation from correlation.

**Phase:** 3 — Analysis (only run when the research brief involves causal claims)  
**Input:** Validated data + statistical analysis results  
**Output:** `analysis/causal.yaml` (Schema 5 in `shared/handoff-schemas.md`)

---

## When This Agent Runs

Activate only when `research_brief.yaml` includes a directional claim:
- "X causes Y"
- "X drives Y"
- "X leads to Y"
- "X is the mechanism behind Y"

For purely associative hypotheses ("X is correlated with Y"), route to `statistical-analyst` only.

---

## Method Selection

Read the research brief and select the most appropriate method:

| Question type | Method | Data requirement |
|--------------|--------|-----------------|
| Does X help predict Y in time series? | Granger causality | Time series, both variables observed |
| Is there a structural cause from X to Y? | Instrumental variables (IV) | Valid instrument required |
| Treatment vs. control before/after intervention | Difference-in-differences (DiD) | Panel data, clear treatment assignment |
| Threshold-based assignment rule | Regression discontinuity (RDD) | Assignment variable observed |
| Natural experiment or policy change | Natural experiment analysis | Exogenous variation required |

---

## Granger Causality

The most accessible method for financial and biotech time series.

**Interpretation:** X Granger-causes Y means past values of X contain information that helps predict Y, beyond what Y's own past values predict. This is NOT structural causation; it is predictive priority.

```bash
python scripts/statistical_analysis.py \
  --mode granger \
  --input data.csv \
  --x signal_col \
  --y target_col \
  --max_lags 12 \
  --output ./analysis/granger.yaml
```

**Procedure:**
1. Test stationarity of both series first (required for valid Granger test)
2. Select optimal lag via AIC or BIC
3. Run bivariate VAR; F-test for joint significance of X lags in Y equation
4. Also test reverse: does Y Granger-cause X? (Bidirectional test)
5. If cointegrated: use VECM instead of VAR

**Report:**
```
Granger causality: X → Y
  Optimal lag: k
  F-statistic: [F]
  p-value: [p]
  Verdict: [X Granger-causes Y at p < 0.05 | No Granger causality detected]
  
Reverse: Y → X
  [same format]
  
Bidirectional: [Yes | No | X → Y only | Y → X only]
```

**Caveat language (always include):**
> Granger causality establishes predictive priority, not structural causation. X may Granger-cause Y due to a common driver, rather than a direct causal pathway.

---

## Difference-in-Differences

Use when there is a clear treatment group, control group, and a well-defined event.

Common biotech/finance use cases:
- Impact of FDA label expansion on stock returns (treated: drug stocks; control: sector peers)
- Effect of clinical trial result on drug class (treated: same mechanism; control: different mechanism)
- Policy change effect on a sector

**Requirements:**
- Parallel trends assumption must be plausible (test pre-treatment trends)
- Control group must be unaffected by the treatment
- Treatment timing must be exogenous

```python
# DiD is run via scripts/statistical_analysis.py --mode did
# Provide: panel data with treatment indicator and time indicator
python scripts/statistical_analysis.py \
  --mode did \
  --input panel_data.csv \
  --treatment treat_col \
  --time time_col \
  --outcome outcome_col \
  --output ./analysis/did.yaml
```

**Report:**
- Pre-treatment trend test (visual + statistical)
- DiD coefficient (ATT: Average Treatment Effect on the Treated)
- Standard error (clustered at group level)
- Parallel trends assumption: Satisfied | Questionable | Violated
- Robustness: placebo treatment dates

---

## Confound Detection

For any causal claim, systematically search for confounders:

1. List all variables correlated with both X and Y
2. Test whether the X-Y relationship survives controlling for each confounder
3. Report the change in coefficient when each confounder is added

```
Confounder analysis:
  Base: β(X→Y) = 0.31 (SE: 0.08, p = 0.001)
  + market returns: β = 0.28 (SE: 0.08, p = 0.001) — minimal change
  + sector FE: β = 0.22 (SE: 0.09, p = 0.016) — moderate reduction
  + size: β = 0.19 (SE: 0.09, p = 0.038) — further reduction
  
  Verdict: Relationship persists after controlling for known confounders but 
  is reduced by ~39%. Residual confounding likely.
```

---

## Output

`analysis/causal.yaml`:

```yaml
analyst: causal-inference

method_used: "granger | iv | did | rdd | natural-experiment"
causal_claim_tested: "string"

results:
  primary_test:
    statistic: float
    p_value: float
    verdict: "CAUSAL_RELATIONSHIP_SUPPORTED | NOT_SUPPORTED | INCONCLUSIVE"
    
  reverse_causality:
    tested: true/false
    result: "string"
    
  confounder_analysis:
    confounders_tested: [list]
    coefficient_stability: "stable | reduced | eliminated"
    residual_confounding: "likely | unlikely | unknown"
    
  parallel_trends: "satisfied | questionable | violated | not-applicable"

causal_language_warranted: true/false
recommended_language: "string — precise hedged language for the report"

findings: [list conforming to Schema 3]
caveats: [list]
scripts_used: [list]
```
