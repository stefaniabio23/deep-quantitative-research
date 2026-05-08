"""
Time series analysis script for deep-quant-research.
Modes: stationarity, lag, decompose, distance_correlation, cointegration.
"""

import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

try:
    import numpy as np
    import pandas as pd
    from scipy import stats
except ImportError as e:
    print(f"Missing required package: {e}. Run: pip install -r requirements.txt")
    sys.exit(1)


def _load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.sort_index(inplace=True)
    return df


def _save_yaml(data: dict, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    except ImportError:
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    print(f"Results saved to {path}")


def _distance_correlation(x: np.ndarray, y: np.ndarray) -> float:
    n = len(x)
    a = np.abs(x[:, None] - x[None, :]).astype(float)
    b = np.abs(y[:, None] - y[None, :]).astype(float)
    a = a - a.mean(0) - a.mean(1)[:, None] + a.mean()
    b = b - b.mean(0) - b.mean(1)[:, None] + b.mean()
    dcov_xy = np.sqrt(max((a * b).mean(), 0))
    dcov_xx = np.sqrt(max((a * a).mean(), 0))
    dcov_yy = np.sqrt(max((b * b).mean(), 0))
    return 0.0 if dcov_xx * dcov_yy == 0 else dcov_xy / np.sqrt(dcov_xx * dcov_yy)


def run_stationarity(input_path: str, columns: str, output: str) -> None:
    try:
        from statsmodels.tsa.stattools import adfuller, kpss
    except ImportError:
        print("statsmodels not installed. Run: pip install statsmodels")
        sys.exit(1)

    df = _load_csv(input_path)
    col_list = [c.strip() for c in columns.split(",")]
    results = {"analyst": "timeseries", "mode": "stationarity", "stationarity": {}}

    print(f"\n{'Series':<25} {'ADF p':>8} {'KPSS p':>8} {'Verdict':>20}")
    print("-" * 65)

    for col in col_list:
        if col not in df.columns:
            print(f"WARNING: Column '{col}' not found. Available: {list(df.columns)}")
            continue

        series = df[col].dropna()

        adf_stat, adf_p, _, _, _, _ = adfuller(series, autolag="AIC")

        try:
            kpss_stat, kpss_p, _, _ = kpss(series, regression="c", nlags="auto")
        except Exception:
            kpss_stat, kpss_p = np.nan, np.nan

        if adf_p < 0.05 and (np.isnan(kpss_p) or kpss_p > 0.05):
            verdict = "stationary"
            transform = "none"
        elif adf_p > 0.05 and not np.isnan(kpss_p) and kpss_p < 0.05:
            verdict = "non-stationary"
            transform = "first-difference"
        elif adf_p < 0.05 and not np.isnan(kpss_p) and kpss_p < 0.05:
            verdict = "trend-stationary"
            transform = "detrend"
        else:
            verdict = "inconclusive"
            transform = "first-difference"

        results["stationarity"][col] = {
            "adf_statistic": round(float(adf_stat), 4),
            "adf_pvalue": round(float(adf_p), 4),
            "kpss_statistic": round(float(kpss_stat), 4) if not np.isnan(kpss_stat) else None,
            "kpss_pvalue": round(float(kpss_p), 4) if not np.isnan(kpss_p) else None,
            "verdict": verdict,
            "transformation_applied": transform,
        }
        print(f"{col:<25} {adf_p:>8.4f} {kpss_p if not np.isnan(kpss_p) else 'N/A':>8} {verdict:>20}")

    _save_yaml(results, output)


def run_lag_analysis(input_path: str, x_col: str, y_col: str, output: str,
                     lags: str = "1,2,5,10,20,60", rolling_window: int = 252) -> None:
    df = _load_csv(input_path)[[x_col, y_col]].dropna()
    lag_list = [int(l.strip()) for l in lags.split(",")]

    print(f"\nLag analysis: {x_col} (lagged) → {y_col}")
    print(f"\n{'Lag':>5} {'Pearson r':>10} {'Spearman r':>11} {'DC':>8} {'t-stat':>8} {'p-value':>8} {'Stability':>12}")
    print("-" * 70)

    results = {"analyst": "timeseries", "mode": "lag_analysis",
               "x": x_col, "y": y_col, "lag_table": {}, "optimal_lag": None}

    best_p = 1.0
    best_lag = None

    for lag in lag_list:
        lagged = df[[x_col, y_col]].copy()
        lagged[x_col] = lagged[x_col].shift(lag)
        lagged = lagged.dropna()

        if len(lagged) < 30:
            print(f"{lag:>5}: insufficient data after lagging")
            continue

        x = lagged[x_col].values
        y = lagged[y_col].values

        r, p = stats.pearsonr(x, y)
        rho, _ = stats.spearmanr(x, y)
        dc = _distance_correlation(x, y)

        n = len(x)
        t_stat = r * np.sqrt(n - 2) / np.sqrt(1 - r**2)

        roll = lagged.rolling(rolling_window)[[x_col, y_col]].corr()
        try:
            roll_corr = roll.unstack()[x_col][y_col]
            pct_pos = (roll_corr > 0).mean()
            stability = "stable" if pct_pos > 0.8 else ("moderate" if pct_pos > 0.6 else "unstable")
        except Exception:
            pct_pos = np.nan
            stability = "unknown"

        results["lag_table"][lag] = {
            "pearson_r": round(float(r), 4),
            "spearman_rho": round(float(rho), 4),
            "distance_corr": round(float(dc), 4),
            "t_stat": round(float(t_stat), 4),
            "p_value": round(float(p), 4),
            "n": n,
            "rolling_pct_positive": round(float(pct_pos), 4) if not np.isnan(pct_pos) else None,
            "stability": stability,
        }

        print(f"{lag:>5} {r:>10.4f} {rho:>11.4f} {dc:>8.4f} {t_stat:>8.2f} {p:>8.4f} {stability:>12}")

        if p < best_p and stability in ("stable", "moderate"):
            best_p = p
            best_lag = lag

    results["optimal_lag"] = best_lag
    print(f"\nOptimal lag (lowest p with stable rolling): {best_lag}")

    _save_yaml(results, output)


def run_decompose(input_path: str, column: str, output: str,
                  model: str = "additive", period: int = 252) -> None:
    try:
        from statsmodels.tsa.seasonal import STL
        from statsmodels.stats.stattools import durbin_watson
    except ImportError:
        print("statsmodels not installed. Run: pip install statsmodels")
        sys.exit(1)

    df = _load_csv(input_path)
    series = df[column].dropna()

    print(f"\nSTL decomposition: {column} (period={period})")
    stl = STL(series, period=period, robust=True)
    res = stl.fit()

    trend_strength = 1 - res.resid.var() / (res.trend + res.resid).var()
    seasonal_strength = 1 - res.resid.var() / (res.seasonal + res.resid).var()
    dw = durbin_watson(res.resid)

    print(f"Trend strength: {trend_strength:.4f}")
    print(f"Seasonal strength: {seasonal_strength:.4f}")
    print(f"Durbin-Watson (residuals): {dw:.4f}")

    results = {
        "analyst": "timeseries",
        "mode": "decomposition",
        "column": column,
        "period": period,
        "trend_strength": round(float(trend_strength), 4),
        "seasonal_strength": round(float(seasonal_strength), 4),
        "durbin_watson": round(float(dw), 4),
        "autocorrelation_in_residuals": "present" if dw < 1.5 or dw > 2.5 else "absent",
        "seasonality": "present" if seasonal_strength > 0.6 else "weak or absent",
    }
    _save_yaml(results, output)


def run_distance_correlation(input_path: str, x_col: str, y_col: str, output: str,
                              rolling: int = 60) -> None:
    df = _load_csv(input_path)[[x_col, y_col]].dropna()
    x = df[x_col].values
    y = df[y_col].values

    overall_dc = _distance_correlation(x, y)

    r_pearson, _ = stats.pearsonr(x, y)
    rho_spearman, _ = stats.spearmanr(x, y)

    # Rolling DC
    roll_dc = []
    roll_dates = []
    for i in range(rolling, len(df)):
        xi = df[x_col].iloc[i - rolling:i].values
        yi = df[y_col].iloc[i - rolling:i].values
        roll_dc.append(_distance_correlation(xi, yi))
        roll_dates.append(df.index[i])

    roll_dc = np.array(roll_dc)

    # Tail DC
    n = len(x)
    threshold = int(n * 0.20)
    sorted_idx = np.argsort(x)
    lower_dc = _distance_correlation(x[sorted_idx[:threshold]], y[sorted_idx[:threshold]])
    upper_dc = _distance_correlation(x[sorted_idx[-threshold:]], y[sorted_idx[-threshold:]])

    print(f"\nDependence Analysis: {x_col} vs {y_col}")
    print(f"Pearson r = {r_pearson:.4f} | Spearman rho = {rho_spearman:.4f} | DC = {overall_dc:.4f}")
    print(f"Lower tail DC = {lower_dc:.4f} | Upper tail DC = {upper_dc:.4f}")

    vs_pearson = "higher" if overall_dc > abs(r_pearson) * 1.2 else ("similar" if overall_dc > abs(r_pearson) * 0.8 else "lower")

    results = {
        "analyst": "timeseries",
        "mode": "distance_correlation",
        "x": x_col, "y": y_col,
        "pearson_r": round(float(r_pearson), 4),
        "spearman_rho": round(float(rho_spearman), 4),
        "overall_dc": round(float(overall_dc), 4),
        "vs_pearson": vs_pearson,
        "non_linearity_detected": vs_pearson == "higher",
        "rolling": {
            "window": rolling,
            "mean_dc": round(float(roll_dc.mean()), 4),
            "min_dc": round(float(roll_dc.min()), 4),
            "max_dc": round(float(roll_dc.max()), 4),
        },
        "tail_dc": {
            "lower_20pct": round(float(lower_dc), 4),
            "upper_20pct": round(float(upper_dc), 4),
            "asymmetric": abs(lower_dc - upper_dc) > 0.1,
        },
    }
    _save_yaml(results, output)


def run_cointegration(input_path: str, columns: str, output: str) -> None:
    try:
        from statsmodels.tsa.stattools import coint
        from statsmodels.tsa.vector_ar.vecm import coint_johansen
    except ImportError:
        print("statsmodels not installed. Run: pip install statsmodels")
        sys.exit(1)

    df = _load_csv(input_path)
    col_list = [c.strip() for c in columns.split(",")]
    df = df[col_list].dropna()

    results = {"analyst": "timeseries", "mode": "cointegration",
               "series": col_list, "pairs": {}, "johansen": {}}

    # Engle-Granger pairwise
    print("\nEngle-Granger pairwise cointegration:")
    for i, c1 in enumerate(col_list):
        for c2 in col_list[i+1:]:
            t_stat, p_val, _ = coint(df[c1], df[c2])
            pair = f"{c1} vs {c2}"
            results["pairs"][pair] = {
                "t_stat": round(float(t_stat), 4),
                "p_value": round(float(p_val), 4),
                "cointegrated": p_val < 0.05,
            }
            print(f"  {pair}: t={t_stat:.3f}, p={p_val:.4f} — {'COINTEGRATED' if p_val < 0.05 else 'not cointegrated'}")

    # Johansen test (all series)
    if len(col_list) >= 2:
        joh = coint_johansen(df, det_order=0, k_ar_diff=1)
        n_coint = int(np.sum(joh.lr1 > joh.cvt[:, 1]))
        results["johansen"] = {
            "n_cointegrating_vectors": n_coint,
            "trace_stats": [round(float(s), 4) for s in joh.lr1],
            "critical_values_5pct": [round(float(v), 4) for v in joh.cvt[:, 1]],
        }
        print(f"\nJohansen: {n_coint} cointegrating vector(s)")

    _save_yaml(results, output)


def main():
    parser = argparse.ArgumentParser(description="Time series analysis for deep-quant-research")
    parser.add_argument("--mode", required=True,
                        choices=["stationarity", "lag", "decompose", "distance_correlation", "cointegration"])
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--columns", help="Comma-separated columns (stationarity, cointegration)")
    parser.add_argument("--column", help="Single column (decompose)")
    parser.add_argument("--x", help="X column (lag, distance_correlation)")
    parser.add_argument("--y", help="Y column (lag, distance_correlation)")
    parser.add_argument("--lags", default="1,2,5,10,20,60")
    parser.add_argument("--rolling_window", type=int, default=252)
    parser.add_argument("--rolling", type=int, default=60)
    parser.add_argument("--model", default="additive", choices=["additive", "multiplicative"])
    parser.add_argument("--period", type=int, default=252)

    args = parser.parse_args()

    if args.mode == "stationarity":
        run_stationarity(args.input, args.columns, args.output)
    elif args.mode == "lag":
        run_lag_analysis(args.input, args.x, args.y, args.output,
                         args.lags, args.rolling_window)
    elif args.mode == "decompose":
        run_decompose(args.input, args.column, args.output, args.model, args.period)
    elif args.mode == "distance_correlation":
        run_distance_correlation(args.input, args.x, args.y, args.output, args.rolling)
    elif args.mode == "cointegration":
        run_cointegration(args.input, args.columns, args.output)


if __name__ == "__main__":
    main()
