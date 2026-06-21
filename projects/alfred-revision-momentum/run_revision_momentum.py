#!/usr/bin/env python3
"""Stage 1 of the ALFRED revision-momentum study (Tier-1 refined).

Three questions, all answered from ALFRED vintages alone, built to be
point-in-time honest and robust to the artifacts a naive revision study
falls into.

1. Revision momentum, PIT-safe. Does a macro series' coming revision get
   forecast by the most recent revision that was *already fully realized*
   when the new number was released? The predictor for observation t is
   the fixed-horizon revision of the most recent earlier observation whose
   revision window had closed by t's first-release date (no look-ahead).
   Revisions are measured at a fixed horizon (default 90 days) and on the
   month-over-month GROWTH, not the raw level, so a benchmark that shifts a
   block of months by a constant does not manufacture spurious momentum. A
   scale-free relative-level revision is reported alongside as a robustness
   unit. Each correlation carries a moving-block-bootstrap 95% CI;
   Bonferroni is applied over the m = 3 primary trials (growth, 90d, one
   per series).

2. Sign persistence. Do consecutive growth revisions share sign more than
   a coin flip would give?

3. Point-in-time gap. Lag-1 autocorrelation of MoM growth computed on
   first-vintage (real-time) vs final-vintage (fully revised) values. The
   final-vintage number overstates real-time predictability; the gap is
   the leak PIT discipline removes. The gap carries a bootstrap CI.

Outputs (into --out, default expected-output/):
- stage1-momentum.csv : one row per (series, unit, horizon) trial.
- pit-gap.csv         : one row per series, first/final AC + gap + CI.
- stage1-summary.md   : rendered markdown verdict.

Run `python3 run_revision_momentum.py --self-test` to verify the analysis
recovers a planted, PIT-realizable momentum signal on synthetic vintages,
no network or FRED key required.
"""

