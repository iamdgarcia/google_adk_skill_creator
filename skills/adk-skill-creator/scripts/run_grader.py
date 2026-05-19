#!/usr/bin/env python3
"""Automated grader: invokes Gemini with grader.md + inlined eval files → writes grading.json.

Uses a stronger model than the executor (default: gemini-2.5-flash-preview-05-20) to
mitigate self-output bias when grader and executor both use Gemini.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from google.genai import Client, types


_AGENTS_DIR = Path(__file__).parent.parent / "agents"


def _build_grading_prompt(eval_dir: Path) -> tuple[str, str]:
    """Return (system_prompt, user_message) by inlining eval file contents."""
    grader_md = (_AGENTS_DIR / "grader.md").read_text(encoding="utf-8")
    system_prompt = (
        grader_md
        + "\n\nIMPORTANT: You are running in automated mode. "
        "Output ONLY the complete grading JSON object. No markdown fences, no commentary."
    )

    metadata = json.loads((eval_dir / "eval_metadata.json").read_text(encoding="utf-8"))
    transcript_path = eval_dir / "outputs" / "transcript.md"
    transcript = transcript_path.read_text(encoding="utf-8") if transcript_path.exists() else "(no transcript)"

    metrics_path = eval_dir / "outputs" / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}

    activation_path = eval_dir / "outputs" / "skill_activation.json"
    activation = json.loads(activation_path.read_text(encoding="utf-8")) if activation_path.exists() else None

    timing_path = eval_dir / "timing.json"
    timing = json.loads(timing_path.read_text(encoding="utf-8")) if timing_path.exists() else {}

    parts = [
        f"## Eval Metadata\n```json\n{json.dumps(metadata, indent=2)}\n```",
        f"## Transcript\n{transcript}",
        f"## Execution Metrics\n```json\n{json.dumps(metrics, indent=2)}\n```",
    ]
    if activation:
        parts.append(f"## Skill Activation\n```json\n{json.dumps(activation, indent=2)}\n```")
    if timing:
        parts.append(f"## Timing\n```json\n{json.dumps(timing, indent=2)}\n```")

    expectations = metadata.get("expectations", [])
    parts.append(f"## Expectations to Grade\n{json.dumps(expectations, indent=2)}")
    parts.append("Output the complete grading JSON now.")

    return system_prompt, "\n\n".join(parts)


def _parse_grading_json(raw: str) -> dict:
    """Parse JSON from model response, stripping markdown fences if present."""
    raw = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    if fence_match:
        raw = fence_match.group(1).strip()
    return json.loads(raw)


def grade_eval(
    eval_dir: Path,
    model: str = "gemini-2.5-flash-preview-05-20",
    api_key: str | None = None,
) -> dict:
    """Grade one eval directory and write grading.json. Returns the grading dict."""
    system_prompt, user_message = _build_grading_prompt(eval_dir)

    client = Client(api_key=api_key or os.environ["GOOGLE_API_KEY"])
    response = client.models.generate_content(
        model=model,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
        ),
    )

    grading = _parse_grading_json(response.text)
    grading_path = eval_dir / "grading.json"
    grading_path.write_text(json.dumps(grading, indent=2, ensure_ascii=False), encoding="utf-8")
    return grading


def main() -> None:
    parser = argparse.ArgumentParser(description="Grade one eval directory using Gemini")
    parser.add_argument("eval_dir", type=Path, help="Path to eval_N/ directory (contains eval_metadata.json)")
    parser.add_argument("--model", default="gemini-2.5-flash-preview-05-20", help="Grader model")
    args = parser.parse_args()

    if not args.eval_dir.is_dir():
        print(f"ERROR: {args.eval_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    grading = grade_eval(args.eval_dir, model=args.model, api_key=api_key)
    summary = grading.get("summary", {})
    print(f"Graded {args.eval_dir.name}: {summary.get('pass_rate', 0):.0%} ({summary.get('passed', 0)}/{summary.get('total', 0)})")
    print(f"Saved: {args.eval_dir / 'grading.json'}")


if __name__ == "__main__":
    main()
