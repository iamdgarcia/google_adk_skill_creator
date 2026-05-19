#!/usr/bin/env python3
"""CI gate: aggregate grading.json results from a run directory and exit non-zero on failure."""

import argparse
import json
import sys
from pathlib import Path


def load_threshold(skill_dir: Path) -> float:
    evals_path = skill_dir / "evals" / "evals.json"
    data = json.loads(evals_path.read_text(encoding="utf-8"))
    return data.get("pass_threshold", 0.85)


def check_pass_rate(run_dir: Path, threshold: float) -> tuple[bool, dict]:
    """Return (passed, report). Checks aggregate pass_rate and skill_activated correctness."""
    grading_files = sorted(run_dir.glob("eval_*/grading.json"))

    if not grading_files:
        return False, {"error": "No grading.json files found", "run_dir": str(run_dir)}

    total_expectations = 0
    passed_expectations = 0
    activation_failures: list[str] = []

    for gf in grading_files:
        grading = json.loads(gf.read_text(encoding="utf-8"))
        summary = grading.get("summary", {})
        total_expectations += summary.get("total", 0)
        passed_expectations += summary.get("passed", 0)

        if grading.get("skill_activated") is False:
            activation_failures.append(gf.parent.name)

    pass_rate = passed_expectations / total_expectations if total_expectations > 0 else 0.0
    passed = pass_rate >= threshold and not activation_failures

    return passed, {
        "pass_rate": pass_rate,
        "threshold": threshold,
        "passed_expectations": passed_expectations,
        "total_expectations": total_expectations,
        "activation_failures": activation_failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CI gate: check eval pass rate against threshold")
    parser.add_argument("run_dir", type=Path, help="Path to runs/<timestamp>/ directory")
    parser.add_argument("skill_dir", type=Path, help="Path to skill directory (to read evals.json threshold)")
    args = parser.parse_args()

    threshold = load_threshold(args.skill_dir)
    passed, report = check_pass_rate(args.run_dir, threshold)

    if "error" in report:
        print(f"ERROR: {report['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"Pass rate: {report['pass_rate']:.0%} ({report['passed_expectations']}/{report['total_expectations']}) — threshold: {threshold:.0%}")

    if report["activation_failures"]:
        print(f"FAIL: skill_activated was wrong for: {', '.join(report['activation_failures'])}")

    if not passed:
        print(f"FAIL: pass rate {report['pass_rate']:.0%} is below threshold {threshold:.0%}")
        sys.exit(1)

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
