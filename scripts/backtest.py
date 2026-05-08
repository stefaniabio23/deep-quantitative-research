"""
Walk-forward backtesting script for deep-quant-research.
Includes transaction costs, drawdown analysis, and benchmark comparison.
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


def _compute_metrics(returns: pd.Series, rf_annual: float = 0.03) -> dict:
    rf_daily = (1 + rf_annual) ** (1 / 252) - 1
    excess = returns - rf_daily

    ann_return = (1 + returns).prod() ** (252 / len(returns)) - 1
    ann_vol = returns.std() * np.sqrt(252)
    sharpe = excess.mean() / excess.std() * np.sqrt(252) if excess.std() > 0 else 0.0

    downside = returns[returns < 0].std() * np.sqrt(252)
    sortino = (ann_return - rf_annual) / downside if downside > 0 else 0.0

    cum = (1 + returns).cumprod()
    rolling_max = cum.cummax()
    drawdowns = cum / rolling_max - 1
    max_dd = drawdowns.min()

    calmar = ann_return / abs(max_dd) if max_dd != 0 else 0.0

    dd_in_dd = drawdowns < 0
    dd_durations = []
    current = 0
    for v in dd_in_dd:
        current = current + 1 if v else 0
        if current > 0:
            dd_durations.append(current)
    max_dd_dur = max(dd_durations) if dd_durations else 0

    var_95 = returns.quantile(0.05)
    cvar_95 = returns[returns <= var_95].mean()

    return {
        "cagr": round(float(ann_return), 4),
        "volatility": round(float(ann_vol), 4),
        "sharpe": round(float(sharpe), 4),
        "sortino": round(float(sortino), 4),
        "calmar": round(float(calmar), 4),
        "max_drawdown": round(float(max_dd), 4),
        "max_drawdown_duration_days": int(max_dd_dur),
        "var_95": round(float(var_95), 4),
        "cvar_95": round(float(cvar_95), 4),
        "n_periods": len(returns),
    }


def run_backtest(signals_path: str, prices_path: str, output: str,
                 commission: float = 0.001, slippage: float = 0.0005,
                 in_sample_end: str = None, benchmark_col: str = None,
                 cost_multipliers: list = None) -> None:

    signals = _load_csv(signals_path)
    prices = _load_csv(prices_path)

    common_idx = signals.index.intersection(prices.index)
    signals = signals.loc[common_idx]
    prices = prices.loc[common_idx]

    if signals.shape[1] > 1:
        signal_col = signals.columns[0]
        print(f"Using first column as signal: {signal_col}")
    else:
        signal_col = signals.columns[0]

    price_col = prices.columns[0] if benchmark_col not in prices.columns else prices.columns[0]
    bench_col = benchmark_col if benchmark_col and benchmark_col in prices.columns else None

    raw_returns = prices[price_col].pct_change()
    signal = signals[signal_col].shift(1)  # Shift by 1 to avoid look-ahead

    # Normalise signal to [-1, 1]
    sig_std = signal.std()
    if sig_std > 0:
        signal = signal / sig_std / 3
        signal = signal.clip(-1, 1)

    total_cost = commission + slippage
    turnover = signal.diff().abs()
    strategy_returns = signal * raw_returns - turnover * total_cost

    strategy_returns = strategy_returns.dropna()
    raw_returns = raw_returns.loc[strategy_returns.index]

    full_metrics = _compute_metrics(strategy_returns)
    full_gross = _compute_metrics(signal.loc[strategy_returns.index] * raw_returns)

    print(f"\n{'='*60}")
    print(f"BACKTEST RESULTS — Full Period")
    print(f"{'='*60}")
    print(f"Period: {strategy_returns.index[0].date()} to {strategy_returns.index[-1].date()}")
    print(f"  CAGR (net):   {full_metrics['cagr']:>8.1%}")
    print(f"  CAGR (gross): {full_gross['cagr']:>8.1%}")
    print(f"  Sharpe (net): {full_metrics['sharpe']:>8.2f}")
    print(f"  Max Drawdown: {full_metrics['max_drawdown']:>8.1%}")
    print(f"  Annual turnover: {turnover.mean() * 252:.0%}")

    ann_turnover = float(turnover.mean() * 252)
    cost_drag = ann_turnover * total_cost

    results = {
        "analyst": "backtest",
        "period": f"{strategy_returns.index[0].date()} to {strategy_returns.index[-1].date()}",
        "signal_col": signal_col,
        "price_col": price_col,
        "costs": {
            "commission": commission,
            "slippage": slippage,
            "total_per_unit_turnover": total_cost,
        },
        "performance": {
            "full": {
                "gross": full_gross,
                "net": full_metrics,
                "annual_turnover_pct": round(ann_turnover, 4),
                "cost_drag_annualised": round(float(cost_drag), 4),
            },
        },
        "red_flags": [],
        "findings": [],
    }

    # Walk-forward validation
    if in_sample_end:
        is_end = pd.to_datetime(in_sample_end)
        is_returns = strategy_returns[strategy_returns.index <= is_end]
        oos_returns = strategy_returns[strategy_returns.index > is_end]

        if len(is_returns) > 60 and len(oos_returns) > 60:
            is_metrics = _compute_metrics(is_returns)
            oos_metrics = _compute_metrics(oos_returns)
            results["performance"]["in_sample"] = is_metrics
            results["performance"]["out_of_sample"] = oos_metrics

            sharpe_degradation = (is_metrics["sharpe"] - oos_metrics["sharpe"]) / is_metrics["sharpe"] if is_metrics["sharpe"] != 0 else 0
            print(f"\n  In-sample Sharpe:  {is_metrics['sharpe']:.2f}")
            print(f"  Out-of-sample Sharpe: {oos_metrics['sharpe']:.2f}")
            print(f"  Sharpe degradation: {sharpe_degradation:.0%}")

            if sharpe_degradation > 0.5:
                results["red_flags"].append("Sharpe degrades >50% out-of-sample: potential overfit")

    # Benchmark comparison
    if bench_col and bench_col in prices.columns:
        bench_returns = prices[bench_col].pct_change().loc[strategy_returns.index].dropna()
        bench_metrics = _compute_metrics(bench_returns)

        cov = np.cov(strategy_returns, bench_returns)[0, 1]
        beta = cov / bench_returns.var() if bench_returns.var() > 0 else 0
        alpha = full_metrics["cagr"] - beta * bench_metrics["cagr"]

        results["benchmark"] = {
            "name": bench_col,
            "benchmark_metrics": bench_metrics,
            "beta": round(float(beta), 4),
            "alpha_annualised": round(float(alpha), 4),
        }
        print(f"\n  Benchmark ({bench_col}) Sharpe: {bench_metrics['sharpe']:.2f}")
        print(f"  Alpha: {alpha:.2%}, Beta: {beta:.2f}")

    # Red flag checks
    if full_metrics["sharpe"] > 3.0:
        results["red_flags"].append(f"In-sample Sharpe > 3.0 ({full_metrics['sharpe']:.2f}): scrutinise for overfitting")
    if full_metrics["max_drawdown"] < -0.5:
        results["red_flags"].append(f"Max drawdown exceeds 50% ({full_metrics['max_drawdown']:.1%}): unacceptable for most mandates")
    if ann_turnover > 10:
        results["red_flags"].append(f"Annual turnover > 1000% ({ann_turnover:.0%}): transaction costs will dominate")

    # Cost sensitivity
    if cost_multipliers is None:
        cost_multipliers = [2, 5]
    results["robustness"] = {"cost_sensitivity": {}}
    for mult in cost_multipliers:
        high_cost = signal.loc[strategy_returns.index] * raw_returns - turnover.loc[strategy_returns.index] * total_cost * mult
        high_cost = high_cost.dropna()
        hc_metrics = _compute_metrics(high_cost)
        results["robustness"]["cost_sensitivity"][f"{mult}x_costs"] = {
            "sharpe": hc_metrics["sharpe"],
            "cagr": hc_metrics["cagr"],
        }
        print(f"  At {mult}x costs: Sharpe = {hc_metrics['sharpe']:.2f}, CAGR = {hc_metrics['cagr']:.1%}")
        if hc_metrics["sharpe"] < 0:
            results["red_flags"].append(f"Strategy loses money at {mult}x base costs: not robust")

    if results["red_flags"]:
        print(f"\n  RED FLAGS: {len(results['red_flags'])}")
        for flag in results["red_flags"]:
            print(f"    - {flag}")

    _save_yaml(results, output)


def main():
    parser = argparse.ArgumentParser(description="Backtesting for deep-quant-research")
    parser.add_argument("--signals", required=True, help="Signals CSV path")
    parser.add_argument("--prices", required=True, help="Prices CSV path")
    parser.add_argument("--output", required=True, help="Output YAML path")
    parser.add_argument("--costs", type=float, default=0.001, help="Commission per side")
    parser.add_argument("--slippage", type=float, default=0.0005, help="Slippage per side")
    parser.add_argument("--in_sample_end", help="Date to split in/out-of-sample (YYYY-MM-DD)")
    parser.add_argument("--benchmark", help="Benchmark column name in prices CSV")
    parser.add_argument("--cost_multipliers", default="2,5",
                        help="Comma-separated cost multipliers for sensitivity test")

    args = parser.parse_args()
    multipliers = [int(m) for m in args.cost_multipliers.split(",")]

    run_backtest(
        args.signals, args.prices, args.output,
        args.costs, args.slippage,
        args.in_sample_end, args.benchmark,
        multipliers,
    )


if __name__ == "__main__":
    main()
