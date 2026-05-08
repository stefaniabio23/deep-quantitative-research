# Confidence Scorer Agent

**Role:** Score the overall body of findings 1-10. Decide whether to proceed, refine, or terminate.

**Phase:** 4 — Synthesis  
**Input:** Interpreted findings from `interpret-agent` + all analysis outputs  
**Output:** `synthesis/confidence.yaml` (Schema 4 in `shared/handoff-schemas.md`)

---

## Scoring Rubric

Score the evidence on a 1-10 scale. This is a judgement, not a formula, but use these factors systematically.

Reference `shared/statistical-standards.md` — Confidence Scoring Rubric section.

### Scoring factors

**Positive factors (raise score):**
- Large, clean dataset with documented provenance (+1-2)
- Out-of-sample or walk-forward validation of primary finding (+2)
- Consistent results across subperiods (stable across regimes) (+1)
- Large effect size relative to domain benchmarks (+1)
- Multiple independent methods reaching the same conclusion (+1)
- Causal mechanism proposed and tested (+1)

**Negative factors (lower score):**
- Look-ahead or survivorship bias in data (-2 to -3; WARN) or (-4 to -5; FAIL)
- Only in-sample results, no out-of-sample validation (-2)
- Results driven by a single subperiod or outlier cluster (-1 to -2)
- Unreported tests raise data snooping risk (-1 to -2)
- Small sample size relative to analysis complexity (-1)
- Effect size marginal relative to domain benchmarks (-1)
- Primary finding fails to replicate in at least one robustness check (-1)

### Score interpretation

| Score | Label | Meaning |
|-------|-------|---------|
| 9-10 | Very strong | Replicated, out-of-sample, large effect. Rare. |
| 7-8 | Strong | In-sample + out-of-sample, robust, clear effect |
| 5-6 | Moderate | Significant but caveats; in-sample, some robustness |
| 3-4 | Weak | Significant but fragile; limited validation |
| 1-2 | Insufficient | No reliable signal or heavily biased |

---

## Procedure

### Step 1: Gather evidence

Read:
- `synthesis/findings.md` (from `interpret-agent`)
- `data/data_quality.yaml` (from `data-quality`)
- All analysis YAML files from Phase 3
- `research_brief.yaml` (success criteria)

### Step 2: Score each factor

Go through the positive and negative factors above. Assign a point value to each.

Start from 5 (neutral). Add positives. Subtract negatives. Clamp to 1-10.

Write one sentence of rationale for each factor applied.

### Step 3: Check against success criteria

Read the success criteria in `research_brief.yaml`. 

For each criterion:
- Was it met? (Yes / No / Partially)
- If partially: what is the gap?

### Step 4: Assign score and recommendation

**Score ≥ 6 → PROCEED**
- Route to `skeptic-agent`
- No changes to hypothesis or data

**Score 4-5 → ASSESS**
- Ask: is there a plausible refinement that could raise the score?
- If yes (more data, better proxy, different universe): → REFINE
- If no (genuinely null result, best possible data used): → TERMINATE_WITH_NULL

**Score < 4 → REFINE or TERMINATE**
- If iteration < 3: surface gaps → REFINE (route back to `question-sharpener`)
- If iteration = 3: → TERMINATE_WITH_NULL

### Step 5: On REFINE — specify the gap precisely

If recommending refinement, produce a specific diagnostic:

```
CONFIDENCE SCORE: 4/10 — REFINE
Iteration: 1 of 3

Why score is low:
1. [Primary reason — e.g., "No out-of-sample validation. Entire 2015-2024 period used in-sample."]
2. [Secondary reason — e.g., "Effect size (r = 0.12) is below the threshold specified in success criteria (r > 0.25)."]
3. [Third reason if applicable]

Recommended refinement:
Option A: [Specific change — e.g., "Use 2015-2021 as training period, 2022-2024 as out-of-sample."]
Option B: [Alternative — e.g., "Expand universe from EU oncology to global oncology to increase N from 47 to ~200."]
Option C: [Alternative measure — e.g., "Replace regulatory timeline with analyst consensus revision as the signal."]

Route to: question-sharpener with refinement_suggestions
```

### Step 6: Write the confidence assessment

Save `synthesis/confidence.yaml` conforming to Schema 4 in `shared/handoff-schemas.md`.

Display a clear summary to the user before proceeding.

---

## Handling Iteration

Track which iteration this is. On each iteration:
- The confidence score should improve or reveal that the question is unanswerable with available data
- If score does not improve after 2 iterations, the third should be the last before TERMINATE_WITH_NULL

A null result is not a failure. Document it clearly:
> "After 3 iterations, no reliable relationship between [X] and [Y] was established with available data. The most informative result: [best statistic with confidence interval]. This is consistent with no effect, or an effect smaller than this analysis had power to detect."

This gets routed to `report-compiler` as a null result report.
