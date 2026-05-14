# CI/CD Guide for ADK Skills

## Pipeline overview

```
PR opened with skill changes
  → quick_validate.py     (fail fast: SKILL.md + tools.py consistency)
  → run_eval.py           (run evals with mock runtime via eval_factory.py)
  → grader agent          (grade each eval_N/ directory)
  → gate: pass_rate >= pass_threshold AND skill_activated correct for all expected cases
  → on pass: package_skill.py → publish to skill registry
  → agent manifest updated to reference new skill version
```

## GitHub Actions example

```yaml
name: Skill CI
on: [pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    env:
      SKILL_DIR: skills/account-movements
      GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install -r requirements.txt
      - name: Validate
        run: |
          PYTHONPATH=skills/adk-skill-creator \
          python skills/adk-skill-creator/scripts/quick_validate.py $SKILL_DIR
      - name: Run evals
        run: |
          PYTHONPATH=skills/adk-skill-creator \
          python skills/adk-skill-creator/scripts/run_eval.py $SKILL_DIR
```

## Skill registry

Package and publish on merge to main:

```bash
PYTHONPATH=skills/adk-skill-creator \
python skills/adk-skill-creator/scripts/package_skill.py skills/my-skill

gsutil cp skills/my-skill.skill \
  gs://my-skill-registry/my-skill/v$(git rev-parse --short HEAD).skill
```

ADK agents can load from GCS via `load_skill_from_gcs_dir` (requires `google-cloud-storage`).

## Pass threshold

Set per skill in `evals/evals.json` using the `pass_threshold` field (default 0.80 if omitted).
The CI gate reads this field and fails if `summary.pass_rate < pass_threshold`.
