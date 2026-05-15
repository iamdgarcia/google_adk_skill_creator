# Design: Make google-adk-skill-creator Installable as a Claude Code Plugin

**Date:** 2026-05-15
**Repo:** `iamdgarcia/google_adk_skill_creator`
**Goal:** Allow users to install the `adk-skill-creator` skill from Claude Code via `/plugin install google-adk-skill-creator@iamdgarcia` and from Codex CLI via its equivalent.

---

## Context

The repo already follows the plugin skills layout: `skills/adk-skill-creator/SKILL.md` is at the correct path. No restructuring is needed. What's missing is the plugin manifest layer that Claude Code and Codex CLI read to register the plugin.

The reference implementation is `thedotmack/claude-mem`, a single-plugin repo that ships `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `.codex-plugin/plugin.json` at the repo root. The `marketplace.json` turns the repo itself into a named marketplace so users can install with `plugin-name@marketplace-name`.

---

## Files to Add

### `.claude-plugin/plugin.json`

Claude Code plugin manifest.

```json
{
  "name": "google-adk-skill-creator",
  "version": "0.1.0",
  "description": "Build, test, evaluate, and compose Google ADK skills with dynamic tool injection.",
  "author": {
    "name": "Daniel García Peña",
    "url": "https://github.com/iamdgarcia"
  },
  "repository": "https://github.com/iamdgarcia/google_adk_skill_creator",
  "license": "Apache-2.0",
  "keywords": ["google-adk", "claude", "claude-code", "gemini", "vertex-ai", "skill", "agent"]
}
```

### `.claude-plugin/marketplace.json`

Registers the GitHub repo as a named marketplace so users can reference it as `@iamdgarcia`. The `source: "./"` means the repo root is the plugin directory (where `skills/` lives).

```json
{
  "name": "iamdgarcia",
  "owner": {
    "name": "Daniel García Peña"
  },
  "metadata": {
    "description": "Plugins by Daniel García Peña",
    "homepage": "https://github.com/iamdgarcia/google_adk_skill_creator"
  },
  "plugins": [
    {
      "name": "google-adk-skill-creator",
      "version": "0.1.0",
      "source": "./",
      "description": "Build, test, evaluate, and compose Google ADK skills with dynamic tool injection."
    }
  ]
}
```

### `.codex-plugin/plugin.json`

Codex CLI plugin manifest. Mirrors `.claude-plugin/plugin.json` but uses Codex-specific fields (`skills`, `interface`) that tell Codex where to find skill files and how to present the plugin.

```json
{
  "name": "google-adk-skill-creator",
  "version": "0.1.0",
  "description": "Build, test, evaluate, and compose Google ADK skills with dynamic tool injection.",
  "author": {
    "name": "Daniel García Peña",
    "url": "https://github.com/iamdgarcia"
  },
  "homepage": "https://github.com/iamdgarcia/google_adk_skill_creator#readme",
  "repository": "https://github.com/iamdgarcia/google_adk_skill_creator",
  "license": "Apache-2.0",
  "keywords": ["google-adk", "codex", "claude", "skill", "gemini", "vertex-ai", "agent"],
  "skills": "./skills/",
  "interface": {
    "displayName": "Google ADK Skill Creator",
    "shortDescription": "Build, test, and compose Google ADK skills from Claude Code or Codex.",
    "longDescription": "A skill for building, evaluating, and composing Google ADK skills using the SkillRuntime + adk_additional_tools pattern. Includes scaffolding, eval runners, description optimizer, and multi-skill composition.",
    "developerName": "Daniel García Peña",
    "category": "Development",
    "capabilities": ["Interactive", "Write"],
    "websiteURL": "https://github.com/iamdgarcia/google_adk_skill_creator",
    "defaultPrompt": [
      "Create a new Google ADK skill for me",
      "Run evals on my existing ADK skill",
      "Help me optimize my skill's description for better activation"
    ],
    "brandColor": "#EA4335"
  }
}
```

---

## README Addition

Add a new section between the existing `## Prerequisites` and `## Auth setup` sections:

```markdown
## Install as a Claude Code plugin

Add the repository as a custom plugin source:

```
/plugin add github:iamdgarcia/google_adk_skill_creator
```

Then install the skill:

```
/plugin install google-adk-skill-creator@iamdgarcia
```

The `adk-skill-creator` skill will then be available in your Claude Code sessions automatically.

**Codex CLI:** The plugin also ships a `.codex-plugin/plugin.json` and is compatible with Codex's plugin system.
```

---

## What Does Not Change

- `skills/adk-skill-creator/` — no changes, already in the correct location
- `scripts/`, `tests/`, `requirements.txt` — unaffected
- `SKILL.md` frontmatter — unaffected

---

## Scope

3 new files, 1 README section. No restructuring, no renamed files, no Python changes.
