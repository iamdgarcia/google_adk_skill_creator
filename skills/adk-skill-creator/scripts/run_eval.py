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


def _write_json(path: Path, payload: object) -> None:
    """Write one JSON payload to disk using UTF-8 encoding."""

    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _tool_call_steps(tool_calls: list[dict]) -> list[dict]:
    """Return the ordered tool-call trace annotated with one-based step numbers."""

    return [
        {
            "step": index,
            "name": call["name"],
            "args": call.get("args", {}),
        }
        for index, call in enumerate(tool_calls, start=1)
    ]


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
    eval_dir = outputs_dir.parent

    start = time.time()
    result = asyncio.run(
        run_eval_case(skill_dir, runtime, eval_case["prompt"], model=model, project=project, location=location)
    )
    duration = time.time() - start
    ordered_tool_calls = _tool_call_steps(result.tool_calls)

    (outputs_dir / "transcript.md").write_text(
        _make_transcript(eval_case, result),
        encoding="utf-8",
    )
    _write_json(
        outputs_dir / "metrics.json",
        {
            "tool_calls": dict(Counter(c["name"] for c in result.tool_calls)),
            "total_tool_calls": len(result.tool_calls),
            "skill_activated": result.skill_activated,
            "output_chars": len(result.response),
        },
    )
    _write_json(
        eval_dir / "eval_metadata.json",
        {
            "eval_id": eval_case["id"],
            "prompt": eval_case["prompt"],
            "expected_output": eval_case.get("expected_output", ""),
            "expected_skill_activated": eval_case.get("expected_skill_activated"),
            "response": result.response,
            "tool_calls": ordered_tool_calls,
        },
    )
    _write_json(
        eval_dir / "timing.json",
        {
            "executor_duration_seconds": round(duration, 2),
        },
    )

    if eval_case.get("expected_skill_activated") is not None:
        skill_name = parse_frontmatter(skill_dir / "SKILL.md")["name"]
        _write_json(
            outputs_dir / "skill_activation.json",
            {
                "expected": eval_case["expected_skill_activated"],
                "actual": result.skill_activated,
                "skill_name": skill_name,
            },
        )

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
