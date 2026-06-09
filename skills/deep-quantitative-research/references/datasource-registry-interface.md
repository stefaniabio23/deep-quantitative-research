# Datasource registry interface

Reference for skills that consume the sibling datasources repo through `src/deep_quantitative_research/registry/`.

## Topology

```text
~/Projects/datasources/                     canonical public-data registry
  entries/<domain>/<slug>.md                one file per source provider
  catalog/<source_id>/                      multi-dataset providers (e.g. EIA)
  schema/                                   JSON Schema definitions
  generated/                                machine artefacts consumed by deep-quant
    index.json                              sources list with full metadata
    sources.csv
    datasets.csv
    fields.csv
    join-keys.csv
    join-key-index.md
```

```text
~/Projects/deep-quant-research/
  config/datasources.yaml                   tells the registry client where the repo lives
  src/deep_quantitative_research/registry/  CSV-native client + scoring + contracts
```

## Python API

```python
from deep_quantitative_research.registry import (
    get_client,
    get_source,
    get_dataset,
    get_fields,
    get_join_keys,
    search_sources,
    search_datasets,
    find_compatible_sources,
    find_join_path,
    build_join_assessment,
    build_dataset_contract,
    score_dataset_fit,
)

client = get_client()
print(client.healthcheck())
print(search_datasets("retail", domain="finance-markets", cadence="monthly", limit=5))
print(build_dataset_contract("eia-electricity-retail-sales", role="predictor"))
```

## CLI

```bash
deep-quant query-datasources --healthcheck
deep-quant query-datasources --query retail --domain finance-markets --limit 5
deep-quant query-datasources --query macro --cadence monthly --output json
deep-quant build-dataset-contract <dataset_id> --role predictor --target-cadence monthly
deep-quant score-dataset <dataset_id> --hypothesis experiments/ideas/<slug>.yaml
deep-quant assess-join <source_dataset_id> <target_dataset_id>
```

## Conventions

- Every research run records `registry_commit` (the datasources repo HEAD SHA at run time).
- Relative `path` in `config/datasources.yaml` is resolved from the deep-quant repo root, so the default `../datasources` points at the sibling repo regardless of CWD.
- `DATASOURCES_PATH` env var wins over the config value.
- The registry client treats single-dataset sources (corpus, registry, time-series with no catalog rows) by surfacing the source as a synthetic dataset (`source_id == dataset_id`, `is_catalog == False`). Panel sources and any source with catalog rows are only surfaced through their catalog datasets.

## Limits and caveats

- The registry is MVP-scoped and does not currently ship `catalog.duckdb`, `join_key_graph.json`, or `source_quality_scores.csv`. The client compensates: CSV-native reads, in-memory join graph, scoring computed in deep-quant.
- `commit_hash()` returns `None` if the datasources repo is not a git checkout. When `versioning.require_commit_hash: true` is set in the config and the hash is unavailable, `client.snapshot()` raises.
- The registry never carries `unit` or precise `release_lag_days` for most sources; dataset-contract must fill these in manually.
