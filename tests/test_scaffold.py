from pathlib import Path
import pytest
from scripts.scaffold import scaffold_skill


def test_scaffold_creates_skill_md(tmp_path):
    scaffold_skill("my-skill", tmp_path)
    assert (tmp_path / "my-skill" / "SKILL.md").exists()
    content = (tmp_path / "my-skill" / "SKILL.md").read_text()
    assert "name: my-skill" in content


def test_scaffold_creates_tools_py(tmp_path):
    scaffold_skill("my-skill", tmp_path)
    tools_py = tmp_path / "my-skill" / "tools.py"
    assert tools_py.exists()
    assert "class SkillRuntime" in tools_py.read_text()


def test_scaffold_creates_evals_structure(tmp_path):
    scaffold_skill("my-skill", tmp_path)
    base = tmp_path / "my-skill"
    assert (base / "evals" / "evals.json").exists()
    assert (base / "evals" / "eval_factory.py").exists()


def test_scaffold_substitutes_name_in_skill_md(tmp_path):
    scaffold_skill("account-movements", tmp_path)
    content = (tmp_path / "account-movements" / "SKILL.md").read_text()
    assert "name: account-movements" in content
    assert "Account Movements" in content


def test_scaffold_creates_optional_dirs(tmp_path):
    scaffold_skill("my-skill", tmp_path)
    base = tmp_path / "my-skill"
    assert (base / "references").is_dir()
    assert (base / "assets").is_dir()


def test_scaffold_raises_if_dir_exists(tmp_path):
    scaffold_skill("my-skill", tmp_path)
    with pytest.raises(FileExistsError):
        scaffold_skill("my-skill", tmp_path)
