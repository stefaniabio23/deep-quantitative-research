"""Vintage-aware target loading.

Many macro / retail / employment series get restated after first
publication. A backtest against final-vintage data overstates the
apparent signal because it uses information that was not visible to a
real-time analyst.

This module reads a vintage CSV with three columns:

    observation_date, vintage_date, value

Each row says "at vintage_date, the published value for the period
observation_date was value." For a given observation_date there may be
multiple vintage_dates (initial release plus later revisions).

The module exposes:

- ``load_vintage_csv``: read the CSV into a typed DataFrame.
- ``first_vintage_series``: per-observation, take the first-published
  value. This is what an analyst would have known shortly after the
  observation period.
- ``as_of_series``: for an arbitrary as-of date, return the value that
  was visible at that date. This is the most general primitive; useful
  for walk-forward backtests.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = ("observation_date", "vintage_date", "value")


def load_vintage_csv(
    path: Path | str,
    *,
    observation_col: str = "observation_date",
    vintage_col: str = "vintage_date",
    value_col: str = "value",
) -> pd.DataFrame:
    """Read a vintage CSV into a DataFrame with parsed dates.

    Returns a DataFrame with columns ``observation_date``,
    ``vintage_date``, ``value`` (all coerced), sorted by
    ``(observation_date, vintage_date)`` so first-vintage lookups are
    trivially ``.first()``.
    """
    df = pd.read_csv(path)
    for col, expected in (
        (observation_col, "observation_date"),
        (vintage_col, "vintage_date"),
        (value_col, "value"),
    ):
        if col not in df.columns:
            raise KeyError(
                f"vintage CSV {path} is missing column {col!r}. "
                f"Required: {observation_col, vintage_col, value_col}."
            )

    df = df.rename(
        columns={
            observation_col: "observation_date",
            vintage_col: "vintage_date",
            value_col: "value",
        }
    )
    df["observation_date"] = pd.to_datetime(df["observation_date"])
    df["vintage_date"] = pd.to_datetime(df["vintage_date"])
    df["value"] = df["value"].astype(float)
    df = df.sort_values(["observation_date", "vintage_date"]).reset_index(drop=True)
    return df


def first_vintage_series(vintage_df: pd.DataFrame) -> pd.Series:
    """Per-observation, return the first-published value.

    The result is a Series indexed by ``observation_date`` with the
    value that was visible immediately after publication. This is the
    most common "honest" vintage view for KPI-prediction backtests.
    """
    if vintage_df.empty:
        return pd.Series(dtype=float, name="value")
    first = (
        vintage_df.sort_values(["observation_date", "vintage_date"])
        .groupby("observation_date", as_index=False)
        .first()
    )
    series = pd.Series(
        first["value"].values,
        index=pd.DatetimeIndex(first["observation_date"], name="date"),
        name="value",
    )
    return series.sort_index()


def as_of_series(
    vintage_df: pd.DataFrame,
    as_of_dates: pd.DatetimeIndex,
) -> pd.Series:
    """For each as-of date, return the latest value visible by that date.

    Walk-forward backtests should use this primitive: at each test
    timestamp t, the target value for any past observation is the
    largest-vintage_date entry with ``vintage_date <= t``.

    Implementation: for each as-of date, restrict to vintages <= as_of,
    then for each observation_date take the maximum vintage_date (the
    most recent value visible). Returns a Series indexed by the
    as-of dates carrying the observable target value at that as-of.
    For dates where no observation was visible, the value is NaN.
    """
    if vintage_df.empty:
        return pd.Series([float("nan")] * len(as_of_dates), index=as_of_dates, name="value")

    sorted_df = vintage_df.sort_values(["observation_date", "vintage_date"])
    out = []
    for ts in as_of_dates:
        visible = sorted_df[sorted_df["vintage_date"] <= ts]
        if visible.empty:
            out.append(float("nan"))
            continue
        # For each observation_date, take the latest vintage <= ts.
        latest = visible.groupby("observation_date", as_index=False).last()
        # The "current" observable value at as_of is the latest observation
        # date that has any vintage <= ts. Use the value at that observation.
        most_recent = latest.sort_values("observation_date").iloc[-1]
        out.append(float(most_recent["value"]))
    return pd.Series(out, index=as_of_dates, name="value")
