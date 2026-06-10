#!/usr/bin/env python3
"""Fetch real data for the Preis-Moat-Stanley replication.

- DJIA: yfinance ^DJI daily close → weekly returns (week ending Sunday).
- Google Trends: pytrends "debt" (and a basket of related terms) weekly
  interest, stitched across multi-year chunks because pytrends switches to
  monthly granularity above ~5-year windows.

Outputs land in this directory:
  target.csv               weekly DJIA close-to-close return
  predictor_debt.csv       weekly Google Trends interest in "debt"
  predictors_family.csv    long-format CSV of the term family for the
                           multiple-testing story

The Google Trends index is normalized per chunk by Google (0-100); we do
not rescale across chunks because the pipeline's zscore transforms handle
within-window normalization for us.

Network calls are slow and Google Trends rate-limits aggressively; the
script retries each chunk a few times and sleeps between fetches.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

OUT_DIR = Path(__file__).parent

START = "2004-01-04"
END = "2025-09-30"
CHUNK_YEARS = 4  # pytrends gives weekly cadence up to about 5y; leave headroom

# The headline term plus a small basket for the multiple-testing demo.
# Preis-Moat-Stanley searched 98 keywords; this is a representative
# subset spanning finance, economy, lifestyle, and general anxiety.
FAMILY = [
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


def fetch_djia_weekly() -> pd.DataFrame:
    import yfinance as yf

    print(f"Fetching DJIA (^DJI) {START} -> {END} ...")
    daily = yf.download("^DJI", start=START, end=END, progress=False, auto_adjust=False)
    if daily.empty:
        raise RuntimeError("yfinance returned no DJIA data; check connectivity.")
    if isinstance(daily.columns, pd.MultiIndex):
        daily.columns = daily.columns.get_level_values(0)
    close = daily["Close"].astype(float)
    weekly_close = close.resample("W-SUN").last().dropna()
    weekly_return = weekly_close.pct_change().dropna()
    out = weekly_return.rename("value").to_frame()
    out.index.name = "date"
    return out.reset_index()


def fetch_trends_chunked(keyword: str, *, sleep_between: float = 1.5, retries: int = 3) -> pd.Series:
    """Stitch weekly Google Trends interest for ``keyword`` across the full range.

    Each chunk gets its own 0-100 normalization by Google; downstream we
    rely on the zscore-12 / zscore-24 transforms to absorb the per-chunk
    scale shift. For the multiple-testing question the absolute scale is
    irrelevant.
    """
    from pytrends.request import TrendReq

    # Don't pass retries / backoff_factor through; pytrends forwards them to a
    # urllib3 Retry that no longer accepts method_whitelist. Our own retry loop
    # handles transient failures.
    pytrend = TrendReq(hl="en-US", tz=360)

    chunks: list[pd.Series] = []
    cursor = pd.Timestamp(START)
    end_ts = pd.Timestamp(END)
    while cursor < end_ts:
        chunk_end = min(cursor + pd.DateOffset(years=CHUNK_YEARS, months=11), end_ts)
        timeframe = f"{cursor.date()} {chunk_end.date()}"
        last_exc: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                pytrend.build_payload([keyword], timeframe=timeframe, geo="US")
                df = pytrend.interest_over_time()
                if df.empty:
                    print(f"  [{keyword}] empty chunk {timeframe}")
                    break
                df = df[~df["isPartial"]]
                chunks.append(df[keyword].rename(keyword))
                print(f"  [{keyword}] {timeframe}: {len(df)} rows")
                break
            except Exception as exc:  # pragma: no cover - depends on network
                last_exc = exc
                print(f"  [{keyword}] attempt {attempt}/{retries} on {timeframe} failed: {exc}")
                time.sleep(sleep_between * attempt)
        else:
            print(f"  [{keyword}] giving up on {timeframe} after {retries} retries: {last_exc}")
        cursor = chunk_end + pd.Timedelta(days=1)
        time.sleep(sleep_between)

    if not chunks:
        return pd.Series(name=keyword, dtype=float)
    stitched = pd.concat(chunks)
    # Multiple chunks may overlap at the edges due to how pytrends rounds
    # weeks; keep the first observation in case of duplicates.
    stitched = stitched[~stitched.index.duplicated(keep="first")]
    stitched = stitched.sort_index()
    stitched.index.name = "date"
    return stitched


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True, parents=True)

    djia = fetch_djia_weekly()
    djia_path = OUT_DIR / "target.csv"
    djia.to_csv(djia_path, index=False)
    print(f"\nWrote {len(djia)} DJIA weekly returns to {djia_path}")

    # Headline term: "debt"
    debt = fetch_trends_chunked("debt")
    if debt.empty:
        print("ERROR: no Google Trends data for 'debt'. Aborting.")
        return 1
    debt_df = debt.to_frame("value").reset_index()
    debt_path = OUT_DIR / "predictor_debt.csv"
    debt_df.to_csv(debt_path, index=False)
    print(f"Wrote {len(debt_df)} 'debt' rows to {debt_path}")

    # Family for multiple-testing story
    family_frames = []
    for term in FAMILY:
        if term == "debt":
            series = debt
        else:
            series = fetch_trends_chunked(term)
        if series.empty:
            print(f"  skipping {term!r}: no data")
            continue
        df = series.to_frame("value").reset_index()
        df["term"] = term
        family_frames.append(df)

    if family_frames:
        family_df = pd.concat(family_frames, ignore_index=True)[["term", "date", "value"]]
        family_path = OUT_DIR / "predictors_family.csv"
        family_df.to_csv(family_path, index=False)
        print(f"Wrote {len(family_df)} family rows ({len(family_frames)} terms) to {family_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
