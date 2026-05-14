from pathlib import Path
import pytest
from conftest import FIXTURE_SKILL_DIR
from scripts.quick_validate import validate_skill_dir


def test_valid_skill_has_no_errors():
    errors = validate_skill_dir(FIXTURE_SKILL_DIR)
    assert errors == []


def test_missing_skill_md_is_error(tmp_path):
    (tmp_path / "tools.py").write_text("class SkillRuntime:\n    def get_tools(self): return []\n")
    errors = validate_skill_dir(tmp_path)
    assert any("SKILL.md" in e for e in errors)


def test_missing_tools_py_is_error(tmp_path):
    (tmp_path / "SKILL.md").write_text("---\nname: x\ndescription: y\n---\n")
    errors = validate_skill_dir(tmp_path)
    assert any("tools.py" in e for e in errors)


def test_missing_skill_runtime_class_is_error(tmp_path):
    (tmp_path / "SKILL.md").write_text("---\nname: x\ndescription: y\n---\n")
    (tmp_path / "tools.py").write_text("# no SkillRuntime\n")
    errors = validate_skill_dir(tmp_path)
    assert any("SkillRuntime" in e for e in errors)


def test_undeclared_method_is_error(tmp_path):
    (tmp_path / "SKILL.md").write_text(
        "---\nname: x\ndescription: y\nmetadata:\n  adk_additional_tools:\n    - foo\n---\n"
    )
    (tmp_path / "tools.py").write_text(
        "class SkillRuntime:\n"
        "    def foo(self): pass\n"
        "    def bar(self): pass\n"  # bar not declared
        "    def get_tools(self): return []\n"
    )
    errors = validate_skill_dir(tmp_path)
    assert any("bar" in e for e in errors)


def test_declared_but_missing_method_is_error(tmp_path):
    (tmp_path / "SKILL.md").write_text(
        "---\nname: x\ndescription: y\nmetadata:\n  adk_additional_tools:\n    - foo\n    - missing\n---\n"
    )
    (tmp_path / "tools.py").write_text(
        "class SkillRuntime:\n"
        "    def foo(self): pass\n"
        "    def get_tools(self): return []\n"
    )
    errors = validate_skill_dir(tmp_path)
    assert any("missing" in e for e in errors)
