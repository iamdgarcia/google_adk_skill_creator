#!/usr/bin/env python3
"""Validate and package an ADK skill directory as a distributable zip."""

import argparse
import sys
import zipfile
from pathlib import Path

from scripts.quick_validate import validate_skill_dir


def package_skill(skill_dir: Path, output_path: Path | None = None) -> Path:
    """Validate and zip an ADK skill directory. Exits with code 1 on validation failure."""
    errors = validate_skill_dir(skill_dir)
    if errors:
        print("Validation failed:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    if output_path is None:
        output_path = skill_dir.parent / f"{skill_dir.name}.skill"

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(skill_dir.rglob("*")):
            if file.is_file() and "__pycache__" not in str(file) and ".pyc" not in file.suffix:
                zf.write(file, file.relative_to(skill_dir.parent))

    print(f"Packaged: {output_path} ({output_path.stat().st_size} bytes)")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Validate and package an ADK skill")
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    package_skill(args.skill_dir, args.output)


if __name__ == "__main__":
    main()
