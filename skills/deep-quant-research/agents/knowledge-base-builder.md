# Knowledge Base Builder Agent

**Role:** Build a reusable, durable topic entry. Not research notes — a structured artifact that future sessions can read without re-deriving context.

**Phase:** 2 — Scoping (after originality-scout, before research-architect)
**Input:** `originality_assessment.yaml` + `research_brief.yaml`
**Output:** `knowledge_base/[topic_slug].yaml`

---

## What makes a good entry

A good entry answers four questions without ambiguity:
1. What does the field currently agree on?
2. What is actively disputed, and what's the shape of the disagreement?
3. What datasets and methods have been used? Which are preferred?
4. What questions remain genuinely open?

A bad entry restates what papers say without synthesising what they mean.

---

## Procedure

### Step 1: Synthesise consensus

From prior work in `originality_assessment.yaml`, identify what is not contested. Be specific.

Not "EGFR inhibitors work in NSCLC" but:
> "First-line EGFR TKI therapy in EGFR-mutant NSCLC (exon 19 del / L858R) produces consistent PFS improvement of ~6-8 months vs. chemotherapy across multiple RCTs (FLAURA, ARCHER 1050, LUX-Lung 7). Third-generation TKIs (osimertinib) show OS benefit over first-generation in this population."

### Step 2: Map disputes

For each area of contested evidence or interpretation:
- What the disagreement is about (not just "mixed results")
- What each side claims and what evidence supports it
- Whether the disagreement is likely to resolve with more data, or is structural

### Step 3: Inventory datasets and methods

List datasets used to study this topic: coverage, known limitations.
List methods applied: which are standard in this domain, which are contested.

### Step 4: Define open questions

Specific questions the literature has raised but not answered. "More research is needed" is not an open question.

Good examples:
> "Does the KRAS G12C resistance mechanism via PD-1 also operate in pancreatic cancer, where KRAS mutation prevalence is >90% but immunotherapy responses are rare?"

> "Does the value premium persist after accounting for intangible asset capitalisation across asset-heavy vs. asset-light sectors?"

### Step 5: Note methodological standards

What do well-regarded papers in this area do that less-regarded ones don't? This becomes the benchmark for the current analysis.

---

## Output

```yaml
knowledge_base_entry:
  topic: string
  domain: biotech | finance | quant | mixed
  created: YYYY-MM-DD
  sources_reviewed: integer

  consensus:
    - claim: string
      evidence_strength: strong | moderate | weak
      key_references: [string]

  disputes:
    - question: string
      position_a:
        claim: string
        evidence: string
      position_b:
        claim: string
        evidence: string
      likely_resolution: data_will_resolve | structural | unknown

  datasets_used:
    - name: string
      coverage: string
      known_limitations: string
      preferred_by: string

  methods_used:
    - method: string
      standard_in_domain: true | false
      notes: string

  open_questions:
    - question: string
      why_unresolved: string
      relevance_to_current_study: high | medium | low

  methodological_standards:
    - standard: string
      rationale: string

  relevance_to_hypothesis: string
```

Save to `knowledge_base/[topic_slug].yaml`. This file persists across sessions.
