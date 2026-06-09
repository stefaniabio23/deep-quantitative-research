"""
Statistical analysis script for deep-quant-research.
Modes: correlation, regression, pca, event_study, granger, did.
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


def _require_columns(df: pd.DataFrame, cols: list[str], source: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        available = ", ".join(df.columns.astype(str))
        print(f"ERROR: {source} is missing column(s): {missing}. Available: {available}", file=sys.stderr)
        sys.exit(2)


def _require_arg(value, name: str, mode: str) -> None:
    if value is None:
        print(f"ERROR: --{name} is required for --mode {mode}", file=sys.stderr)
        sys.exit(2)


def _save_yaml(data: dict, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    except ImportError:
        # Fallback: write as JSON with .yaml extension
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    print(f"Results saved to {path}")


def run_correlation(input_path: str, x_col: str, y_col: str, output: str,
                    methods: str = "pearson,spearman,distance", rolling: int = None) -> None:
    df = _load_csv(input_path)
    _require_columns(df, [x_col, y_col], input_path)
    df = df.dropna(subset=[x_col, y_col])
    x = df[x_col].values
    y = df[y_col].values
    n = len(x)

    results = {"analyst": "statistical", "mode": "correlation", "n": n,
               "x": x_col, "y": y_col, "findings": []}

    method_list = [m.strip() for m in methods.split(",")]

    if "pearson" in method_list:
        r, p = stats.pearsonr(x, y)
        se = np.sqrt((1 - r**2) / (n - 2))
        ci_lo = np.tanh(np.arctanh(r) - 1.96 / np.sqrt(n - 3))
        ci_hi = np.tanh(np.arctanh(r) + 1.96 / np.sqrt(n - 3))
        results["pearson"] = {"r": round(r, 4), "p_value": round(p, 4),
                               "ci_95": [round(ci_lo, 4), round(ci_hi, 4)], "se": round(se, 4)}
        print(f"Pearson r = {r:.4f} (p = {p:.4f}, 95% CI: [{ci_lo:.3f}, {ci_hi:.3f}])")

    if "spearman" in method_list:
        rho, p = stats.spearmanr(x, y)
        ci_lo = np.tanh(np.arctanh(rho) - 1.96 / np.sqrt(n - 3))
        ci_hi = np.tanh(np.arctanh(rho) + 1.96 / np.sqrt(n - 3))
        results["spearman"] = {"rho": round(rho, 4), "p_value": round(p, 4),
                                "ci_95": [round(ci_lo, 4), round(ci_hi, 4)]}
        print(f"Spearman rho = {rho:.4f} (p = {p:.4f})")

    if "distance" in method_list:
        dc = _distance_correlation(x, y)
        results["distance_correlation"] = {"dc": round(dc, 4)}
        print(f"Distance correlation = {dc:.4f}")

    if rolling and "pearson" in method_list:
        roll_corr = df[[x_col, y_col]].rolling(rolling).corr().unstack()[x_col][y_col]
        pct_positive = (roll_corr > 0).mean()
        results["rolling"] = {
            "window": rolling,
            "mean": round(roll_corr.mean(), 4),
            "pct_positive": round(pct_positive, 4),
            "stability": "stable" if pct_positive > 0.8 else ("moderate" if pct_positive > 0.6 else "unstable"),
        }
        print(f"Rolling {rolling}-period correlation: mean={roll_corr.mean():.4f}, {pct_positive:.0%} positive")

    _save_yaml(results, output)


def _distance_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Compute distance correlation (Szekely et al. 2007)."""
    n = len(x)
    a = np.abs(x[:, None] - x[None, :])
    b = np.abs(y[:, None] - y[None, :])

    a = a - a.mean(axis=0)[None, :] - a.mean(axis=1)[:, None] + a.mean()
    b = b - b.mean(axis=0)[None, :] - b.mean(axis=1)[:, None] + b.mean()

    dcov_xy = np.sqrt(max((a * b).mean(), 0))
    dcov_xx = np.sqrt(max((a * a).mean(), 0))
    dcov_yy = np.sqrt(max((b * b).mean(), 0))

    if dcov_xx * dcov_yy == 0:
        return 0.0
    return dcov_xy / np.sqrt(dcov_xx * dcov_yy)


