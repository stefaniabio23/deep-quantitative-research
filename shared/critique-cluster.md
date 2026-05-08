# Critique Cluster Protocol

Critics are adversarial reviewers, not collaborators.

Their job is to determine whether the work survives scrutiny — not to improve it, not to validate the producing agent's reasoning, not to find something kind to say.

---

## What critics receive

Each critic receives only:
- The original user request (task brief)
- The final output of the phase being reviewed (not intermediate reasoning)
- The acceptance criteria for this phase
- Their own domain checklist (see `critique-checklists/`)

## What critics must NOT receive

- Other critics' feedback or verdicts
- The producing agent's reasoning or chain of thought
- Suggested correct answers or fixes from other agents
- Context from prior conversation turns beyond the task brief

This isolation is intentional. Agreement between isolated critics is evidence of correctness. Agreement between non-isolated critics is noise.

---

## Output Schema

Each critic returns exactly this structure:

```yaml
critic_report:
  critic: "methods | data | logic | interpretation"
  phase_reviewed: "string — e.g. Phase 3: Analysis"
  verdict: "PASS | REVISE | FAIL"
  severity: "low | medium | high | blocking"
  
  checklist_results:
    - item: "string — exact checklist item text"
      status: "pass | fail | uncertain"
      evidence: "string — specific observation from the output that supports this status"
  
  issues:
    - issue: "string — precise statement of the problem"
      why_it_matters: "string — consequence if not fixed"
      recommended_revision: "string — specific change, not vague improvement"
  
  confidence: 1-10  # How confident the critic is in this verdict
  human_review_recommended: true/false
```

---

## Verdict Rules

**PASS:** No material issue found. The output satisfies all checklist items. Minor observations may be noted but do not trigger revision.

**REVISE:** One or more checklist items failed. The issue is fixable without changing the core result or conclusion. The producing agent can address it and resubmit.

**FAIL:** The conclusion, method, data, or claim is unreliable. The core result is invalid or unsupportable. A FAIL requires returning to an earlier phase, not just surface revision.

---

## Retry Policy

```yaml
retry_policy:
  max_revision_loops: 3
  
  if_blocking_severity:
    action: revise_before_continuing
    note: blocking issues are FAIL verdicts on core claims
    
  if_same_failure_twice:
    action: human_review_recommended
    note: set human_review_recommended true; do not loop a third time on the same issue
    
  if_3_revision_loops_exhausted:
    action: mark_as_human_review_required; route to report-compiler with explicit caveat
    
  if_critic_missing_or_error:
    action: continue_with_critique_incomplete_flag
    note: note in report_metadata that one critic did not complete
```

---

## Reconciliation (findings-evaluator)

After all critics return their reports, `findings-evaluator` reconciles:

1. Collect all three critic verdicts
2. If all PASS: proceed to confidence scoring
3. If any REVISE: aggregate issues, route back to producing agent with specific revisions required
4. If any FAIL: determine scope of failure
   - Single-critic FAIL with low severity: treat as REVISE
   - Single-critic FAIL with blocking severity: treat as FAIL
   - Multi-critic FAIL: FAIL — return to earlier phase

The reconciler does NOT average verdicts. A blocking FAIL from one critic overrides two PASSes.

---

## Instructions for the Producing Agent

When a revision is requested:

1. Read the specific checklist item that failed
2. Make only the targeted change
3. Do not rewrite sections that were not flagged
4. Resubmit the corrected section only (not the entire output)

Do not ask critics whether the revision is sufficient. Critics review the resubmitted output independently.

---

## Checklist Reference

| Phase | Checklist |
|-------|-----------|
| Phase 2: Data | `critique-checklists/data-checklist.md` |
| Phase 3: Analysis (methods) | `critique-checklists/methods-checklist.md` |
| Phase 3: Analysis (logic) | `critique-checklists/logic-checklist.md` |
| Phase 4-5: Synthesis and interpretation | `critique-checklists/interpretation-checklist.md` |
| Phase 6: Report | `critique-checklists/report-checklist.md` |
