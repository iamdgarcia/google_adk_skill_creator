---
title: Skill Creation Flow Diagram
date: 2026-05-15
type: design
---

# Skill Creation Flow Diagram

## Goal

A standalone `docs/skill-creation-flow.html` file that visually documents the logical flow for creating a new ADK skill. Designed to be opened in a browser by developers actively building a skill — not just a static overview.

## Output

Single file: `docs/skill-creation-flow.html`
- No external dependencies (no CDN, no remote fonts)
- Pure HTML + CSS + vanilla JS

## Structure & Layout

- Header: project name + tagline
- Vertical pipeline of 8 numbered step cards connected by a thin vertical line
- "Feedback loop" section between steps 7–8 with three labeled branch paths pointing back to earlier steps
- Steps marked as conditional/optional with a muted badge: "Optimize Description" (step 9) and "Package" (step 10)

## Step Cards

Each collapsed card shows:
- Colored numbered badge
- Bold title
- One-sentence summary

Clicking expands to reveal:
- Shell command in a styled code block + copy button (where applicable)
- "What to edit / check" — 1–2 bullets
- "What you get" — the artifact or output produced

Steps without a shell command (edit SKILL.md, edit tools.py) show the file path and key fields to fill.

## Steps Content

| # | Title | Command | Output |
|---|-------|---------|--------|
| 1 | Scaffold | `scaffold.py <name> <output_dir>` | SKILL.md, tools.py, evals/ |
| 2 | Edit SKILL.md | — | description + instructions body |
| 3 | Edit tools.py | — | SkillRuntime with tool methods |
| 4 | Validate | `quick_validate.py <skill_dir>` | list of mismatches or "OK" |
| 5 | Write evals | — | evals.json + eval_factory.py |
| 6 | Run evals | `run_eval.py <skill_dir> --model ...` | runs/<timestamp>/eval_N/ |
| 7 | Grade | grader agent on eval_N/ | pass/fail per assertion |
| 8 | Iterate | — | fixes to SKILL.md / tools.py |
| 9 | Optimize description | `run_loop.py <skill_dir> triggers.json` | accuracy score + failing cases |
| 10 | Package | `package_skill.py <skill_dir>` | <skill_dir>.skill zip |

## Feedback Loop (between steps 7–8)

Three branch paths shown as labeled arrows curving left back to earlier steps:
- `skill_activated: false` → back to step 9 (Optimize description) / step 2
- `tool calls wrong` → back to step 3 (Edit tools.py)
- `expectations fail` → back to step 2 (Edit SKILL.md) or step 3

## Interactivity

- Click to expand/collapse cards (accordion; multiple open simultaneously)
- "Expand all / Collapse all" toggle at top-right
- Copy-to-clipboard on each code block (button appears on hover)
- Feedback loop branch arrows have hover tooltips with the branch condition

## Visual Style

- Light background, clean typography (system font stack)
- Google blue (#1a73e8) for active state left border and badge accent
- Muted gray pipeline line
- Optional/conditional steps use a yellow/amber badge instead of blue
- Code blocks: dark background, monospace, syntax-free (no highlighting library needed)