def run_regression(input_path: str, target: str, features: str, output: str,
                   se_type: str = "newey_west", lags: int = 12) -> None:
    try:
        import statsmodels.api as sm
    except ImportError:
        print("statsmodels not installed. Run: pip install statsmodels")
        sys.exit(1)

    df = _load_csv(input_path)
    feature_list = [f.strip() for f in features.split(",") if f.strip()]
    _require_columns(df, [target] + feature_list, input_path)
    df = df[[target] + feature_list].dropna()

    X = sm.add_constant(df[feature_list])
    y = df[target]

    model = sm.OLS(y, X).fit()

    if se_type == "newey_west":
        model_robust = model.get_robustcov_results(cov_type="HAC", maxlags=lags)
    else:
        model_robust = model

    results = {
        "analyst": "statistical",
        "mode": "regression",
        "target": target,
        "features": feature_list,
        "se_type": se_type,
        "n": int(model.nobs),
        "r_squared": round(model.rsquared, 4),
        "adj_r_squared": round(model.rsquared_adj, 4),
        "f_statistic": round(float(model_robust.fvalue), 4),
        "f_pvalue": round(float(model_robust.f_pvalue), 4),
        "coefficients": {},
        "findings": [],
    }

    print(f"\nOLS Regression: {target} ~ {' + '.join(feature_list)}")
    print(f"N = {int(model.nobs)}, R² = {model.rsquared:.4f}, Adj R² = {model.rsquared_adj:.4f}")
    print(f"\n{'Variable':<20} {'Coef':>8} {'t-stat':>8} {'p-value':>8} {'[95% CI]':>20}")
    print("-" * 70)

    for var in model_robust.params.index:
        coef = model_robust.params[var]
        tstat = model_robust.tvalues[var]
        pval = model_robust.pvalues[var]
        ci = model_robust.conf_int().loc[var]
        results["coefficients"][var] = {
            "coef": round(float(coef), 6),
            "t_stat": round(float(tstat), 4),
            "p_value": round(float(pval), 4),
            "ci_95": [round(float(ci.iloc[0]), 6), round(float(ci.iloc[1]), 6)],
        }
        sig = "***" if pval < 0.01 else ("**" if pval < 0.05 else ("*" if pval < 0.1 else ""))
        print(f"{var:<20} {coef:>8.4f} {tstat:>8.2f} {pval:>8.4f} [{ci.iloc[0]:>8.4f}, {ci.iloc[1]:>8.4f}] {sig}")

    _save_yaml(results, output)


def run_pca(input_path: str, output: str, n_components: int = 5) -> None:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    df = _load_csv(input_path).dropna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df)

    pca = PCA(n_components=min(n_components, df.shape[1]))
    pca.fit(X_scaled)

    cumvar = np.cumsum(pca.explained_variance_ratio_)

    print(f"\nPCA: {df.shape[1]} variables → {pca.n_components_} components")
    print(f"Variance explained: {', '.join([f'PC{i+1}: {v:.1%}' for i, v in enumerate(pca.explained_variance_ratio_)])}")
    print(f"Cumulative: {cumvar[-1]:.1%}")

    loadings = pd.DataFrame(
        pca.components_.T,
        index=df.columns,
        columns=[f"PC{i+1}" for i in range(pca.n_components_)],
    )

    results = {
        "analyst": "statistical",
        "mode": "pca",
        "n_variables": df.shape[1],
        "n_components": pca.n_components_,
        "variance_explained": [round(v, 4) for v in pca.explained_variance_ratio_],
        "cumulative_variance": [round(v, 4) for v in cumvar],
        "eigenvalues": [round(v, 4) for v in pca.explained_variance_],
        "loadings": {col: {var: round(float(loadings.loc[var, col]), 4)
                           for var in loadings.index}
                     for col in loadings.columns},
        "findings": [],
    }

    _save_yaml(results, output)


def run_event_study(events_path: str, prices_path: str, output: str,
                    window: str = "-20,+60") -> None:
    prices = _load_csv(prices_path)
    try:
        events = pd.read_csv(events_path, parse_dates=["date"])
    except ValueError as e:
        print(f"ERROR: events file {events_path} must have a 'date' column. ({e})", file=sys.stderr)
        sys.exit(2)
    if "ticker" not in events.columns:
        print(f"WARNING: events file {events_path} has no 'ticker' column; falling back to first price column for all events.")

    parts = window.replace("+", "").split(",")
    pre, post = int(parts[0]), int(parts[1])

    returns = prices.pct_change()
    market_col = prices.columns[0] if "SPY" not in prices.columns else "SPY"

    all_car = []
    for _, event in events.iterrows():
        ticker = event.get("ticker", market_col)
        event_date = event["date"]
        if ticker not in returns.columns:
            continue
        idx = returns.index.searchsorted(event_date)
        if idx + post >= len(returns) or idx + pre < 0:
            continue
        window_returns = returns[ticker].iloc[idx + pre: idx + post + 1]
        market_returns = returns[market_col].iloc[idx + pre: idx + post + 1]
        abnormal = window_returns - market_returns
        all_car.append(abnormal.values)

    if not all_car:
        print("WARNING: No events could be processed")
        return

    car_matrix = np.array([r for r in all_car if len(r) == post - pre])
    mean_car = car_matrix.mean(axis=0)
    cumulative = np.cumsum(mean_car)

    t_stat, p_val = stats.ttest_1samp(car_matrix[:, -1], 0)

    print(f"\nEvent Study: {len(car_matrix)} events, window [{pre}, +{post}]")
    print(f"Mean CAR at window end: {cumulative[-1]:.4f}")
    print(f"t-stat: {t_stat:.2f}, p-value: {p_val:.4f}")

    results = {
        "analyst": "statistical",
        "mode": "event_study",
        "n_events": len(car_matrix),
        "window": window,
        "mean_car_end": round(float(cumulative[-1]), 4),
        "t_statistic": round(float(t_stat), 4),
        "p_value": round(float(p_val), 4),
        "findings": [],
    }
    _save_yaml(results, output)


