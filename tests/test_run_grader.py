import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from conftest import FIXTURE_SKILL_DIR
from scripts.run_grader import _build_grading_prompt, _parse_grading_json, grade_eval


def _make_eval_dir(tmp_path: Path) -> Path:
    eval_dir = tmp_path / "eval_1"
    outputs = eval_dir / "outputs"
    outputs.mkdir(parents=True)

    (eval_dir / "eval_metadata.json").write_text(json.dumps({
        "eval_id": 1,
        "prompt": "How do I create an ADK skill?",
        "expected_output": "Agent scaffolds the skill",
        "expected_skill_activated": True,
        "response": "Here is how to scaffold...",
        "tool_calls": [],
        "expectations": ["Agent runs scaffold.py", "Agent explains SkillRuntime"],
    }))
    (outputs / "transcript.md").write_text("# Eval 1\n\n**Prompt:** How do I create an ADK skill?\n\n## Response\nHere is how...")
    (outputs / "metrics.json").write_text(json.dumps({"total_tool_calls": 2, "skill_activated": True, "output_chars": 500}))
    (outputs / "skill_activation.json").write_text(json.dumps({"expected": True, "actual": True, "skill_name": "adk-skill-creator"}))
    (eval_dir / "timing.json").write_text(json.dumps({"executor_duration_seconds": 12.3}))
    return eval_dir


def test_build_grading_prompt_includes_transcript(tmp_path):
    eval_dir = _make_eval_dir(tmp_path)
    system_prompt, user_message = _build_grading_prompt(eval_dir)
    assert "Eval 1" in user_message
    assert "How do I create an ADK skill?" in user_message
    assert "Agent runs scaffold.py" in user_message
    assert len(system_prompt) > 100  # grader.md loaded


def test_build_grading_prompt_includes_activation(tmp_path):
    eval_dir = _make_eval_dir(tmp_path)
    _, user_message = _build_grading_prompt(eval_dir)
    assert "adk-skill-creator" in user_message


def test_build_grading_prompt_handles_missing_optional_files(tmp_path):
    eval_dir = _make_eval_dir(tmp_path)
    (eval_dir / "outputs" / "skill_activation.json").unlink()
    (eval_dir / "timing.json").unlink()
    system_prompt, user_message = _build_grading_prompt(eval_dir)
    assert "How do I create an ADK skill?" in user_message


def test_parse_grading_json_valid():
    raw = json.dumps({
        "expectations": [{"text": "Agent runs scaffold.py", "passed": True, "evidence": "Seen in transcript"}],
        "summary": {"passed": 1, "failed": 0, "total": 1, "pass_rate": 1.0},
        "skill_activated": True,
    })
    result = _parse_grading_json(raw)
    assert result["summary"]["pass_rate"] == 1.0
    assert result["expectations"][0]["passed"] is True


def test_parse_grading_json_strips_markdown_fences():
    raw = "```json\n{\"summary\": {\"pass_rate\": 0.5}, \"expectations\": []}\n```"
    result = _parse_grading_json(raw)
    assert result["summary"]["pass_rate"] == 0.5


def test_grade_eval_writes_grading_json(tmp_path):
    eval_dir = _make_eval_dir(tmp_path)
    grading_payload = {
        "skill_activated": True,
        "expectations": [
            {"text": "Agent runs scaffold.py", "passed": True, "evidence": "Found in transcript"},
            {"text": "Agent explains SkillRuntime", "passed": True, "evidence": "Mentioned in response"},
        ],
        "summary": {"passed": 2, "failed": 0, "total": 2, "pass_rate": 1.0},
        "claims": [],
        "eval_feedback": {"suggestions": [], "overall": "Evals look solid."},
    }
    mock_response = MagicMock()
    mock_response.text = json.dumps(grading_payload)

    with patch("scripts.run_grader.Client") as MockClient:
        mock_client = MockClient.return_value
        mock_client.models.generate_content.return_value = mock_response
        grade_eval(eval_dir, model="gemini-2.5-flash-preview-05-20", api_key="test-key")

    grading_file = eval_dir / "grading.json"
    assert grading_file.exists()
    grading = json.loads(grading_file.read_text())
    assert grading["summary"]["pass_rate"] == 1.0
    assert len(grading["expectations"]) == 2
