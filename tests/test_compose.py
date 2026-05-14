from pathlib import Path
from unittest.mock import MagicMock, patch
import yaml
import pytest
from scripts.compose import load_manifest, compose_agent
from conftest import FIXTURE_SKILL_DIR


def test_load_manifest(tmp_path):
    manifest = {
        "name": "test-agent",
        "model": "gemini-2.0-flash",
        "skills": ["skills/sample-skill"],
        "runtime_factory": "runtime_factory.py",
    }
    p = tmp_path / "agent.yaml"
    p.write_text(yaml.dump(manifest))
    result = load_manifest(p)
    assert result["name"] == "test-agent"
    assert result["skills"] == ["skills/sample-skill"]


def test_load_manifest_missing_field_raises(tmp_path):
    p = tmp_path / "agent.yaml"
    p.write_text("name: test-agent\n")
    with pytest.raises(ValueError, match="model"):
        load_manifest(p)


@patch("scripts.compose.LlmAgent")
@patch("scripts.compose.SkillToolset")
@patch("scripts.compose.load_skill_from_dir")
def test_compose_agent_wires_skills_and_tools(mock_load_skill, mock_toolset, mock_agent, tmp_path):
    manifest = {
        "name": "test-agent",
        "model": "gemini-2.0-flash",
        "skills": [str(FIXTURE_SKILL_DIR)],
        "runtime_factory": "runtime_factory.py",
    }
    (tmp_path / "agent.yaml").write_text(yaml.dump(manifest))

    mock_skill = MagicMock()
    mock_skill.name = "sample-skill"
    mock_load_skill.return_value = mock_skill

    tool_fn = MagicMock()
    runtime = MagicMock()
    runtime.get_tools.return_value = [tool_fn]
    runtimes = {"sample-skill": runtime}

    compose_agent(tmp_path / "agent.yaml", runtimes)

    mock_agent.assert_called_once()
    mock_toolset.assert_called_once()
    _, kwargs = mock_toolset.call_args
    assert mock_skill in kwargs["skills"]
    assert tool_fn in kwargs["additional_tools"]
