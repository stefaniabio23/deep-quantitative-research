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

**Finance examples:**
> "The analysis uses Pearson correlation on monthly equity returns. Returns are fat-tailed and heteroskedastic — Spearman rank correlation is more appropriate and should be reported alongside."

> "12 factor combinations were tested; 2 pass at p < 0.05. Without Bonferroni correction, the expected number of false discoveries at this rate is ~0.6 — the findings may be noise."

> "The regression uses levels of both variables without checking stationarity. If either series is I(1), the regression is spurious. ADF tests required."

**Biotech examples:**
> "The meta-analysis pools hazard ratios from trials with different patient populations, endpoints, and comparators. The I² statistic is not reported. Heterogeneity may make the pooled estimate uninterpretable."

> "Phase 2 sample sizes average n=47 in this dataset. The analysis estimates 5 parameters per trial. With this ratio, estimates are unstable — confidence intervals will be wide and the pattern may not replicate."

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

**Finance examples:**
> "The backtest uses current S&P 500 constituents as the universe, applied historically. This induces severe survivorship bias — roughly 50% of 2004 constituents are not in the current index. The strategy is picking stocks we know survived, which is information unavailable at the time."

> "Compustat data is used with period-end fiscal dates. Earnings are typically announced 30-60 days after period end. Any signal using fiscal-period variables before the announcement date is look-ahead biased."

**Biotech examples:**
> "ClinicalTrials.gov registration became mandatory in 2007. The analysis includes trials from 2000. Pre-2007 trial coverage is incomplete and skewed toward registered (typically positive or significant) trials. This understates historical termination rates."

> "The PubMed sentiment analysis weights papers equally regardless of journal impact or citation count. High-profile negative results (e.g., trial failures published in NEJM) should carry more weight than low-impact positive results. The current method may overstate field sentiment."

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

**Finance examples:**
> "Finding: regulatory filing speed predicts 30-day post-approval returns (r=0.31). Alternative explanation: pipeline quality drives both. Companies with better drugs file faster (more confident in their package) AND earn higher returns (better drugs command premium valuations). Filing speed is a proxy for drug quality, not an independent signal. Test: does the relationship hold when controlling for prior phase trial success rates?"

> "Finding: the value factor outperforms during high-inflation regimes. Alternative: the sample period (1970-2024) has limited high-inflation observations outside 1970-1982. The result may be driven by a single economic episode, not a general relationship. Test: what is the confidence interval on regime-conditional Sharpe ratios separately?"

**Biotech examples:**
> "Finding: upstream pathway targets have lower Phase 2→3 transition rates. Alternative: upstream targets are newer (KRAS only became druggable post-2019) and newer targets simply have less accumulated pipeline infrastructure and development expertise, not a pathway-specific biology problem. Test: does the pattern hold within cohorts of similar target age?"

> "Finding: sentiment leads trial terminations by ~3 years for PD-1. Alternative: the sentiment decline reflects the field rationally updating on early readouts from Phase 2 trials, which are the same trials that subsequently terminate. The sentiment and termination share a common cause (trial data) rather than sentiment predicting termination."

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
