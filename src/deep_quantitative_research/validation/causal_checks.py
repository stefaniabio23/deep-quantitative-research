"""Relationship classification.

Heuristic only. Maps the backtest's lead-lag profile and Granger feasibility
to the closed enum from spec section 7.9:

    causal | proxy | coincident | lagging | mechanically_linked
    | spurious | regime_dependent | unknown

"causal" is reserved for cases with strong evidence; the default for most
observational signals is "proxy".
"""

from __future__ import annotations

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


def classify_relationship(
    profile: list[dict[str, float | int]],
    *,
    predictor: pd.Series | None = None,
    target: pd.Series | None = None,
    survives_oos: bool = True,
    granger_alpha: float = 0.05,
) -> tuple[str, str]:
    """Return ``(relationship_type, justification)``.

    Heuristics:
    - Best lag > 0 and Granger-causal → "causal" (with strong caveats).
    - Best lag > 0 without Granger evidence → "proxy".
    - Best lag = 0 → "coincident".
    - Best lag < 0 → "lagging" (target leads predictor).
    - Signal does not survive OOS → "spurious".
    - Empty profile → "unknown".
    """
    if not profile:
        return "unknown", "no lead-lag profile available."

    if not survives_oos:
        return "spurious", "headline relationship did not survive out-of-sample."

    best_lag, best_corr = _best_lag_corr(profile)

    if best_lag == 0:
        return (
            "coincident",
            f"strongest correlation at lag 0 ({best_corr:.2f}); same-period co-movement.",
        )
    if best_lag < 0:
        return (
            "lagging",
            f"strongest correlation at lag {best_lag} ({best_corr:.2f}); "
            "target leads predictor.",
        )

    granger_p: float | None = None
    if predictor is not None and target is not None:
        granger_p = _granger_p(predictor, target, max_lag=min(4, max(1, best_lag + 1)))

    if granger_p is not None and granger_p < granger_alpha:
        return (
            "causal",
            f"best lag {best_lag} ({best_corr:.2f}); Granger p={granger_p:.3f} < {granger_alpha}; "
            "treat as causal with mechanism caveats from the hypothesis.",
        )
    if granger_p is not None:
        return (
            "proxy",
            f"best lag {best_lag} ({best_corr:.2f}); Granger p={granger_p:.3f} not significant; "
            "predictor likely a proxy, not a cause.",
        )
    return (
        "proxy",
        f"best lag {best_lag} ({best_corr:.2f}); no Granger evidence available; "
        "default to proxy.",
    )
