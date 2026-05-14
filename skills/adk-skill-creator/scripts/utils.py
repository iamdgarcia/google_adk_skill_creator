import importlib.util
from pathlib import Path
from typing import Any

import yaml


def parse_frontmatter(skill_md_path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from SKILL.md. Returns empty dict if none found."""
    text = skill_md_path.read_text()
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def list_adk_additional_tools(frontmatter: dict) -> list[str]:
    """Extract adk_additional_tools list from frontmatter metadata. Returns [] if absent."""
    return frontmatter.get("metadata", {}).get("adk_additional_tools", [])


def load_runtime_class(tools_py_path: Path):
    """Dynamically import SkillRuntime class from a skill's tools.py."""
    spec = importlib.util.spec_from_file_location("_skill_tools", tools_py_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SkillRuntime


def import_eval_factory(eval_factory_path: Path):
    """Import build_eval_runtime callable from a skill's evals/eval_factory.py."""
    spec = importlib.util.spec_from_file_location("_eval_factory", eval_factory_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_eval_runtime
