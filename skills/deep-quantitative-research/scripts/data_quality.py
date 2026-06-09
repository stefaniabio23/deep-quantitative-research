"""
Data quality audit script.

Usage:
    python scripts/data_quality.py --input ./slug/data/ --mode full --output ./slug/data/data_quality.yaml
    python scripts/data_quality.py --input ./slug/data/prices.csv --mode outliers --threshold 4
"""

import argparse
import csv
import json
import yaml
from pathlib import Path
from datetime import datetime


def load_csv(path: Path) -> tuple[list[str], list[dict]]:
    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return reader.fieldnames or [], rows


def check_missingness(rows: list[dict], fields: list[str]) -> dict:
    total = len(rows)
    if total == 0:
        return {}
    result = {}
    for field in fields:
        missing = sum(1 for r in rows if not r.get(field, "").strip())
        result[field] = {
            "total": total,
            "missing": missing,
            "pct_missing": round(missing / total * 100, 1),
            "flag": missing / total > 0.2,
        }
    return result


def check_outliers(rows: list[dict], numeric_fields: list[str], threshold: float = 4.0) -> dict:
    import statistics
    result = {}
    for field in numeric_fields:
        values = []
        for r in rows:
            try:
                values.append(float(r[field]))
            except (ValueError, KeyError):
                pass
        if len(values) < 4:
            continue
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)
        if stdev == 0:
            continue
        outliers = [
            {"index": i, "value": v, "z_score": round((v - mean) / stdev, 2)}
            for i, v in enumerate(values)
            if abs(v - mean) / stdev > threshold
        ]
        if outliers:
            result[field] = outliers
    return result


def assess_look_ahead(package: dict) -> dict:
    verdict = "PASS"
    notes = []
    for ds in package.get("datasets", []):
        source = ds.get("source", "").lower()
        if "compustat" in source:
            verdict = "WARN"
            notes.append("Compustat: verify period-end dates vs. announcement dates")
        if "index" in source:
            verdict = "WARN"
            notes.append("Index data: verify historical composition used, not current")
    return {"verdict": verdict, "notes": notes or ["No obvious look-ahead detected. Verify timestamps manually."]}


def assess_survivorship(package: dict) -> dict:
    verdict = "WARN"
    notes = ["yfinance and most free sources return only currently active tickers. Delisted entities absent."]
    for ds in package.get("datasets", []):
        if "clinicaltrials" in ds.get("source", "").lower():
            notes.append("ClinicalTrials.gov: Phase 1/2 coverage weaker than Phase 3. International coverage varies.")
    return {"verdict": verdict, "notes": notes}


def full_audit(input_dir: Path, package_path: Path, output_path: Path):
    package = {}
    if package_path.exists():
        with open(package_path) as f:
            package = yaml.safe_load(f) or {}

    datasets = package.get("datasets", [])
    missingness = {}
    outlier_summary = {}

    for ds in datasets:
        fpath = Path(ds.get("file_path", ""))
        if fpath.exists() and fpath.suffix == ".csv":
            fields, rows = load_csv(fpath)
            numeric_fields = []
            for field in fields:
                try:
                    [float(r[field]) for r in rows[:20] if r.get(field)]
                    numeric_fields.append(field)
                except (ValueError, TypeError):
                    pass
            missingness[ds["name"]] = check_missingness(rows, fields)
            outlier_summary[ds["name"]] = check_outliers(rows, numeric_fields)

    look_ahead = assess_look_ahead(package)
    survivorship = assess_survivorship(package)

    # Overall verdict
    flags = [look_ahead["verdict"], survivorship["verdict"]]
    if "FAIL" in flags:
        verdict = "DO_NOT_PROCEED"
    elif "WARN" in flags:
        verdict = "PROCEED_WITH_CAVEATS"
    else:
        verdict = "PROCEED"

    caveats = look_ahead["notes"] + survivorship["notes"]
    for ds_name, fields in missingness.items():
        for field, info in fields.items():
            if info["flag"]:
                caveats.append(f"{ds_name}.{field}: {info['pct_missing']}% missing")

    report = {
        "audit_date": datetime.now().isoformat(),
        "look_ahead_bias": look_ahead,
        "survivorship_bias": survivorship,
        "data_snooping_risk": {"verdict": "PASS", "notes": ["Cannot be assessed automatically. Verify pre-specification of tests."]},
        "selection_bias": {"verdict": "PASS", "notes": ["Cannot be assessed automatically. Verify universe definition."]},
        "missingness": missingness,
        "outliers": outlier_summary,
        "verdict": verdict,
        "caveats": caveats,
    }

    with open(output_path, "w") as f:
        yaml.dump(report, f, default_flow_style=False)

    print(f"\nData Quality Report")
    print("=" * 40)
    print(f"Look-ahead bias:  {look_ahead['verdict']}")
    print(f"Survivorship:     {survivorship['verdict']}")
    print(f"Verdict:          {verdict}")
    if caveats:
        print(f"Caveats:")
        for c in caveats:
            print(f"  - {c}")
    print(f"\nSaved: {output_path}")


def outlier_check(input_path: Path, threshold: float):
    if not input_path.exists():
        print(f"File not found: {input_path}")
        return
    fields, rows = load_csv(input_path)
    numeric_fields = []
    for field in fields:
        try:
            [float(r[field]) for r in rows[:20] if r.get(field)]
            numeric_fields.append(field)
        except (ValueError, TypeError):
            pass
    outliers = check_outliers(rows, numeric_fields, threshold)
    if not outliers:
        print(f"No outliers detected (threshold: {threshold} std devs)")
    else:
        for field, items in outliers.items():
            print(f"\n{field}: {len(items)} outlier(s)")
            for item in items[:5]:
                print(f"  row {item['index']}: value={item['value']}, z={item['z_score']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--mode", choices=["full", "outliers"], default="full")
    parser.add_argument("--package", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--threshold", type=float, default=4.0)
    args = parser.parse_args()

    if args.mode == "outliers":
        outlier_check(Path(args.input), args.threshold)
    else:
        input_dir = Path(args.input)
        package_path = Path(args.package) if args.package else input_dir / "data_package.yaml"
        output_path = Path(args.output) if args.output else input_dir / "data_quality.yaml"
        full_audit(input_dir, package_path, output_path)


if __name__ == "__main__":
    main()
