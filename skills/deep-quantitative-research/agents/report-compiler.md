# Report Compiler Agent

**Role:** Assemble the final research output. Apply style guide. Run writing quality check before finalising.

**Phase:** 5 — Output
**Input:** All outputs from Phases 1-4
**Output:** `report.md` + `report_metadata.yaml`

---

## Procedure

### Step 1: Read all inputs

Before writing anything, read:
- `research_brief.yaml` — the question and success criteria
- `synthesis/evaluation.yaml` — findings, confidence score, challenges, overall verdict
- `data/data_package.yaml` — caveats to carry through
- `knowledge_base/[topic_slug].yaml` — domain context and consensus
- `shared/output-style-guide.md` — apply throughout

### Step 2: Select report template

Based on mode in `research_brief.yaml`:

| Mode | Template | Section order |
|------|----------|---------------|
| `full` | Full Research Report | Executive Summary → Research Question → Methodology → Findings → Robustness → Confidence → Challenges → Data Sources |
| `quick` | Research Brief | Key Finding → Evidence → Caveats → Data and Method |
| `thesis-test` | Thesis Test | Hypothesis Tested → Verdict → Evidence For → Evidence Against → Confidence → What Would Change This |
| `data-first` | Data Story | Dataset → Key Patterns → Findings → Implications → Limitations |
| `literature` | Literature Synthesis | State of Evidence → Key Studies → Gaps → Implications |
| `thorough` | Full Research Report + Appendix | all of `full` + critique cluster detail + revision loop log |

### Step 3: Write the report

Follow `shared/output-style-guide.md` strictly:
- Prose over bullets unless structure earns its place
- State findings first, methodology second
- Numbers embedded in prose with appropriate precision
- No AI filler language
- No em dashes as clause connectors

#### Writing the Executive Summary (full / thorough mode)

The executive summary must stand alone. A reader who reads only this should understand: what was asked, what was found, how confident we are, and the main caveat.

4-6 sentences. No bullets. Start with the finding, not with the question.

**Finance example:**
> "Regulatory filing speed is a moderate predictor of 30-day equity returns among European oncology companies at the point of FDA approval (Spearman r = 0.31, p = 0.003). The relationship holds across pre- and post-2021 subperiods and survives controlling for company size and indication, though not for pipeline quality proxies — adding prior Phase 2 success rate as a covariate reduces the coefficient to 0.19 (p = 0.038). Confidence is moderate (6/10): the finding is statistically reliable but the sample covers 47 approvals, and residual confounding from drug quality cannot be fully resolved without proprietary clinical data. The relationship may be exploitable with informational advantage on regulatory timelines but is too noisy for systematic strategy construction at current sample sizes."

**Biotech example:**
> "Biomarker-selected Phase 2 trials in solid tumours achieve Phase 2→3 transition at 41% versus 27% for unselected trials (OR 1.88, 95% CI 1.24-2.85, p = 0.003, n = 312 trials). The gap is consistent across large pharma and mid-sized sponsor cohorts, suggesting the effect is not driven by sponsor capability alone, though target maturity remains a partially unresolved confound. Confidence is moderate-high (7/10): the finding replicates the directional result from Sargent et al. (2013) with more recent data and a cleaner universe definition. The result does not establish whether the improvement stems from patient matching or from the tendency to apply biomarker strategies to more validated targets."

#### Writing findings sections

For each key finding from `synthesis/evaluation.yaml`:
1. Lead with the result, not the method
2. Embed statistics in the sentence, not in a table
3. Include the domain context from `evaluation.key_findings[].domain_context`
4. Close with the specific limitation of that finding

Do not restate numbers already given verbatim in the executive summary.

#### Writing the challenges section

For each challenge in `evaluation.challenges` with severity ≥ moderate:
- State the challenge directly (one sentence)
- State the response and its source (analysis result or remaining gap)
- State the residual risk honestly

If `overall_verdict` is WEAKENED or OVERTURNED: this must appear in the executive summary, not only in the challenges section.

### Step 4: Run writing quality check

Before finalising, scan the draft for every item on this list:

**Banned phrases:**
- "it's worth noting" → delete or rephrase
- "importantly" as opener → delete
- "certainly" / "absolutely" → delete
- "in today's [X] landscape" → delete
- "delve" in any form → delete
- "fascinating" / "exciting" / "groundbreaking" → delete unless quoting
- "in conclusion, ..." → delete the phrase, keep the conclusion
- "this report will..." → delete
- Sentences starting with "It is important to..."

**Language calibration check:**
- If `revised_confidence_score` < 6: no finding should use "strong evidence", "clearly", "shows"
- If `revised_confidence_score` ≥ 8: no finding should say "preliminary" or "warrants investigation"
- Every paragraph starts with a topic sentence, not a transition phrase

### Step 5: Assemble data sources

```
Data Sources
============
[Source name] — [URL or description] — accessed [date]
Coverage: [period, universe, variables]
```

### Step 6: Write report metadata

`report_metadata.yaml` conforming to Schema 8 in `shared/handoff-schemas.md`.

### Step 7: Save and confirm

Save `report.md` to `./[topic_slug]/report.md`.
Save `report_metadata.yaml` to `./[topic_slug]/report_metadata.yaml`.

Present the report to the user.
Ask: any sections to expand, revise, or add?

---

## Null Result Report

If routed from `findings-evaluator` with TERMINATE_WITH_NULL, or with `overall_verdict: OVERTURNED`:

Write a null result report using this template:

```
[TOPIC] — NULL RESULT

Research Question
[The hypothesis tested]

Result
No reliable [relationship/signal/finding] was established between [X] and [Y]
with the available data and methodology.

Best result obtained: [most significant result, with statistics]
Statistical power: [minimum detectable effect at current sample size]

Why the null result is informative
[What the data ruled out; what it could not rule out]

What would be needed to resolve this
[Specific: data source, sample size, alternative method]

Methodology
[Brief: what was done, in what period, with what data]
```

A null result report is a complete output, not a failure. It should be written to the same standard as a positive finding report.
