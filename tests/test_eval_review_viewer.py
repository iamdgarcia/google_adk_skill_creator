import importlib.util
import json
from pathlib import Path

from conftest import FIXTURE_SKILL_DIR
from scripts.adk_runner import RunResult
from scripts import run_eval as run_eval_script


def _load_generate_review_module():
    """Import the eval review module from its file path."""

    module_path = (
        Path(__file__).parent.parent
        / "skills"
        / "adk-skill-creator"
        / "eval-viewer"
        / "generate_review.py"
    )
    spec = importlib.util.spec_from_file_location("test_generate_review", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_run_reads_explicit_eval_metadata_and_sequence(tmp_path: Path):
    """The review builder should expose prompt, response, and ordered tool calls."""

    generate_review = _load_generate_review_module()
    run_dir = tmp_path / "eval_7"
    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(parents=True)

    (run_dir / "eval_metadata.json").write_text(
        json.dumps(
            {
                "eval_id": 7,
                "prompt": "Quiero ver las compras de mi tarjeta.",
                "expected_output": "La skill debe listar tarjetas y consultar movimientos.",
                "response": "He recuperado un movimiento.",
                "tool_calls": [
                    {"step": 1, "name": "load_skill", "args": {"skill_name": "consulta-movimientos"}},
                    {"step": 2, "name": "listado_tarjetas", "args": {}},
                ],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "timing.json").write_text(
        json.dumps({"executor_duration_seconds": 3.4}),
        encoding="utf-8",
    )
    (outputs_dir / "metrics.json").write_text(
        json.dumps({"total_tool_calls": 2, "skill_activated": True}),
        encoding="utf-8",
    )
    (outputs_dir / "skill_activation.json").write_text(
        json.dumps({"expected": True, "actual": True, "skill_name": "consulta-movimientos"}),
        encoding="utf-8",
    )
    (outputs_dir / "result.json").write_text(json.dumps({"status": "ok"}), encoding="utf-8")

    run = generate_review.build_run(tmp_path, run_dir)

    assert run["prompt"] == "Quiero ver las compras de mi tarjeta."
    assert run["expected_output"] == "La skill debe listar tarjetas y consultar movimientos."
    assert run["response"] == "He recuperado un movimiento."
    assert run["eval_id"] == 7
    assert run["tool_calls"][1]["name"] == "listado_tarjetas"
    assert run["metrics"]["total_tool_calls"] == 2
    assert run["skill_activation"]["actual"] is True
    assert run["timing"]["executor_duration_seconds"] == 3.4
    assert run["outputs"][0]["name"] == "result.json"


def test_build_run_falls_back_to_transcript_parsing_for_legacy_runs(tmp_path: Path):
    """The review builder should recover prompt and tool sequence from legacy transcripts."""

    generate_review = _load_generate_review_module()
    run_dir = tmp_path / "eval_3"
    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(parents=True)

    (outputs_dir / "transcript.md").write_text(
        "# Eval 3\n\n"
        "**Prompt:** Quiero ver los movimientos de la tarjeta acabada en 1234.\n\n"
        "**Expected:** La skill debe identificar la tarjeta y consultar movimientos.\n\n"
        "## Skill Activated\n"
        "YES — `load_skill` was called\n\n"
        "## Tool Calls\n"
        '- `load_skill({"skill_name": "consulta-movimientos"})`\n'
        "- `listado_tarjetas({})`\n"
        '- `consultar_movimientos_tarjeta({"ppp": "001"})`\n\n'
        "## Response\n"
        "He recuperado un movimiento.\n",
        encoding="utf-8",
    )

    run = generate_review.build_run(tmp_path, run_dir)

    assert run["eval_id"] == 3
    assert run["prompt"] == "Quiero ver los movimientos de la tarjeta acabada en 1234."
    assert run["expected_output"] == "La skill debe identificar la tarjeta y consultar movimientos."
    assert run["response"] == "He recuperado un movimiento."
    assert len(run["tool_calls"]) == 3
    assert run["tool_calls"][0]["name"] == "load_skill"
    assert run["tool_calls"][2]["args"] == {"ppp": "001"}


def test_run_eval_writes_eval_metadata_for_the_viewer(
    tmp_path: Path,
    monkeypatch,
):
    """The eval runner should write metadata that the review viewer can render directly."""

    async def fake_run_eval_case(*_args, **_kwargs):
        return RunResult(
            response="Respuesta final",
            skill_activated=True,
            tool_calls=[
                {"name": "load_skill", "args": {"skill_name": "sample-skill"}},
                {"name": "greet_user", "args": {"name": "Alice"}},
            ],
        )

    monkeypatch.setattr(run_eval_script, "run_eval_case", fake_run_eval_case)
    run_eval_script._run_single(
        FIXTURE_SKILL_DIR,
        {
            "id": 9,
            "prompt": "Hola",
            "expected_output": "Saludo",
            "expected_skill_activated": True,
        },
        runtime=object(),
        model="fake-model",
        run_dir=tmp_path,
        project=None,
        location="global",
    )

    metadata = json.loads((tmp_path / "eval_9" / "eval_metadata.json").read_text(encoding="utf-8"))
    activation = json.loads(
        (tmp_path / "eval_9" / "outputs" / "skill_activation.json").read_text(encoding="utf-8")
    )

    assert metadata["prompt"] == "Hola"
    assert metadata["response"] == "Respuesta final"
    assert metadata["tool_calls"][0]["step"] == 1
    assert metadata["tool_calls"][1]["name"] == "greet_user"
    assert activation["skill_name"] == "sample-skill"
