"""
Pipeline monitor validation script.

Usage:
    python scripts/validate_output.py --phase data-scout-quality --output_dir ./slug/
    python scripts/validate_output.py --all --output_dir ./slug/
    python scripts/validate_output.py --all --output_dir ./slug/ --report
"""

import argparse
import sys
import yaml
from pathlib import Path
from datetime import datetime

REQUIRED_FILES = {
    "question-sharpener":     ["research_brief.yaml"],
    "originality-scout":      ["originality_assessment.yaml"],
    "knowledge-base-builder": ["knowledge_base"],
    "research-architect":     ["research_brief.yaml"],
    "data-scout-quality":     ["data/data_package.yaml"],
    "analysis-engine":        ["analysis/statistical.yaml"],
    "backtest-engine":        ["analysis/backtest.yaml"],
    "causal-inference":       ["analysis/causal.yaml"],
    "critique/methods":       ["critique/methods.yaml"],
    "critique/data":          ["critique/data.yaml"],
    "critique/logic":         ["critique/logic.yaml"],
    "findings-evaluator":     ["synthesis/evaluation.yaml"],
    "report-compiler":        ["report.md"],
}

CONFIDENCE_REQUIRED = {"findings-evaluator", "report-compiler"}


def load_all_status(output_dir: Path) -> dict:
    status_file = output_dir / "pipeline_status.yaml"
    if not status_file.exists():
        return {}
    with open(status_file) as f:
        return yaml.safe_load(f) or {}


def write_status(output_dir: Path, phase: str, status: dict):
    status_file = output_dir / "pipeline_status.yaml"
    all_status = load_all_status(output_dir)
    all_status[phase] = status
    with open(status_file, "w") as f:
        yaml.dump(all_status, f, default_flow_style=False)


def validate_phase(output_dir: Path, phase: str) -> dict:
    required = REQUIRED_FILES.get(phase, [])
    missing = [r for r in required if not (output_dir / r).exists()]

    completed = len(missing) == 0
    failure_reason = f"Missing: {missing}" if missing else None

    confidence_defined = True
    if phase in CONFIDENCE_REQUIRED:
        for req in required:
            path = output_dir / req
            if path.exists() and path.suffix == ".yaml":
                with open(path) as f:
                    content = str(yaml.safe_load(f) or {})
                if not any(k in content for k in ["confidence", "verdict", "score", "recommendation"]):
                    confidence_defined = False
                    failure_reason = (failure_reason or "") + " Missing confidence/verdict field."

    downstream_ready = completed and confidence_defined

    status = {
        "phase": phase,
        "completed": completed,
        "required_fields_present": completed,
        "evidence_attached": completed,
        "confidence_defined": confidence_defined,
        "downstream_ready": downstream_ready,
        "retry_required": not downstream_ready,
        "failure_reason": failure_reason,
        "degraded_output": False,
        "degraded_fields": missing,
        "validated_at": datetime.now().isoformat(),
    }

    write_status(output_dir, phase, status)
    return status


def mark_degraded(output_dir: Path, phase: str):
    all_status = load_all_status(output_dir)
    if phase in all_status:
        all_status[phase]["degraded_output"] = True
        all_status[phase]["retry_required"] = False
        all_status[phase]["downstream_ready"] = True
        with open(output_dir / "pipeline_status.yaml", "w") as f:
            yaml.dump(all_status, f, default_flow_style=False)


def print_status(status: dict):
    icon = "✓" if status["downstream_ready"] else ("~" if status["degraded_output"] else "✗")
    print(f"  {icon} {status['phase']}")
    if status["failure_reason"] and not status["degraded_output"]:
        print(f"      {status['failure_reason']}")
    if status["degraded_output"]:
        print(f"      [degraded] missing: {status['degraded_fields']}")


def main():
    parser = argparse.ArgumentParser(description="Validate pipeline output", add_help=True)
    parser.add_argument("--phase", help="Validate a specific phase")
    parser.add_argument("--all", action="store_true", help="Validate all phases")
    parser.add_argument("--output_dir", default=None)
    parser.add_argument("--report", action="store_true", help="Print summary")
    parser.add_argument("--mark-degraded", metavar="PHASE", help="Mark a phase as degraded and continue")
    args = parser.parse_args()

    if not args.output_dir:
        parser.print_help()
        sys.exit(0)

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        print(f"Output directory not found: {output_dir}")
        sys.exit(1)

    if args.mark_degraded:
        mark_degraded(output_dir, args.mark_degraded)
        print(f"Marked {args.mark_degraded} as degraded. Pipeline will continue with low_confidence flag.")
        return

    if args.phase:
        status = validate_phase(output_dir, args.phase)
        print_status(status)
        if not status["downstream_ready"]:
            print(f"\n  Retry instruction: complete the following fields before producing the handoff block:")
            print(f"  {status['failure_reason']}")
            sys.exit(1)

    elif args.all:
        print(f"\nPipeline validation — {output_dir.name}")
        print("=" * 50)
        results = []
        for phase in REQUIRED_FILES:
            status = validate_phase(output_dir, phase)
            results.append(status)
            print_status(status)

        if args.report:
            print("\n" + "=" * 50)
            passed = sum(1 for s in results if s["downstream_ready"])
            degraded = [s["phase"] for s in results if s["degraded_output"]]
            failed = [s["phase"] for s in results if not s["downstream_ready"] and not s["degraded_output"]]
            print(f"  {passed}/{len(results)} phases ready")
            if degraded:
                print(f"  Degraded (low confidence): {degraded}")
            if failed:
                print(f"  Failed (blocking): {failed}")
                sys.exit(1)


if __name__ == "__main__":
    main()
