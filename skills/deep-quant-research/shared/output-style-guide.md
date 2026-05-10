# Output Style Guide

Standards for all written output from the deep-quant-research skill.
Applied by `report-compiler` agent. Referenced by `findings-evaluator`.

---

## Core Principles

Write like a senior analyst at a rigorous research shop: precise, direct, confident where the evidence warrants it, cautious where it does not. The goal is clarity for a reader who is intelligent but time-constrained.

- Prose over bullets unless structure genuinely earns its place
- State findings first, methodology second
- Never bury the conclusion
- One idea per sentence when the idea is complex
- No word that does not earn its position

---

## Tone and Register

**Correct register:**
> "The 60-day lag between ClinicalTrials.gov primary completion and FDA submission is the strongest predictor of stock price movement across the 47 oncology NMEs in this dataset (β = 0.31, p = 0.003, R² = 0.24 out-of-sample)."

**Wrong register:**
> "It's worth noting that there appears to be an interesting relationship between the lag and prices."

Rules:
- State effect sizes with the finding, not in a separate paragraph
- Hedging is for genuinely uncertain claims, not for stylistic softness
- No exclamation marks, no rhetorical questions
- Avoid: "it is important to note", "as we can see", "interestingly", "notably", "crucially"
- Avoid: "deep dive", "delve into", "unpack", "explore", "leverage" (as a verb)

---

## Sentence and Paragraph Length

- Sentences: target 15-25 words. Vary length deliberately. Short sentences land hard. Long sentences, which carry subordinate clauses and qualifications, require the reader to hold more in working memory and should be used sparingly.
- Paragraphs: 3-6 sentences. Each paragraph has one central claim. Topic sentence first.
- Never use em dashes as clause connectors.

---

## Numbers and Statistics

- Round to 2-3 significant figures in prose ("0.31", not "0.3127")
- Percentages in prose: "24%" not "24.0%"
- Large numbers: "£1.4bn" not "£1,400,000,000"; "47 companies" not "forty-seven companies"
- Always specify the timeframe: "annualised Sharpe of 1.4 over 2015-2024"
- p-values: exact values ("p = 0.003"), not "p < 0.05"
- Confidence intervals: always report alongside point estimates where relevant

---

## Structure by Output Type

### Research Brief (quick mode)
```
[Title]

Key Finding
[1-2 sentences. The most important result. No hedging if evidence is strong.]

Evidence
[3-5 bullet points: data, method, result for each. Stats included.]

Caveats
[What would change this conclusion. Honest.]

Data and Method
[2-3 sentences. What was used and why.]
```

### Full Research Report (full mode)
```
[Title]

Executive Summary
[4-6 sentences. Finding, evidence, confidence, caveats. Readable standalone.]

Research Question
[The original question and the refined testable hypothesis.]

Methodology
[What data, what period, what tests, what validation approach.]

Findings
[Section per major finding. Lead with the result. Evidence follows.]

Robustness and Limitations
[What was tested beyond the primary analysis. What the analysis cannot say.]

Confidence Assessment
[Score from findings-evaluator with reasoning.]

Challenges and Responses
[From findings-evaluator. Each challenge, the response, and residual risk.]

Data Sources
[List with dates accessed and any provenance notes.]
```

### Thesis Test (thesis-test mode)
```
[Hypothesis Tested]

Verdict: [SUPPORTED / PARTIALLY SUPPORTED / NOT SUPPORTED / INCONCLUSIVE]

Evidence For
[Numbered list with stats.]

Evidence Against
[Numbered list with stats. Be as thorough here as above.]

Confidence: [X/10]

What Would Change This Verdict
[Specific: more data, different period, alternative measure.]
```

### Literature Synthesis (literature mode)
```
[Topic]

State of Evidence
[What is established, what is contested, what is unknown.]

Key Studies
[Table: Author, Year, Design, Sample, Finding, Limitations]

Gaps
[What has not been studied that matters for your question.]

Implications
[What the evidence means for the specific question asked.]
```

---

## Anti-AI Checklist

Before finalising any output, `report-compiler` must check for and remove:

**Banned phrases:**
- "it's worth noting" → delete or rephrase
- "importantly" (as a sentence opener) → delete
- "certainly" / "absolutely" → delete
- "it is important to" → delete
- "in today's [X] landscape" → delete
- "let's explore" / "let's dive into" → delete
- "delve" in any form → delete
- "fascinating" / "exciting" / "groundbreaking" → delete unless quoting
- "in conclusion, ..." → delete the phrase, keep the conclusion
- "this report will..." → delete; just do it

**Structural tells:**
- Three-part list ending with "and finally" → restructure
- Every paragraph starting with a transition word → vary
- Findings presented as questions ("Could X cause Y?") → state what the data shows
- Excessive hedging on well-supported findings → tighten

---

## Domain-Specific Conventions

### Finance and investing
- Equity returns: log returns for analysis, simple returns in reporting
- Currency: specify (USD, GBP, EUR); use company's reporting currency unless stated
- Timeframes: be precise ("Q1 2023", "FY2023 ending December", "trailing 12 months to March 2024")
- Consensus: distinguish between buy-side and sell-side consensus where relevant

### Biotech and clinical
- Drug names: use INN (generic name) primary, brand name in parentheses on first use
- Trial phases: "Phase 2" not "Phase II" unless citing a specific trial identifier
- Endpoints: distinguish primary from secondary endpoints clearly
- Statistical convention: report hazard ratios with confidence intervals for survival data; odds ratios for binary outcomes

### Quant and factors
- Factor names: capitalise (Value, Momentum, Quality, Low Volatility)
- Report factor exposures (loadings) alongside alphas
- Distinguish between long-only and long-short factor construction
- Turnover: report monthly/annual turnover for any strategy

---

## Citations and Data Attribution

- Cite data sources inline on first use: "ClinicalTrials.gov (accessed 2026-05-08)"
- Web sources: full URL and access date
- Papers: Author (Year) format in prose; full citation in Data Sources section
- Do not fabricate citations; if a specific paper is referenced, confirm it exists
