# Contributing

Contributions are welcome. This document covers how to add new agents, scripts, and domain context skills.

---

## What can be contributed

**New agents**, add to `skills/deep-quant-research/agents/`. Follow the template: Role, Phase, Input/Output, Procedure. Register the agent in the relevant mode block of `skills/deep-quant-research/SKILL.md`.

**New scripts**, add to `skills/deep-quant-research/scripts/`. Must accept `--output` as YAML path, print progress to stdout, handle errors gracefully.

**New data sources**, extend `skills/deep-quant-research/scripts/fetch_data.py` and document in `skills/deep-quant-research/references/data-sources.md`.

**Domain context skills**, skills that add specialist knowledge to a specific research area. Place in their own folder at the repo root alongside `skills/`. See `Domain Context Skills` below.

**Shared protocols**, additions to `skills/deep-quant-research/shared/` for new statistical methods, interpretation rubrics, or style conventions.

**New critique checklist**, add to `skills/deep-quant-research/shared/critique-checklists/` and register the trigger point in `skills/deep-quant-research/shared/critique-cluster.md`.

---

## Skill file requirements

All files in `skills/` must comply with the Claude Skills specification:
- `SKILL.md` named exactly (case-sensitive)
- YAML frontmatter with `name` (kebab-case) and `description` (includes trigger phrases)
- No XML angle brackets in frontmatter
- No `README.md` inside skill folders

---

## Domain Context Skills

A domain context skill adds specialist knowledge for a specific research subfield. Examples:
- `oncology-genomics-context` — pathway biology, biomarker interpretation, clinical trial design conventions
- `eu-healthcare-equity-context` — European pharma pricing, EMA vs FDA pathway differences, reimbursement
- `macro-quant-context` — central bank reaction functions, regime identification, macro factor construction

Structure:
```
[domain-name]-context/
├── SKILL.md          # Description triggers on the domain name
└── references/
    └── [domain-specific knowledge files]
```

The `deep-quant-research` orchestrator detects loaded context skills and passes them to `question-sharpener` and `research-architect`.

---

## Agent template

```markdown
# [Agent Name] Agent

**Role:** One sentence.

**Phase:** N — Phase name
**Input:** What it reads
**Output:** What it produces (file path + schema reference)

---

## Procedure

### Step 1: [Action]
[Instructions]

### Step 2: [Action]
[Instructions]

---

## [Domain-specific sections if needed]
```

---

## Code standards

Python scripts:
- Type hints on function signatures
- `argparse` CLI with `--output` as YAML path
- Print progress to stdout (not stderr)
- Graceful error messages with actionable fix instructions
- No hardcoded paths; all paths via arguments
- Compatible with Python 3.10+

---

## Testing

Before submitting:
1. Verify `skills/deep-quant-research/SKILL.md` frontmatter passes YAML lint
2. Run `python skills/deep-quant-research/scripts/[script].py --help` to confirm CLI works
3. Run a minimal end-to-end test with the trigger phrase documented in the PR

---

## Pull request format

Title: `[type]: brief description`
Types: `agent`, `script`, `protocol`, `context-skill`, `fix`, `docs`

Body:
- What was added/changed
- Test performed
- Any known limitations
