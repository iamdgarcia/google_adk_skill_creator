#!/usr/bin/env python3
"""Run evals for an ADK skill. Saves transcripts and metrics compatible with the grader agent."""

import argparse
import asyncio
import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.adk_runner import run_eval_case
from scripts.utils import import_eval_factory, parse_frontmatter


def _make_transcript(eval_case: dict, result) -> str:
    """Format a RunResult as markdown for the grader agent."""
    lines = [
        f"# Eval {eval_case['id']}",
        "",
        f"**Prompt:** {eval_case['prompt']}",
        "",
        f"**Expected:** {eval_case.get('expected_output', '')}",
        "",
        f"## Skill Activated",
        f"{'YES' if result.skill_activated else 'NO'} — `load_skill` {'was' if result.skill_activated else 'was NOT'} called",
        "",
        "## Tool Calls",
    ]
    if result.tool_calls:
        for call in result.tool_calls:
            lines.append(f"- `{call['name']}({json.dumps(call['args'])})`")
    else:
        lines.append("_(none)_")
    lines += ["", "## Response", result.response or "_(empty)_"]
    return "\n".join(lines)


def _run_single(
    skill_dir: Path,
    eval_case: dict,
    runtime,
    model: str,
    run_dir: Path,
    project: str | None = None,
    location: str = "us-central1",
) -> None:
    outputs_dir = run_dir / f"eval_{eval_case['id']}" / "outputs"
    outputs_dir.mkdir(parents=True)

    start = time.time()
    result = asyncio.run(
        run_eval_case(skill_dir, runtime, eval_case["prompt"], model=model, project=project, location=location)
    )
    duration = time.time() - start

    (outputs_dir / "transcript.md").write_text(_make_transcript(eval_case, result))
    (outputs_dir / "metrics.json").write_text(json.dumps({
        "tool_calls": dict(Counter(c["name"] for c in result.tool_calls)),
        "total_tool_calls": len(result.tool_calls),
        "skill_activated": result.skill_activated,
        "output_chars": len(result.response),
    }, indent=2))
    (outputs_dir.parent / "timing.json").write_text(json.dumps({
        "executor_duration_seconds": round(duration, 2),
    }, indent=2))

    if eval_case.get("expected_skill_activated") is not None:
        skill_name = parse_frontmatter(skill_dir / "SKILL.md")["name"]
        (outputs_dir / "skill_activation.json").write_text(json.dumps({
            "expected": eval_case["expected_skill_activated"],
            "actual": result.skill_activated,
            "skill_name": skill_name,
        }, indent=2))

    status = "ACTIVATED" if result.skill_activated else "NOT ACTIVATED"
    print(f"  [{status}] Eval {eval_case['id']} — {len(result.tool_calls)} tool calls, {duration:.1f}s")


def main():
    parser = argparse.ArgumentParser(description="Run ADK skill evals")
    parser.add_argument("skill_dir", type=Path, help="Path to ADK skill directory")
    parser.add_argument("--model", default="gemini-2.0-flash")
    parser.add_argument("--project", default=None, help="Google Cloud project ID for Vertex AI (uses ADC auth)")
    parser.add_argument("--location", default="us-central1", help="Vertex AI region (default: us-central1)")
    parser.add_argument("--evals", type=int, nargs="+", help="Specific eval IDs to run")
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("runs") / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"),
    )
    args = parser.parse_args()

    evals_data = json.loads((args.skill_dir / "evals" / "evals.json").read_text())
    runtime = import_eval_factory(args.skill_dir / "evals" / "eval_factory.py")()
    cases = evals_data["evals"]
    if args.evals:
        cases = [c for c in cases if c["id"] in args.evals]

    args.run_dir.mkdir(parents=True, exist_ok=True)
    print(f"Running {len(cases)} eval(s) for: {evals_data['skill_name']}")
    for case in cases:
        _run_single(args.skill_dir, case, runtime, args.model, args.run_dir, project=args.project, location=args.location)

    print(f"\nResults written to: {args.run_dir}")
    print("Next: run the grader agent on each eval_N/ directory.")


if __name__ == "__main__":
    main()
