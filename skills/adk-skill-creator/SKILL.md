---
name: adk-skill-creator
description: "Create, test, debug, and compose Google ADK skills with per-skill dynamic tool injection. Use when the user wants to build a new ADK skill from scratch, run evals on an existing skill, improve a skill's description for better activation accuracy, or assemble multiple skills into a single agent."
---

# ADK Skill Creator

A skill for building, evaluating, and composing Google ADK skills using the `SkillRuntime` + `adk_additional_tools` pattern.

## When to use

- User wants to create a new ADK skill
- User wants to run or interpret evals for an existing ADK skill
- User's skill is not activating reliably — description needs optimization
- User wants to assemble multiple skills into a single agent and test cross-skill flows
- User wants to package and publish a skill

## Workflow

### 1. Create a new skill

```bash
PYTHONPATH=skills/adk-skill-creator \
python skills/adk-skill-creator/scripts/scaffold.py <name> <output_dir>
```

Then:
1. Edit `SKILL.md` — write a precise `description` (this controls when the agent uses the skill) and the instructions body
2. Edit `tools.py` — implement `SkillRuntime.__init__` with real dependencies, add tool methods, update `get_tools()`
3. Update `adk_additional_tools` in SKILL.md frontmatter to match the method names exactly

See `references/adk-skill-format.md` and `references/adk-tools-pattern.md`.

### 2. Validate

```bash
PYTHONPATH=skills/adk-skill-creator \
python skills/adk-skill-creator/scripts/quick_validate.py <skill_dir>
```

Fix any reported mismatches before running evals.

### 3. Write evals

Edit `evals/evals.json` with realistic user prompts. Each eval needs:
- `prompt`: a realistic user message
- `expected_skill_activated: true` for prompts that should trigger this skill
- `expectations`: list of verifiable assertions about the response

Edit `evals/eval_factory.py` to return a mock `SkillRuntime` with fixture data.

### 4. Run evals

```bash
PYTHONPATH=skills/adk-skill-creator \
python skills/adk-skill-creator/scripts/run_eval.py <skill_dir> --model gemini-2.0-flash
```

Results land in `runs/<timestamp>/eval_N/`. Run the grader agent (`agents/grader.md`) on each `eval_N/` directory to grade the assertions.

### 5. Iterate

After grading:
- `skill_activated: false` on cases that should trigger → description needs work → go to step 6
- Tool calls are wrong → improve the instructions body in SKILL.md
- Expectations fail → refine instructions or fix tool implementations

Use `agents/comparator.md` to compare two versions of a skill head-to-head.

### 6. Optimize description (when skill is not activating)

Create a trigger evals file (JSON array):

```json
[
  {"query": "show my recent transactions", "should_trigger": true},
  {"query": "what is the weather today", "should_trigger": false},
  {"query": "what did I spend last week", "should_trigger": true}
]
```

Test a candidate description:

```bash
PYTHONPATH=skills/adk-skill-creator \
python skills/adk-skill-creator/scripts/run_loop.py <skill_dir> trigger_evals.json \
  --description "Your candidate description here"
```

The script prints accuracy and per-query results. Propose improved descriptions based on failing cases and repeat until accuracy is satisfactory.

### 7. Compose multiple skills into one agent

Create `agent.yaml` at the project root (see `references/schemas.md`):

```yaml
name: banking-assistant
model: gemini-2.0-flash
skills:
  - skills/account-movements
  - skills/transfer
runtime_factory: runtime_factory.py
```

Create `runtime_factory.py` with `build_runtimes() -> dict[str, object]` (see `references/adk-tools-pattern.md`).

Test composition:

```bash
PYTHONPATH=skills/adk-skill-creator python -c "
from pathlib import Path
from scripts.compose import compose_agent
from runtime_factory import build_runtimes
agent = compose_agent(Path('agent.yaml'), build_runtimes())
print('Agent composed successfully:', agent.name)
"
```

Write `multi_skill_evals.json` and run evals for cross-skill scenarios (see `references/schemas.md`).

### 8. Package for distribution

```bash
PYTHONPATH=skills/adk-skill-creator \
python skills/adk-skill-creator/scripts/package_skill.py <skill_dir>
```

Validates and produces `<skill_dir>.skill` zip. See `references/cicd-guide.md` for publishing.

## Reference docs

- `references/adk-skill-format.md` — skill directory structure, SKILL.md format, how ADK activates skills
- `references/adk-tools-pattern.md` — SkillRuntime class pattern, runtime_factory.py, eval_factory.py
- `references/schemas.md` — all JSON/YAML schemas
- `references/cicd-guide.md` — CI/CD pipeline and skill registry

## Agents

- `agents/grader.md` — grades eval results (includes deterministic skill_activated check)
- `agents/analyzer.md` — post-hoc analysis of comparator results
- `agents/comparator.md` — blind A/B comparison of two skill versions
