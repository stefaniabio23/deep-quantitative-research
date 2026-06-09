"""Unit tests for the registry client against the registry-mini fixture."""

from __future__ import annotations

import pytest

from deep_quantitative_research.registry import (
    RegistryError,
    build_dataset_contract,
    build_join_assessment,
    find_compatible_sources,
    find_join_path,
    get_dataset,
    get_fields,
    get_join_keys,
    get_source,
    score_dataset_fit,
    search_datasets,
    search_sources,
)


def test_healthcheck_counts(client):
    info = client.healthcheck()
    counts = info["counts"]
    assert counts["sources"] == 3
    # 3 catalog rows (eia + 2 fred rows) + 1 synthesised (arxiv corpus). fred has
    # catalog rows so it is NOT also synthesised; eia is panel so it is NOT
    # synthesised.
    assert counts["datasets"] == 4
    assert counts["fields"] == 8
    assert counts["join_keys"] == 5


def test_get_source(client):
    arxiv = get_source("arxiv", client=client)
    assert arxiv.name == "arXiv"
    assert arxiv.domain == "academic"
    assert "ARXIV_ID" in arxiv.join_keys
    assert arxiv.license == "CC0"


def test_get_source_missing(client):
    with pytest.raises(RegistryError):
        get_source("nope", client=client)


def test_arxiv_synthesised_as_dataset(client):
    """Single-dataset sources (corpus) get surfaced as datasets with source_id == dataset_id."""
    dataset = get_dataset("arxiv", client=client)
    assert dataset.source_id == "arxiv"
    assert dataset.is_catalog is False
    assert "ARXIV_ID" in dataset.join_keys


def test_panel_source_not_synthesised(client):
    """Panel sources (EIA) should NOT have a synthesised dataset; only the real catalog rows."""
    with pytest.raises(RegistryError):
        get_dataset("eia-open-data", client=client)


def test_catalog_dataset_is_real(client):
    dataset = get_dataset("eia-electricity-retail-sales", client=client)
    assert dataset.is_catalog is True
    assert dataset.source_id == "eia-open-data"
    assert "monthly" in dataset.time_grain
    assert "DATE" in dataset.join_keys


def test_get_fields_returns_schema(client):
    fields = get_fields("eia-electricity-retail-sales", client=client)
    names = [f.name for f in fields]
    assert "period" in names
    assert any(f.role == "time_index" for f in fields)
    assert any(f.role == "measure" for f in fields)


def test_get_fields_empty_for_sources_without_schema(client):
    """A source-level synthesised dataset has no schema rows."""
    assert get_fields("arxiv", client=client) == []


def test_get_join_keys_lookup(client):
    keys = get_join_keys("eia-electricity-retail-sales", client=client)
    by_name = {k.name: k for k in keys}
    assert "DATE" in by_name
    assert by_name["DATE"].entity_type == "time"
    assert by_name["US_STATE_CODE"].pattern is not None


def test_search_datasets_basic(client):
    hits = search_datasets("retail", client=client, limit=5)
    assert hits, "expected at least one hit for 'retail'"
    ids = {h.id for h in hits}
    assert "fred-retail-sales" in ids or "eia-electricity-retail-sales" in ids


def test_search_datasets_filter_by_cadence(client):
    monthly_only = search_datasets("", cadence="monthly", client=client, limit=20)
    assert all("monthly" in (get_dataset(h.id, client=client).time_grain) for h in monthly_only)


def test_search_sources_filter_by_domain(client):
    hits = search_sources("", domain="academic", client=client, limit=20)
    assert {h.id for h in hits} == {"arxiv"}


def test_find_compatible_sources(client):
    # eia-electricity-retail-sales has DATE + US_STATE_CODE; FRED shares DATE + US_STATE_CODE.
    compatible = find_compatible_sources("eia-electricity-retail-sales", client=client)
    ids = {s.id for s in compatible}
    assert "fred" in ids
    assert "arxiv" not in ids


def test_find_join_path(client):
    direct = find_join_path("fred-retail-sales", "eia-electricity-retail-sales", client=client)
    assert "DATE" in direct
    assert "US_STATE_CODE" not in direct  # fred-retail-sales does not declare US_STATE_CODE


def test_join_assessment_strong_when_time_and_place_shared(client):
    """fred-unemployment shares DATE with the EIA dataset but no geographic key, so it's medium."""
    assessment = build_join_assessment(
        "fred-unemployment", "eia-electricity-retail-sales", client=client
    )
    assert assessment.direct_join_keys == ["DATE"]
    assert assessment.join_quality in {"medium", "weak"}
    assert assessment.warnings  # should explain why


def test_join_assessment_incompatible(client):
    """arxiv shares no join keys with EIA datasets."""
    assessment = build_join_assessment("arxiv", "eia-electricity-retail-sales", client=client)
    assert assessment.direct_join_keys == []
    assert assessment.join_quality == "incompatible"


def test_build_dataset_contract_shape(client):
    contract = build_dataset_contract(
        "eia-electricity-retail-sales", role="predictor", client=client
    )
    assert contract["dataset_id"] == "eia-electricity-retail-sales"
    assert contract["role"] == "predictor"
    assert contract["cadence"]["native_cadence"] == "monthly"
    assert contract["fields"]["date_field"] == "period"
    assert contract["fields"]["value_field"] in {"sales", "price"}
    assert "US_STATE_CODE" in contract["join_keys"]["available"]


def test_score_dataset_fit_scales(client):
    hypothesis = {
        "statement": "Electricity retail sales predict next-quarter consumer demand.",
        "target_variable": "US retail sales",
        "target_cadence": "monthly",
    }
    score = score_dataset_fit(hypothesis, "eia-electricity-retail-sales", client=client)
    assert 0 <= score["total_score"] <= 10
    assert score["cadence_fit"] == 10  # native monthly matches target monthly
    assert score["coverage"] >= 7      # has 'US' and 'global'


def test_snapshot_dataset_ids(client):
    """Snapshot block is the building material for registry-lock.yaml."""
    snap = client.snapshot(["arxiv", "eia-electricity-retail-sales"])
    assert snap["repo"] == "datasources"
    assert len(snap["datasets"]) == 2
    assert {d["dataset_id"] for d in snap["datasets"]} == {"arxiv", "eia-electricity-retail-sales"}
