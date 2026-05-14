import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "adk-skill-creator"))

FIXTURE_SKILL_DIR = Path(__file__).parent / "fixtures" / "sample-skill"
