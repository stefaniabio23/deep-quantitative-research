"""Join-key compatibility: find a join path between two datasets, build an explicit
join assessment that names the direct keys, missing bridges, and quality."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .client import RegistryClient, get_client
from .index import get_dataset


@dataclass
class JoinAssessment:
    """Explicit join assumptions between two datasets. Spec section 11."""

    source_dataset: str
    target_dataset: str
    direct_join_keys: list[str]
    missing_semantic_bridge: list[str] = field(default_factory=list)
    join_quality: str = "unknown"
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_dataset": self.source_dataset,
            "target_dataset": self.target_dataset,
            "direct_join_keys": list(self.direct_join_keys),
            "missing_semantic_bridge": list(self.missing_semantic_bridge),
            "join_quality": self.join_quality,
            "warnings": list(self.warnings),
        }


_TIME_KEYS = {"DATE", "PERIOD", "MONTH", "QUARTER", "YEAR"}
_PLACE_KEYS = {"ISO_3", "ISO_3166_1", "ISO_3166_2", "US_STATE_CODE", "NUTS"}


def find_join_path(
    source_dataset_id: str,
    target_dataset_id: str,
    *,
    client: RegistryClient | None = None,
) -> list[str]:
    """Return the direct join keys shared by two datasets, in registry order.

    No transitive bridges yet; that requires a manually curated bridge graph.
    Spec section 11 leaves that as an explicit warning rather than guesswork.
    """
    client = client or get_client()
    src = get_dataset(source_dataset_id, client=client)
    tgt = get_dataset(target_dataset_id, client=client)
    return [k for k in tgt.join_keys if k in src.join_keys]


def build_join_assessment(
    source_dataset_id: str,
    target_dataset_id: str,
    *,
    client: RegistryClient | None = None,
) -> JoinAssessment:
    """Spec section 11. Names direct keys, identifies missing semantic bridges,
    rates join quality."""
    client = client or get_client()
    direct = find_join_path(source_dataset_id, target_dataset_id, client=client)
    src = get_dataset(source_dataset_id, client=client)
    tgt = get_dataset(target_dataset_id, client=client)

    warnings: list[str] = []
    missing: list[str] = []

    has_time = bool(_TIME_KEYS.intersection(direct))
    has_place = bool(_PLACE_KEYS.intersection(direct))

    if not direct:
        join_quality = "incompatible"
        warnings.append("No shared join keys; this requires a manually curated bridge.")
        for k in tgt.join_keys:
            missing.append(f"{tgt.id}.{k}")
        for k in src.join_keys:
            missing.append(f"{src.id}.{k}")
    elif len(direct) == 1 and not has_time:
        join_quality = "weak"
        warnings.append(
            "Only one non-time join key; cross-section panel joins likely incomplete."
        )
    elif has_time and not has_place and _PLACE_KEYS.intersection(set(tgt.join_keys + src.join_keys)):
        join_quality = "medium"
        warnings.append(
            "Time keys overlap but geography differs; verify the geographic granularity is comparable."
        )
    elif has_time and has_place:
        join_quality = "strong"
    else:
        join_quality = "medium"

    return JoinAssessment(
        source_dataset=source_dataset_id,
        target_dataset=target_dataset_id,
        direct_join_keys=direct,
        missing_semantic_bridge=missing,
        join_quality=join_quality,
        warnings=warnings,
    )
