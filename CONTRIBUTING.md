# Contributing

Contributions welcome. This document covers how to add datasets, agents, sub-skills, Python modules, and domain context skills under the v3 architecture.

## Two repos, two responsibilities

- **`~/Projects/datasources/`** owns dataset metadata, schemas, fields, join keys, cadence, release lag, point-in-time safety.
- **`~/Projects/deep-quant-research/`** (this repo) owns hypotheses, signal specs, feature grids, backtests, validation, signal cards, dashboards.

A dataset entry never lives in this repo. A signal never lives in `datasources`. If you find one in the wrong place, that is a bug to fix.

## What can be contributed

**New datasets.** Add an entry to `~/Projects/datasources/entries/<domain>/<dataset-id>.yaml` and regenerate the catalog. This repo will pick it up via the registry client.

**New sub-skill.** Add a folder under `skills/deep-quantitative-research/skills/<skill-name>/` with a `SKILL.md` and a `references/` directory. Register the skill in the top-level `skills/deep-quantitative-research/SKILL.md` sub-skill table.

**New agent.** Add to `skills/deep-quantitative-research/agents/<agent-name>.md`. The canonical set is the 8 listed in the top-level SKILL.md; new agents should orchestrate sub-skills, not duplicate them.

**New Python module.** Add under the appropriate subpackage in `src/deep_quantitative_research/`. Every module ships with a unit test in `tests/`.

**New CLI subcommand.** Wire into `src/deep_quantitative_research/cli.py` (Phase 4), then add a thin wrapper in `scripts/` if a standalone script is useful.

**New template.** Add to `skills/deep-quantitative-research/templates/`. Reference it from the sub-skill that produces the artefact.

**New reference doc.** Add to `skills/deep-quantitative-research/references/` (for prose) or `docs/` (for architecture-level docs).

**Domain context skill.** Specialist knowledge for a research subfield (e.g. `oncology-genomics-context`). Place in its own folder at the repo root alongside `skills/`. The orchestrator detects loaded context skills and passes them to `research-architect`.

## Skill file requirements

Every `SKILL.md` must comply with the Claude Skills spec:

- File named exactly `SKILL.md` (case-sensitive).
- YAML frontmatter with `name` (kebab-case) and `description` (includes trigger phrases).
- No XML angle brackets in frontmatter.
- No `README.md` inside skill folders. (`README.md` at repo root is fine.)

## Python code standards

- Type hints on function signatures.
- `click` CLI; fail fast on missing required args with an actionable message.
- Print progress to stdout, errors to stderr.
- No hardcoded paths; resolve via `config/` or CLI args.
- Compatible with Python 3.10+.
- Pinned deps in `pyproject.toml`; no loose dependency drift.
- Validate every output against the corresponding schema in `src/deep_quantitative_research/schemas/`.

## Testing

Before opening a PR:

```bash
python -m py_compile src/deep_quantitative_research/**/*.py
pytest -q
deep-quant --help
deep-quant query-datasources --healthcheck
```

If your change adds or modifies a sub-skill, run the matching example in `examples/` end-to-end and confirm `expected-output/` still matches.

## Pull request format

Title: `[type]: brief description`

Types: `agent`, `sub-skill`, `module`, `template`, `reference`, `docs`, `fix`, `chore`.

Body:

- What was added or changed.
- Which sub-skill or module it touches.
- Tests performed.
- Any known limitations.
- For new agents: which sub-skills it orchestrates.
- For new datasets: confirm the entry lives in `~/Projects/datasources/`, not here.

## Deprecated names

`deep-research` and `deep-quant-research` are deprecated. Use `deep-quantitative-research` everywhere in new code.
