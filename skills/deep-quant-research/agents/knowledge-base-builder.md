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

From prior work in `originality_assessment.yaml`, identify what is not contested. Be specific — a vague consensus statement is not useful.

**Biotech example (good):**
> "First-line EGFR TKI therapy in EGFR-mutant NSCLC (exon 19 del / L858R) produces consistent PFS improvement of ~6-8 months vs. chemotherapy across multiple RCTs (FLAURA, ARCHER 1050, LUX-Lung 7). Third-generation TKIs (osimertinib) show OS benefit over first-generation. Consensus: target is validated, drug class is mature, competitive differentiation is now driven by combination strategies and resistance sequencing."

**Finance example (good):**
> "The size premium (small-cap outperformance) documented by Fama & French (1992) has largely disappeared in US markets post-publication. Hou & Dijk (2019) show it is insignificant after 1980 in the US but persists in international markets. Consensus: the US size premium is weak to non-existent; international evidence is stronger but data-dependent."

**Quant example (good):**
> "Momentum (12-1 month prior return) predicts cross-sectional equity returns in most developed markets (Asness et al. 2013). The factor has a known crash risk: momentum strategies lose severely in sharp reversals (e.g., 2009). Consensus: momentum is a real premium but requires drawdown management; its source (risk vs. behavioural) remains disputed."

### Step 2: Map disputes

For each area of contested evidence, map the shape of the disagreement — not just that views differ, but why.

Note especially:
- **Replication failures.** Finance has a documented factor zoo problem. Many published factors fail to replicate out-of-sample (Harvey, Liu & Zhu 2016 screen ~300 factors; Hou et al. 2020 replicate ~452, most fail). If the topic involves a financial factor, note its replication status explicitly.
- **Publication bias.** Biotech literature overrepresents positive results. Registered reports and meta-analyses of trial-level data are more reliable than aggregated published literature.
- **Structural disagreements.** Some disputes won't resolve with more data because the parties are measuring different things or using incompatible definitions.

**Dispute example (finance):**
> Question: Does low volatility predict outperformance (low-vol anomaly)?
> Position A (Baker et al.): Yes — institutional mandates create demand pressure for high-beta stocks, making low-vol cheap.
> Position B (Blitz et al.): The effect conflates betting-against-beta (BAB) with quality. Controlling for quality, low vol adds little.
> Likely resolution: Structural — depends on which factor definition you adopt.

**Dispute example (biotech):**
> Question: Does biomarker selection in Phase 2 improve Phase 3 success rates?
> Position A (multiple observational studies): Yes — biomarker-selected trials show 15-20pp higher Phase 3 success.
> Position B (Sargent et al.): The effect is confounded by target maturity. Established targets use biomarker selection more often; better outcomes may reflect target quality, not selection strategy.
> Likely resolution: Data will resolve — requires controlling for target class in a larger dataset.

### Step 3: Inventory datasets and methods

For each dataset used in the prior work:
- Coverage (geography, time period, entities, completeness)
- Known limitations (survivorship bias, registration gaps, access requirements)
- Who uses it (academic standard vs. practitioner standard)

For each method:
- Is it the field standard, or contested?
- Any known failure modes for this specific topic?

**Example (clinical trials):**
> ClinicalTrials.gov: US registration required since 2007; international coverage variable before 2012; Phase 1/2 registration less consistent than Phase 3. Standard for academic POS research. Does not capture trials that were never registered or abandoned before registration.

### Step 4: Define open questions

Specific. Not "more research is needed."

**Strong open questions:**
> "Does the KRAS G12C resistance mechanism via PD-1 upregulation also operate in pancreatic ductal adenocarcinoma, where KRAS mutation prevalence is >90% but checkpoint inhibitor responses are rare? Prior work is limited to NSCLC."

> "Does the size premium persist in European small-cap healthcare specifically, or is the documented international size effect driven by other sectors? No domain-specific analysis exists."

> "Do walk-forward backtests of sentiment-based biotech trading signals survive realistic transaction cost assumptions? Prior work uses daily closing prices; bid-ask spreads in small-cap biotech are material."

**Weak open questions (do not write these):**
> "Future work should explore other markets." (Too vague)
> "More data is needed." (What data, for what specific test?)

### Step 5: Note methodological standards

The specific practices that distinguish rigorous work in this area from sloppy work. This becomes the benchmark for the current analysis.

**Finance:**
- Walk-forward validation, not in-sample only
- Transaction cost adjustment for any strategy claim
- Multiple testing correction if more than ~5 hypotheses tested
- Subperiod analysis for stability

**Biotech:**
- Distinguish statistical from clinical significance
- Report confidence intervals on hazard ratios, not just p-values
- Account for publication bias in literature-based analyses
- Distinguish primary from secondary endpoint results

**Quant:**
- Stationarity checks before any time series regression
- Structural break tests for long time series
- Factor exposure decomposition before claiming alpha

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
