---
name: causal-inference
description: Classify the relationship between predictor and target as causal, proxy, coincident, lagging, mechanically linked, spurious, or regime dependent. Use the closed enum from spec section 7.9. Invoke after the backtest, before signal synthesis. Implementation reads the lead-lag profile, the best-feature embedded lag, the OOS survival verdict, and (when sample size allows) a Granger test. Blocks causal language in the signal card unless evidence justifies it.
---

# causal-inference

## When to invoke

After a KPI backtest produces a lead-lag profile and an OOS verdict, before the signal card is rendered. The classification flows into the `validation-report.yaml` as `relationship_type` and into the signal card.

The skill exists to keep the project's intellectual honesty: most observational signals are proxies, not causes, and naming them as such early prevents marketing creep later.

## Inputs

- The backtest's `lead_lag_profile` (correlation at each lag).
- The best-feature column name (carries the embedded `::lag_N` shift).
- `survives_oos` from the backtest verdict.
- Optional: the cadence-aligned predictor and target Series (for an optional Granger test when sample size permits).

## The closed enum

| Type | When |
|---|---|
| `causal` | Effective lead > 0 AND a Granger test rejects no-causality at α = 0.05 |
| `proxy` | Effective lead > 0 without Granger evidence; the conservative default for most signals |
| `coincident` | Effective lead == 0 |
| `lagging` | Effective lead < 0 (target leads predictor) |
| `mechanically_linked` | Variable B is an algebraic function of variable A (revenue = units × price); flag manually, the skill cannot detect it |
| `spurious` | OOS verdict is false |
| `regime_dependent` | OOS holds in some regimes and not others (set when a regime split fails) |
| `unknown` | Profile empty or skill cannot run |

## Procedure

1. Parse the best-feature name. Extract the embedded lag (`aact::raw::lag_1` → 1).
2. Find the best lag in the profile (the lag where |corr| is maximum).
3. Effective lead = embedded-feature lag + profile-best lag.
4. If `survives_oos` is false → `spurious`. Stop.
5. If effective lead < 0 → `lagging`. Stop.
6. If effective lead == 0 → `coincident`. Stop.
7. Effective lead > 0. Try Granger:
   - If predictor and target Series available and sample size ≥ max_lag + 10, run statsmodels' `grangercausalitytests`.
   - Take the minimum p-value across lags 1..max_lag.
   - If p < α → `causal`. Stop.
   - If p >= α → `proxy`.
8. If Granger unavailable → `proxy` (the conservative default).
9. Mechanical-link and regime-dependent classifications require human input; flag them in the recommendations rather than auto-assigning.

## Hard rules

- **Default to `proxy` when uncertain.** Calling a relationship causal when it is not invites worse decisions downstream.
- **Causal requires evidence beyond correlation.** Granger is necessary, not sufficient; the signal card should still caveat the call.
- **Mechanical links override every other classification.** If the analyst knows the predictor is definitionally part of the target, write `mechanically_linked` and skip the rest.
- **Spurious caps confidence at low.** Do not present a refuted signal as "would be medium without the OOS issue".

## Output

A `(relationship_type, justification)` tuple written into the `ValidationReport.relationship_type` field. The justification is appended to `recommended_next_iterations` when the type is `spurious` or `lagging` so the next iteration knows what to interrogate.

## Cross-references

- Implementation: `src/deep_quantitative_research/validation/causal_checks.py`.
- Reference: `skills/deep-quantitative-research/references/causal-inference-notes.md` (future Phase 8 fill).
- Spec: `BUILD_CHECKLIST.md` section 7.9.
