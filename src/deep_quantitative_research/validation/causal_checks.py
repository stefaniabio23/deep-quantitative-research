"""Relationship classification.

Heuristic only. Maps the backtest's lead-lag profile and Granger feasibility
to the closed enum from spec section 7.9:

    causal | proxy | coincident | lagging | mechanically_linked
    | spurious | regime_dependent | unknown

"causal" is reserved for cases with strong evidence; the default for most
observational signals is "proxy".
"""

from __future__ import annotations

import re
import warnings
from typing import Iterable

import numpy as np
import pandas as pd


def _best_lag_corr(profile: Iterable[dict[str, float | int]]) -> tuple[int, float]:
    best_lag = 0
    best_corr = 0.0
    for entry in profile:
        corr = entry.get("corr")
        if corr is None or np.isnan(corr):
            continue
        if abs(corr) > abs(best_corr):
            best_corr = corr
            best_lag = int(entry["lag"])
    return best_lag, best_corr


def _granger_p(
    predictor: pd.Series,
    target: pd.Series,
    *,
    max_lag: int = 4,
) -> float | None:
    joined = pd.concat([target.rename("t"), predictor.rename("p")], axis=1).dropna()
    if len(joined) < max_lag + 10:
        return None
    try:
        from statsmodels.tsa.stattools import grangercausalitytests

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            results = grangercausalitytests(joined[["t", "p"]], maxlag=max_lag, verbose=False)
    except Exception:  # pragma: no cover - statsmodels backend issues
        return None
    p_values = []
    for lag in range(1, max_lag + 1):
        try:
            p_values.append(float(results[lag][0]["ssr_ftest"][1]))
        except (KeyError, IndexError):
            continue
    return min(p_values) if p_values else None


_FEATURE_LAG_RE = re.compile(r"::lag_(\d+)$")


def _feature_lag(feature_name: str | None) -> int:
    """Parse the embedded ``::lag_N`` suffix from a feature column name."""
    if not feature_name:
        return 0
    match = _FEATURE_LAG_RE.search(feature_name)
    return int(match.group(1)) if match else 0


def classify_relationship(
    profile: list[dict[str, float | int]],
    *,
    predictor: pd.Series | None = None,
    target: pd.Series | None = None,
    survives_oos: bool = True,
    granger_alpha: float = 0.05,
    feature_name: str | None = None,
) -> tuple[str, str]:
    """Return ``(relationship_type, justification)``.

    The lead-lag profile is computed against the already-lagged best
    feature, so its lag-0 represents the headline. The true predictor-to-
    target lead is the sum of the feature's embedded lag plus the best lag
    in the profile.

    Heuristics:
    - Effective lead > 0 with Granger evidence → "causal".
    - Effective lead > 0 without Granger → "proxy".
    - Effective lead == 0 → "coincident".
    - Effective lead < 0 → "lagging" (target leads predictor).
    - Signal does not survive OOS → "spurious".
    - Empty profile → "unknown".
    """
    if not profile:
        return "unknown", "no lead-lag profile available."

    if not survives_oos:
        return "spurious", "headline relationship did not survive out-of-sample."

    profile_lag, best_corr = _best_lag_corr(profile)
    feature_lag = _feature_lag(feature_name)
    effective_lead = feature_lag + profile_lag

    if effective_lead == 0:
        return (
            "coincident",
            f"effective predictor-to-target lead is 0 (feature lag {feature_lag} + "
            f"profile lag {profile_lag}); same-period co-movement at corr={best_corr:.2f}.",
        )
    if effective_lead < 0:
        return (
            "lagging",
            f"effective lead is {effective_lead} (feature lag {feature_lag} + "
            f"profile lag {profile_lag}); target leads predictor at corr={best_corr:.2f}.",
        )

    granger_p: float | None = None
    if predictor is not None and target is not None:
        granger_p = _granger_p(predictor, target, max_lag=min(4, max(1, effective_lead + 1)))

    if granger_p is not None and granger_p < granger_alpha:
        return (
            "causal",
            f"effective lead {effective_lead} (feature lag {feature_lag} + "
            f"profile lag {profile_lag}); Granger p={granger_p:.3f} < {granger_alpha}; "
            "treat as causal with mechanism caveats from the hypothesis.",
        )
    if granger_p is not None:
        return (
            "proxy",
            f"effective lead {effective_lead}; Granger p={granger_p:.3f} not significant; "
            "predictor likely a proxy, not a cause.",
        )
    return (
        "proxy",
        f"effective lead {effective_lead}; no Granger evidence available; default to proxy.",
    )
