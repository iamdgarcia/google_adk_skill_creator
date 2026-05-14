"""ADK execution backend. Replaces the claude -p subprocess used in the original skill-creator."""

from dataclasses import dataclass, field
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset
from google.genai import types


@dataclass
class RunResult:
    response: str
    skill_activated: bool
    tool_calls: list[dict]
    events: list = field(default_factory=list)


def was_skill_activated(events: list, skill_name: str) -> bool:
    """Return True if load_skill was called for skill_name in the event trace."""
    for event in events:
        for fc in event.get_function_calls():
            if fc.name == "load_skill" and (fc.args or {}).get("skill_name") == skill_name:
                return True
    return False


def extract_response(events: list) -> str:
    """Return text from the final model response event."""
    for event in reversed(events):
        if event.is_final_response() and event.content and event.content.parts:
            texts = [p.text for p in event.content.parts if p.text]
            if texts:
                return " ".join(texts)
    return ""


def extract_tool_calls(events: list) -> list[dict]:
    """Return all function calls from the event stream in order."""
    calls = []
    for event in events:
        for fc in event.get_function_calls():
            calls.append({"name": fc.name, "args": fc.args or {}})
    return calls


async def run_eval_case(
    skill_dir: Path,
    runtime: object,
    prompt: str,
    model: str = "gemini-2.0-flash",
) -> RunResult:
    """Run a single eval prompt against the skill and return the result."""
    skill = load_skill_from_dir(skill_dir)
    tools = runtime.get_tools()

    agent = LlmAgent(
        model=model,
        tools=[SkillToolset(skills=[skill], additional_tools=tools)],
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="adk-eval",
        session_service=session_service,
    )
    session = session_service.create_session(app_name="adk-eval", user_id="eval-user")

    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    events = []
    async for event in runner.run_async(
        user_id="eval-user",
        session_id=session.id,
        new_message=message,
    ):
        events.append(event)

    return RunResult(
        response=extract_response(events),
        skill_activated=was_skill_activated(events, skill.name),
        tool_calls=extract_tool_calls(events),
        events=events,
    )
