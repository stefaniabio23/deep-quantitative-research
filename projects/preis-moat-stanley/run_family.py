#!/usr/bin/env python3
"""Family-wide Bonferroni test for the Preis-Moat-Stanley replication.

Runs the same zscore_12 / lag_k feature across 10 search terms x 3 lags
= 30 trials. Computes:

- Train (in-sample) correlation and Bonferroni-adjusted p (m = 30).
- Test (OOS) correlation and Bonferroni-adjusted p (m = 30).
- The publication-decay diff: train_r - test_r per trial.
- Family-wide verdict: do any (term, lag) pairs survive Bonferroni at
  alpha = 0.05?

Output
- expected-output/family-results.csv: one row per (term, lag) trial.
- expected-output/family-summary.md: a markdown table + headline result.
- stdout: a printable summary.

The point: even the in-sample (pre-publication) headline does not
survive proper multiple-testing accounting at m = 30. The
Preis-Moat-Stanley 2013 result was selection bias from the start.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Pipeline primitives
from deep_quantitative_research.timeseries.transformations import zscore
from deep_quantitative_research.validation.selection_bias import correlation_p_value

HERE = Path(__file__).parent
DATA_DIR = HERE / "data"
OUT_DIR = HERE / "expected-output"

# Train window matches the SignalSpec; covers the available pre-2014
# data (the original paper's 2004-2011 in-sample window overlaps the
# tail of this; we don't have weekly Google Trends back to 2004).
TRAIN_START = pd.Timestamp("2008-12-07")
TRAIN_END = pd.Timestamp("2014-12-31")
# Test window is fully out-of-sample relative to the paper's 2013
# publication; covers post-publication through 2025-09-30.
TEST_START = pd.Timestamp("2015-01-04")
TEST_END = pd.Timestamp("2025-09-28")

# Z-score window matches the SignalSpec's chosen transform; 3 lags
# matches the SignalSpec's lag set (1, 2, 3).
ZSCORE_WINDOW = 12
LAGS = (1, 2, 3)
ALPHA = 0.05

# Family terms; m = 10 terms x 3 lags = 30 trials.
FAMILY_TERMS = [
    "debt",
    "stocks",
    "credit",
    "unemployment",
    "inflation",
    "recession",
    "mortgage",
    "savings",
    "investment",
    "bankruptcy",
]


def load_inputs() -> tuple[pd.Series, dict[str, pd.Series]]:
    target_path = DATA_DIR / "target.csv"
    family_path = DATA_DIR / "predictors_family.csv"
    if not target_path.exists() or not family_path.exists():
        raise SystemExit(
            f"missing data files; run ./data/fetch_data.py first. Expected:\n"
            f"  {target_path}\n  {family_path}"
        )
    target = pd.read_csv(target_path, parse_dates=["date"]).set_index("date")["value"]
    family = pd.read_csv(family_path, parse_dates=["date"])
    predictors: dict[str, pd.Series] = {}
    for term, group in family.groupby("term"):
        predictors[str(term)] = group.set_index("date")["value"].astype(float).sort_index()
    return target.astype(float).sort_index(), predictors


def run_trial(
    target: pd.Series,
    predictor: pd.Series,
    *,
    lag_periods: int,
) -> tuple[float, float, int, float, float, int]:
    """Return (train_corr, train_p_raw, train_n, test_corr, test_p_raw, test_n)."""
    feature = zscore(predictor, window=ZSCORE_WINDOW).shift(lag_periods)
    joined = pd.concat([target.rename("y"), feature.rename("x")], axis=1).dropna()
    train = joined[(joined.index >= TRAIN_START) & (joined.index <= TRAIN_END)]
    test = joined[(joined.index >= TEST_START) & (joined.index <= TEST_END)]
    train_r = float(train["x"].corr(train["y"])) if len(train) > 3 else float("nan")
    test_r = float(test["x"].corr(test["y"])) if len(test) > 3 else float("nan")
    train_p = correlation_p_value(train_r, len(train))
    test_p = correlation_p_value(test_r, len(test))
    return train_r, train_p, len(train), test_r, test_p, len(test)


def render_markdown_summary(df: pd.DataFrame, m: int, alpha: float) -> str:
    train_survivors = df[df["train_p_bonferroni"] < alpha]
    test_survivors = df[df["test_p_bonferroni"] < alpha]

    headline = []
    headline.append(
        f"**Family-wide Bonferroni at m = {m} trials (alpha = {alpha}):**"
    )
    headline.append("")
    headline.append(
        f"- In-sample (train, 2008-12 to 2014-12) survivors: "
        f"**{len(train_survivors)} of {m}**."
    )
    headline.append(
        f"- Out-of-sample (test, 2015-01 to 2025-09) survivors: "
        f"**{len(test_survivors)} of {m}**."
    )
    if not len(train_survivors):
        headline.append("")
        headline.append(
            "The original Preis-Moat-Stanley 2013 result does not survive "
            "honest multiple-testing accounting even in-sample. The famous "
            "326% PnL was selection bias from the 98-keyword search."
        )

    lines = ["", "## Family-wide Bonferroni results", ""]
    lines.append("| Term | Lag | Train r | Train n | Test r | Test n | Train p (raw) | Train p (Bonferroni, m=30) | Test p (raw) | Test p (Bonferroni, m=30) | Decay (|r_train|−|r_test|) |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for _, row in df.sort_values(["term", "lag"]).iterrows():
        decay = abs(row["train_r"]) - abs(row["test_r"])
        lines.append(
            f"| {row['term']} | {int(row['lag'])} "
            f"| {row['train_r']:.3f} | {int(row['train_n'])} "
            f"| {row['test_r']:.3f} | {int(row['test_n'])} "
            f"| {row['train_p_raw']:.3f} | {row['train_p_bonferroni']:.3f} "
            f"| {row['test_p_raw']:.3f} | {row['test_p_bonferroni']:.3f} "
            f"| {decay:+.3f} |"
        )

    return "\n".join(headline + lines) + "\n"


def main() -> int:
    target, predictors = load_inputs()

    rows = []
    for term in FAMILY_TERMS:
        if term not in predictors:
            print(f"skipping {term!r}: not in predictors_family.csv")
            continue
        for lag_periods in LAGS:
            train_r, train_p, train_n, test_r, test_p, test_n = run_trial(
                target, predictors[term], lag_periods=lag_periods
            )
            rows.append(
                {
                    "term": term,
                    "lag": lag_periods,
                    "train_r": train_r,
                    "train_p_raw": train_p,
                    "train_n": train_n,
                    "test_r": test_r,
                    "test_p_raw": test_p,
                    "test_n": test_n,
                }
            )

    df = pd.DataFrame(rows)
    m = len(df)
    df["train_p_bonferroni"] = (df["train_p_raw"] * m).clip(upper=1.0)
    df["test_p_bonferroni"] = (df["test_p_raw"] * m).clip(upper=1.0)
    df["train_survives_bonferroni"] = df["train_p_bonferroni"] < ALPHA
    df["test_survives_bonferroni"] = df["test_p_bonferroni"] < ALPHA

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "family-results.csv"
    df.to_csv(csv_path, index=False)

    summary = render_markdown_summary(df, m=m, alpha=ALPHA)
    summary_path = OUT_DIR / "family-summary.md"
    summary_path.write_text(summary)

    print(summary)
    print()
    print(f"wrote {csv_path}")
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
