# Handoff Schemas

Structured data contracts passed between agents. Each agent must produce output conforming to its schema before the next phase starts. The pipeline monitor (`scripts/validate_output.py`) checks these automatically.

---

## Schema 1: Research Brief

**Produced by:** `question-sharpener` + `research-architect`
**Consumed by:** all subsequent agents
**File:** `research_brief.yaml`

```yaml
research_brief:
  original_question: "string"
  refined_hypothesis: "string — testable, falsifiable, specifies population and metric"
  research_type: "biotech | finance | quant | mixed"
  mode: "full | quick | thesis-test | data-first | literature | thorough"

  success_criteria:
    - criterion: "string"
      measurable: true
      threshold: "string — e.g. Spearman r > 0.25, p < 0.05 two-tailed"
    - criterion: "string — out-of-sample validation threshold"
      measurable: true
      threshold: "string"
    - criterion: "string — null result definition"
      measurable: true
      threshold: "string — e.g. |r| < 0.15 or p > 0.10 → report as no signal"

  study_design:
    primary_analyses: ["list"]
    secondary_analyses: ["list"]
    data_requirements: ["list of datasets needed"]
    time_period: "string"
    universe: "string — entities, assets, compounds, trials"
    falsification_criteria: "string — what result would disprove the hypothesis"

  out_of_scope: ["list"]

  domain_context:
    type: "biotech | finance | quant | mixed"
    subtype: "string — e.g. EU oncology, equity factor, macro regime"
    known_priors: ["relevant established results"]
```

---

## Schema 2: Originality Assessment

**Produced by:** `originality-scout`
**Consumed by:** `knowledge-base-builder`, `research-architect`
**File:** `originality_assessment.yaml`

```yaml
originality_assessment:
  hypothesis: "string — from research_brief"
  search_date: "YYYY-MM-DD"

  prior_work:
    - title: "string"
      authors: "string"
      year: integer
      source: "string"
      url: "string"
      claim: "string"
      method_summary: "string — sample, period, universe, test"
      quality: "peer_reviewed | working_paper | practitioner | grey_literature"
      overlap: "high | medium | low"
      gap_left: "string"

  novelty_level: "well_trodden | partially_answered | under_explored | genuinely_novel"
  novelty_rationale: "string"
  differentiation_angle: "string — what makes this analysis different"

  unresolved_questions:
    - "string"

  recommendation: "PROCEED | PIVOT | REPLICATE_EXPLICITLY"
  pivot_suggestion: "string — populated if PIVOT"
```

---

## Schema 3: Knowledge Base Entry

**Produced by:** `knowledge-base-builder`
**Consumed by:** `research-architect`, `findings-evaluator`, `report-compiler`
**File:** `knowledge_base/[topic_slug].yaml`

```yaml
knowledge_base_entry:
  topic: "string"
  domain: "biotech | finance | quant | mixed"
  created: "YYYY-MM-DD"
  sources_reviewed: integer

  consensus:
    - claim: "string — specific, not vague"
      evidence_strength: "strong | moderate | weak"
      key_references: ["string"]

  disputes:
    - question: "string"
      position_a:
        claim: "string"
        evidence: "string"
      position_b:
        claim: "string"
        evidence: "string"
      likely_resolution: "data_will_resolve | structural | unknown"

  datasets_used:
    - name: "string"
      coverage: "string"
      known_limitations: "string"
      preferred_by: "string"

  methods_used:
    - method: "string"
      standard_in_domain: true
      notes: "string"

  open_questions:
    - question: "string"
      why_unresolved: "string"
      relevance_to_current_study: "high | medium | low"

  methodological_standards:
    - standard: "string"
      rationale: "string"

  relevance_to_hypothesis: "string"
```

---

## Schema 4: Data Package

**Produced by:** `data-scout-quality`
**Consumed by:** `analysis-engine`, `backtest-engine`, `causal-inference`
**File:** `data/data_package.yaml`

```yaml
data_package:
  datasets:
    - name: "string"
      source: "string — URL or API name"
      access_date: "YYYY-MM-DD"
      period: "YYYY-MM-DD to YYYY-MM-DD"
      frequency: "daily | weekly | monthly | quarterly | event-driven"
      observations: integer
      variables: ["list"]
      file_path: "string — relative path"

  quality_report:
    look_ahead_bias: "PASS | WARN | FAIL"
    survivorship_bias: "PASS | WARN | FAIL"
    data_snooping_risk: "PASS | WARN | FAIL"
    selection_bias: "PASS | WARN | FAIL"
    verdict: "PROCEED | PROCEED_WITH_CAVEATS | DO_NOT_PROCEED"
    caveats: ["list — carried into all downstream outputs"]

  preprocessing_applied:
    - step: "string"
      rationale: "string"
```

---

## Schema 5: Analysis Results

