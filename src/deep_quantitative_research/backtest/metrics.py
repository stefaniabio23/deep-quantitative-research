"""KPI-prediction metrics. Tradable metrics live in trading_backtest (Phase 4b)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class KpiMetrics:
    correlation: float
    rank_correlation: float
    directional_accuracy: float
    mae: float
    mape: float
    rmse: float
    hit_rate: float
    sample_size: int

    def to_dict(self) -> dict[str, float | int]:
        return {
            "correlation": _round(self.correlation),
            "rank_correlation": _round(self.rank_correlation),
            "directional_accuracy": _round(self.directional_accuracy),
            "mae": _round(self.mae),
            "mape": _round(self.mape),
            "rmse": _round(self.rmse),
            "hit_rate": _round(self.hit_rate),
            "sample_size": self.sample_size,
        }


def _round(x: float, n: int = 4) -> float:
    if x is None or np.isnan(x):
        return float("nan")
    return float(np.round(x, n))


def _safe_corr(a: pd.Series, b: pd.Series, method: str) -> float:
    if len(a) < 3:
        return float("nan")
    try:
        return float(a.corr(b, method=method))
    except Exception:  # pragma: no cover - defensive
        return float("nan")


def kpi_metrics(predictor: pd.Series, target: pd.Series) -> KpiMetrics:
    """Compute the full KPI panel between predictor and target.

    Both series are aligned on the inner index. NaN pairs are dropped before
    computation; the surviving count becomes ``sample_size``.
    """
    joined = pd.concat([predictor.rename("p"), target.rename("t")], axis=1).dropna()
    if joined.empty:
        return KpiMetrics(
            correlation=float("nan"),
            rank_correlation=float("nan"),
            directional_accuracy=float("nan"),
            mae=float("nan"),
            mape=float("nan"),
            rmse=float("nan"),
            hit_rate=float("nan"),
            sample_size=0,
        )

    p, t = joined["p"], joined["t"]
    correlation = _safe_corr(p, t, "pearson")
    rank = _safe_corr(p, t, "spearman")

    direction_match = np.sign(p) == np.sign(t)
    directional = float(direction_match.mean()) if len(direction_match) else float("nan")

    error = (p - t).abs()
    mae = float(error.mean())
    # MAPE is only meaningful when the target is strictly positive. For
    # signed series (returns, deltas), it blows up near zero and on sign
    # flips; surface NaN rather than a meaningless number.
    if (t > 0).all() and len(t) > 0:
        mape = float((error / t).mean() * 100)
    else:
        mape = float("nan")
    rmse = float(np.sqrt(((p - t) ** 2).mean()))

    # Hit rate: predictor sign agrees with realised target sign. Same as
    # directional_accuracy here; kept distinct so future variants (top-decile,
    # sign-of-change) can diverge cleanly.
    hit = directional

    return KpiMetrics(
        correlation=correlation,
        rank_correlation=rank,
        directional_accuracy=directional,
        mae=mae,
        mape=mape,
        rmse=rmse,
        hit_rate=hit,
        sample_size=int(len(joined)),
    )


def lead_lag_profile(
    predictor: pd.Series,
    target: pd.Series,
    *,
    max_lag: int = 6,
) -> list[dict[str, float | int]]:
    """Pearson correlation at predictor shifts 0..max_lag.

    Positive lag = predictor leads target. The profile is the diagnostic
    that tells you whether your "the predictor leads" claim holds.
    """
    profile: list[dict[str, float | int]] = []
    for k in range(0, max_lag + 1):
        corr = _safe_corr(predictor.shift(k), target, "pearson")
        profile.append({"lag": k, "corr": _round(corr)})
    return profile


def oos_degradation(train_metric: float, test_metric: float) -> float:
    """Percent drop from train to test. Negative when test improves.

    Returns ``nan`` if either input is nan or train is zero.
    """
    if np.isnan(train_metric) or np.isnan(test_metric) or train_metric == 0:
        return float("nan")
    return float(_round(((train_metric - test_metric) / train_metric) * 100, 2))
