"""Create a new ADK skill directory from templates."""

from pathlib import Path

_TEMPLATES = Path(__file__).parent / "templates"


def _render(template_name: str, **kwargs) -> str:
    return (_TEMPLATES / template_name).read_text().format(**kwargs)


def scaffold_skill(name: str, output_dir: Path) -> Path:
    """Create output_dir/name with SKILL.md, tools.py, and eval structure.

    Raises FileExistsError if the directory already exists.
    """
    skill_dir = output_dir / name
    if skill_dir.exists():
        raise FileExistsError(f"Skill directory already exists: {skill_dir}")

    title = name.replace("-", " ").title()

    (skill_dir / "evals").mkdir(parents=True)
    (skill_dir / "references").mkdir()
    (skill_dir / "assets").mkdir()

    (skill_dir / "SKILL.md").write_text(_render("SKILL.md.tmpl", name=name, title=title))
    (skill_dir / "tools.py").write_text(_render("tools.py.tmpl", name=name))
    (skill_dir / "evals" / "evals.json").write_text(_render("evals.json.tmpl", name=name))
    (skill_dir / "evals" / "eval_factory.py").write_text(_render("eval_factory.py.tmpl", name=name))

    return skill_dir
