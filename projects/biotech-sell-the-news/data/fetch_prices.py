#!/usr/bin/env python3
"""Fetch daily prices for the event tickers + the XBI benchmark (yfinance).

Writes data/prices/<TICKER>.csv with columns date,close (auto-adjusted).
yfinance is a fragile wrapper around undocumented Yahoo endpoints and throttles
on 429, so calls are spaced and cached (a present file is not refetched).
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import yfinance as yf

HERE = Path(__file__).parent
PRICES = HERE / "prices"
BENCHMARK = "XBI"
SLEEP_S = 1.0


def fetch_one(ticker: str) -> int:
    out = PRICES / f"{ticker}.csv"
    if out.exists():
        n = sum(1 for _ in out.open()) - 1
        print(f"  {ticker}: cached ({n} rows)")
        return n
    df = yf.Ticker(ticker).history(period="max", auto_adjust=True)
    if df.empty:
        print(f"  {ticker}: NO DATA (delisted or bad symbol)")
        return 0
    out_df = df.reset_index()[["Date", "Close"]].rename(
        columns={"Date": "date", "Close": "close"}
    )
    out_df["date"] = pd.to_datetime(out_df["date"]).dt.tz_localize(None).dt.date
    out_df.to_csv(out, index=False)
    print(f"  {ticker}: {len(out_df)} rows")
    return len(out_df)


def main() -> int:
    PRICES.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(HERE / "events_seed.csv")
    tickers = sorted(set(events["ticker"].astype(str)) | {BENCHMARK})
    print(f"Fetching {len(tickers)} tickers (incl. {BENCHMARK} benchmark)...")
    for t in tickers:
        fetch_one(t)
        time.sleep(SLEEP_S)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
