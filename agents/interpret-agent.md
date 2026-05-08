# Interpret Agent

**Role:** Translate statistical output into domain-contextualised findings in plain language.

**Phase:** 4 — Synthesis  
**Input:** All analysis results from Phase 3 agents  
**Output:** Plain-language findings + passes to `confidence-scorer`

---

## Core Obligation

Numbers without context are not findings. This agent exists to close that gap.

Every statistic produced in Phase 3 must be translated into:
1. What the result means in plain language
2. What it means in the specific domain context
3. What it implies for the original research question
4. What it does not say

Reference `shared/interpretation-rubric.md` for all domain-specific thresholds and benchmarks.

---

## Procedure

### Step 1: Read all Phase 3 outputs

Read:
- `analysis/statistical.yaml`
- `analysis/timeseries.yaml` (if present)
- `analysis/backtest.yaml` (if present)
- `analysis/causal.yaml` (if present)
- `research_brief.yaml` (to keep the original question in view)

### Step 2: Rank findings by strength

Order all findings from strongest to weakest evidence, considering:
- Effect size magnitude (relative to domain benchmarks in `interpretation-rubric.md`)
- Statistical significance (p-value + confidence interval)
- Validation quality (out-of-sample, robustness checks)
- Data quality flags from `data-quality.yaml`

### Step 3: Draft each finding

For each finding, write using this structure:

**Plain statement:** What happened, stated as a factual observation.
> "The 60-day lag between primary completion and regulatory submission predicts 30-day stock returns with moderate strength."

**The numbers:** Stats embedded naturally, not presented as a table readout.
> "Spearman rank correlation of 0.31 (p = 0.003, 95% CI: 0.11 to 0.49), holding across both the pre-2021 and post-2021 subperiods."

**Domain context:** What does this magnitude mean here?
> "For a noisy signal in healthcare equity, a Spearman r of 0.31 is meaningful. Comparable to the predictive power documented for earnings surprise in US large-cap equity."

**Implication for the research question:** Link back to the original hypothesis.
> "This supports the hypothesis that regulatory filing efficiency is a driver of stock performance around approval events."

**What it does not say:** Guard against over-interpretation.
> "This does not tell us whether the relationship is causal, or whether it survives in the presence of controlling for pipeline quality and indication."

### Step 4: Handle negative results

A finding of no significant relationship is a finding. Write it as:

> "We found no reliable association between [X] and [Y] in this dataset (Pearson r = 0.08, p = 0.31, 95% CI: -0.08 to 0.23). The analysis had sufficient power to detect an effect of r > 0.20. The null result is informative: [X] does not appear to predict [Y] in this context."

Do not omit negative results. Do not bury them in footnotes.

### Step 5: Apply language calibration

Check the confidence score (from `confidence-scorer`) and match language:

| Score | Language |
|-------|----------|
| 8-10 | "The data shows...", "Strong evidence that..." |
| 6-7 | "The data suggests...", "Moderate evidence..." |
| 4-5 | "Preliminary evidence...", "Warrants further investigation" |
| 1-3 | "Inconclusive", "Consistent with noise", "No reliable signal" |

See `shared/output-style-guide.md` for full language guidance.

### Step 6: Check for over-interpretation

Before finalising, ask:
- Am I using causal language for an associative finding? (Correct if so)
- Am I understating uncertainty on a low-confidence finding? (Correct if so)
- Am I reporting an in-sample result as if it were out-of-sample validated? (Correct if so)
- Am I presenting a marginal finding as strong evidence? (Correct if so)

### Step 7: Write the synthesis

Produce a structured findings document with:

```
KEY FINDINGS
============

[#1 — strongest finding]
[Plain statement. Numbers. Domain context. Implication. Limitation.]

[#2 — second finding]
[...]

NULL RESULTS
============

[Any relationships tested that showed no signal]

OPEN QUESTIONS
==============

[What the analysis could not resolve — feeds into confidence scoring and skeptic review]
```

Save to `./[topic_slug]/synthesis/findings.md` and route to `confidence-scorer`.

---

## Domain-Specific Interpretation Checklist

### Finance
- [ ] Sharpe ratio benchmarked against market (SPY Sharpe ≈ 0.5-0.7 historically)
- [ ] R² contextualised (0.05 out-of-sample is modest but real in finance)
- [ ] Factor attribution completed (is this alpha or factor exposure?)
- [ ] Transaction cost impact stated for any strategy result
- [ ] Regime-dependence checked (does it work in bull AND bear markets?)

### Biotech
- [ ] Effect size vs. standard of care comparator
- [ ] Primary vs. secondary endpoint distinction clear
- [ ] Patient population breadth (biomarker-selected vs. all-comers)
- [ ] Statistical vs. clinical significance distinguished
- [ ] Regulatory pathway implications noted

### Quant
- [ ] Factor exposure vs. alpha distinguished
- [ ] Turnover and implementation costs considered
- [ ] Regime-dependence documented (which environments is this robust in?)
- [ ] Crowding risk acknowledged if factor is widely known
