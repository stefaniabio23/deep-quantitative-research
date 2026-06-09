"""Direct lookup helpers: get_dataset, get_source, get_fields, get_join_keys."""

from __future__ import annotations

from .client import RegistryClient, RegistryError, get_client
from .types import Dataset, Field, JoinKey, Source


def get_source(source_id: str, *, client: RegistryClient | None = None) -> Source:
    client = client or get_client()
    try:
        return client.sources[source_id]
    except KeyError as exc:
        raise RegistryError(f"Unknown source_id: {source_id!r}") from exc


def get_dataset(dataset_id: str, *, client: RegistryClient | None = None) -> Dataset:
    client = client or get_client()
    try:
        return client.datasets[dataset_id]
    except KeyError as exc:
        raise RegistryError(f"Unknown dataset_id: {dataset_id!r}") from exc


def get_fields(dataset_id: str, *, client: RegistryClient | None = None) -> list[Field]:
    """Return the field list for a dataset; empty list if no schema is registered.

    Empty results are valid (most single-dataset sources do not ship a
    machine-readable schema yet); callers should treat absence as a flag, not
    an error.
    """
    client = client or get_client()
    return list(client.fields_by_dataset.get(dataset_id, []))


def get_join_keys(dataset_id: str, *, client: RegistryClient | None = None) -> list[JoinKey]:
    """Return JoinKey records for every join key the dataset declares."""
    client = client or get_client()
    dataset = get_dataset(dataset_id, client=client)
    keys: list[JoinKey] = []
    for name in dataset.join_keys:
        registered = client.join_keys.get(name)
        if registered is not None:
            keys.append(registered)
        else:
            keys.append(JoinKey(name=name, entity_type=None, pattern=None, examples=[], description=None))
    return keys
