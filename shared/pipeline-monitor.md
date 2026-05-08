# Pipeline Monitor

Tracks the state of a research session. Updated at each phase transition.

The pipeline monitor exists to prevent silent failures: phases being skipped, critiques not running, revision loops not terminating.

---

## Session State Schema

```yaml
session:
  topic_slug: "string"
  research_type: "biotech | finance | quant | mixed"
  mode: "full | quick | thesis-test | data-first | literature"
  start_time: "ISO 8601"
  iteration: integer  # hypothesis refinement iteration (starts at 1)
  
phases:
  scoping:
    status: "pending | in_progress | complete | skipped"
    agents_run: ["question-sharpener", "research-architect"]
    output: "research_brief.yaml"
    
  data:
    status: "pending | in_progress | complete | skipped"
    agents_run: ["data-scout", "data-quality"]
    data_quality_verdict: "PROCEED | PROCEED_WITH_CAVEATS | DO_NOT_PROCEED"
    critique_run: true/false
    
  analysis:
    status: "pending | in_progress | complete | skipped"
    agents_run: []  # list of which analysis agents actually ran
    critique_run: true/false
    critique_verdict: "PASS | REVISE | FAIL"
    revision_count: integer
    
  synthesis:
    status: "pending | in_progress | complete | skipped"
    agents_run: ["interpret-agent", "confidence-scorer"]
    confidence_score: integer
    loop_decision: "PROCEED | REFINE | TERMINATE_WITH_NULL"
    critique_run: true/false
    critique_verdict: "PASS | REVISE | FAIL"
    revision_count: integer
    
  challenge:
    status: "pending | in_progress | complete | skipped"
    agents_run: ["skeptic-agent"]
    verdict: "STANDS | STANDS_WITH_CAVEATS | WEAKENED | OVERTURNED"
    
  output:
    status: "pending | in_progress | complete"
    agents_run: ["report-compiler"]
    critique_run: true/false
    critique_verdict: "PASS | REVISE | FAIL"
    revision_count: integer
    report_path: "string"
    
flags:
  human_review_recommended: true/false
  human_review_required: true/false
  critique_incomplete: true/false  # set if any critic failed to return
  null_result: true/false
  
final:
  confidence_score: integer
  skeptic_verdict: "string"
  report_delivered: true/false
```

---

## Critique Cluster Trigger Points

Critique runs at three points in the pipeline:

| Point | Critics active | Checklists |
|-------|---------------|------------|
| After Phase 3 (Analysis) | methods + data + logic | methods-checklist + data-checklist + logic-checklist |
| After Phase 4 (Synthesis) | logic + interpretation | logic-checklist + interpretation-checklist |
| After Phase 6 (Report) | report | report-checklist |

In `quick` mode, the Phase 4 critique runs; Phase 3 and Phase 6 critiques are abbreviated (report-checklist only for output).

In `literature` mode, only the interpretation and report critiques run (no methods or data critique).

---

## Abort Conditions

The pipeline monitor flags an abort when:

1. `data_quality_verdict = DO_NOT_PROCEED` and user has not explicitly overridden
2. `revision_count > 3` on any phase (escalate to human review)
3. `iteration > 3` (hypothesis refinement loop exhausted — report null result)
4. `skeptic_verdict = OVERTURNED` and no viable reformulation exists

On abort, route to `report-compiler` with the abort reason and current best state.

---

## Monitoring During a Session

At the start of each new phase, update the pipeline monitor:

```
Pipeline status:
Phase 1 Scoping:    COMPLETE
Phase 2 Data:       COMPLETE (quality verdict: PROCEED_WITH_CAVEATS)
Phase 3 Analysis:   IN_PROGRESS
  - statistical-analyst: running
  - Critique: pending
  - Revision count: 0
```

Display this status block to the user at each phase transition. It prevents silent loops and keeps the research traceable.
