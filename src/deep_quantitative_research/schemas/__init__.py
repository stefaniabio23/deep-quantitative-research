"""JSON Schemas for every artefact the pipeline emits, plus a small validator.

Schemas live as ``.schema.yaml`` files next to this module. Load and validate
through ``validate(name, payload)``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator

_SCHEMA_DIR = Path(__file__).parent
_SCHEMA_FILES = {
    "hypothesis": "hypothesis.schema.yaml",
    "signal": "signal.schema.yaml",
    "dataset-contract": "dataset-contract.schema.yaml",
    "feature-grid": "feature-grid.schema.yaml",
    "backtest-result": "backtest-result.schema.yaml",
    "validation-report": "validation-report.schema.yaml",
}


class SchemaError(RuntimeError):
    """Raised when a payload fails its schema."""


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict[str, Any]:
    """Load a schema by short name (e.g. ``"signal"``)."""
    if name not in _SCHEMA_FILES:
        raise KeyError(f"Unknown schema: {name!r}. Known: {sorted(_SCHEMA_FILES)}")
    path = _SCHEMA_DIR / _SCHEMA_FILES[name]
    if not path.exists():
        raise FileNotFoundError(f"Schema file missing: {path}")
    return yaml.safe_load(path.read_text())


def validate(name: str, payload: dict[str, Any]) -> None:
    """Validate ``payload`` against the schema ``name``.

    Raises ``SchemaError`` listing every violation when invalid.
    """
    schema = load_schema(name)
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))
    if errors:
        lines = [
            f"  - {'.'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in errors
        ]
        raise SchemaError(
            f"{len(errors)} validation error(s) for schema {name!r}:\n" + "\n".join(lines)
        )


def schema_names() -> list[str]:
    return sorted(_SCHEMA_FILES)


__all__ = ["SchemaError", "load_schema", "schema_names", "validate"]
