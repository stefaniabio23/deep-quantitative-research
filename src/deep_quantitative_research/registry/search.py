"""Search the registry. Keyword search across sources / datasets / fields,
plus compatibility queries by join key."""

from __future__ import annotations

from dataclasses import dataclass

from .client import RegistryClient, get_client
from .index import get_dataset
from .types import Dataset, Source


@dataclass
class SearchHit:
    """A scored search result. `kind` is 'source' or 'dataset'."""

    kind: str
    id: str
    name: str
    domain: str
    entry_kind: str
    score: int
    matched_on: list[str]


def _haystack(*parts: str | None) -> str:
    return " ".join(p for p in parts if p).lower()


def _score(query_tokens: list[str], hay: str) -> tuple[int, list[str]]:
    matched: list[str] = []
    score = 0
    for token in query_tokens:
        if token in hay:
            score += 1
            matched.append(token)
    return score, matched


def search_sources(
    query: str,
    *,
    domain: str | None = None,
    entry_kind: str | None = None,
    join_key: str | None = None,
    client: RegistryClient | None = None,
    limit: int = 20,
) -> list[SearchHit]:
    """Search across the source catalog (entries/)."""
    client = client or get_client()
    tokens = [t for t in query.lower().split() if t]
    hits: list[SearchHit] = []
    for source in client.sources.values():
        if domain and source.domain != domain:
            continue
        if entry_kind and source.entry_kind != entry_kind:
            continue
        if join_key and join_key not in source.join_keys:
            continue
        hay = _haystack(
            source.id,
            source.name,
            source.description,
            " ".join(source.raw.get("agent_use_cases") or []),
            " ".join(source.join_keys),
        )
        score, matched = _score(tokens, hay) if tokens else (1, [])
        if score == 0 and tokens:
            continue
        hits.append(
            SearchHit(
                kind="source",
                id=source.id,
                name=source.name,
                domain=source.domain,
                entry_kind=source.entry_kind,
                score=score,
                matched_on=matched,
            )
        )
    hits.sort(key=lambda h: (-h.score, h.name.lower()))
    return hits[:limit]


def search_datasets(
    query: str,
    *,
    domain: str | None = None,
    cadence: str | None = None,
    join_key: str | None = None,
    entry_kind: str | None = None,
    client: RegistryClient | None = None,
    limit: int = 20,
) -> list[SearchHit]:
    """Search across the dataset catalog (datasets.csv + single-dataset sources)."""
    client = client or get_client()
    tokens = [t for t in query.lower().split() if t]
    hits: list[SearchHit] = []
    for dataset in client.datasets.values():
        source = client.sources.get(dataset.source_id)
        if domain and (not source or source.domain != domain):
            continue
        if entry_kind and dataset.entry_kind != entry_kind:
            continue
        if cadence and cadence not in dataset.time_grain:
            continue
        if join_key and join_key not in dataset.join_keys:
            continue
        hay = _haystack(
            dataset.id,
            dataset.name,
            source.description if source else "",
            " ".join(dataset.join_keys),
            " ".join(dataset.time_grain),
            dataset.entry_kind,
        )
        score, matched = _score(tokens, hay) if tokens else (1, [])
        if score == 0 and tokens:
            continue
        hits.append(
            SearchHit(
                kind="dataset",
                id=dataset.id,
                name=dataset.name,
                domain=(source.domain if source else ""),
                entry_kind=dataset.entry_kind,
                score=score,
                matched_on=matched,
            )
        )
    hits.sort(key=lambda h: (-h.score, h.name.lower()))
    return hits[:limit]


def find_compatible_sources(
    target_dataset_id: str,
    *,
    client: RegistryClient | None = None,
    limit: int = 20,
) -> list[Source]:
    """Sources that share at least one join key with the target dataset."""
    client = client or get_client()
    target = get_dataset(target_dataset_id, client=client)
    target_keys = set(target.join_keys)
    if not target_keys:
        return []
    compatible: list[tuple[int, Source]] = []
    for source in client.sources.values():
        if source.id == target.source_id:
            continue
        overlap = len(target_keys.intersection(source.join_keys))
        if overlap == 0:
            continue
        compatible.append((overlap, source))
    compatible.sort(key=lambda pair: (-pair[0], pair[1].name.lower()))
    return [src for _, src in compatible[:limit]]
