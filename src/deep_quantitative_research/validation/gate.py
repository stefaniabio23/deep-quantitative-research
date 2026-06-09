"""Assemble a validation report from individual checks + the feature search log."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .data_quality import Check

_TIER_RANK = {"low": 1, "medium": 2, "high": 3}


@dataclass
class ValidationReport:
    signal_id: str
    checked_at: str
    checks: list[Check]
    confidence_cap: str
    binding_constraint: str | None
    relationship_type: str
    recommended_next_iterations: list[str] = field(default_factory=list)
    registry_commit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "registry_commit": self.registry_commit,
            "checked_at": self.checked_at,
            "checks": [c.to_dict() for c in self.checks],
            "confidence_cap": self.confidence_cap,
            "binding_constraint": self.binding_constraint,
            "relationship_type": self.relationship_type,
            "recommended_next_iterations": list(self.recommended_next_iterations),
        }


def _cap_for_check(verdict: str) -> str:
    return {"pass": "high", "warn": "medium", "fail": "low"}[verdict]


def assemble(
    *,
    signal_id: str,
    checks: list[Check],
    feature_search_cap: str,
    survives_oos: bool,
    walk_forward: bool,
    relationship_type: str = "proxy",
    registry_commit: str | None = None,
    recommended: list[str] | None = None,
) -> ValidationReport:
    """Combine per-check verdicts + the feature search cap + OOS verdict.

    Confidence cap is the minimum of every constraint. Binding constraint is
    the name of the check that produced the minimum.
    """
    caps: list[tuple[str, str]] = [(c.name, _cap_for_check(c.verdict)) for c in checks]
    caps.append(("feature_search", feature_search_cap))
    caps.append(("out_of_sample", "medium" if survives_oos else "low"))
    if not walk_forward:
        caps.append(("walk_forward", "medium"))

    cap_name, cap_value = min(caps, key=lambda pair: _TIER_RANK[pair[1]])

    return ValidationReport(
        signal_id=signal_id,
        checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        checks=checks,
        confidence_cap=cap_value,
        binding_constraint=cap_name if _TIER_RANK[cap_value] < _TIER_RANK["high"] else None,
        relationship_type=relationship_type,
        recommended_next_iterations=list(recommended or []),
        registry_commit=registry_commit,
    )
