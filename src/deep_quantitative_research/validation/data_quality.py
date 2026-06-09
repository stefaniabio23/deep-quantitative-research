"""Data quality checks: sample size, missingness, outliers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class Check:
    name: str
    verdict: str  # pass | warn | fail
    value: Any
    threshold: Any
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "verdict": self.verdict,
            "value": self.value,
            "threshold": self.threshold,
            "explanation": self.explanation,
        }


def check_sample_size(
    n: int,
    *,
    low: int = 30,
    medium: int = 60,
    high: int = 120,
) -> Check:
    if n >= high:
        verdict = "pass"
        explanation = f"{n} samples clears every tier."
    elif n >= medium:
        verdict = "warn"
        explanation = f"{n} samples is enough for medium; high requires {high}."
    elif n >= low:
        verdict = "warn"
        explanation = f"{n} samples is enough for low only; medium requires {medium}."
    else:
        verdict = "fail"
        explanation = f"{n} samples is below the low threshold of {low}."
    return Check(
        name="sample_size",
        verdict=verdict,
        value=int(n),
        threshold={"low": low, "medium": medium, "high": high},
        explanation=explanation,
    )


def check_missingness(
    series: pd.Series,
    *,
    warn_pct: float = 5.0,
    fail_pct: float = 25.0,
) -> Check:
    if series.empty:
        return Check(
            name="missingness",
            verdict="fail",
            value=100.0,
            threshold={"warn": warn_pct, "fail": fail_pct},
            explanation="series is empty.",
        )
    pct = float(series.isna().mean() * 100)
    if pct >= fail_pct:
        verdict = "fail"
    elif pct >= warn_pct:
        verdict = "warn"
    else:
        verdict = "pass"
    return Check(
        name="missingness",
        verdict=verdict,
        value=round(pct, 2),
        threshold={"warn": warn_pct, "fail": fail_pct},
        explanation=f"{pct:.1f}% of observations are NaN.",
    )


def check_outliers(
    series: pd.Series,
    *,
    z_threshold: float = 4.0,
) -> Check:
    clean = series.dropna()
    if len(clean) < 4:
        return Check(
            name="outliers",
            verdict="warn",
            value=None,
            threshold=z_threshold,
            explanation="not enough observations to score outliers.",
        )
    std = clean.std(ddof=0)
    if std == 0:
        return Check(
            name="outliers",
            verdict="pass",
            value=0,
            threshold=z_threshold,
            explanation="series is constant; no outliers possible.",
        )
    z = ((clean - clean.mean()) / std).abs()
    extremes = int((z > z_threshold).sum())
    if extremes == 0:
        verdict = "pass"
    elif extremes / len(clean) < 0.01:
        verdict = "warn"
    else:
        verdict = "fail"
    return Check(
        name="outliers",
        verdict=verdict,
        value=extremes,
        threshold=z_threshold,
        explanation=f"{extremes} observations exceed |z| > {z_threshold}.",
    )
