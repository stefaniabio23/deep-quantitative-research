#!/usr/bin/env python3
"""Biotech sell-the-news event study.

A cross-sectional test: for each biotech catalyst (a ticker x readout event),
does the pre-event run-up and the pre-event news attention predict NEGATIVE
post-event abnormal drift? Sell-the-news = a stock that ran up and was loudly
covered underperforms after the readout, regardless of outcome.

Per event, on market-adjusted (ticker minus XBI) returns:
- pre_runup       : cumulative AR over [-60, -2] trading days
- pre_news        : summed GDELT article volume over [-30, -2] calendar days
- pre_tone        : mean GDELT tone over the same window
- event_reaction  : cumulative AR over [-1, +1] (a control)
- post_drift      : cumulative AR over [+2, +21]  (the outcome)

Cross-sectional analysis (cross_sectional_analysis):
- OLS  post_drift ~ z(pre_runup) + z(pre_news) + event_reaction
- cross-sectional bootstrap 95% CIs on the coefficients
- quintile sort by pre_runup; Q5-Q1 post_drift spread
- directional consistency (DC): share of top-tercile run-up events that drift
  down; R: corr(pre_runup, post_drift)

Sell-the-news survives if the pre_runup coefficient is negative with a
bootstrap CI clear of zero.

Run `python3 run_sell_the_news.py --self-test` to verify the analysis on
synthetic events with a planted sell-the-news effect (no network).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
DATA_DIR = HERE / "data"
OUT_DIR = HERE / "expected-output"

BENCHMARK = "XBI"
PRE_RUNUP = (-60, -2)   # trading days
REACTION = (-1, 1)
POST_DRIFT = (2, 21)
PRE_NEWS = (-30, -2)    # calendar days
OOS_SPLIT = pd.Timestamp("2021-01-01")
N_BOOT = 2000
SEED = 20260621


# ---------------------------------------------------------- feature build


def _cum(ar: pd.Series, anchor: int, lo: int, hi: int) -> float:
    s, e = anchor + lo, anchor + hi
    if s < 0 or e >= len(ar):
        return float("nan")
    return float(ar.iloc[s : e + 1].sum())


def build_event_features(
    events: pd.DataFrame,
    prices: dict[str, pd.Series],
    news: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Live path: turn events + price/news series into one row per event."""
    bench = prices.get(BENCHMARK)
    if bench is None:
        raise SystemExit(f"benchmark {BENCHMARK} prices missing")
    bench_ret = bench.pct_change()
    rows = []
    for _, ev in events.iterrows():
        tic = str(ev["ticker"])
        cdate = pd.Timestamp(ev["catalyst_date"])
        px = prices.get(tic)
        if px is None:
            continue
        ar = (px.pct_change() - bench_ret).dropna().sort_index()
        pos = int(ar.index.searchsorted(cdate, side="right")) - 1
        if pos < 0:
            continue
        nv = news.get(tic)
        pre_news = pre_tone = float("nan")
        if nv is not None and not nv.empty:
            w = nv[
                (nv.index >= cdate + pd.Timedelta(days=PRE_NEWS[0]))
                & (nv.index <= cdate + pd.Timedelta(days=PRE_NEWS[1]))
            ]
            if len(w):
                pre_news = float(w["article_count"].sum())
                pre_tone = float(w["avg_tone"].mean())
        rows.append(
            {
                "event_id": ev.get("event_id", f"{tic}:{cdate.date()}"),
                "ticker": tic,
                "catalyst_date": cdate,
                "pre_runup": _cum(ar, pos, *PRE_RUNUP),
                "event_reaction": _cum(ar, pos, *REACTION),
                "post_drift": _cum(ar, pos, *POST_DRIFT),
                "pre_news_intensity": pre_news,
                "pre_news_tone": pre_tone,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- stats


def _z(s: pd.Series) -> pd.Series:
    sd = s.std()
    return (s - s.mean()) / sd if sd and sd == sd else s * 0.0


def _ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def _design(f: pd.DataFrame, use_news: bool) -> tuple[np.ndarray, list[str]]:
    cols = ["intercept", "z_runup"]
    mats = [np.ones(len(f)), f["z_runup"].values]
    if use_news:
        cols.append("z_news")
        mats.append(f["z_news"].values)
    cols.append("event_reaction")
    mats.append(np.nan_to_num(f["event_reaction"].values))
    return np.column_stack(mats), cols


def cross_sectional_analysis(feat: pd.DataFrame) -> dict:
    f = feat.dropna(subset=["pre_runup", "post_drift"]).copy()
    n = len(f)
    out: dict = {"n_events": n}
    if n < 12:
        out["error"] = "too few events"
        return out
    f["z_runup"] = _z(f["pre_runup"])
    use_news = f["pre_news_intensity"].notna().sum() >= 0.5 * n
    f["z_news"] = _z(f["pre_news_intensity"].fillna(f["pre_news_intensity"].mean())) if use_news else 0.0

    X, cols = _design(f, use_news)
    y = f["post_drift"].values
    beta = _ols(X, y)
    coef = dict(zip(cols, beta))

    rng = np.random.default_rng(SEED)
    boot = {c: [] for c in cols}
    idx = np.arange(n)
    for _ in range(N_BOOT):
        b = rng.choice(idx, size=n, replace=True)
        try:
            bb = _ols(X[b], y[b])
        except np.linalg.LinAlgError:
            continue
        for c, v in zip(cols, bb):
            boot[c].append(v)

    def ci(c):
        a = boot[c]
        return (float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))) if a else (float("nan"), float("nan"))

    out["runup_coef"] = float(coef["z_runup"])
    out["runup_ci_lo"], out["runup_ci_hi"] = ci("z_runup")
    out["uses_news"] = bool(use_news)
    if use_news:
        out["news_coef"] = float(coef["z_news"])
        out["news_ci_lo"], out["news_ci_hi"] = ci("z_news")

    # Quintile sort by pre_runup.
    f = f.sort_values("pre_runup")
    qidx = np.array_split(np.arange(len(f)), 5)
    out["quintile_post_drift"] = [float(f.iloc[ix]["post_drift"].mean()) for ix in qidx]
    out["q5_minus_q1"] = out["quintile_post_drift"][-1] - out["quintile_post_drift"][0]

    # Directional consistency: top-tercile run-up events that drift down.
    top = f[f["pre_runup"] >= f["pre_runup"].quantile(2 / 3)]
    out["dc_top_tercile_down"] = float((top["post_drift"] < 0).mean())
    out["r_runup_drift"] = float(f["pre_runup"].corr(f["post_drift"]))
    out["sell_the_news"] = bool(out["runup_coef"] < 0 and out["runup_ci_hi"] < 0)
    return out


