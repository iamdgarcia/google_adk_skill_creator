from pathlib import Path
from conftest import FIXTURE_SKILL_DIR
from scripts.utils import (
    parse_frontmatter,
    list_adk_additional_tools,
    load_runtime_class,
    import_eval_factory,
)


def test_parse_frontmatter_returns_name():
    fm = parse_frontmatter(FIXTURE_SKILL_DIR / "SKILL.md")
    assert fm["name"] == "sample-skill"


def test_parse_frontmatter_returns_metadata():
    fm = parse_frontmatter(FIXTURE_SKILL_DIR / "SKILL.md")
    assert "adk_additional_tools" in fm["metadata"]


def test_list_adk_additional_tools():
    fm = parse_frontmatter(FIXTURE_SKILL_DIR / "SKILL.md")
    tools = list_adk_additional_tools(fm)
    assert tools == ["greet_user", "get_greeting"]


def test_list_adk_additional_tools_empty_when_missing():
    assert list_adk_additional_tools({}) == []


def test_load_runtime_class():
    RuntimeClass = load_runtime_class(FIXTURE_SKILL_DIR / "tools.py")
    assert hasattr(RuntimeClass, "get_tools")
    instance = RuntimeClass(greeting="Hi")
    assert instance.greeting == "Hi"


def test_import_eval_factory():
    build_fn = import_eval_factory(FIXTURE_SKILL_DIR / "evals" / "eval_factory.py")
    runtime = build_fn()
    assert hasattr(runtime, "get_tools")
    assert hasattr(runtime, "greet_user")
