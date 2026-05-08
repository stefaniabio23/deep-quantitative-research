# Critique Cluster

A parallel adversarial review phase. Three critics run simultaneously, each attacking the analysis from a different angle. Their outputs feed `findings-evaluator`, which reconciles them with the main analysis.

The critics are trying to break the analysis. A finding that survives all three is stronger. One that doesn't needs to be qualified or retracted.

---

## When it runs

Controlled by `run_critique_cluster` in SKILL.md:

| Mode | Runs? | require_all_critics | allow_revision_loop |
|------|-------|--------------------|--------------------|
| quick | No | — | — |
| full | Yes | No | No |
| thesis-test | Yes | Yes | No |
| data-first | Yes | No | No |
| literature | Yes | No | No |
| thorough | Yes | Yes | Yes |

If `require_all_critics: false` and one critic fails, `findings-evaluator` proceeds with `critique_incomplete: true` on that dimension.

If `require_all_critics: true` and one critic fails, it retries once. If it fails again, the pipeline pauses and alerts the user.

---

## methods-critic

**Attacks:** Statistical choices, sample adequacy, test selection, multiple comparisons, stationarity assumptions, model specification.

Questions to answer:
- Is the statistical test appropriate for the data structure (distribution, dependence, time series properties)?
- Is the sample size adequate for the number of parameters estimated?
- How many tests were run? Has a multiple comparisons correction been applied?
- Are stationarity assumptions checked for time series inputs?
- Is the model specification justified, or were alternative specifications tried and discarded?
- Does the effect size meet domain-appropriate thresholds, or is it statistically significant but practically negligible?

```yaml
methods_critique:
  challenges:
    - id: MC1
      aspect: string
      severity: critical | moderate | minor
      challenge: string
      suggested_alternative: string
      verdict: FATAL | WEAKENS | MINOR_CAVEAT
  overall_assessment: string
  fatal_flaws: integer
```

---

## data-critic

**Attacks:** Data provenance, survivorship bias, look-ahead leakage, coverage gaps, selection effects, measurement error, staleness.

Questions to answer:
- Is there any path by which future information entered the analysis window?
- Which entities are absent from the dataset that should be present? What direction does this bias create?
- How was the universe defined? Could the definition be endogenous to the outcome?
- Is the data source known to have systematic errors for this domain?
- How old is the most recent data? Is this a current or historical snapshot?
- For biotech: does publication bias affect the literature search?

```yaml
data_critique:
  challenges:
    - id: DC1
      bias_type: look_ahead | survivorship | selection | coverage | measurement | staleness
      severity: critical | moderate | minor
      challenge: string
      evidence: string
      verdict: FATAL | WEAKENS | MINOR_CAVEAT
  overall_assessment: string
  fatal_flaws: integer
```

---

## logic-critic

**Attacks:** The causal story, alternative explanations, scope of claims, internal consistency, leap from data to conclusion.

Questions to answer:
- What is the strongest alternative explanation that does not require the claimed mechanism?
- Is causality direction established, or could it run the other way?
- Does the conclusion match the scope of the analysis? (Don't claim global when tested in a subset.)
- Are there internal inconsistencies between findings from different phases?
- What known theory or prior evidence contradicts this finding? Has it been addressed?
- Would an informed domain expert find this conclusion surprising? If yes, is the surprise justified?

```yaml
logic_critique:
  challenges:
    - id: LC1
      type: alternative_explanation | reverse_causality | scope_overreach | inconsistency | contradicts_prior
      severity: critical | moderate | minor
      challenge: string
      counter_argument: string
      verdict: FATAL | WEAKENS | MINOR_CAVEAT
  overall_assessment: string
  fatal_flaws: integer
```

---

## Independence requirement

The three critics do not see each other's outputs. They receive only the main analysis outputs. Reconciliation is `findings-evaluator`'s job.

If two critics independently raise the same challenge, that is a stronger signal than if one was anchored on the other's framing.

---

## Reconciliation in findings-evaluator

For each challenge raised by any critic:
1. Already addressed by existing analysis: cite evidence, mark resolved
2. Addressable with feasible additional analysis: flag as actionable
3. Cannot be resolved: becomes residual risk in final output

Challenges with `verdict: FATAL` require explicit user acknowledgement before the report proceeds.

---

## Thorough mode: revision loop

If `allow_revision_loop: true`, a FATAL challenge routes back to the relevant analysis agent for a targeted fix (not back to question-sharpener). Maximum 2 revision rounds. If FATAL challenges remain after 2 rounds, the finding is reported as WEAKENED with full documentation.
