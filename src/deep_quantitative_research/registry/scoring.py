"""Score a dataset against a hypothesis. Spec section 8.

The scoring is heuristic and explicit; weights are configurable so domain teams
can re-tune without forking the code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .client import RegistryClient, get_client
from .index import get_dataset, get_source
from .types import Dataset, Source

DEFAULT_WEIGHTS: dict[str, float] = {
    "economic_proximity": 1.5,
    "coverage": 1.0,
    "cadence_fit": 1.2,
    "release_lag_clarity": 1.0,
    "point_in_time_safety": 1.3,
    "survivorship_bias_risk": 1.1,
    "api_scriptability": 0.8,
    "cost_access_practicality": 0.6,
}


def _load_weights(path: Path | str | None) -> dict[str, float]:
    if not path:
        return dict(DEFAULT_WEIGHTS)
    p = Path(path)
    if not p.exists():
        return dict(DEFAULT_WEIGHTS)
    cfg = yaml.safe_load(p.read_text()) or {}
    weights = cfg.get("weights") or {}
    out = dict(DEFAULT_WEIGHTS)
    out.update({k: float(v) for k, v in weights.items()})
    return out


def _economic_proximity(dataset: Dataset, source: Source, hypothesis: dict[str, Any]) -> int:
    """How close in the causal chain is this dataset to the target variable?

    Heuristic: tokens from the hypothesis statement / target_variable that
    appear in the source description or agent_use_cases get full marks.
    """
    text = " ".join(
        [
            hypothesis.get("statement") or "",
            hypothesis.get("target_variable") or "",
            hypothesis.get("mechanism") or "",
        ]
    ).lower()
    tokens = [t for t in text.split() if len(t) > 3]
    if not tokens:
        return 5
    hay = " ".join(
        [
            source.description.lower(),
            source.name.lower(),
            " ".join(source.raw.get("agent_use_cases") or []).lower(),
        ]
    )
    hits = sum(1 for t in tokens if t in hay)
    return min(10, 2 + int(round(hits * 8 / max(len(tokens), 1))))


def _coverage(source: Source) -> int:
    geo = source.geography
    if not geo:
        return 4
    if "global" in geo:
        return 9
    if len(geo) > 1:
        return 7
    return 6


def _cadence_fit(dataset: Dataset, hypothesis: dict[str, Any]) -> int:
    expected = (hypothesis.get("target_cadence") or "").lower()
    grains = [g.lower() for g in dataset.time_grain]
    if not expected:
        return 7 if grains else 4
    if expected in grains:
        return 10
    rank = {"daily": 0, "weekly": 1, "monthly": 2, "quarterly": 3, "annual": 4}
    if expected not in rank or not grains:
        return 5
    finest = min(rank.get(g, 99) for g in grains)
    if finest < rank[expected]:
        # Source is finer than target; can roll up cleanly.
        return 8
    return 3  # Source is coarser; can't downsample without faking data.


def _release_lag_clarity(source: Source) -> int:
    return 8 if source.lag else 4


def _point_in_time_safety(dataset: Dataset, source: Source) -> int:
    description = " ".join([source.description.lower(), source.lag or ""])
    if "restated" in description or "revisions" in description:
        return 3
    if source.entry_kind in {"registry", "corpus"}:
        return 8
    if source.entry_kind == "time-series":
        return 6
    return 5


def _survivorship_bias_risk(dataset: Dataset, source: Source) -> int:
    # Lower score = higher risk. Equity / finance datasets are the usual offenders.
    if source.domain == "finance-markets" and dataset.entry_kind == "time-series":
        return 4
    return 8


def _api_scriptability(source: Source) -> int:
    types = source.raw.get("type") or []
    if "rest-api" in types or "bulk-download" in types:
        return 9
    if "scrape" in types:
        return 4
    return 6


def _cost_access_practicality(source: Source) -> int:
    cost = (source.cost or "").lower()
    auth = (source.auth_required or "").lower()
    base = 10 if cost in {"free", ""} else 5 if "freemium" in cost else 3
    if "account" in auth or "api-key" in auth:
        base -= 1
    return max(1, base)


def score_dataset_fit(
    hypothesis: dict[str, Any],
    dataset_id: str,
    *,
    client: RegistryClient | None = None,
    weights_path: Path | str | None = "config/scoring_weights.yaml",
) -> dict[str, Any]:
    """Spec section 8: returns the dataset_fit_score block plus a total.

    `hypothesis` is the Hypothesis YAML dict (statement, target_variable,
    target_cadence, mechanism, ...). Missing keys reduce specific axis confidence
    but never raise.
    """
    client = client or get_client()
    dataset = get_dataset(dataset_id, client=client)
    source = get_source(dataset.source_id, client=client)
    weights = _load_weights(weights_path)

    axes = {
        "economic_proximity": _economic_proximity(dataset, source, hypothesis),
        "coverage": _coverage(source),
        "cadence_fit": _cadence_fit(dataset, hypothesis),
        "release_lag_clarity": _release_lag_clarity(source),
        "point_in_time_safety": _point_in_time_safety(dataset, source),
        "survivorship_bias_risk": _survivorship_bias_risk(dataset, source),
        "api_scriptability": _api_scriptability(source),
        "cost_access_practicality": _cost_access_practicality(source),
    }
    weighted_sum = sum(axes[k] * weights.get(k, 1.0) for k in axes)
    weight_total = sum(weights.get(k, 1.0) for k in axes) or 1.0
    total = round(weighted_sum / weight_total, 2)

    return {
        "dataset_id": dataset_id,
        **axes,
        "total_score": total,
    }