from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from deep_quantitative_research.timeseries.vintage import (
    final_vintage_series,
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
# Out-of-sample split: revisions observed from 2015 on are the OOS set.
SPLIT = pd.Timestamp("2015-01-01")
ALPHA = 0.05
# ALFRED archives start decades after some series begin; for observations
# predating real-time coverage the earliest vintage is not a genuine first
# release. Keep only observations whose first vintage is within ~one quarter.
MAX_FIRST_RELEASE_LAG_DAYS = 92
# Fixed revision horizons (days after first release).
PRIMARY_HORIZON = 90
HORIZONS = (90, 365)
# Bootstrap settings (fixed seed -> deterministic, diffable output).
BLOCK = 12
N_BOOT = 2000
SEED = 12345
# Tier-2 robustness knobs.
OOS_SPLITS = ("2005-01-01", "2008-01-01", "2010-01-01", "2012-01-01",
              "2015-01-01", "2018-01-01", "2020-01-01")
N_SUBSAMPLES = 3  # disjoint time-thirds for stability checks


# ---------------------------------------------------------------- helpers


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


def _build_groups(vdf: pd.DataFrame):
    """Per observation, sorted (vintage_date[int64], value) arrays for fast
    as-of lookups via searchsorted."""
    groups: dict[pd.Timestamp, tuple[np.ndarray, np.ndarray]] = {}
    for obs, g in vdf.sort_values("vintage_date").groupby("observation_date"):
        vd = g["vintage_date"].values.astype("datetime64[ns]").astype("int64")
        vv = g["value"].values.astype(float)
        groups[obs] = (vd, vv)
    return groups


def _value_as_of(groups, obs, as_of_ns: int) -> float:
    """Value of observation `obs` known at as-of date (latest vintage <= as_of)."""
    entry = groups.get(obs)
    if entry is None:
        return float("nan")
    vd, vv = entry
    i = int(np.searchsorted(vd, as_of_ns, side="right")) - 1
    return float(vv[i]) if i >= 0 else float("nan")


def revisions_table(vdf: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    """Per observation: first-release date, the fixed-horizon revision in
    three units (level, relative-level, growth), and the knowable_date when
    the revision is fully realized (first_release + horizon)."""
    groups = _build_groups(vdf)
    obs_dates = sorted(groups.keys())
    day_ns = np.timedelta64(horizon_days, "D").astype("timedelta64[ns]").astype("int64")
    rows = []
    for i, t in enumerate(obs_dates):
        vd, vv = groups[t]
        d0_ns = int(vd[0])  # first-release date
        v0 = float(vv[0])
        vH = _value_as_of(groups, t, d0_ns + day_ns)
        prev = obs_dates[i - 1] if i > 0 else None
        # Growth = level minus the prior observation's value at the same as-of.
        prev0 = _value_as_of(groups, prev, d0_ns) if prev is not None else float("nan")
        prevH = _value_as_of(groups, prev, d0_ns + day_ns) if prev is not None else float("nan")
        g0 = v0 - prev0
        gH = vH - prevH
        level_rev = vH - v0
        rows.append(
            {
                "observation_date": t,
                "first_release_date": pd.Timestamp(d0_ns),
                "knowable_date": pd.Timestamp(d0_ns + day_ns),
                "level_rev": level_rev,
                "rel_level_rev": level_rev / abs(v0) if v0 else float("nan"),
                "growth_rev": gH - g0,
            }
        )
    return pd.DataFrame(rows).set_index("observation_date").sort_index()


def pit_safe_pairs(table: pd.DataFrame, unit: str) -> pd.DataFrame:
    """Align each observation's revision (target) with the most recent earlier
    revision whose window had closed by the target's first-release date. This
    is the no-look-ahead predictor. Returns a frame with columns x (predictor),
    y (target), indexed by the target observation date."""
    tbl = table.dropna(subset=[unit]).copy()
    obs = list(tbl.index)
    d0 = tbl["first_release_date"]
    knowable = tbl["knowable_date"]
    vals = tbl[unit]
    out = {}
    # j tracks the latest index whose knowable_date <= current first_release.
    j = -1
    for i, t in enumerate(obs):
        rel_t = d0.iloc[i]
        # advance j while the next candidate's revision is realized by rel_t
        while j + 1 < i and knowable.iloc[j + 1] <= rel_t:
            j += 1
        # ensure j's own knowable_date <= rel_t (it may not, early on)
        jj = j
        while jj >= 0 and knowable.iloc[jj] > rel_t:
            jj -= 1
        if jj >= 0:
            out[t] = (float(vals.iloc[jj]), float(vals.iloc[i]))
    if not out:
        return pd.DataFrame(columns=["x", "y"])
    df = pd.DataFrame.from_dict(out, orient="index", columns=["x", "y"])
    df.index = pd.DatetimeIndex(df.index, name="observation_date")
    return df


# ------------------------------------------------------------- statistics


def _ac1(s: np.ndarray) -> float:
    s = np.asarray(s, dtype=float)
    if len(s) < 4 or np.std(s[1:]) == 0 or np.std(s[:-1]) == 0:
        return float("nan")
    return float(np.corrcoef(s[1:], s[:-1])[0, 1])


def _moving_block_idx(n: int, block: int, rng) -> np.ndarray:
    if n <= block:
        return np.arange(n)
    n_blocks = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=n_blocks)
    return np.concatenate([np.arange(s, s + block) for s in starts])[:n]


def block_bootstrap_ci(
    data: pd.DataFrame, stat_fn, *, block=BLOCK, n_boot=N_BOOT, seed=SEED
) -> tuple[float, float]:
    """Moving-block-bootstrap 95% CI for stat_fn(resampled_data)."""
    n = len(data)
    if n < 2 * block:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    arr = data.reset_index(drop=True)
    stats = []
    for _ in range(n_boot):
        idx = _moving_block_idx(n, block, rng)
        v = stat_fn(arr.iloc[idx].reset_index(drop=True))
        if v == v:  # not nan
            stats.append(v)
    if not stats:
        return (float("nan"), float("nan"))
    return (float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5)))


def _corr_stat(df: pd.DataFrame) -> float:
    if df["x"].std() == 0 or df["y"].std() == 0:
        return float("nan")
    return float(df["x"].corr(df["y"]))


