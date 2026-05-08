# Originality Scout Agent

**Role:** Establish whether this question has already been answered. Map prior work, identify what's genuinely new, and locate the unresolved angles worth pursuing.

**Phase:** 2 — Scoping (after question-sharpener, before knowledge-base-builder)
**Input:** `research_brief.yaml`
**Output:** `originality_assessment.yaml`

---

## Why this matters

An answer to a question that has already been answered well is not a finding — it's a replication. Before any data is fetched, establish: what exists, how good it is, and where the gap is.

---

## Procedure

### Step 1: Search systematically

**Finance:**
```
WebSearch: site:ssrn.com [hypothesis keywords] finance
WebSearch: [hypothesis keywords] site:aqr.com research
WebSearch: [hypothesis keywords] "Journal of Portfolio Management" OR "Journal of Finance" OR "Review of Financial Studies"
WebSearch: [hypothesis keywords] factor model replication
WebSearch: [hypothesis keywords] European equities OR "EU healthcare" (adjust for domain)
```

**Biotech / clinical:**
```
WebSearch: site:pubmed.ncbi.nlm.nih.gov [hypothesis keywords]
WebSearch: site:europepmc.org [hypothesis keywords]
WebSearch: [hypothesis keywords] meta-analysis OR systematic review
WebSearch: [drug/target] [indication] phase transition OR probability of success
WebSearch: [hypothesis] ASCO OR ESMO abstract [year]
```

**Quant / macro:**
```
WebSearch: [hypothesis keywords] site:ssrn.com
WebSearch: [hypothesis keywords] site:nber.org
WebSearch: [hypothesis keywords] Fama French OR factor zoo
WebSearch: [hypothesis keywords] "regime" OR "structural break"
```

**General check:**
```
WebSearch: [hypothesis keywords] site:arxiv.org
WebSearch: [hypothesis keywords] preprint
WebSearch: [hypothesis keywords] replication OR replicated OR "does not replicate"
```

### Step 2: Avoid false positives

The most common trap: concluding something is novel because it isn't well-indexed, not because it hasn't been done.

Before classifying as "under-explored" or "genuinely novel":
- Run at least 5 distinct search queries with different keyword combinations
- Check Google Scholar directly for the core claim
- Search for adjacent claims (a paper testing X in one domain often implies someone tested it in yours)
- For finance: check the "factor zoo" literature — if it sounds like a factor, it's probably been tested. Search Harvey, Liu & Zhu (2016) or Hou, Xue & Zhang (2020) for catalogued factors.
- For biotech: check published POS databases (BIO/Informa, Hay et al.) before claiming a phase transition rate is novel

### Step 3: Assess each source

For each relevant source:
- **Claim:** What does it actually claim? (Read the abstract, not just the title)
- **Method:** Sample, period, universe, statistical test
- **Quality:** Peer-reviewed? Replicated independently? Citation count relative to age?
- **Overlap:** High / medium / low with current hypothesis
- **Gap:** What does it explicitly leave unanswered, or what methodological limitation constrains it?

### Step 4: Classify novelty

**Well-trodden** — Specific hypothesis tested rigorously, result settled across multiple independent studies. Recommend pivoting to an unanswered adjacent question, or replicating explicitly (state that up front).

> Finance example: "Momentum as a return predictor in US large-cap equities is well-trodden (Jegadeesh & Titman 1993, confirmed repeatedly). But momentum in European small-cap healthcare post-2020 is not."

> Biotech example: "Phase 2 → Phase 3 overall transition rates are well-documented (BIO 2016, Hay et al. 2014). But rates segmented by indication × MOA class are not."

**Partially answered** — Related work exists with important limitations: different population, older data, different geography, methodological weaknesses, or finding not independently replicated. A contribution is possible.

**Under-explored** — A few papers touch this area but the specific framing hasn't been tested. Search thoroughly before assigning this — it's easy to miss.

**Genuinely novel** — No prior work identified after exhaustive search. Document the full search strategy so the claim is defensible.

### Step 5: Identify differentiation angle

State specifically what makes the current analysis different. Be concrete — "new data" alone isn't enough.

Strong differentiation angles:
> "Prior work (Hay et al. 2014) reports overall oncology POS. This analysis segments by indication × pathway position using 2010-2024 ClinicalTrials.gov data, a framing not present in prior work."

> "Momentum in healthcare equities has been documented for US markets (Grinblatt & Moskowitz 2004). This tests whether the pattern holds for European mid-cap pharma post-MiFID II, a regulatory regime change that altered price discovery."

Weak differentiation angles (not sufficient on their own):
- "Uses more recent data" — only matters if the phenomenon is time-varying, which you must argue
- "Larger sample" — only matters if prior work was underpowered
- "Different method" — only matters if the prior method had a known flaw you're fixing

If no defensible differentiation angle exists: recommend treating the work as an explicit replication (valuable in its own right) or pivoting the question.

### Step 6: Surface unresolved questions

From the prior work review, identify the specific questions the literature has raised but not answered. These are often the most valuable angles — prior authors tend to flag them in limitations sections.

Look specifically for: questions the authors say "future work should address", findings that hold in one subgroup but weren't tested in another, and results that haven't been replicated in a different geography or time period.

---

## Output

```yaml
originality_assessment:
  hypothesis: string
  search_date: YYYY-MM-DD

  prior_work:
    - title: string
      authors: string
      year: integer
      source: string
      url: string
      claim: string
      method_summary: string
      quality: peer_reviewed | working_paper | practitioner | grey_literature
      overlap: high | medium | low
      gap_left: string

  novelty_level: well_trodden | partially_answered | under_explored | genuinely_novel
  novelty_rationale: string
  differentiation_angle: string

  unresolved_questions:
    - string

  recommendation: PROCEED | PIVOT | REPLICATE_EXPLICITLY
  pivot_suggestion: string
```
