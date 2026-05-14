from unittest.mock import MagicMock
from scripts.adk_runner import (
    RunResult,
    was_skill_activated,
    extract_response,
    extract_tool_calls,
)


def _fc(name: str, args: dict):
    """Build a mock FunctionCall."""
    fc = MagicMock()
    fc.name = name
    fc.args = args
    return fc


def _event(function_calls=None, is_final=False, text=None):
    """Build a mock ADK Event matching the real Event API."""
    event = MagicMock()
    event.get_function_calls.return_value = [_fc(fc["name"], fc.get("args", {})) for fc in (function_calls or [])]
    event.is_final_response.return_value = is_final
    if text:
        part = MagicMock()
        part.text = text
        event.content = MagicMock()
        event.content.parts = [part]
    else:
        event.content = None
    return event


def test_was_skill_activated_true():
    events = [_event(function_calls=[{"name": "load_skill", "args": {"skill_name": "sample-skill"}}])]
    assert was_skill_activated(events, "sample-skill") is True


def test_was_skill_activated_false_wrong_skill():
    events = [_event(function_calls=[{"name": "load_skill", "args": {"skill_name": "other-skill"}}])]
    assert was_skill_activated(events, "sample-skill") is False


def test_was_skill_activated_false_no_load_skill():
    events = [_event(function_calls=[{"name": "list_skills", "args": {}}])]
    assert was_skill_activated(events, "sample-skill") is False


def test_was_skill_activated_no_events():
    assert was_skill_activated([], "sample-skill") is False


def test_extract_response_returns_final_response_text():
    events = [
        _event(text="ignored", is_final=False),
        _event(text="Hello, Alice!", is_final=True),
    ]
    assert extract_response(events) == "Hello, Alice!"


def test_extract_response_empty_when_no_final():
    events = [_event(text="ignored", is_final=False)]
    assert extract_response(events) == ""


def test_extract_tool_calls():
    events = [
        _event(function_calls=[
            {"name": "load_skill", "args": {"skill_name": "sample-skill"}},
            {"name": "greet_user", "args": {"name": "Alice"}},
        ])
    ]
    calls = extract_tool_calls(events)
    assert len(calls) == 2
    assert calls[0] == {"name": "load_skill", "args": {"skill_name": "sample-skill"}}
    assert calls[1] == {"name": "greet_user", "args": {"name": "Alice"}}


def test_extract_tool_calls_empty():
    assert extract_tool_calls([]) == []


def test_run_result_fields():
    r = RunResult(response="hi", skill_activated=True, tool_calls=[])
    assert r.response == "hi"
    assert r.skill_activated is True
    assert r.events == []