# --------------------------------------------------------------- render


def render_summary(res: dict, oos: dict | None) -> str:
    L = ["# Biotech sell-the-news event study", ""]
    if res.get("error"):
        L.append(f"Insufficient data: {res['error']} (n = {res.get('n_events', 0)}).")
        return "\n".join(L) + "\n"
    L.append(f"**Events analyzed: {res['n_events']}.**")
    L.append("")
    verdict = "SELL-THE-NEWS CONFIRMED" if res["sell_the_news"] else "not confirmed"
    L.append(f"**Verdict: {verdict}** (pre-run-up coefficient negative with CI excluding 0).")
    L.append("")
    L.append("## Cross-sectional OLS (post-drift on standardized predictors)")
    L.append("")
    L.append("| Predictor | Coefficient | 95% CI |")
    L.append("|---|---:|---|")
    L.append(f"| pre_runup (z) | {res['runup_coef']:+.4f} | [{res['runup_ci_lo']:+.4f}, {res['runup_ci_hi']:+.4f}] |")
    if res.get("uses_news"):
        L.append(f"| pre_news (z) | {res['news_coef']:+.4f} | [{res['news_ci_lo']:+.4f}, {res['news_ci_hi']:+.4f}] |")
    else:
        L.append("| pre_news (z) | n/a | (news coverage < 50% of events) |")
    L.append("")
    L.append("## Quintile sort by pre-run-up (mean post-drift)")
    L.append("")
    L.append("| Q1 (low run-up) | Q2 | Q3 | Q4 | Q5 (high run-up) | Q5-Q1 |")
    L.append("|---:|---:|---:|---:|---:|---:|")
    q = res["quintile_post_drift"]
    L.append(f"| {q[0]:+.4f} | {q[1]:+.4f} | {q[2]:+.4f} | {q[3]:+.4f} | {q[4]:+.4f} | {res['q5_minus_q1']:+.4f} |")
    L.append("")
    L.append(
        f"Directional consistency (top-tercile run-up events drifting down): "
        f"**{res['dc_top_tercile_down']:.3f}**. "
        f"R(run-up, post-drift) = {res['r_runup_drift']:+.3f}."
    )
    if oos and not oos.get("error"):
        L += ["", "## Out-of-sample (events from 2021)"]
        L.append(
            f"\npost-2021 run-up coefficient: {oos['runup_coef']:+.4f} "
            f"[{oos['runup_ci_lo']:+.4f}, {oos['runup_ci_hi']:+.4f}] "
            f"(n = {oos['n_events']})."
        )
    return "\n".join(L) + "\n"


