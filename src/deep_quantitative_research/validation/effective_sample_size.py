"""Bartlett's effective-sample-size adjustment for correlation p-values.

Standard correlation inference assumes independent observations. When two
series are autocorrelated, the standard error of the sample correlation is
understated and the reported p-value is too small. The pipeline already
detects this with Ljung-Box; this module is the correction.

Bartlett's formula for the effective sample size of a correlation between
two stationary series with autocorrelations rho_x and rho_y::

    n_eff = n / (1 + 2 * sum_{k=1}^{m} (1 - k/n) * rho_x(k) * rho_y(k))

The check activates only when Ljung-Box rejects, so a series with no
detectable serial dependence pays no penalty.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .data_quality import Check
from .selection_bias import correlation_p_value


def autocorrelations(series: pd.Series, max_lag: int) -> list[float]:
    """Sample autocorrelations rho(1) ... rho(max_lag) for a cleaned series."""
    clean = series.dropna()
    n = len(clean)
    if n < max_lag + 5:
        return []
    centered = (clean - clean.mean()).to_numpy(dtype=float)
    var = float((centered ** 2).sum())
    if var <= 0:
        return [0.0] * max_lag
    out: list[float] = []
    for k in range(1, max_lag + 1):
        cov = float((centered[k:] * centered[:-k]).sum())
        out.append(cov / var)
    return out


def bartlett_effective_n(
    series_a: pd.Series,
    series_b: pd.Series,
    *,
    max_lag: int | None = None,
) -> int:
    """Effective sample size for the correlation between two series.

    Floored at 3 (a correlation needs three observations to have a defined
    p-value) and capped at the joint sample size.
    """
    joined = pd.concat([series_a.rename("a"), series_b.rename("b")], axis=1).dropna()
    n = len(joined)
    if n < 10:
        return n
    if max_lag is None:
        max_lag = max(1, int(n ** (1 / 3)))

    rho_a = autocorrelations(joined["a"], max_lag)
    rho_b = autocorrelations(joined["b"], max_lag)
    if not rho_a or not rho_b:
        return n

    correction = 1.0 + 2.0 * sum(
        (1 - k / n) * rho_a[k - 1] * rho_b[k - 1]
        for k in range(1, max_lag + 1)
    )
    if correction <= 0:
        # Negative-autocorrelation regime: take the conservative choice and
        # do not inflate n.
        return n
    return max(3, min(n, int(round(n / correction))))


def check_effective_sample_size(
    predictor: pd.Series,
    target: pd.Series,
    headline_corr: float,
    *,
    autocorr_ljungbox_p: float | None = None,
    alpha: float = 0.05,
    activation_p: float = 0.05,
) -> Check:
    """ESS-adjusted significance check, gated on Ljung-Box.

    When Ljung-Box does not reject (or no p is provided), the series have
    no detectable autocorrelation and the check passes trivially. When
    Ljung-Box rejects, the ESS-adjusted p-value becomes the headline.
    """
    joined = pd.concat([predictor.rename("p"), target.rename("t")], axis=1).dropna()
    n = len(joined)

    if n < 10 or np.isnan(headline_corr):
        return Check(
            name="effective_sample_size",
            verdict="warn",
            value=None,
            threshold=alpha,
            explanation="too few samples or NaN correlation; ESS adjustment skipped.",
        )

    if autocorr_ljungbox_p is None or autocorr_ljungbox_p >= activation_p:
        return Check(
            name="effective_sample_size",
            verdict="pass",
            value={"n": n, "n_eff": n, "ess_ratio": 1.0, "ess_adjusted_p": None},
            threshold=alpha,
            explanation=(
                "Ljung-Box did not detect autocorrelation; ESS adjustment "
                "not required."
            ),
        )

    n_eff = bartlett_effective_n(joined["p"], joined["t"])
    ess_p = correlation_p_value(headline_corr, n_eff)
    ess_ratio = float(n_eff) / n if n > 0 else 1.0

    value_block = {
        "n": int(n),
        "n_eff": int(n_eff),
        "ess_ratio": round(ess_ratio, 3),
        "ess_adjusted_p": round(ess_p, 4) if not math.isnan(ess_p) else None,
    }

    if not math.isnan(ess_p) and ess_p < alpha:
        verdict = "pass"
        explanation = (
            f"autocorrelation present (Ljung-Box rejected); ESS reduces n "
            f"from {n} to {n_eff}, headline still clears alpha at p={ess_p:.4f}."
        )
    else:
        verdict = "warn"
        explanation = (
            f"autocorrelation present (Ljung-Box rejected); ESS reduces n "
            f"from {n} to {n_eff}, headline does not reach significance at "
            f"p={ess_p:.4f}. Consider block bootstrap for confidence intervals."
        )

    return Check(
        name="effective_sample_size",
        verdict=verdict,
        value=value_block,
        threshold=alpha,
        explanation=explanation,
    )
