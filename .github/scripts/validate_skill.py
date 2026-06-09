"""Validate SKILL.md frontmatter across every skills/ folder.

Checks per skill:
- ``SKILL.md`` exists.
- YAML frontmatter parses.
- ``name`` is kebab-case and not reserved.
- ``description`` exists, fits the 1024-char limit, and has no XML angle
  brackets in it.
- No ``README.md`` lives next to the SKILL.md.

Trigger-phrase rule is intentionally relaxed: any description that hints at
when to invoke (mentions "when", "invoke", "use", or "after") is accepted.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

_TRIGGER_HINTS = ("when", "invoke", "use ", "after ", "triggers")


def validate_skill(skill_path: Path) -> tuple[list[str], list[str]]:
    """Return ``(errors, warnings)`` for a single skill folder."""
    errors: list[str] = []
    warnings: list[str] = []
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        return [f"{skill_path}: SKILL.md not found"], []

    content = skill_md.read_text()

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return (
            [f"{skill_path}: missing or malformed YAML frontmatter (must start with ---)"],
            [],
        )

    try:
        fm = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return [f"{skill_path}: invalid YAML in frontmatter: {exc}"], []

    if not fm:
        return [f"{skill_path}: empty frontmatter"], []

    name = fm.get("name", "")
    if not name:
        errors.append(f"{skill_path}: 'name' field is required")
    elif not re.match(r"^[a-z0-9-]+$", name):
        errors.append(
            f"{skill_path}: 'name' must be kebab-case (lowercase, hyphens only). Got: {name!r}"
        )
    elif "claude" in name.lower() or "anthropic" in name.lower():
        errors.append(f"{skill_path}: 'name' cannot contain 'claude' or 'anthropic' (reserved)")

    desc = fm.get("description", "")
    if not desc:
        errors.append(f"{skill_path}: 'description' field is required")
    elif len(desc) > 1024:
        errors.append(
            f"{skill_path}: 'description' exceeds 1024 characters ({len(desc)} chars)"
        )
    elif "<" in desc or ">" in desc:
        errors.append(f"{skill_path}: 'description' contains forbidden XML characters (< >)")
    else:
        lowered = desc.lower()
        if not any(hint in lowered for hint in _TRIGGER_HINTS):
            warnings.append(
                f"{skill_path}: 'description' lacks an invocation hint "
                f"({list(_TRIGGER_HINTS)}); consider adding one so callers know "
                "when to invoke."
            )

    if (skill_path / "README.md").exists():
        errors.append(
            f"{skill_path}: README.md found inside skill folder (not allowed; "
            "use repo-level README)"
        )

    return errors, warnings


def main() -> int:
    repo_root = Path.cwd()
    skill_md_files: list[Path] = sorted(repo_root.rglob("skills/**/SKILL.md"))
    if not skill_md_files:
        print("No SKILL.md files found under any skills/ directory.")
        return 0

    all_errors: list[str] = []
    all_warnings: list[str] = []
    seen_dirs: set[Path] = set()
    for skill_md in skill_md_files:
        skill_dir = skill_md.parent
        if skill_dir in seen_dirs:
            continue
        seen_dirs.add(skill_dir)
        errors, warnings = validate_skill(skill_dir)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    if all_warnings:
        print("WARNINGS:")
        for warn in all_warnings:
            print(f"  - {warn}")
        print()

    if all_errors:
        print("SKILL VALIDATION ERRORS:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print(f"All {len(seen_dirs)} skill(s) passed validation ({len(all_warnings)} warnings).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
