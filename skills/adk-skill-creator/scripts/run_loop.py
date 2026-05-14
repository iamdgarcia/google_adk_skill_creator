#!/usr/bin/env python3
"""Test a skill description for ADK activation accuracy.

Called with --description to evaluate one candidate. Run repeatedly with
different descriptions to find the best one. The loop is driven by the
adk-skill-creator skill instructions, not by this script.
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.skills import load_skill_from_dir
from google.adk.skills.models import Frontmatter, Skill
from google.adk.tools.skill_toolset import SkillToolset
from google.genai import types

from scripts.adk_runner import was_skill_activated
from scripts.utils import import_eval_factory


async def _evaluate_description(
    skill_dir: Path,
    description: str,
    queries: list[dict[str, Any]],
    runtime: object,
    model: str,
) -> dict:
    """Test description accuracy. Returns accuracy metrics and per-query results."""
    base_skill = load_skill_from_dir(skill_dir)
    fm_data = base_skill.frontmatter.model_dump()
    fm_data["description"] = description
    test_skill = Skill(
        frontmatter=Frontmatter(**fm_data),
        instructions=base_skill.instructions,
        resources=base_skill.resources,
    )

    agent = LlmAgent(
        model=model,
        tools=[SkillToolset(skills=[test_skill], additional_tools=runtime.get_tools())],
    )
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="loop", session_service=session_service)

    results = []
    for q in queries:
        session = session_service.create_session(app_name="loop", user_id="loop-user")
        message = types.Content(role="user", parts=[types.Part(text=q["query"])])
        events = []
        async for event in runner.run_async(
            user_id="loop-user", session_id=session.id, new_message=message
        ):
            events.append(event)
        activated = was_skill_activated(events, test_skill.name)
        correct = activated == q["should_trigger"]
        results.append({"query": q["query"], "expected": q["should_trigger"], "actual": activated, "correct": correct})

    accuracy = sum(r["correct"] for r in results) / len(results) if results else 0.0
    return {"description": description, "accuracy": accuracy, "results": results}


def main():
    parser = argparse.ArgumentParser(description="Test a skill description for activation accuracy")
    parser.add_argument("skill_dir", type=Path, help="Path to ADK skill directory")
    parser.add_argument("trigger_evals", type=Path, help="JSON array of {query, should_trigger} objects")
    parser.add_argument("--description", required=True, help="Description string to test")
    parser.add_argument("--model", default="gemini-2.0-flash")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    queries = json.loads(args.trigger_evals.read_text())
    runtime = import_eval_factory(args.skill_dir / "evals" / "eval_factory.py")()

    result = asyncio.run(_evaluate_description(args.skill_dir, args.description, queries, runtime, args.model))

    print(f"Accuracy: {result['accuracy']:.0%} ({sum(r['correct'] for r in result['results'])}/{len(result['results'])})")
    for r in result["results"]:
        mark = "✓" if r["correct"] else "✗"
        print(f"  {mark} [{r['expected']}→{r['actual']}] {r['query']}")

    if args.output:
        args.output.write_text(json.dumps(result, indent=2))
        print(f"\nSaved to: {args.output}")


if __name__ == "__main__":
    main()