def run(data_dir: Path, out_dir: Path) -> dict:
    events_path = data_dir / "events_seed.csv"
    if not events_path.exists():
        raise SystemExit(f"no events file at {events_path}")
    events = pd.read_csv(events_path, parse_dates=["catalyst_date"])
    prices = _load_prices(data_dir / "prices")
    news = _load_news(data_dir / "news")
    feat = build_event_features(events, prices, news)
    res = cross_sectional_analysis(feat)
    oos = None
    if "catalyst_date" in feat.columns:
        late = feat[feat["catalyst_date"] >= OOS_SPLIT]
        if len(late) >= 12:
            oos = cross_sectional_analysis(late)

    out_dir.mkdir(parents=True, exist_ok=True)
    if not feat.empty:
        feat.to_csv(out_dir / "event-features.csv", index=False)
    summary = render_summary(res, oos)
    (out_dir / "sell-the-news-summary.md").write_text(summary)
    print(summary)
    return res


def _load_prices(d: Path) -> dict[str, pd.Series]:
    out = {}
    if d.exists():
        for p in d.glob("*.csv"):
            df = pd.read_csv(p, parse_dates=["date"]).set_index("date")["close"].astype(float)
            out[p.stem] = df.sort_index()
    return out


def _load_news(d: Path) -> dict[str, pd.DataFrame]:
    out = {}
    if d.exists():
        for p in d.glob("*.csv"):
            df = pd.read_csv(p, parse_dates=["date"]).set_index("date").sort_index()
            out[p.stem] = df
    return out


# --------------------------------------------------------------- self-test


def _self_test() -> int:
    rng = np.random.default_rng(11)
    n = 300
    runup = rng.normal(0, 1, n)
    news = rng.normal(0, 1, n)
    reaction = rng.normal(0, 0.05, n)
    # Planted sell-the-news: high run-up and loud news -> negative post-drift.
    post = -0.45 * runup - 0.25 * news + rng.normal(0, 1.0, n)
    feat = pd.DataFrame(
        {
            "event_id": np.arange(n),
            "pre_runup": runup,
            "pre_news_intensity": news,
            "pre_news_tone": 0.0,
            "event_reaction": reaction,
            "post_drift": post,
        }
    )
    res = cross_sectional_analysis(feat)
    assert res["runup_coef"] < -0.2, res["runup_coef"]
    assert res["runup_ci_hi"] < 0, res
    assert res["sell_the_news"]
    assert res["news_coef"] < -0.1, res["news_coef"]
    assert res["q5_minus_q1"] < 0, res["q5_minus_q1"]

    # Null: post-drift independent of run-up.
    feat0 = feat.copy()
    feat0["post_drift"] = rng.normal(0, 1.0, n)
    res0 = cross_sectional_analysis(feat0)
    assert not res0["sell_the_news"], "null should not confirm sell-the-news"
    print("self-test OK: planted sell-the-news recovered, null rejected.")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    out_dir = OUT_DIR
    if "--out" in argv:
        out_dir = Path(argv[argv.index("--out") + 1])
    run(DATA_DIR, out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
