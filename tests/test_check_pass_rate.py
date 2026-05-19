import json
from pathlib import Path
import pytest
from scripts.check_pass_rate import check_pass_rate, load_threshold


def _write_grading(run_dir: Path, eval_id: int, pass_rate: float, passed: int, total: int, skill_activated: bool | None = None) -> None:
    eval_dir = run_dir / f"eval_{eval_id}"
    eval_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "expectations": [{"text": f"exp{i}", "passed": i < passed, "evidence": "x"} for i in range(total)],
        "summary": {"passed": passed, "failed": total - passed, "total": total, "pass_rate": pass_rate},
    }
    if skill_activated is not None:
        payload["skill_activated"] = skill_activated
    (eval_dir / "grading.json").write_text(json.dumps(payload))


def _write_evals_json(skill_dir: Path, threshold: float) -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "evals").mkdir(exist_ok=True)
    (skill_dir / "evals" / "evals.json").write_text(json.dumps({"skill_name": "test", "pass_threshold": threshold, "evals": []}))


def test_load_threshold_reads_from_evals_json(tmp_path):
    _write_evals_json(tmp_path / "skill", 0.9)
    assert load_threshold(tmp_path / "skill") == 0.9


def test_load_threshold_defaults_to_0_85(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "evals").mkdir()
    (skill_dir / "evals" / "evals.json").write_text(json.dumps({"skill_name": "test", "evals": []}))
    assert load_threshold(skill_dir) == 0.85


def test_all_passing_returns_true(tmp_path):
    run_dir = tmp_path / "run"
    _write_grading(run_dir, 1, 1.0, 3, 3)
    _write_grading(run_dir, 2, 1.0, 2, 2)
    passed, report = check_pass_rate(run_dir, threshold=0.85)
    assert passed is True
    assert report["pass_rate"] == 1.0
    assert report["total_expectations"] == 5


def test_below_threshold_returns_false(tmp_path):
    run_dir = tmp_path / "run"
    _write_grading(run_dir, 1, 0.5, 1, 2)
    _write_grading(run_dir, 2, 0.5, 1, 2)
    passed, report = check_pass_rate(run_dir, threshold=0.85)
    assert passed is False
    assert report["pass_rate"] == 0.5


def test_activation_failure_returns_false_even_if_pass_rate_ok(tmp_path):
    run_dir = tmp_path / "run"
    _write_grading(run_dir, 1, 1.0, 3, 3, skill_activated=False)
    passed, report = check_pass_rate(run_dir, threshold=0.85)
    assert passed is False
    assert "eval_1" in report["activation_failures"]


def test_no_grading_files_returns_false(tmp_path):
    run_dir = tmp_path / "empty_run"
    run_dir.mkdir()
    passed, report = check_pass_rate(run_dir, threshold=0.85)
    assert passed is False
    assert "error" in report


def test_activation_true_does_not_flag_failure(tmp_path):
    run_dir = tmp_path / "run"
    _write_grading(run_dir, 1, 1.0, 2, 2, skill_activated=True)
    passed, report = check_pass_rate(run_dir, threshold=0.85)
    assert passed is True
    assert report["activation_failures"] == []
