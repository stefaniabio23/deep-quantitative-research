"""Build experiment-specific dataset contracts from registry metadata.

Spec section 12. Every signal materialises a contract before backtesting.
"""

from __future__ import annotations

from typing import Any, Literal

from .client import RegistryClient, get_client
from .index import get_dataset, get_fields, get_source
from .types import Dataset, Source

Role = Literal["target", "predictor", "context", "benchmark"]


def _native_cadence(dataset: Dataset) -> str:
    if not dataset.time_grain:
        return "irregular"
    # Pick the finest-grain cadence the dataset advertises.
    rank = {"daily": 0, "weekly": 1, "monthly": 2, "quarterly": 3, "annual": 4, "irregular": 5}
    return min(dataset.time_grain, key=lambda g: rank.get(g, 99))


def _variable_type_hint(source: Source) -> str:
    """Guess variable_type from source metadata. Default to 'flow' when unknown;
    the contract caller MUST override if the guess is wrong.
    """
    kind = (source.entry_kind or "").lower()
    domain = (source.domain or "").lower()
    if kind == "time-series" and "finance" in domain:
        return "price"
    if kind == "registry":
        return "event"
    if "consumer-signal" in domain or "sentiment" in source.description.lower():
        return "sentiment"
    return "flow"


def _default_aggregation(variable_type: str) -> str:
    return {
        "flow": "sum",
        "stock": "last",
        "rate": "mean",
        "price": "last",
        "count": "sum",
        "sentiment": "mean",
        "event": "sum",
    }.get(variable_type, "mean")


def build_dataset_contract(
    dataset_id: str,
    role: Role = "predictor",
    *,
    target_cadence: str | None = None,
    client: RegistryClient | None = None,
) -> dict[str, Any]:
    """Materialise a dataset_contract block per spec section 12.

    The contract is intentionally a plain dict so it can be merged into a
    SignalSpec or serialised straight to YAML without a type-system tax.
    """
    client = client or get_client()
    dataset = get_dataset(dataset_id, client=client)
    source = get_source(dataset.source_id, client=client)
    fields = get_fields(dataset_id, client=client)

    native_cadence = _native_cadence(dataset)
    if target_cadence is None:
        target_cadence = native_cadence if native_cadence in {"monthly", "quarterly"} else "monthly"

    variable_type = _variable_type_hint(source)

    time_field = next((f.name for f in fields if f.role == "time_index"), dataset.time_index)
    value_fields = [f.name for f in fields if f.role == "measure"]
    value_field = value_fields[0] if value_fields else None
    entity_fields = [f.name for f in fields if f.role == "dimension"]

    field_join_keys = [f.join_key for f in fields if f.join_key]
    declared_keys = list(dataset.join_keys) or field_join_keys

    known_limitations: list[str] = []
    if not fields:
        known_limitations.append(
            "Registry has no machine-readable field schema for this dataset; "
            "field selection is best-effort and should be confirmed manually."
        )
    if source.auth_required and source.auth_required != "none":
        known_limitations.append(f"auth_required: {source.auth_required}")
    if source.cost and source.cost != "free":
        known_limitations.append(f"cost: {source.cost}")

    contract: dict[str, Any] = {
        "dataset_id": dataset.id,
        "role": role,
        "registry_commit": client.commit_hash(),
        "fields": {
            "date_field": time_field,
            "value_field": value_field,
            "entity_fields": entity_fields,
        },
        "join_keys": {
            "required": [],
            "available": declared_keys,
            "missing": [],
        },
        "cadence": {
            "native_cadence": native_cadence,
            "target_cadence": target_cadence,
            "aggregation": _default_aggregation(variable_type),
        },
        "variable": {
            "variable_type": variable_type,
            "unit": None,
            "transform_allowed": True,
        },
        "timing": {
            "release_lag_days": None,
            "point_in_time_safe": None,
            "revisions_possible": None,
        },
        "quality": {
            "coverage_start": None,
            "coverage_end": None,
            "missingness_policy": "flag",
            "known_limitations": known_limitations,
        },
        "source_metadata": {
            "source_id": source.id,
            "license": source.license,
            "lag": source.lag,
            "frequency": source.frequency,
            "homepage_url": source.homepage_url,
        },
    }
    return contract
