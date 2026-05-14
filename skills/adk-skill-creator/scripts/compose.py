"""Assemble multiple ADK skills into a single LlmAgent."""

from pathlib import Path
from typing import Any

import yaml

from google.adk.agents import LlmAgent
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset

_REQUIRED = {"name", "model", "skills"}


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load and validate agent.yaml. Raises ValueError on missing required fields."""
    config = yaml.safe_load(manifest_path.read_text()) or {}
    missing = _REQUIRED - set(config.keys())
    if missing:
        raise ValueError(f"agent.yaml missing required fields: {sorted(missing)}")
    return config


def compose_agent(manifest_path: Path, runtimes: dict[str, object]) -> LlmAgent:
    """Build LlmAgent from agent.yaml using pre-initialized SkillRuntime instances.

    runtimes maps skill name (str) -> initialized SkillRuntime instance.
    """
    config = load_manifest(manifest_path)

    skills, all_tools = [], []
    for skill_path_str in config["skills"]:
        skill_dir = Path(skill_path_str)
        if not skill_dir.is_absolute():
            skill_dir = manifest_path.parent / skill_dir
        skill = load_skill_from_dir(skill_dir)
        runtime = runtimes[skill.name]
        skills.append(skill)
        all_tools.extend(runtime.get_tools())

    return LlmAgent(
        model=config["model"],
        tools=[SkillToolset(skills=skills, additional_tools=all_tools)],
    )
