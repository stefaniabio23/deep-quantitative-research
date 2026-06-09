"""Stationarity and autocorrelation diagnostics.

Wraps statsmodels primitives behind the ``Check`` dataclass so the gate
treats them uniformly. Each function returns a ``Check`` with pass / warn /
fail verdict, the observed value, the threshold, and a one-line explanation.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from .data_quality import Check


def _clean(series: pd.Series, min_len: int = 20) -> pd.Series | None:
    s = series.dropna()
    if len(s) < min_len:
        return None
    return s


def check_stationarity_adf(series: pd.Series, *, alpha: float = 0.05) -> Check:
    """Augmented Dickey-Fuller. Null: non-stationary (unit root present).

    p < alpha → reject the null → series is stationary → pass.
    p >= alpha → cannot reject → likely non-stationary → warn.
    """
    s = _clean(series)
    if s is None:
        return Check(
            name="stationarity_adf",
            verdict="warn",
            value=None,
            threshold=alpha,
            explanation="fewer than 20 observations; ADF unreliable.",
        )
    try:
        from statsmodels.tsa.stattools import adfuller

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = adfuller(s.values, autolag="AIC")
        p_value = float(result[1])
    except Exception as exc:  # pragma: no cover - statsmodels backend issues
        return Check(
            name="stationarity_adf",
            verdict="warn",
            value=None,
            threshold=alpha,
            explanation=f"ADF failed: {exc}",
        )
    if p_value < alpha:
        verdict = "pass"
        explanation = f"ADF p={p_value:.3f} < {alpha}; series is stationary."
    else:
        verdict = "warn"
        explanation = (
            f"ADF p={p_value:.3f} >= {alpha}; cannot reject unit root, "
            "consider differencing or detrending."
        )
    return Check(
        name="stationarity_adf",
        verdict=verdict,
        value=round(p_value, 4),
        threshold=alpha,
        explanation=explanation,
    )


def check_stationarity_kpss(series: pd.Series, *, alpha: float = 0.05) -> Check:
    """KPSS. Null: stationary. Complementary to ADF.

    p < alpha → reject the null → series is non-stationary → warn.
    p >= alpha → cannot reject → likely stationary → pass.
    """
    s = _clean(series)
    if s is None:
        return Check(
            name="stationarity_kpss",
            verdict="warn",
            value=None,
            threshold=alpha,
            explanation="fewer than 20 observations; KPSS unreliable.",
        )
    try:
        from statsmodels.tsa.stattools import kpss

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            stat, p_value, *_ = kpss(s.values, regression="c", nlags="auto")
        p_value = float(p_value)
    except Exception as exc:  # pragma: no cover
        return Check(
            name="stationarity_kpss",
            verdict="warn",
            value=None,
            threshold=alpha,
            explanation=f"KPSS failed: {exc}",
        )
    if p_value >= alpha:
        verdict = "pass"
        explanation = f"KPSS p={p_value:.3f} >= {alpha}; series is stationary."
    else:
        verdict = "warn"
        explanation = (
            f"KPSS p={p_value:.3f} < {alpha}; null of stationarity rejected, "
            "treat as non-stationary."
        )
    return Check(
        name="stationarity_kpss",
        verdict=verdict,
        value=round(p_value, 4),
        threshold=alpha,
        explanation=explanation,
    )


def check_autocorrelation(
    series: pd.Series,
    *,
    lags: int = 10,
    alpha: float = 0.05,
) -> Check:
    """Ljung-Box test for residual serial correlation.

    Apply to the residual of a regression, typically. Here used as a check on
    a series's own dependence structure. Null: no autocorrelation.
    """
    s = _clean(series)
    if s is None:
        return Check(
            name="autocorrelation",
            verdict="warn",
            value=None,
            threshold=alpha,
            explanation="fewer than 20 observations; autocorrelation check unreliable.",
        )
    try:
        from statsmodels.stats.diagnostic import acorr_ljungbox

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lag_count = min(lags, max(1, len(s) // 4))
            result = acorr_ljungbox(s.values, lags=[lag_count], return_df=True)
        p_value = float(result["lb_pvalue"].iloc[0])
    except Exception as exc:  # pragma: no cover
        return Check(
            name="autocorrelation",
            verdict="warn",
            value=None,
            threshold=alpha,
            explanation=f"Ljung-Box failed: {exc}",
        )
    if p_value < alpha:
        verdict = "warn"
        explanation = (
            f"Ljung-Box p={p_value:.3f} < {alpha}; residuals have serial "
            "correlation. Standard errors understated; use Newey-West."
        )
    else:
        verdict = "pass"
        explanation = f"Ljung-Box p={p_value:.3f} >= {alpha}; no significant autocorrelation."
    return Check(
        name="autocorrelation",
        verdict=verdict,
        value=round(p_value, 4),
        threshold=alpha,
        explanation=explanation,
    )
