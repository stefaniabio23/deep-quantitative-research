"""Registry client: bridge to the sibling datasources repo.

Loads the generated catalog (index.json + sources.csv + datasets.csv +
fields.csv + join-keys.csv) and exposes typed access plus the registry
API listed in BUILD_CHECKLIST.md section 4.4.
"""

from .client import RegistryClient, RegistryError, get_client
from .contracts import build_dataset_contract
from .index import get_dataset, get_fields, get_join_keys, get_source
from .join_graph import build_join_assessment, find_join_path
from .scoring import score_dataset_fit
from .search import find_compatible_sources, search_datasets, search_sources
from .types import Dataset, Field, JoinKey, Source

__all__ = [
    "RegistryClient",
    "RegistryError",
    "get_client",
    "get_dataset",
    "get_source",
    "get_fields",
    "get_join_keys",
    "search_datasets",
    "search_sources",
    "find_compatible_sources",
    "find_join_path",
    "build_join_assessment",
    "build_dataset_contract",
    "score_dataset_fit",
    "Dataset",
    "Field",
    "JoinKey",
    "Source",
]
