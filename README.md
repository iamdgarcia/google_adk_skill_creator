# Google ADK Skill Creator

![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)
![Google ADK](https://img.shields.io/badge/google--adk-1.33+-EA4335?logo=google&logoColor=white)
![Vertex AI](https://img.shields.io/badge/vertex--ai-enabled-4285F4?logo=googlecloud&logoColor=white)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)

A library and Claude skill for building, testing, and composing [Google ADK](https://google.github.io/adk-docs/) skills — modular agent capabilities with dynamic tool injection.

## What this is

ADK skills are discrete agent behaviours: a `SKILL.md` description, a `tools.py` runtime, and an `evals/` suite. This repo provides:

- **`scaffold.py`** — generate a new skill from a template
- **`run_eval.py`** — run eval prompts against a skill using a live Gemini model on Vertex AI
- **`run_loop.py`** — iterate on a skill's description to improve activation accuracy
- **`compose.py`** — assemble multiple skills into a single agent
- **`quick_validate.py`** — catch mismatches between `SKILL.md` and `tools.py` without a model call
- **`adk-skill-creator` Claude skill** — drive the whole workflow from a Claude session

→ **[Visual flow diagram](docs/skill-creation-flow.html)** — interactive step-by-step guide to creating a skill

---

## Prerequisites

- Python 3.11+
- `gcloud` CLI authenticated with Application Default Credentials
- A Google Cloud project with the Vertex AI API enabled and billing active

---

## Auth setup

This is the most common source of errors. Read carefully.

**1. Set up Application Default Credentials (ADC):**

```bash
gcloud auth application-default login
```

**2. If `GOOGLE_APPLICATION_CREDENTIALS` is set in your environment, unset it:**

```bash
unset GOOGLE_APPLICATION_CREDENTIALS
```

> The Python `google-auth` library respects `GOOGLE_APPLICATION_CREDENTIALS` and uses the service account it points to — which often lacks Vertex AI access. The `gcloud` CLI ignores this variable and reads ADC directly. This mismatch causes 404s that look like a model access problem but are actually an auth problem.

**3. Verify ADC works for your project:**

```bash
PROJECT_ID="your-project-id"
MODEL_ID="gemini-3.1-flash-lite"

curl -X POST \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  "https://aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/global/publishers/google/models/${MODEL_ID}:streamGenerateContent" \
  -d '{"contents": {"role": "user", "parts": [{"text": "Hello"}]}}'
```

If this returns a response, your auth is correct and the model is accessible.

---

## Install

```bash
pip install -r requirements.txt
```

---

## Creating a skill

```bash
PYTHONPATH=skills/adk-skill-creator python3 skills/adk-skill-creator/scripts/scaffold.py my-skill-name
```

This creates:

```
my-skill-name/
  SKILL.md              # description + metadata
  tools.py              # SkillRuntime class with your tools
  assets/               # optional files the skill references
  references/           # optional docs for the skill author
  evals/
    evals.json          # eval cases
    eval_factory.py     # mock runtime for evals (no real API needed)
```

---

## Skill anatomy

### `SKILL.md`

```markdown
---
name: my-skill
description: "Use this skill when the user asks about X."
metadata:
  adk_additional_tools:
    - tool_one
    - tool_two
---

# My Skill

Instructions for the agent...
```

`adk_additional_tools` declares which methods from `SkillRuntime` are injected when the skill activates. Only declared tools are available to the agent.

### `tools.py`

```python
class SkillRuntime:
    def __init__(self, base_url: str, session=None):
        self.base_url = base_url
        self.session = session or requests.Session()

    def tool_one(self) -> list:
        """Description shown to the agent."""
        ...

    def tool_two(self, param: str) -> dict:
        """Description shown to the agent."""
        ...

    def get_tools(self) -> list:
        return [self.tool_one, self.tool_two]
```

Dependencies go in `__init__` — inject mocks in evals, real clients in production.

### `evals/eval_factory.py`

```python
def build_eval_runtime() -> SkillRuntime:
    return SkillRuntime(base_url="http://mock.local", session=MockSession())
```

The mock session returns fixture data — no real API call needed to run evals.

---

## Running evals

```bash
unset GOOGLE_APPLICATION_CREDENTIALS

PYTHONPATH=skills/adk-skill-creator python3 skills/adk-skill-creator/scripts/run_eval.py <skill-dir> \
  --project your-gcp-project \
  --location global \
  --model gemini-3.1-flash-lite
```

Options:

| Flag | Default | Description |
|---|---|---|
| `--project` | none | GCP project ID. Required for Vertex AI. Omit to use Gemini Developer API with `GOOGLE_API_KEY`. |
| `--location` | `us-central1` | Vertex AI region. Use `global` to avoid region-specific model availability issues. |
| `--model` | `gemini-2.0-flash` | Model ID. See your project's Vertex AI Model Garden for available models. |
| `--evals` | all | Space-separated eval IDs to run, e.g. `--evals 1 3`. |
| `--run-dir` | `runs/<timestamp>` | Where to write results. |

Results are written to `runs/<timestamp>/eval_N/outputs/`:

```
transcript.md       # prompt, tool calls, response
metrics.json        # tool call counts, skill activation flag
skill_activation.json  # expected vs actual activation
../timing.json      # wall-clock duration
```

---

## Validating a skill (no model needed)

```bash
PYTHONPATH=skills/adk-skill-creator python3 -c "
from pathlib import Path
from scripts.quick_validate import validate_skill_dir
errors = validate_skill_dir(Path('my-skill-name'))
print('OK' if not errors else '\n'.join(errors))
"
```

Catches mismatches between `adk_additional_tools` in `SKILL.md` and methods in `SkillRuntime` before spending a model call.

---

## Composing skills

Define an `agent.yaml`:

```yaml
name: my-agent
model: gemini-3.1-flash-lite
skills:
  - ../skill-one
  - ../skill-two
```

Then compose:

```python
from scripts.compose import compose_agent
from pathlib import Path

runtimes = {
    "skill-one": SkillOneRuntime(...),
    "skill-two": SkillTwoRuntime(...),
}
agent = compose_agent(Path("agent.yaml"), runtimes)
```

---

## Known issues and gotchas

**`GOOGLE_APPLICATION_CREDENTIALS` overrides ADC silently.** Always `unset` it before running evals if you use a service account for other work.

**Model availability varies by region.** Not all Gemini models are available in all Vertex AI regions. Use `--location global` unless you have a specific reason not to.

**Preview model names are opaque.** Check the Vertex AI Model Garden in the Cloud Console for the exact model ID available in your project.

**`runs/` accumulates quickly.** It is gitignored. Clean it periodically or use `--run-dir` to direct output elsewhere.

---

## Running tests

```bash
pytest
```

Tests use mocked ADK components — no Vertex AI or API key required.
