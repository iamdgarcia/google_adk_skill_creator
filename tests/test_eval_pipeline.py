import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from scripts.eval_pipeline import build_arg_parser, run_pipeline
import scripts.eval_pipeline as ep


def _write_minimal_skill(skill_dir: Path) -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("---\nname: test\ndescription: test skill\n---\n# Test\n")
    (skill_dir / "tools.py").write_text("class SkillRuntime:\n    def get_tools(self): return []\n")
    (skill_dir / "evals").mkdir(exist_ok=True)
    (skill_dir / "evals" / "evals.json").write_text(json.dumps({
        "skill_name": "test-skill",
        "pass_threshold": 0.85,
        "evals": [{"id": 1, "prompt": "hello", "expected_skill_activated": True, "expectations": ["Agent responds"]}],
    }))
    (skill_dir / "evals" / "eval_factory.py").write_text(
        "class MockRuntime:\n    def get_tools(self): return []\n\ndef build_eval_runtime(): return MockRuntime()\n"
    )


def test_arg_parser_sets_defaults():
    parser = build_arg_parser()
    args = parser.parse_args(["skills/my-skill"])
    assert args.model == "gemini-2.0-flash"
    assert args.grader_model == "gemini-2.5-flash-preview-05-20"
    assert args.skill_dir == Path("skills/my-skill")


def test_pipeline_exits_1_on_validation_failure(tmp_path):
    empty_skill = tmp_path / "bad-skill"
    empty_skill.mkdir()
    with pytest.raises(SystemExit) as exc:
        run_pipeline(empty_skill, model="gemini-2.0-flash", grader_model="gemini-2.5-flash-preview-05-20", run_dir=tmp_path / "run")
    assert exc.value.code == 1


def test_pipeline_calls_grade_eval_for_each_eval_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    skill_dir = tmp_path / "skill"
    _write_minimal_skill(skill_dir)
    run_dir = tmp_path / "run"
    fake_eval_dir = run_dir / "eval_1"

    with patch.object(ep, "run_eval_cases", return_value=[fake_eval_dir]) as mock_run, \
         patch.object(ep, "grade_eval", return_value={"summary": {"pass_rate": 1.0, "passed": 1, "total": 1}}) as mock_grade, \
         patch.object(ep, "check_pass_rate", return_value=(True, {"pass_rate": 1.0, "passed_expectations": 1, "total_expectations": 1, "activation_failures": []})):
        run_pipeline(skill_dir, model="gemini-2.0-flash", grader_model="gemini-2.5-flash-preview-05-20", run_dir=run_dir)
        mock_run.assert_called_once()
        mock_grade.assert_called_once_with(fake_eval_dir, model="gemini-2.5-flash-preview-05-20", api_key="test-key")


def test_pipeline_exits_1_when_check_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    skill_dir = tmp_path / "skill"
    _write_minimal_skill(skill_dir)
    run_dir = tmp_path / "run"

    with patch.object(ep, "run_eval_cases", return_value=[]), \
         patch.object(ep, "grade_eval"), \
         patch.object(ep, "check_pass_rate", return_value=(False, {"pass_rate": 0.5, "passed_expectations": 1, "total_expectations": 2, "activation_failures": []})):
        with pytest.raises(SystemExit) as exc:
            run_pipeline(skill_dir, model="gemini-2.0-flash", grader_model="gemini-2.5-flash-preview-05-20", run_dir=run_dir)
        assert exc.value.code == 1
