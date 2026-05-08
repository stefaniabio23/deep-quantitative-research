"""Validate SKILL.md frontmatter in skills/ directory."""
import sys
import re
from pathlib import Path

import yaml


def validate_skill(skill_path: Path) -> list[str]:
    errors = []
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        return [f"SKILL.md not found in {skill_path}"]

    content = skill_md.read_text()

    # Extract frontmatter
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return [f"{skill_path}: missing or malformed YAML frontmatter (must start with ---)"]

    try:
        fm = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        return [f"{skill_path}: invalid YAML in frontmatter: {e}"]

    if not fm:
        return [f"{skill_path}: empty frontmatter"]

    # name checks
    name = fm.get("name", "")
    if not name:
        errors.append(f"{skill_path}: 'name' field is required")
    elif not re.match(r"^[a-z0-9-]+$", name):
        errors.append(f"{skill_path}: 'name' must be kebab-case (lowercase, hyphens only). Got: '{name}'")
    elif "claude" in name.lower() or "anthropic" in name.lower():
        errors.append(f"{skill_path}: 'name' cannot contain 'claude' or 'anthropic' (reserved)")

    # description checks
    desc = fm.get("description", "")
    if not desc:
        errors.append(f"{skill_path}: 'description' field is required")
    elif len(desc) > 1024:
        errors.append(f"{skill_path}: 'description' exceeds 1024 characters ({len(desc)} chars)")
    elif "<" in desc or ">" in desc:
        errors.append(f"{skill_path}: 'description' contains forbidden XML characters (< >)")

    # Check description has trigger phrases
    trigger_words = ["use when", "triggers on", "trigger", "use for", "when user"]
    if desc and not any(t in desc.lower() for t in trigger_words):
        errors.append(f"{skill_path}: 'description' should include when to use the skill (trigger conditions)")

    # No README.md inside skill folder
    readme = skill_path / "README.md"
    if readme.exists():
        errors.append(f"{skill_path}: README.md found inside skill folder (not allowed; use repo-level README)")

    return errors


def main():
    skills_dir = Path("skills")
    if not skills_dir.exists():
        print("No skills/ directory found")
        sys.exit(0)

    all_errors = []
    for skill_path in skills_dir.iterdir():
        if skill_path.is_dir():
            errors = validate_skill(skill_path)
            all_errors.extend(errors)

    if all_errors:
        print("SKILL VALIDATION ERRORS:")
        for err in all_errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        skill_count = sum(1 for p in skills_dir.iterdir() if p.is_dir())
        print(f"All {skill_count} skill(s) passed validation.")
        sys.exit(0)


if __name__ == "__main__":
    main()