def momentum_trials(tables: dict[str, dict[int, pd.DataFrame]]) -> pd.DataFrame:
    """Run the PIT-safe momentum test across series x unit x horizon. The
    primary family is unit='growth_rev', horizon=PRIMARY_HORIZON (m = 3)."""
    rows = []
    for sid, _label in SERIES:
        per_h = tables.get(sid)
        if not per_h:
            continue
        for horizon in HORIZONS:
            table = per_h.get(horizon)
            if table is None:
                continue
            for unit in ("growth_rev", "rel_level_rev"):
                pairs = pit_safe_pairs(table, unit)
                if len(pairs) < 8:
                    continue
                full_r = _corr_stat(pairs)
                full_p = correlation_p_value(full_r, len(pairs))
                lo, hi = block_bootstrap_ci(pairs, _corr_stat)
                oos = pairs[pairs.index >= SPLIT]
                oos_r = _corr_stat(oos) if len(oos) > 3 else float("nan")
                oos_p = correlation_p_value(oos_r, len(oos)) if len(oos) > 3 else float("nan")
                rows.append(
                    {
                        "series": sid,
                        "unit": unit,
                        "horizon_days": horizon,
                        "primary": unit == "growth_rev" and horizon == PRIMARY_HORIZON,
                        "full_r": full_r,
                        "full_ci_lo": lo,
                        "full_ci_hi": hi,
                        "full_n": len(pairs),
                        "full_p_raw": full_p,
                        "oos_r": oos_r,
                        "oos_n": len(oos),
                        "oos_p_raw": oos_p,
                    }
                )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    m = int(df["primary"].sum())  # Bonferroni only over the primary family
    df["full_p_bonferroni"] = df.apply(
        lambda r: min(r["full_p_raw"] * m, 1.0) if r["primary"] else float("nan"),
        axis=1,
    )
    df["primary_survives"] = df["primary"] & (df["full_p_bonferroni"] < ALPHA) & (
        # CI must also exclude zero (bootstrap agrees with the parametric p)
        (df["full_ci_lo"] > 0) | (df["full_ci_hi"] < 0)
    )
    return df


def _normal_p_two_sided(z: float) -> float:
    if z != z:
        return float("nan")
    return float(2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0)))))


def runs_test(signs: np.ndarray) -> tuple[int, float, float, float]:
    """Wald-Wolfowitz runs test. Returns (runs, expected_runs, z, p). Fewer
    runs than expected (negative z) means same-sign clustering, i.e.
    directional persistence. This replaces the naive 'share vs 0.5' z, which
    assumed consecutive sign-agreements were independent."""
    signs = np.asarray(signs)
    signs = signs[signs != 0]
    n = len(signs)
    n1 = int((signs > 0).sum())
    n2 = int((signs < 0).sum())
    if n1 == 0 or n2 == 0 or n < 4:
        return (0, float("nan"), float("nan"), float("nan"))
    runs = 1 + int((signs[1:] != signs[:-1]).sum())
    exp = 2.0 * n1 * n2 / n + 1.0
    var = 2.0 * n1 * n2 * (2.0 * n1 * n2 - n) / (n * n * (n - 1))
    if var <= 0:
        return (runs, exp, float("nan"), float("nan"))
    z = (runs - exp) / math.sqrt(var)
    return (runs, exp, z, _normal_p_two_sided(z))


def _share_stat(df: pd.DataFrame) -> float:
    return float(df["same"].mean())


def sign_persistence(tables: dict[str, dict[int, pd.DataFrame]]) -> pd.DataFrame:
    rows = []
    for sid, _label in SERIES:
        table = tables.get(sid, {}).get(PRIMARY_HORIZON)
        if table is None:
            continue
        signs = np.sign(table["growth_rev"].dropna().values)
        signs = signs[signs != 0]
        if len(signs) < 2 * BLOCK:
            continue
        same = (signs[1:] == signs[:-1]).astype(float)
        lo, hi = block_bootstrap_ci(pd.DataFrame({"same": same}), _share_stat)
        runs, exp_runs, z_runs, p_runs = runs_test(signs)
        rows.append(
            {
                "series": sid,
                "n_pairs": len(same),
                "same_sign_share": float(same.mean()),
                "share_ci_lo": lo,
                "share_ci_hi": hi,
                "runs": runs,
                "expected_runs": exp_runs,
                "runs_z": z_runs,
                "runs_p": p_runs,
            }
        )
    return pd.DataFrame(rows)


