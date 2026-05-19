#!/usr/bin/env python3
"""Full eval pipeline: validate → run evals → grade → check pass rate.

Usage:
    PYTHONPATH=skills/adk-skill-creator \
    python skills/adk-skill-creator/scripts/eval_pipeline.py skills/my-skill \
      --model gemini-2.0-flash \
      --grader-model gemini-2.5-flash-preview-05-20
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.check_pass_rate import check_pass_rate, load_threshold
from scripts.quick_validate import validate_skill_dir
from scripts.run_eval import _run_single
from scripts.run_grader import grade_eval
from scripts.utils import import_eval_factory


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Full ADK skill eval pipeline")
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("--model", default="gemini-2.0-flash", help="Executor model")
    parser.add_argument(
        "--grader-model",
        default="gemini-2.5-flash-preview-05-20",
        dest="grader_model",
        help="Grader model (should be stronger than executor to reduce self-output bias)",
    )
    parser.add_argument("--project", default=None, help="Google Cloud project ID for Vertex AI")
    parser.add_argument("--location", default="us-central1")
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        dest="run_dir",
        help="Output directory for this run (default: runs/<timestamp>)",
    )
    return parser


def run_eval_cases(
    skill_dir: Path,
    evals_data: dict,
    runtime: object,
    model: str,
    run_dir: Path,
    project: str | None = None,
    location: str = "us-central1",
) -> list[Path]:
    """Run all eval cases and return the list of eval_N directories created."""
    eval_dirs = []
    for case in evals_data["evals"]:
        _run_single(skill_dir, case, runtime, model, run_dir, project=project, location=location)
        eval_dirs.append(run_dir / f"eval_{case['id']}")
    return eval_dirs


def run_pipeline(
    skill_dir: Path,
    model: str,
    grader_model: str,
    run_dir: Path,
    project: str | None = None,
    location: str = "us-central1",
) -> None:
    """Run full pipeline. Exits with code 1 on any failure."""
    # Step 1: validate
    errors = validate_skill_dir(skill_dir)
    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    print("✓ Validation passed")

    # Step 2: load evals and runtime
    evals_data = json.loads((skill_dir / "evals" / "evals.json").read_text(encoding="utf-8"))
    runtime = import_eval_factory(skill_dir / "evals" / "eval_factory.py")()

    # Step 3: run evals
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"Running {len(evals_data['evals'])} eval(s) → {run_dir}")
    eval_dirs = run_eval_cases(skill_dir, evals_data, runtime, model, run_dir, project=project, location=location)
    print("✓ Evals complete")

    # Step 4: grade each eval
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set — cannot run automated grading", file=sys.stderr)
        sys.exit(1)

    for eval_dir in eval_dirs:
        grading = grade_eval(eval_dir, model=grader_model, api_key=api_key)
        summary = grading.get("summary", {})
        print(f"  Graded {eval_dir.name}: {summary.get('pass_rate', 0):.0%} ({summary.get('passed', 0)}/{summary.get('total', 0)})")
    print("✓ Grading complete")

    # Step 5: CI gate
    threshold = load_threshold(skill_dir)
    passed, report = check_pass_rate(run_dir, threshold)

    print(f"\nResults: {report['pass_rate']:.0%} ({report['passed_expectations']}/{report['total_expectations']}) — threshold {threshold:.0%}")

    if report.get("activation_failures"):
        print(f"  Activation wrong for: {', '.join(report['activation_failures'])}")

    if not passed:
        print("FAIL")
        sys.exit(1)

    print("PASS")


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    run_dir = args.run_dir or Path("runs") / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    run_pipeline(
        skill_dir=args.skill_dir,
        model=args.model,
        grader_model=args.grader_model,
        run_dir=run_dir,
        project=args.project,
        location=args.location,
    )


if __name__ == "__main__":
    main()
