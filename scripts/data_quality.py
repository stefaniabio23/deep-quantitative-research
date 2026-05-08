"""
Data quality audit script for deep-quant-research.
Checks for outliers, missing data, and generates the data quality report skeleton.
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
    print(f"Report saved to {path}")


def run_full_audit(input_path: str, output: str, threshold: float = 4.0) -> None:
    df = _load_csv(input_path)

    print(f"\nDATA QUALITY AUDIT")
    print(f"{'='*60}")
    print(f"File: {input_path}")
    print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"Period: {df.index[0]} to {df.index[-1]}")

    results = {
        "file": input_path,
        "shape": {"rows": df.shape[0], "columns": df.shape[1]},
        "period": {"start": str(df.index[0].date()), "end": str(df.index[-1].date())},
        "variables": {},
        "bias_assessment": {
            "look_ahead_bias": "MANUAL_CHECK_REQUIRED",
            "survivorship_bias": "MANUAL_CHECK_REQUIRED",
            "data_snooping_risk": "MANUAL_CHECK_REQUIRED",
            "selection_bias": "MANUAL_CHECK_REQUIRED",
        },
        "notes": [
            "Bias checks require manual review — see shared/data-quality-protocol.md",
            "look_ahead_bias: confirm signal uses only data available at decision time",
            "survivorship_bias: confirm universe includes delisted/failed entities",
            "data_snooping_risk: confirm all tests run are documented, not just passing ones",
            "selection_bias: confirm sample represents target population",
        ],
        "verdict": "PROCEED_WITH_CAVEATS",
    }

    print(f"\n{'Column':<30} {'Type':>8} {'N':>6} {'Missing':>8} {'Outliers':>9} {'Min':>12} {'Max':>12}")
    print("-" * 90)

    for col in df.columns:
        series = df[col]
        n = series.notna().sum()
        missing_pct = series.isna().mean()
        dtype = str(series.dtype)

        outlier_info = {}
        if np.issubdtype(series.dtype, np.number):
            clean = series.dropna()
            if len(clean) > 10:
                mean, std = clean.mean(), clean.std()
                if std > 0:
                    z_scores = np.abs((clean - mean) / std)
                    outliers = clean[z_scores > threshold]
                    n_outliers = len(outliers)
                    outlier_info = {
                        "count": n_outliers,
                        "threshold_z": threshold,
                        "values": [round(v, 4) for v in outliers.values[:5]],
                    }
                else:
                    n_outliers = 0
                    outlier_info = {"count": 0, "note": "zero variance"}

                col_min = round(float(clean.min()), 4)
                col_max = round(float(clean.max()), 4)
            else:
                n_outliers = 0
                col_min = col_max = None
        else:
            n_outliers = 0
            col_min = col_max = None

        results["variables"][col] = {
            "dtype": dtype,
            "n_valid": int(n),
            "n_missing": int(series.isna().sum()),
            "missing_pct": round(float(missing_pct), 4),
            "outliers": outlier_info,
            "min": col_min,
            "max": col_max,
        }

        flag = ""
        if missing_pct > 0.2:
            flag = " ⚠ HIGH MISSING"
            results["verdict"] = "PROCEED_WITH_CAVEATS"
        if n_outliers > 5:
            flag += " ⚠ OUTLIERS"

        print(f"{col:<30} {dtype:>8} {n:>6} {missing_pct:>7.1%} {n_outliers:>9} "
              f"{str(col_min):>12} {str(col_max):>12}{flag}")

    high_missing = [c for c, v in results["variables"].items() if v["missing_pct"] > 0.2]
    if high_missing:
        print(f"\n⚠ High missing data (>20%): {high_missing}")
        results["notes"].append(f"High missing data in: {high_missing}")

    print(f"\nBias checks: MANUAL_CHECK_REQUIRED (see shared/data-quality-protocol.md)")
    print(f"\nVERDICT: {results['verdict']}")
    print("  Complete bias assessment manually before running analysis.")

    _save_yaml(results, output)


def run_outlier_check(input_path: str, output: str, threshold: float = 4.0) -> None:
    df = _load_csv(input_path)
    numeric = df.select_dtypes(include=[np.number])

    all_outliers = {}
    print(f"\nOutlier Analysis (Z-score threshold: {threshold}σ)")
    print(f"\n{'Column':<30} {'N Outliers':>12} {'Dates':>40}")
    print("-" * 85)

    for col in numeric.columns:
        series = numeric[col].dropna()
        if len(series) < 10:
            continue
        z = np.abs((series - series.mean()) / series.std())
        outliers = series[z > threshold]
        if len(outliers) > 0:
            all_outliers[col] = {
                "count": len(outliers),
                "dates": [str(d.date()) for d in outliers.index[:10]],
                "values": [round(float(v), 4) for v in outliers.values[:10]],
            }
            dates_str = ", ".join([str(d.date()) for d in outliers.index[:3]])
            if len(outliers) > 3:
                dates_str += f" ... (+{len(outliers)-3} more)"
            print(f"{col:<30} {len(outliers):>12} {dates_str:>40}")

    results = {"mode": "outliers", "threshold": threshold, "outliers": all_outliers}
    _save_yaml(results, output)


def main():
    parser = argparse.ArgumentParser(description="Data quality for deep-quant-research")
    parser.add_argument("--input", required=True, help="Input CSV path (or directory)")
    parser.add_argument("--output", required=True, help="Output YAML path")
    parser.add_argument("--mode", default="full", choices=["full", "outliers"])
    parser.add_argument("--threshold", type=float, default=4.0,
                        help="Z-score threshold for outlier detection")
    parser.add_argument("--package", help="data_package.yaml path (optional)")

    args = parser.parse_args()

    if args.mode == "full":
        run_full_audit(args.input, args.output, args.threshold)
    elif args.mode == "outliers":
        run_outlier_check(args.input, args.output, args.threshold)


if __name__ == "__main__":
    main()
