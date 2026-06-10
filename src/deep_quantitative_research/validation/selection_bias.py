"""Multiple-testing accounting: Bonferroni + deflated correlation.

A correlation reported without a trial count is not a finding. The gate
refuses to certify any result whose feature-search log does not record
``features_tested``. When the count is logged, a Bonferroni-adjusted
p-value and a deflated correlation (extreme-value adjustment for the
expected null-max across N trials) are surfaced alongside the headline.

References:
    Bailey & López de Prado (2014), *The Deflated Sharpe Ratio*. The
    deflated correlation implemented here is the correlation analogue:
    headline reduced by the expected maximum correlation under the null
    over N independent trials.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm
from scipy.stats import t as student_t

from .data_quality import Check


def bonferroni(p_values: list[float], *, alpha: float = 0.05) -> list[bool]:
    """Bonferroni: reject hypothesis i if p_i <= alpha / m.

    Conservative; trades power for strong control of family-wise error.
    """
    m = len(p_values)
    if m == 0:
        return []
    threshold = alpha / m
    return [p <= threshold for p in p_values]


def correlation_p_value(r: float, n: int) -> float:
    """Two-sided p-value for a sample correlation under the null of zero."""
    if n <= 2 or np.isnan(r):
        return float("nan")
    if abs(r) >= 1.0:
        return 0.0
    t_stat = r * math.sqrt(n - 2) / math.sqrt(max(1e-12, 1 - r * r))
    return float(2 * (1 - student_t.cdf(abs(t_stat), df=n - 2)))


def deflated_correlation(r: float, n: int, n_trials: int) -> float:
    """Deflate the headline correlation by the expected null-max over N trials.

    Returns ``r`` minus the expected maximum correlation under the null
    over ``n_trials`` independent tests of ``n`` samples. Preserves the
    sign of r; floor at zero so the deflated value never crosses sign.
    """
    if n_trials <= 1 or n <= 3 or np.isnan(r):
        return float(r)
    sigma_z = 1.0 / math.sqrt(n - 3)  # Fisher-z standard error approximation
    quantile = 1 - 1.0 / n_trials
    if quantile <= 0 or quantile >= 1:
        return float(r)
    expected_null_max_z = sigma_z * float(norm.ppf(quantile))
    # Back to correlation space via tanh^-1 inverse (Fisher-z); the
    # expected null max in r-space is approximately tanh(expected_null_max_z).
    correction = math.tanh(expected_null_max_z)
    sign = 1.0 if r >= 0 else -1.0
    return float(sign * max(0.0, abs(r) - correction))


def _one_sided_p(p_two_sided: float, observed_r: float, expected_direction: str | None) -> float:
    """Halve the two-sided p when the observed sign matches a pre-declared direction.

    A pre-specified directional hypothesis is testing a one-sided alternative;
    using a two-sided p wastes half the power for no methodological gain.
    """
    if math.isnan(p_two_sided) or expected_direction is None:
        return p_two_sided
    if expected_direction == "positive" and observed_r > 0:
        return p_two_sided / 2
    if expected_direction == "negative" and observed_r < 0:
        return p_two_sided / 2
    return p_two_sided


def check_selection_bias(
    headline_corr: float,
    sample_size: int,
    n_features_tested: int | None,
    *,
    alpha: float = 0.05,
    pre_specified: bool = False,
    expected_direction: str | None = None,
) -> Check:
    """Refuse to certify a correlation without logged trial count.

    Failure modes:
    - ``n_features_tested`` is None or 0 → ``fail``. The gate refuses to
      issue a confidence cap without a denominator.
    - Pre-specified single feature → ``pass``, no correction required.
    - Bonferroni-adjusted p-value < ``alpha`` → ``pass``.
    - Bonferroni-adjusted p-value >= ``alpha`` → ``warn``; the result is
      plausibly a search artifact. The check value carries the deflated
      correlation so a reader can see how much of the headline survives.
    """
    if n_features_tested is None or n_features_tested <= 0:
        return Check(
            name="multiple_testing",
            verdict="fail",
            value=None,
            threshold=alpha,
            explanation=(
                "features_tested not logged; the gate refuses to certify a "
                "result without a denominator. Record the trial count in "
                "feature_search_log.features_tested."
            ),
        )
    if sample_size <= 3:
        return Check(
            name="multiple_testing",
            verdict="warn",
            value=None,
            threshold=alpha,
            explanation=(
                "sample size too small to compute a Bonferroni-adjusted "
                "p-value reliably."
            ),
        )
    if np.isnan(headline_corr):
        return Check(
            name="multiple_testing",
            verdict="warn",
            value=None,
            threshold=alpha,
            explanation="headline correlation is NaN; selection-bias check skipped.",
        )

    if pre_specified:
        # Pre-specification commits the analyst to a hypothesis before looking
        # at the data; the headline gets the raw p, no Bonferroni inflation
        # regardless of how many other features were tried as sanity checks.
        # A pre-specified DIRECTIONAL hypothesis additionally gets a one-sided
        # test (half the p) when the observed sign matches.
        p_two = correlation_p_value(headline_corr, sample_size)
        p = _one_sided_p(p_two, headline_corr, expected_direction)
        value_block = {
            "p": round(p, 4) if not math.isnan(p) else None,
            "adjusted_p": None,
            "deflated_r": round(headline_corr, 4),
        }
        if not math.isnan(p) and p < alpha:
            return Check(
                name="multiple_testing",
                verdict="pass",
                value=value_block,
                threshold=alpha,
                explanation=(
                    f"pre-specified feature; p={p:.4f} < {alpha}. "
                    "No Bonferroni inflation needed because the analyst "
                    "committed to this feature in advance."
                ),
            )
        # Pre-specified but not significant even at the raw p: warn (not
        # fail) because the commitment limits the false-positive risk to
        # what the raw p reflects.
        return Check(
            name="multiple_testing",
            verdict="warn",
            value=value_block,
            threshold=alpha,
            explanation=(
                f"pre-specified feature; raw p={p:.4f} >= {alpha}. "
                "Result is suggestive but does not reach significance at "
                "the chosen alpha."
            ),
        )

    p = correlation_p_value(headline_corr, sample_size)
    adjusted_p = min(1.0, p * n_features_tested) if not math.isnan(p) else float("nan")
    deflated = deflated_correlation(headline_corr, sample_size, n_features_tested)

    value_block = {
        "p": round(p, 4) if not math.isnan(p) else None,
        "adjusted_p": round(adjusted_p, 4) if not math.isnan(adjusted_p) else None,
        "deflated_r": round(deflated, 4),
    }

    if not math.isnan(adjusted_p) and adjusted_p < alpha:
        verdict = "pass"
        explanation = (
            f"headline r={headline_corr:.3f} survives Bonferroni at "
            f"m={n_features_tested} (adjusted p={adjusted_p:.4f} < {alpha}). "
            f"Deflated r={deflated:.3f}."
        )
    else:
        # Bonferroni rejects: the headline does not clear multiple-testing
        # at the chosen alpha. With no pre-specification to limit the
        # false-positive risk, the result is plausibly noise. Cap the
        # overall verdict at low.
        verdict = "fail"
        adj_str = f"{adjusted_p:.4f}" if not math.isnan(adjusted_p) else "nan"
        explanation = (
            f"headline r={headline_corr:.3f} does NOT survive Bonferroni at "
            f"m={n_features_tested} (adjusted p={adj_str} >= {alpha}). "
            f"Deflated r={deflated:.3f}. Result is plausibly a search artifact."
        )

    return Check(
        name="multiple_testing",
        verdict=verdict,
        value=value_block,
        threshold=alpha,
        explanation=explanation,
    )
