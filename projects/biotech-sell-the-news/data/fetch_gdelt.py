#!/usr/bin/env python3
"""Fetch pre-event news volume + tone per company from GDELT (free, no auth).

Uses the GDELT 2.0 DOC API timeline modes (timelinevol = article share over
time, timelinetone = average tone over time) queried by company name, then
writes data/news/<TICKER>.csv with columns date,article_count,avg_tone.

GDELT covers global news from 2015. The DOC API has no formal rate limit but
~1 req/sec is the community guidance, so calls are spaced and cached.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).parent
NEWS = HERE / "news"
DOC = "https://api.gdeltproject.org/api/v2/doc/doc"
SLEEP_S = 1.2


def _timeline(query: str, mode: str) -> pd.DataFrame:
    params = {
        "query": query,
        "mode": mode,
        "format": "json",
        "timespan": "10y",  # GDELT max history for the DOC API
    }
    data = None
    for attempt in range(5):
        r = requests.get(DOC, params=params, timeout=60)
        if r.status_code == 429:  # GDELT rate-limits aggressively; back off
            time.sleep(3 * (attempt + 1))
            continue
        if r.status_code != 200:
            return pd.DataFrame(columns=["date", "value"])  # graceful skip
        try:
            data = r.json()
        except ValueError:
            return pd.DataFrame(columns=["date", "value"])
        break
    if data is None:
        return pd.DataFrame(columns=["date", "value"])
    series = data.get("timeline", [])
    if not series:
        return pd.DataFrame(columns=["date", "value"])
    pts = series[0].get("data", [])
    rows = [(p["date"][:8], float(p["value"])) for p in pts]
    df = pd.DataFrame(rows, columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d").dt.date
    return df


def fetch_company(ticker: str, company_name: str) -> int:
    out = NEWS / f"{ticker}.csv"
    if out.exists():
        n = sum(1 for _ in out.open()) - 1
        print(f"  {ticker}: cached ({n} rows)")
        return n
    query = f'"{company_name}"'
    vol = _timeline(query, "timelinevol").rename(columns={"value": "article_count"})
    time.sleep(SLEEP_S)
    tone = _timeline(query, "timelinetone").rename(columns={"value": "avg_tone"})
    if vol.empty:
        print(f"  {ticker} ({company_name}): no GDELT coverage")
        return 0
    merged = vol.merge(tone, on="date", how="left")
    merged.to_csv(out, index=False)
    print(f"  {ticker} ({company_name}): {len(merged)} rows")
    return len(merged)


def main() -> int:
    NEWS.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(HERE / "events_seed.csv")
    pairs = events[["ticker", "company_name"]].drop_duplicates()
    print(f"Fetching GDELT timelines for {len(pairs)} companies...")
    for _, r in pairs.iterrows():
        fetch_company(str(r["ticker"]), str(r["company_name"]))
        time.sleep(SLEEP_S)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
