#!/usr/bin/env python3
"""Stage 1 of the ALFRED revision-momentum study.

Two questions, both answered from ALFRED vintages alone:

1. Revision momentum. Does the signed first revision of a macro series
   predict the next period's first revision? For each series and lag k,
   correlate revision_t against revision_{t-k}, with Bonferroni
   correction over the m = (series x lags) family and an out-of-sample
   split. A positive, surviving correlation is evidence that revisions
   are not white noise.

2. Point-in-time gap. Compute month-over-month growth two ways: on
   first-vintage (real-time) values and on final-vintage (fully revised)
   values. Report the lag-1 autocorrelation of growth under each. The
   final-vintage number overstates real-time predictability; the gap is
   the information leak that PIT discipline removes.

Outputs (into the chosen --out dir, default expected-output/):
- stage1-momentum.csv : one row per (series, lag) trial.
- pit-gap.csv         : one row per series, first- vs final-vintage AC.
- stage1-summary.md   : rendered markdown verdict.

Run `python3 run_revision_momentum.py --self-test` to verify the analysis
recovers a planted revision-momentum signal on synthetic vintages, no
network or FRED key required.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from deep_quantitative_research.timeseries.vintage import (
    final_vintage_series,
    first_revisions,
    first_vintage_series,
    load_vintage_csv,
)
from deep_quantitative_research.validation.selection_bias import correlation_p_value

HERE = Path(__file__).parent
DATA_DIR = HERE / "data"
OUT_DIR = HERE / "expected-output"

SERIES = [
    ("PAYEMS", "nonfarm payrolls"),
    ("RSAFS", "retail sales"),
    ("INDPRO", "industrial production"),
]
LAGS = (1, 2, 3)
# Out-of-sample split: revisions observed from 2015 on are the OOS set.
SPLIT = pd.Timestamp("2015-01-01")
ALPHA = 0.05
# ALFRED vintage archives start decades after some series begin. For
# observations predating real-time coverage, the earliest archived vintage
# is not the genuine initial release, so its "first revision" is an artifact.
# Keep only observations whose first vintage lands within ~one quarter of the
# observation date (a real initial print we actually caught).
MAX_FIRST_RELEASE_LAG_DAYS = 92


def timely_vintage_df(
    vdf: pd.DataFrame, max_lag_days: int = MAX_FIRST_RELEASE_LAG_DAYS
) -> pd.DataFrame:
    """Restrict to observations with a genuine (timely) first release."""
    if vdf.empty:
        return vdf
    first_v = vdf.groupby("observation_date")["vintage_date"].min()
    lag_days = (first_v - first_v.index.to_series()).dt.days
    keep = set(lag_days[lag_days <= max_lag_days].index)
    return vdf[vdf["observation_date"].isin(keep)]


def _corr(joined: pd.DataFrame) -> tuple[float, float, int]:
    n = len(joined)
    if n <= 3:
        return float("nan"), float("nan"), n
    r = float(joined["x"].corr(joined["y"]))
    return r, correlation_p_value(r, n), n


def momentum_trials(revisions: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for sid, _label in SERIES:
        rev = revisions.get(sid)
        if rev is None or rev.empty:
            continue
        for k in LAGS:
            joined = pd.concat(
                [rev.rename("y"), rev.shift(k).rename("x")], axis=1
            ).dropna()
            full_r, full_p, full_n = _corr(joined)
            oos = joined[joined.index >= SPLIT]
            oos_r, oos_p, oos_n = _corr(oos)
            rows.append(
                {
                    "series": sid,
                    "lag": k,
                    "full_r": full_r,
                    "full_p_raw": full_p,
                    "full_n": full_n,
                    "oos_r": oos_r,
                    "oos_p_raw": oos_p,
                    "oos_n": oos_n,
                }
            )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    m = len(df)
    df["full_p_bonferroni"] = (df["full_p_raw"] * m).clip(upper=1.0)
    df["oos_p_bonferroni"] = (df["oos_p_raw"] * m).clip(upper=1.0)
    df["full_survives"] = df["full_p_bonferroni"] < ALPHA
    df["oos_survives"] = df["oos_p_bonferroni"] < ALPHA
    return df


def sign_persistence(revisions: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for sid, _label in SERIES:
        rev = revisions.get(sid)
        if rev is None:
            continue
        signs = np.sign(rev.dropna().values)
        signs = signs[signs != 0]
        if len(signs) < 4:
            continue
        same = (signs[1:] == signs[:-1]).astype(float)
        share = float(same.mean())
        n = len(same)
        # z under the 50%-same null (a coin flip on sign agreement).
        z = (share - 0.5) / np.sqrt(0.25 / n)
        rows.append({"series": sid, "n_pairs": n, "same_sign_share": share, "z_vs_half": z})
    return pd.DataFrame(rows)


def pit_gap(vintage_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for sid, _label in SERIES:
        vdf = vintage_frames.get(sid)
        if vdf is None or vdf.empty:
            continue
        first = first_vintage_series(vdf).pct_change().dropna()
        final = final_vintage_series(vdf).pct_change().dropna()
        ac_first = float(first.corr(first.shift(1)))
        ac_final = float(final.corr(final.shift(1)))
        rows.append(
            {
                "series": sid,
                "ac1_first_vintage": ac_first,
                "ac1_final_vintage": ac_final,
                "gap_final_minus_first": ac_final - ac_first,
            }
        )
    return pd.DataFrame(rows)


def render_summary(
    mom: pd.DataFrame, persist: pd.DataFrame, gap: pd.DataFrame, m: int
) -> str:
    lines = ["# ALFRED revision-momentum, stage 1", ""]
    if mom.empty:
        lines.append("No revision data available. Run data/fetch_alfred.py first.")
        return "\n".join(lines) + "\n"

    full_survivors = int(mom["full_survives"].sum())
    oos_survivors = int(mom["oos_survives"].sum())
    lines.append(f"**Revision momentum, Bonferroni at m = {m} trials (alpha = {ALPHA}):**")
    lines.append("")
    lines.append(f"- Full-sample survivors: **{full_survivors} of {m}**.")
    lines.append(f"- Out-of-sample (>= 2015) survivors: **{oos_survivors} of {m}**.")
    lines.append("")
    lines.append("## Momentum trials")
    lines.append("")
    lines.append(
        "| Series | Lag | Full r | Full n | Full p (Bonferroni) | OOS r | OOS n | OOS p (Bonferroni) |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for _, r in mom.sort_values(["series", "lag"]).iterrows():
        lines.append(
            f"| {r['series']} | {int(r['lag'])} | {r['full_r']:.3f} | {int(r['full_n'])} "
            f"| {r['full_p_bonferroni']:.3f} | {r['oos_r']:.3f} | {int(r['oos_n'])} "
            f"| {r['oos_p_bonferroni']:.3f} |"
        )

    if not persist.empty:
        lines += ["", "## Sign persistence (share of consecutive revisions sharing sign)", ""]
        lines.append("| Series | Pairs | Same-sign share | z vs 0.5 |")
        lines.append("|---|---:|---:|---:|")
        for _, r in persist.iterrows():
            lines.append(
                f"| {r['series']} | {int(r['n_pairs'])} | {r['same_sign_share']:.3f} | {r['z_vs_half']:.2f} |"
            )

    if not gap.empty:
        lines += ["", "## Point-in-time gap (lag-1 autocorrelation of MoM growth)", ""]
        lines.append("| Series | First-vintage AC1 | Final-vintage AC1 | Gap (final - first) |")
        lines.append("|---|---:|---:|---:|")
        for _, r in gap.iterrows():
            lines.append(
                f"| {r['series']} | {r['ac1_first_vintage']:.3f} | {r['ac1_final_vintage']:.3f} "
                f"| {r['gap_final_minus_first']:+.3f} |"
            )
        lines.append("")
        lines.append(
            "A positive gap means a naive analyst using fully-revised data "
            "would see growth autocorrelation that was not knowable in real time."
        )

    return "\n".join(lines) + "\n"


def run(data_dir: Path, out_dir: Path) -> pd.DataFrame:
    vintage_frames: dict[str, pd.DataFrame] = {}
    revisions: dict[str, pd.Series] = {}
    for sid, _label in SERIES:
        path = data_dir / f"{sid}_vintages.csv"
        if not path.exists():
            continue
        vdf = timely_vintage_df(load_vintage_csv(path))
        vintage_frames[sid] = vdf
        revisions[sid] = first_revisions(vdf)

    mom = momentum_trials(revisions)
    persist = sign_persistence(revisions)
    gap = pit_gap(vintage_frames)
    m = len(mom)

    out_dir.mkdir(parents=True, exist_ok=True)
    if not mom.empty:
        mom.to_csv(out_dir / "stage1-momentum.csv", index=False)
    if not gap.empty:
        gap.to_csv(out_dir / "pit-gap.csv", index=False)
    summary = render_summary(mom, persist, gap, m)
    (out_dir / "stage1-summary.md").write_text(summary)
    print(summary)
    return mom


def _self_test() -> int:
    """Plant AR(1) revision momentum and confirm the runner recovers it."""
    rng = np.random.default_rng(7)
    months = pd.date_range("1990-01-31", "2024-12-31", freq="ME")
    with tempfile.TemporaryDirectory() as td:
        data_dir = Path(td) / "data"
        data_dir.mkdir()
        # PAYEMS gets a strong planted momentum; the others are noise.
        for sid in ("PAYEMS", "RSAFS", "INDPRO"):
            rev = np.zeros(len(months))
            phi = 0.6 if sid == "PAYEMS" else 0.0
            for i in range(1, len(months)):
                rev[i] = phi * rev[i - 1] + rng.normal(0, 1.0)
            rows = ["observation_date,vintage_date,value"]
            level = 100.0
            for i, obs in enumerate(months):
                level += rng.normal(0.2, 0.5)
                first_v = obs + pd.Timedelta(days=45)
                second_v = obs + pd.Timedelta(days=365)
                rows.append(f"{obs.date()},{first_v.date()},{level:.4f}")
                rows.append(f"{obs.date()},{second_v.date()},{level + rev[i]:.4f}")
            (data_dir / f"{sid}_vintages.csv").write_text("\n".join(rows) + "\n")

        out_dir = Path(td) / "out"
        mom = run(data_dir, out_dir)

    payems_lag1 = mom[(mom["series"] == "PAYEMS") & (mom["lag"] == 1)].iloc[0]
    assert payems_lag1["full_r"] > 0.4, payems_lag1["full_r"]
    assert payems_lag1["full_survives"], "planted PAYEMS momentum should survive Bonferroni"
    rsafs_lag1 = mom[(mom["series"] == "RSAFS") & (mom["lag"] == 1)].iloc[0]
    assert not rsafs_lag1["full_survives"], "noise series should not survive"
    print("\nself-test OK: planted PAYEMS momentum recovered, noise rejected.")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    out_dir = OUT_DIR
    if "--out" in argv:
        out_dir = Path(argv[argv.index("--out") + 1])
    if not any((DATA_DIR / f"{sid}_vintages.csv").exists() for sid, _ in SERIES):
        raise SystemExit(
            "No vintage CSVs in data/. Run data/fetch_alfred.py first "
            "(needs FRED_API_KEY), or use --self-test for a synthetic check."
        )
    run(DATA_DIR, out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
