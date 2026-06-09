---
name: datasource-query
description: Query the sibling datasources repo for datasets relevant to a hypothesis. Returns candidate target, predictor, and context datasets with fields, join keys, cadence, point-in-time safety, release-lag metadata, and access constraints. Invoke after hypothesis-formulation and before dataset-selection.
---

# datasource-query

## When to invoke

You have a Hypothesis YAML and need to know what data the registry actually offers. This is the bridge between abstract predictor concepts and concrete `dataset_id` references.

Always invoke through the `deep-quant query-datasources` CLI (which wraps `src/deep_quantitative_research/registry/`). Never hand-edit dataset metadata; if the registry is wrong, fix it in the datasources repo.

## Inputs

- Hypothesis YAML at `experiments/ideas/<slug>.yaml`.
- Optional filters from the hypothesis: target cadence, geography, required history window.

## Procedure

1. Read the hypothesis. Extract: `target_variable`, `candidate_predictors`, `target_cadence`, `expected_lag_periods`, `domain`.
2. For each `candidate_predictor`, run one or more queries:
   ```bash
   deep-quant query-datasources --query "<predictor concept>" --domain <domain> --limit 10
   deep-quant query-datasources --query "<predictor concept>" --cadence <target_cadence> --limit 10
   ```
3. For the target variable, search separately for the canonical KPI dataset.
4. For each candidate, verify cadence compatibility against `target_cadence`. A predictor finer than the target rolls up; a predictor coarser is suspect.
5. For each candidate, fetch the join keys (`deep-quant assess-join <source> <target>`) and record whether a direct join exists.
6. Flag missing required variables, weak proxies, insufficient history, point-in-time safety concerns, licensing or access constraints.
7. Emit `experiments/specs/dataset-candidates.yaml` (schema below).
8. Suggest the next step: `/find-datasets` produced the candidate set; `dataset-selection` will score and choose.

## Hard rules

- **Reference datasets by `dataset_id` only.** Never paraphrase the dataset name in the output.
- **Record the registry commit hash for every query.** If `query-datasources --healthcheck` cannot produce one, abort.
- **Flag rather than filter.** Surfacing a weak candidate with a warning is better than silently dropping it.
- **Do not score yet.** That is dataset-selection's job.

## Output schema

```yaml
candidates:
  hypothesis_id: HYP-2026-NNN
  registry_commit: <sha>
  target_candidates:
    - dataset_id: <id>
      role: target
      fields_of_interest: [<field>]
      cadence_match: native | rollup | mismatch
      join_keys: [<key>]
      caveats: [<string>]
  predictor_candidates:
    - dataset_id: <id>
      role: predictor
      predictor_concept: <which hypothesis predictor this fills>
      fields_of_interest: [<field>]
      cadence_match: native | rollup | mismatch
      join_keys: [<key>]
      caveats: [<string>]
  context_candidates: []
  rejected:
    - dataset_id: <id>
      reason: <one-liner>
```

## CLI cheat sheet

```bash
deep-quant query-datasources --healthcheck
deep-quant query-datasources --query retail --domain finance-markets --limit 5
deep-quant query-datasources --query macro --cadence monthly --output json
deep-quant query-datasources --join-key DATE --kind time-series --limit 20
deep-quant assess-join google-trends-retail-searches ons-retail-sales-index
```

## Cross-references

- Registry API: `src/deep_quantitative_research/registry/__init__.py`.
- Reference: `references/datasource-registry-interface.md`.
- Next sub-skill: `dataset-selection`.
- Spec: `BUILD_CHECKLIST.md` section 7.2.
