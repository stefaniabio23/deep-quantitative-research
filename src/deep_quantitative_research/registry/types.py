"""Typed records the registry client returns.

Kept deliberately minimal. Raw upstream metadata stays on `.raw` so consumers
can reach for fields we haven't promoted yet without us blocking access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Source:
    """A data provider (arxiv, fred, yfinance, eia-open-data, ...).

    Sources come from the datasources `entries/<domain>/<slug>.md` files,
    flattened into generated/index.json.
    """

    id: str
    name: str
    domain: str
    entry_kind: str
    description: str
    join_keys: list[str]
    primary_keys: list[str]
    geography: list[str]
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def homepage_url(self) -> str | None:
        return self.raw.get("homepage_url")

    @property
    def docs_url(self) -> str | None:
        return self.raw.get("docs_url")

    @property
    def frequency(self) -> str | None:
        return self.raw.get("frequency")

    @property
    def lag(self) -> str | None:
        return self.raw.get("lag")

    @property
    def license(self) -> str | None:
        return self.raw.get("license")

    @property
    def cost(self) -> str | None:
        return self.raw.get("cost")

    @property
    def auth_required(self) -> str | None:
        return self.raw.get("auth_required")

    @property
    def mcp_status(self) -> str | None:
        return self.raw.get("mcp_status")


@dataclass
class Dataset:
    """A specific dataset / endpoint within a source.

    For single-dataset sources (corpus, registry, time-series), the dataset_id
    equals the source_id and `is_catalog` is False. For multi-dataset sources
    (panel sources with a catalog/ folder, like EIA), one Dataset per row in
    generated/datasets.csv and `is_catalog` is True.
    """

    id: str
    source_id: str
    name: str
    entry_kind: str
    time_index: str | None
    time_grain: list[str]
    primary_keys: list[str]
    join_keys: list[str]
    field_schema: str | None
    is_catalog: bool = False
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Field:
    """A column within a dataset's schema."""

    source_id: str
    dataset_id: str
    name: str
    type: str | None
    role: str | None
    join_key: str | None
    unit: str | None
    required: bool
    description: str | None


@dataclass
class JoinKey:
    """A canonical join key in the datasources registry."""

    name: str
    entity_type: str | None
    pattern: str | None
    examples: list[str]
    description: str | None
