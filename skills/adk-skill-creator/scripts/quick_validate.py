import inspect
from pathlib import Path

from scripts.utils import parse_frontmatter, list_adk_additional_tools, load_runtime_class


def validate_skill_dir(skill_dir: Path) -> list[str]:
    """Return list of validation errors for an ADK skill directory. Empty list means valid."""
    errors = []

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ["SKILL.md not found"]

    tools_py = skill_dir / "tools.py"
    if not tools_py.exists():
        return ["tools.py not found"]

    frontmatter = parse_frontmatter(skill_md)
    declared = set(list_adk_additional_tools(frontmatter))

    try:
        RuntimeClass = load_runtime_class(tools_py)
    except AttributeError:
        return ["tools.py must define a SkillRuntime class"]

    public_methods = {
        name
        for name, _ in inspect.getmembers(RuntimeClass, predicate=inspect.isfunction)
        if not name.startswith("_") and name != "get_tools"
    }

    for name in declared - public_methods:
        errors.append(f"'{name}' declared in adk_additional_tools but not a method of SkillRuntime")
    for name in public_methods - declared:
        errors.append(f"SkillRuntime method '{name}' not declared in adk_additional_tools")

    return errors