**Produced by:** `analysis-engine`, `backtest-engine`, `causal-inference` (one file each)
**Consumed by:** `critique-cluster`, `findings-evaluator`
**Files:** `analysis/statistical.yaml`, `analysis/backtest.yaml`, `analysis/causal.yaml`

```yaml
analysis_results:
  analyst: "statistical | timeseries | backtest | causal"
  produced_at: "YYYY-MM-DDTHH:MM:SS"

  findings:
    - id: "string — unique within session, e.g. F1"
      description: "string — what was tested"
      result: "string — plain statement"
      statistics:
        test: "string — e.g. Spearman correlation, OLS, walk-forward AUC"
        value: number
        p_value: number
        confidence_interval: [lower, upper]
        effect_size: number
        effect_size_type: "string — Cohen's d | R² | Spearman r | AUC | HR"
        n_observations: integer
      validation:
        method: "string — walk-forward | hold-out | k-fold | subperiod"
        out_of_sample_result: number
        is_robust: true
        robustness_notes: "string"

  negative_results:
    - id: "string — e.g. N1"
      description: "string — what was tested and found nothing"
      statistics:
        value: number
        p_value: number
        confidence_interval: [lower, upper]
        power_to_detect: "string — e.g. powered to detect r > 0.20"

  data_quality_flags: ["issues encountered during analysis"]
  scripts_used: ["list"]
  output_files: ["list"]
```

---

## Schema 6: Critique Reports

**Produced by:** `critique-cluster` (three parallel critics)
**Consumed by:** `findings-evaluator`
**Files:** `critique/methods.yaml`, `critique/data.yaml`, `critique/logic.yaml`

Each critic produces the same structure:

```yaml
critique_report:
  critic: "methods | data | logic"
  produced_at: "YYYY-MM-DDTHH:MM:SS"
  critique_incomplete: false  # true if critic failed and was skipped

  challenges:
    - id: "string — e.g. MC1, DC1, LC1"
      finding_id: "string — links to Schema 5 finding id"
      aspect: "string — what specifically is being challenged"
      severity: "critical | moderate | minor"
      challenge: "string — the specific challenge"
      suggested_alternative: "string — what should have been done instead"
      verdict: "FATAL | WEAKENS | MINOR_CAVEAT"

  overall_assessment: "string"
  fatal_flaws: integer
```

---

## Schema 7: Evaluation

**Produced by:** `findings-evaluator`
**Consumed by:** `report-compiler`
**File:** `synthesis/evaluation.yaml`

```yaml
evaluation:
  confidence_score: integer  # 1-10
  recommendation: "PROCEED | REFINE | TERMINATE_WITH_NULL"
  iteration: integer  # starts at 1, max 3

  key_findings:
    - finding_id: "string — links to Schema 5"
      plain_language: "string — no jargon"
      domain_context: "string — what this magnitude means in this domain"
      confidence_contribution: "positive | neutral | negative"

  score_rationale:
    data_quality: "string"
    sample_size: "string"
    out_of_sample: "string"
    robustness: "string"
    effect_magnitude: "string"
    critique_outcome: "string — summary of what the critics found"

  challenges:
    - id: "string"
      type: "alternative_explanation | data_concern | methodology | generalisability"
      severity: "critical | moderate | minor"
      challenge: "string"
      response: "string"
      residual_risk: "string"
      verdict: "RESOLVED | PARTIALLY_RESOLVED | UNRESOLVED"
      source: "main | methods_critic | data_critic | logic_critic"

  overall_verdict: "STANDS | STANDS_WITH_CAVEATS | WEAKENED | OVERTURNED"
  revised_confidence_score: integer

  what_would_change_verdict:
    - "string"

  refinement_suggestions:
    - "string"  # populated if recommendation is REFINE
```

---

## Schema 8: Report Metadata

**Produced by:** `report-compiler`
**File:** `report_metadata.yaml` (stored alongside `report.md`)

```yaml
report_metadata:
  title: "string"
  date: "YYYY-MM-DD"
  mode: "full | quick | thesis-test | data-first | literature | thorough"
  research_type: "biotech | finance | quant | mixed"
  iterations: integer
  critique_cluster_ran: true
  final_confidence_score: integer
  final_verdict: "STANDS | STANDS_WITH_CAVEATS | WEAKENED | OVERTURNED | NULL_RESULT"

  data_sources:
    - name: "string"
      url: "string"
      access_date: "YYYY-MM-DD"

  degraded_phases: ["list — phases that ran with degraded output"]
  scripts_run: ["list"]
  output_files:
    - type: "report | data | chart | metadata"
      path: "string"

  caveats: ["list — carried from data quality + unresolved critique challenges"]
  limitations: "string — paragraph"
  next_questions: ["list — what the analysis surfaces but does not answer"]
```