def run_granger(input_path: str, x_col: str, y_col: str, output: str, max_lags: int = 12) -> None:
    try:
        from statsmodels.tsa.stattools import grangercausalitytests
    except ImportError:
        print("statsmodels not installed. Run: pip install statsmodels")
        sys.exit(1)

    df = _load_csv(input_path)
    _require_columns(df, [x_col, y_col], input_path)
    df = df[[x_col, y_col]].dropna()

    print(f"\nGranger causality: {x_col} -> {y_col} (max lags = {max_lags})")
    gc_results = grangercausalitytests(df[[y_col, x_col]], maxlag=max_lags, verbose=False)

    best_lag = min(gc_results, key=lambda k: gc_results[k][0]["ssr_ftest"][1])
    best_f = gc_results[best_lag][0]["ssr_ftest"][0]
    best_p = gc_results[best_lag][0]["ssr_ftest"][1]

    print(f"Best lag: {best_lag} | F = {best_f:.2f} | p = {best_p:.4f}")

    lag_table = {}
    for lag, res in gc_results.items():
        f_stat = res[0]["ssr_ftest"][0]
        p_val = res[0]["ssr_ftest"][1]
        lag_table[lag] = {"f_stat": round(float(f_stat), 4), "p_value": round(float(p_val), 4)}

    results = {
        "analyst": "causal-inference",
        "mode": "granger",
        "x": x_col,
        "y": y_col,
        "best_lag": best_lag,
        "best_f_stat": round(float(best_f), 4),
        "best_p_value": round(float(best_p), 4),
        "verdict": "GRANGER_CAUSE" if best_p < 0.05 else "NO_GRANGER_CAUSE",
        "lag_table": lag_table,
        "findings": [],
    }
    _save_yaml(results, output)


def main():
    parser = argparse.ArgumentParser(description="Statistical analysis for deep-quant-research")
    parser.add_argument("--mode", required=True,
                        choices=["correlation", "regression", "pca", "event_study", "granger", "did"])
    parser.add_argument("--input", help="Primary input CSV path")
    parser.add_argument("--output", required=True, help="Output YAML path")

    parser.add_argument("--x", help="X variable column name")
    parser.add_argument("--y", help="Y variable column name")
    parser.add_argument("--target", help="Regression target column")
    parser.add_argument("--features", help="Comma-separated feature columns")
    parser.add_argument("--method", default="pearson,spearman,distance", help="Correlation methods")
    parser.add_argument("--rolling", type=int, help="Rolling window for correlation")
    parser.add_argument("--se_type", default="newey_west", help="SE type for regression")
    parser.add_argument("--lags", type=int, default=12, help="Newey-West lags or Granger max lags")
    parser.add_argument("--n_components", type=int, default=5, help="PCA components")
    parser.add_argument("--events", help="Events CSV path for event study")
    parser.add_argument("--prices", help="Prices CSV path for event study")
    parser.add_argument("--window", default="-20,+60", help="Event study window")
    parser.add_argument("--max_lags", type=int, default=12, help="Granger max lags")

    args = parser.parse_args()

    if args.mode == "correlation":
        run_correlation(args.input, args.x, args.y, args.output,
                        args.method, args.rolling)
    elif args.mode == "regression":
        run_regression(args.input, args.target, args.features, args.output,
                       args.se_type, args.lags)
    elif args.mode == "pca":
        run_pca(args.input, args.output, args.n_components)
    elif args.mode == "event_study":
        run_event_study(args.events, args.prices, args.output, args.window)
    elif args.mode == "granger":
        run_granger(args.input, args.x, args.y, args.output, args.max_lags)
    else:
        print(f"Mode '{args.mode}' not yet implemented. Available: correlation, regression, pca, event_study, granger")


if __name__ == "__main__":
    main()
