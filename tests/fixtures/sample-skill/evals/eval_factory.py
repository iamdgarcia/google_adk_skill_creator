import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools import SkillRuntime


def build_eval_runtime() -> SkillRuntime:
    return SkillRuntime(greeting="Hello")
