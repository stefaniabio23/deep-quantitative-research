# Handoff Schemas

Structured data contracts passed between agents in the research pipeline.
Agents must produce outputs conforming to the schema for their phase before the next agent proceeds.

---

## Schema 1: Research Brief (Phase 1 output → all subsequent agents)

Produced by `question-sharpener` + `research-architect`.

```yaml
research_brief:
  original_question: "string"
  refined_hypothesis: "string — testable, falsifiable"
  research_type: "biotech | finance | quant | mixed"
  mode: "full | quick | thesis-test | data-first | literature"
  
  success_criteria:
    - criterion: "string"
      measurable: true/false
      threshold: "string — e.g. p < 0.05, R² > 0.1 out-of-sample"
  
  study_design:
    primary_analyses: ["list of analyses to run"]
    secondary_analyses: ["list"]
    data_requirements: ["list of datasets needed"]
    time_period: "string"
    universe: "string — what entities/assets/compounds"
  
  out_of_scope: ["list — what this analysis will not address"]
  
  domain_context:
    type: "biotech | finance | quant | mixed"
    subtype: "oncology | EU-healthcare | equity-factor | macro | etc."
    known_priors: ["relevant known results from literature or prior analysis"]
```

---

## Schema 2: Data Package (Phase 2 output → analysis agents)

Produced by `data-scout` after `data-quality` sign-off.

```yaml
data_package:
  datasets:
    - name: "string"
      source: "string — URL or API"
      access_date: "YYYY-MM-DD"
      period: "YYYY-MM-DD to YYYY-MM-DD"
      frequency: "daily | weekly | monthly | quarterly | event-driven"
      observations: integer
      variables: ["list"]
      file_path: "string — relative path to data file"
      
  quality_report:
    look_ahead_bias: "PASS | WARN | FAIL"
    survivorship_bias: "PASS | WARN | FAIL"
    data_snooping_risk: "PASS | WARN | FAIL"
    selection_bias: "PASS | WARN | FAIL"
    verdict: "PROCEED | PROCEED_WITH_CAVEATS | DO_NOT_PROCEED"
    caveats: ["list"]
    
  preprocessing_applied:
    - step: "string"
      rationale: "string"
```

---

## Schema 3: Analysis Results (Phase 3 output → interpret-agent)

Produced by analysis agents (`statistical-analyst`, `timeseries-analyst`, `backtest-engine`, `causal-inference`).

```yaml
analysis_results:
  analyst: "statistical | timeseries | backtest | causal"
  
  findings:
    - id: "string — unique within session"
      description: "string — what was tested"
      result: "string — plain statement of result"
      statistics:
        test: "string — e.g. Pearson correlation, OLS regression"
        value: number
        p_value: number
        confidence_interval: [lower, upper]
        effect_size: number
        effect_size_type: "string — e.g. Cohen's d, R², partial η²"
        n_observations: integer
      validation:
        method: "string — e.g. walk-forward, hold-out, k-fold"
        out_of_sample_result: number
        is_robust: true/false
        robustness_notes: "string"
      
  negative_results:
    - description: "string — what was tested and found nothing"
      notes: "string"
  
  data_quality_flags: ["any issues encountered during analysis"]
  scripts_used: ["list of scripts run"]
  output_files: ["list of files generated"]
```

---

## Schema 4: Confidence Assessment (Phase 4 output → skeptic-agent + report-compiler)

Produced by `interpret-agent` + `confidence-scorer`.

```yaml
confidence_assessment:
  score: integer  # 1-10
  
  key_findings:
    - finding_id: "string — links to Schema 3"
      plain_language: "string — finding stated without jargon"
      domain_context: "string — what this means in this domain"
      confidence_contribution: "positive | neutral | negative"
  
  score_rationale:
    data_quality: "string"
    sample_size: "string"
    out_of_sample: "string"
    robustness: "string"
    bias_flags: "string"
    effect_magnitude: "string"
  
  recommendation: "PROCEED_TO_SKEPTIC | REFINE_HYPOTHESIS | TERMINATE"
  refinement_suggestions: ["if REFINE_HYPOTHESIS: what to change"]
  
  iteration: integer  # which loop iteration this is (starts at 1)
```

---

## Schema 5: Skeptic Review (Phase 5 output → report-compiler)

Produced by `skeptic-agent`.

```yaml
skeptic_review:
  challenges:
    - id: "string"
      type: "alternative_explanation | data_concern | methodology | generalisability"
      challenge: "string — the specific challenge"
      severity: "critical | moderate | minor"
      response: "string — how the finding addresses this"
      residual_risk: "string — what remains after response"
  
  overall_verdict: "STANDS | STANDS_WITH_CAVEATS | WEAKENED | OVERTURNED"
  revised_confidence_score: integer  # may differ from Phase 4 score
  
  what_would_change_verdict:
    - "string — specific evidence or analysis that would alter the conclusion"
```

---

## Schema 6: Final Report Metadata

Produced by `report-compiler`. Stored alongside the output file.

```yaml
report_metadata:
  title: "string"
  date: "YYYY-MM-DD"
  mode: "full | quick | thesis-test | data-first | literature"
  research_type: "biotech | finance | quant | mixed"
  iterations: integer  # how many hypothesis refinement loops
  final_confidence_score: integer
  final_verdict: "string"
  
  data_sources:
    - name: "string"
      url: "string"
      access_date: "YYYY-MM-DD"
  
  scripts_run: ["list"]
  output_files:
    - type: "report | data | charts | scripts"
      path: "string"
  
  caveats: ["list — carried through from data quality + skeptic"]
  
  limitations: "string — paragraph"
```
