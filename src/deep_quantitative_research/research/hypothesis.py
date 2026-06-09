"""Hypothesis YAML loader, validator, and typed view."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ..schemas import validate


@dataclass
class Hypothesis:
    hypothesis_id: str
    statement: str
    target_variable: str
    target_cadence: str
    expected_direction: str
    mechanism: str
    candidate_predictors: list[str]
    falsification: list[str]
    domain: str = "mixed"
    expected_lag_periods: list[int] = field(default_factory=list)
    upstream_variables: list[str] = field(default_factory=list)
    downstream_effects: list[str] = field(default_factory=list)
    knock_on_effects: list[str] = field(default_factory=list)
    status: str = "candidate"
    created_at: str | None = None
    notes: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


def load_hypothesis(path: Path | str) -> Hypothesis:
    """Load + schema-validate a hypothesis YAML."""
    path = Path(path)
    raw = yaml.safe_load(path.read_text()) or {}
    validate("hypothesis", raw)
    return Hypothesis(
        hypothesis_id=raw["hypothesis_id"],
        statement=raw["statement"],
        target_variable=raw["target_variable"],
        target_cadence=raw["target_cadence"],
        expected_direction=raw["expected_direction"],
        mechanism=raw["mechanism"],
        candidate_predictors=list(raw["candidate_predictors"]),
        falsification=list(raw["falsification"]),
        domain=raw.get("domain", "mixed"),
        expected_lag_periods=list(raw.get("expected_lag_periods") or []),
        upstream_variables=list(raw.get("upstream_variables") or []),
        downstream_effects=list(raw.get("downstream_effects") or []),
        knock_on_effects=list(raw.get("knock_on_effects") or []),
        status=raw.get("status", "candidate"),
        created_at=raw.get("created_at"),
        notes=raw.get("notes", ""),
        raw=raw,
    )
