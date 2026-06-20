#!/usr/bin/env python3
"""Fetch ALFRED vintage histories for the revision-momentum study.

ALFRED is FRED's archival service: it stores every historical vintage of
a series, so you can reconstruct exactly what was published on any date.
We use the FRED observations endpoint with ``output_type=3`` ("new and
revised observations only"), which returns, for each observation period,
one row per time its value changed, tagged with the vintage date the new
value took effect. That is the full revision history in a single call,
and it maps directly onto the long vintage schema the pipeline expects:

    observation_date, vintage_date, value

Outputs (written next to this script, in ./):
- PAYEMS_vintages.csv, RSAFS_vintages.csv, INDPRO_vintages.csv  (stage 1)
- DGS10.csv, DGS2.csv                                            (stage 2)

Requires a free FRED API key in the environment (FRED_API_KEY) or in a
.env file at the repo root. Get one: https://fred.stlouisfed.org/docs/api/api_key.html
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).parent
REPO_ROOT = HERE.parents[2]
BASE = "https://api.stlouisfed.org/fred/series/observations"

# Stage 1: heavily-revised monthly macro series.
VINTAGE_SERIES = ["PAYEMS", "RSAFS", "INDPRO"]
# Stage 2: Treasury yields (current vintage is fine; no revisions).
ASSET_SERIES = ["DGS10", "DGS2"]

WIDE_START = "1900-01-01"
WIDE_END = "9999-12-31"
POLITE_SLEEP_S = 0.6  # FRED allows ~120 req/min; stay well under.


def _load_api_key() -> str:
    key = os.environ.get("FRED_API_KEY", "").strip()
    if key:
        return key
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("FRED_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                if key:
                    return key
    raise SystemExit(
        "FRED_API_KEY not found. Add it to the environment or to "
        f"{env_path} (copy from .env.example). Free key: "
        "https://fred.stlouisfed.org/docs/api/api_key.html"
    )


def _get(params: dict[str, str]) -> dict:
    for attempt in range(4):
        resp = requests.get(BASE, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:  # rate limited; back off
            time.sleep(2 ** attempt)
            continue
        raise SystemExit(
            f"FRED request failed ({resp.status_code}) for "
            f"{params.get('series_id')}: {resp.text[:200]}"
        )
    raise SystemExit("FRED request failed after retries (rate limit).")


def fetch_vintages(series_id: str, api_key: str) -> int:
    """Fetch the full revision history; write <series_id>_vintages.csv."""
    data = _get(
        {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "output_type": "3",  # new and revised observations only
            "realtime_start": WIDE_START,
            "realtime_end": WIDE_END,
        }
    )
    rows = []
    for obs in data.get("observations", []):
        value = obs.get("value", ".")
        if value in (".", "", None):  # FRED's missing-value sentinel
            continue
        rows.append(
            (obs["date"], obs["realtime_start"], value)
        )
    if not rows:
        raise SystemExit(f"{series_id}: no observations returned.")
    out = HERE / f"{series_id}_vintages.csv"
    lines = ["observation_date,vintage_date,value"]
    lines += [f"{obs},{vint},{val}" for obs, vint, val in rows]
    out.write_text("\n".join(lines) + "\n")
    print(f"  {series_id}: {len(rows)} vintage rows -> {out.name}")
    return len(rows)


def fetch_current(series_id: str, api_key: str) -> int:
    """Fetch the current (latest-vintage) series; write <series_id>.csv."""
    data = _get(
        {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
        }
    )
    rows = [
        (obs["date"], obs["value"])
        for obs in data.get("observations", [])
        if obs.get("value", ".") not in (".", "", None)
    ]
    if not rows:
        raise SystemExit(f"{series_id}: no observations returned.")
    out = HERE / f"{series_id}.csv"
    lines = ["date,value"] + [f"{d},{v}" for d, v in rows]
    out.write_text("\n".join(lines) + "\n")
    print(f"  {series_id}: {len(rows)} rows -> {out.name}")
    return len(rows)


def main() -> int:
    api_key = _load_api_key()
    print("Fetching ALFRED vintage histories (stage 1)...")
    for sid in VINTAGE_SERIES:
        fetch_vintages(sid, api_key)
        time.sleep(POLITE_SLEEP_S)
    print("Fetching Treasury yields (stage 2)...")
    for sid in ASSET_SERIES:
        fetch_current(sid, api_key)
        time.sleep(POLITE_SLEEP_S)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
