# Confidence tiers

The confidence cap in a validation report compresses a complex set of
checks into a single label. Without explicit semantics, "medium" decays
into "looks okay-ish." This doc fixes the semantics so a reader of a
signal card knows exactly what they're entitled to assume.

## Tier definitions

### High

The cap is **high** when every required check passes and the headline
survives every adversarial probe. The result is conclusive at the
chosen alpha after multiple-testing correction.

| Required check | Threshold |
|---|---|
| `sample_size` | >= 120 observations on the test window |
| `missingness` | pass (< 5% missing) |
| `outliers` | pass or warn (no clustered extremes) |
| `stationarity_adf` | pass (ADF rejects unit root) |
| `stationarity_kpss` | pass (KPSS does not reject stationarity) |
| `autocorrelation` (Ljung-Box) | pass, OR ESS-adjusted check passes |
| `lookahead` | pass (release lags applied) |
| `multiple_testing` | pre-specified pass, OR Bonferroni-clear at the chosen alpha |
| `walk_forward` | enabled and validation windows traversed |
| `regime_split` | pass (if enabled) |
| `lag_sensitivity` | pass (headline survives ±1 lag) |
| `outlier_sensitivity` | pass (headline survives top-1% drop) |
| `effective_sample_size` | pass (no ESS shrinkage required, or ESS-adjusted p still clears alpha) |
| `survives_oos` | True with sign-confirmed Bonferroni-adjusted (or one-sided pre-spec) significance |

**Reader entitlements at high:**

- Treat the relationship as established with the chosen alpha.
- Use the signal as a primary input in production decisions, subject to the run's caveats.
- Cite the signal as confirmed evidence in a thesis or memo.

### Medium

The cap is **medium** when the headline is well-supported but at least
one structural check warns. The result is plausible but not yet
conclusive at the chosen alpha.

Typical binding constraints at medium:

- `sample_size` warn (60 to 119 test observations).
- `regime_split` warn (correlation diverges across the split).
- `lag_sensitivity` warn (result depends strongly on a single lag).
- `stationarity_adf` warn (cannot reject unit root; consider transforms).
- `outlier_sensitivity` warn (drop-1% changes the correlation materially).

**Reader entitlements at medium:**

- Treat the relationship as probable but not definitive.
- Use the signal as one input among many in a decision, not the sole driver.
- Cite the signal as suggestive evidence; pair with corroborating signals before acting.

### Low

The cap is **low** when any required check fails or the headline does
not survive multiple-testing correction.

Triggered by any of:

- `multiple_testing` fail (Bonferroni rejects; not pre-specified).
- `survives_oos` False (no statistical survival, or sign mismatch).
- `sample_size` fail (< 30 observations).
- `missingness` fail (>= 25% missing).
- Any other `fail` verdict across the catalogue.

**Reader entitlements at low:**

- Treat the relationship as not yet established.
- Do not use the signal as a basis for production decisions.
- Cite the signal as a hypothesis under investigation, not as evidence.

A low cap with a named binding constraint is the canonical
**documented null.** It says: "We looked. With this data and these
checks, we cannot claim a signal." That is a valid finding, not a
failure of the pipeline.

## What confidence does NOT mean

- **Confidence is not the predictor's correlation magnitude.** A strong
  sample correlation with too few observations is still low.
- **Confidence is not the analyst's belief.** Priors are irrelevant
  once the data has been checked.
- **Confidence is not a probability of being right.** It is a tier in
  a defined discipline.

## Reader summary

| Tier | Decision use | Citation strength | Production-ready |
|---|---|---|---|
| Low | Hypothesis only | Under investigation | No |
| Medium | One input among many | Suggestive | With caveats |
| High | Primary input | Confirmed | Yes |

## Where tier thresholds live

In `config/validation_thresholds.yaml`. The thresholds for each check
(`sample_size`, `missingness`, etc.) define what passes / warns / fails.
The gate caps the overall confidence at the lowest tier any required
check produces.

The mapping from per-check verdict to tier:

| Verdict | Tier ceiling |
|---|---|
| `pass` | high |
| `warn` | medium |
| `fail` | low |

The overall cap is the minimum across every check.

## When a tier feels wrong

Two failure modes:

- **Medium feels too low for what I see.** Read the binding constraint.
  The failure is named; either fix the underlying issue (more data,
  different transform, different cadence) or accept the cap.
- **Medium feels too high for what I see.** The thresholds may be too
  lenient for the use case. Tighten in `validation_thresholds.yaml`
  for this run, or open an issue to propose a global tightening.

The whole point of the discipline is that the tier is not negotiated.
