# ADK Skill Format

An ADK skill is a directory with this structure:

```
my-skill/
  SKILL.md          ← required: frontmatter + instructions
  tools.py          ← required: SkillRuntime class
  evals/
    evals.json      ← required: test cases
    eval_factory.py ← required: mock runtime for evals
  references/       ← optional: domain docs, API schemas
  assets/           ← optional: templates, examples
```

## SKILL.md frontmatter

```yaml
---
name: my-skill                          # kebab-case, max 64 chars
description: "When to use this skill"   # max 1024 chars — controls activation
metadata:
  adk_additional_tools:
    - tool_one                          # must match SkillRuntime method names exactly
    - tool_two
---
```

## How ADK activates skills

1. Agent starts with `SkillToolset` loaded — exposes `list_skills`, `load_skill`, `load_skill_resource`
2. LLM reads `list_skills` — sees each skill's `name` and `description`
3. LLM decides which skill to use based on `description` and calls `load_skill(skill_name=...)`
4. ADK sets `_adk_activated_skill_{agent_name}` in session state
5. On the next `get_tools()` call, `SkillToolset._resolve_additional_tools_from_state` reads the activated skill's `adk_additional_tools` and injects only those tools
6. Subsequent tool calls in the same turn use the skill's domain tools

**Key:** `adk_additional_tools` values must be the exact Python function names returned by `SkillRuntime.get_tools()`. `quick_validate.py` enforces this.