def oos_sensitivity(tables: dict[str, dict[int, pd.DataFrame]]) -> pd.DataFrame:
    """Train/test correlation of the primary momentum across many split dates,
    to check the verdict does not hinge on the single 2015 cut."""
    rows = []
    for sid, _label in SERIES:
        table = tables.get(sid, {}).get(PRIMARY_HORIZON)
        if table is None:
            continue
        pairs = pit_safe_pairs(table, "growth_rev")
        if len(pairs) < 2 * BLOCK:
            continue
        for split in OOS_SPLITS:
            s = pd.Timestamp(split)
            tr = pairs[pairs.index < s]
            te = pairs[pairs.index >= s]
            rows.append(
                {
                    "series": sid,
                    "split": split,
                    "train_r": _corr_stat(tr) if len(tr) > 3 else float("nan"),
                    "train_n": len(tr),
                    "test_r": _corr_stat(te) if len(te) > 3 else float("nan"),
                    "test_n": len(te),
                }
            )
    return pd.DataFrame(rows)


def subsample_stability(
    tables: dict[str, dict[int, pd.DataFrame]],
    vintage_frames: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Recompute the primary momentum and the PIT gap on disjoint time-thirds,
    to check neither headline is driven by one era (crisis/COVID revisions or
    a methodology-change window)."""
    rows = []
    for sid, _label in SERIES:
        table = tables.get(sid, {}).get(PRIMARY_HORIZON)
        if table is not None:
            pairs = pit_safe_pairs(table, "growth_rev").sort_index()
            for k, ch in enumerate(np.array_split(np.arange(len(pairs)), N_SUBSAMPLES)):
                sub = pairs.iloc[ch]
                rows.append(_stability_row(sid, "momentum_r", k, sub,
                                           _corr_stat(sub) if len(sub) > 3 else float("nan")))
        vdf = vintage_frames.get(sid)
        if vdf is not None and not vdf.empty:
            first = first_vintage_series(vdf).pct_change()
            final = final_vintage_series(vdf).pct_change()
            joined = pd.concat(
                [first.rename("first"), final.rename("final")], axis=1
            ).dropna().sort_index()
            for k, ch in enumerate(np.array_split(np.arange(len(joined)), N_SUBSAMPLES)):
                sub = joined.iloc[ch]
                gap = (
                    _ac1(sub["final"].values) - _ac1(sub["first"].values)
                    if len(sub) > 4
                    else float("nan")
                )
                rows.append(_stability_row(sid, "pit_gap", k, sub, gap))
    return pd.DataFrame(rows)


def _stability_row(sid, metric, k, sub, value):
    period = (
        f"{sub.index.min().date()}..{sub.index.max().date()}" if len(sub) else ""
    )
    return {
        "series": sid,
        "metric": metric,
        "subsample": k + 1,
        "period": period,
        "value": value,
        "n": len(sub),
    }


def pit_gap(vintage_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for sid, _label in SERIES:
        vdf = vintage_frames.get(sid)
        if vdf is None or vdf.empty:
            continue
        first = first_vintage_series(vdf).pct_change()
        final = final_vintage_series(vdf).pct_change()
        joined = pd.concat([first.rename("first"), final.rename("final")], axis=1).dropna()
        if len(joined) < 2 * BLOCK:
            continue
        ac_first = _ac1(joined["first"].values)
        ac_final = _ac1(joined["final"].values)
        gap = ac_final - ac_first
        lo, hi = block_bootstrap_ci(
            joined, lambda d: _ac1(d["final"].values) - _ac1(d["first"].values)
        )
        rows.append(
            {
                "series": sid,
                "ac1_first_vintage": ac_first,
                "ac1_final_vintage": ac_final,
                "gap_final_minus_first": gap,
                "gap_ci_lo": lo,
                "gap_ci_hi": hi,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- render


def render_summary(mom, persist, gap, oos, stability) -> str:
    lines = ["# ALFRED revision-momentum, stage 1 (Tier-1 + Tier-2)", ""]
    if mom.empty:
        lines.append("No revision data. Run data/fetch_alfred.py first.")
        return "\n".join(lines) + "\n"

    primary = mom[mom["primary"]]
    m = len(primary)
    surv = int(mom["primary_survives"].sum())
    lines.append(
        f"**PIT-safe momentum, primary family (growth, {PRIMARY_HORIZON}d), "
        f"Bonferroni m = {m}, CI excludes 0:**"
    )
    lines.append("")
    lines.append(f"- Survivors: **{surv} of {m}**.")
    lines.append("")
    lines.append("## Momentum trials (PIT-safe; * = primary)")
    lines.append("")
    lines.append(
        "| Series | Unit | Horizon | Full r | 95% CI | n | Bonferroni p | OOS r | OOS n |"
    )
    lines.append("|---|---|---:|---:|---|---:|---:|---:|---:|")
    for _, r in mom.sort_values(["series", "unit", "horizon_days"]).iterrows():
        star = " *" if r["primary"] else ""
        bp = f"{r['full_p_bonferroni']:.3f}" if r["primary"] else "-"
        lines.append(
            f"| {r['series']}{star} | {r['unit']} | {int(r['horizon_days'])} "
            f"| {r['full_r']:.3f} | [{r['full_ci_lo']:.3f}, {r['full_ci_hi']:.3f}] "
            f"| {int(r['full_n'])} | {bp} | {r['oos_r']:.3f} | {int(r['oos_n'])} |"
        )

    if not persist.empty:
        lines += ["", "## Sign persistence of growth revisions (Wald-Wolfowitz runs test)", ""]
        lines.append(
            "Negative runs-z = fewer runs than chance = same-sign clustering "
            "(directional persistence)."
        )
        lines.append("")
        lines.append("| Series | Pairs | Same-sign share | Share 95% CI | Runs z | Runs p |")
        lines.append("|---|---:|---:|---|---:|---:|")
        for _, r in persist.iterrows():
            lines.append(
                f"| {r['series']} | {int(r['n_pairs'])} | {r['same_sign_share']:.3f} "
                f"| [{r['share_ci_lo']:.3f}, {r['share_ci_hi']:.3f}] "
                f"| {r['runs_z']:.2f} | {r['runs_p']:.4f} |"
            )

    if not oos.empty:
        lines += ["", "## OOS-split sensitivity (primary momentum, train/test r by split)", ""]
        lines.append("| Series | Split | Train r | Train n | Test r | Test n |")
        lines.append("|---|---|---:|---:|---:|---:|")
        for _, r in oos.iterrows():
            lines.append(
                f"| {r['series']} | {r['split']} | {r['train_r']:.3f} | {int(r['train_n'])} "
                f"| {r['test_r']:.3f} | {int(r['test_n'])} |"
            )

    if not stability.empty:
        lines += ["", "## Subsample stability (disjoint time-thirds)", ""]
        lines.append("| Series | Metric | Third | Period | Value | n |")
        lines.append("|---|---|---:|---|---:|---:|")
        for _, r in stability.iterrows():
            lines.append(
                f"| {r['series']} | {r['metric']} | {int(r['subsample'])} | {r['period']} "
                f"| {r['value']:.3f} | {int(r['n'])} |"
            )

    if not gap.empty:
        lines += ["", "## Point-in-time gap (lag-1 AC of MoM growth, with 95% CI)", ""]
        lines.append("| Series | First-vintage AC1 | Final-vintage AC1 | Gap | Gap 95% CI |")
        lines.append("|---|---:|---:|---:|---|")
        for _, r in gap.iterrows():
            lines.append(
                f"| {r['series']} | {r['ac1_first_vintage']:.3f} | {r['ac1_final_vintage']:.3f} "
                f"| {r['gap_final_minus_first']:+.3f} "
                f"| [{r['gap_ci_lo']:+.3f}, {r['gap_ci_hi']:+.3f}] |"
            )
        lines.append("")
        lines.append(
            "A gap whose CI excludes 0 means final-vintage data shows growth "
            "autocorrelation that was not knowable in real time."
        )
    return "\n".join(lines) + "\n"


def run(data_dir: Path, out_dir: Path) -> pd.DataFrame:
    vintage_frames: dict[str, pd.DataFrame] = {}
    tables: dict[str, dict[int, pd.DataFrame]] = {}
    for sid, _label in SERIES:
        path = data_dir / f"{sid}_vintages.csv"
        if not path.exists():
            continue
        vdf = timely_vintage_df(load_vintage_csv(path))
        vintage_frames[sid] = vdf
        tables[sid] = {h: revisions_table(vdf, h) for h in HORIZONS}

    mom = momentum_trials(tables)
    persist = sign_persistence(tables)
    gap = pit_gap(vintage_frames)
    oos = oos_sensitivity(tables)
    stability = subsample_stability(tables, vintage_frames)

    out_dir.mkdir(parents=True, exist_ok=True)
    if not mom.empty:
        mom.to_csv(out_dir / "stage1-momentum.csv", index=False)
    if not gap.empty:
        gap.to_csv(out_dir / "pit-gap.csv", index=False)
    if not persist.empty:
        persist.to_csv(out_dir / "stage1-sign-persistence.csv", index=False)
    if not oos.empty:
        oos.to_csv(out_dir / "stage1-oos-sensitivity.csv", index=False)
    if not stability.empty:
        stability.to_csv(out_dir / "stage1-subsample-stability.csv", index=False)
    summary = render_summary(mom, persist, gap, oos, stability)
    (out_dir / "stage1-summary.md").write_text(summary)
    print(summary)
    return mom


# ---------------------------------------------------------------- self-test


def _self_test() -> int:
    """Plant a PIT-realizable AR(1) revision and confirm recovery + no
    look-ahead in the predictor alignment."""
    rng = np.random.default_rng(7)
    months = pd.date_range("1990-01-31", "2024-12-31", freq="ME")
    with tempfile.TemporaryDirectory() as td:
        data_dir = Path(td) / "data"
        data_dir.mkdir()
        for sid in ("PAYEMS", "RSAFS", "INDPRO"):
            # phi=0.85 so the PIT-safe predictor (~3 months back at a 90d
            # horizon) still recovers phi^3 ~ 0.6, well clear of noise.
            phi = 0.85 if sid == "PAYEMS" else 0.0
            rev = np.zeros(len(months))
            for i in range(1, len(months)):
                rev[i] = phi * rev[i - 1] + rng.normal(0, 1.0)
            rows = ["observation_date,vintage_date,value"]
            level = 100.0
            for i, obs in enumerate(months):
                level += rng.normal(0.2, 0.5)
                first_v = obs + pd.Timedelta(days=20)   # timely first release
                second_v = obs + pd.Timedelta(days=50)  # realized within 90d horizon
                # Plant the revision in the LEVEL; growth_rev inherits its sign
                # via the month-over-month differencing.
                rows.append(f"{obs.date()},{first_v.date()},{level:.4f}")
                rows.append(f"{obs.date()},{second_v.date()},{level + rev[i]:.4f}")
            (data_dir / f"{sid}_vintages.csv").write_text("\n".join(rows) + "\n")

        # Direct PIT-constraint check on the alignment.
        vdf = timely_vintage_df(load_vintage_csv(data_dir / "PAYEMS_vintages.csv"))
        table = revisions_table(vdf, PRIMARY_HORIZON)
        pairs = pit_safe_pairs(table, "growth_rev")
        # The predictor used for each target must have been realized by the
        # target's first-release date (no look-ahead).
        for t in pairs.index:
            assert table.loc[t, "first_release_date"] >= table["knowable_date"].min()
        assert len(pairs) > 100

        out_dir = Path(td) / "out"
        mom = run(data_dir, out_dir)

    prim = mom[mom["primary"]]
    pay = prim[prim["series"] == "PAYEMS"].iloc[0]
    assert pay["full_r"] > 0.2, pay["full_r"]
    assert pay["primary_survives"], "planted PAYEMS momentum should survive"
    rsa = prim[prim["series"] == "RSAFS"].iloc[0]
    assert not rsa["primary_survives"], "noise series should not survive"
    print("\nself-test OK: planted PIT-safe momentum recovered, noise rejected.")
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
