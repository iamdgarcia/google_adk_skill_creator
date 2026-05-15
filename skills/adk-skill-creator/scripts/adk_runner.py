"""ADK execution backend. Replaces the claude -p subprocess used in the original skill-creator."""

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset
from google.genai import Client, types


def _make_vertex_model(model_name: str, project: str, location: str) -> Gemini:
    """Create a Gemini model instance backed by Vertex AI. Auth via ADC."""
    _project = project
    _location = location

    class VertexGemini(Gemini):
        @cached_property
        def api_client(self) -> Client:
            return Client(vertexai=True, project=_project, location=_location)

    return VertexGemini(model=model_name)


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
    project: str | None = None,
    location: str = "us-central1",
) -> RunResult:
    """Run a single eval prompt against the skill and return the result."""
    skill = load_skill_from_dir(skill_dir)
    tools = runtime.get_tools()

    model_obj = _make_vertex_model(model, project, location) if project else model
    agent = LlmAgent(
        name="adk_eval_agent",
        model=model_obj,
        tools=[SkillToolset(skills=[skill], additional_tools=tools)],
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="adk-eval",
        session_service=session_service,
    )
    session = await session_service.create_session(app_name="adk-eval", user_id="eval-user")

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
