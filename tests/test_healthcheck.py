"""Tests for the healthcheck warnings + ok flag."""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import pytest

from deep_quantitative_research.registry import RegistryClient


# ---------------------------------------------------------------- fixtures


def _write_min_registry(repo_path: Path, *, with_datasets: bool = True, with_join_keys: bool = True) -> None:
    """Write a barebones registry-mini at ``repo_path``."""
    generated = repo_path / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    (generated / "index.json").write_text(json.dumps([
        {
            "id": "fake-source",
            "name": "Fake Source",
            "domain": "academic",
            "entry_kind": "corpus",
            "description": "fake source for tests.",
            "join_keys": ["DOI"] if with_join_keys else [],
            "primary_keys": [],
            "geography": ["global"],
        }
    ]))
    with (generated / "datasets.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "source_id", "name", "entry_level", "entry_kind", "route",
            "data_endpoint", "metadata_endpoint", "time_index", "time_grain",
            "primary_keys", "join_keys", "field_schema", "agent_use_cases",
        ])
        if with_datasets:
            writer.writerow([
                "fake-dataset", "fake-source", "Fake Dataset", "dataset",
                "time-series", "", "", "", "date", "daily", "", "DATE", "", "",
            ])
    (generated / "fields.csv").write_text(
        "source_id,dataset_id,field_name,type,role,join_key,unit,required,description\n"
    )
    with (generated / "join-keys.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["join_key", "entity_type", "pattern", "examples", "description"])
        if with_join_keys:
            writer.writerow(["DOI", "scholarly_work", "^10\\..*", "10.1038/x", "DOI."])


# ---------------------------------------------------------------- API tests


def test_healthcheck_ok_when_populated(tmp_path: Path):
    _write_min_registry(tmp_path)
    client = RegistryClient(repo_path=tmp_path)
    info = client.healthcheck()
    assert info["ok"] is True
    assert info["warnings"] == []
    assert info["counts"]["sources"] >= 1
    assert info["counts"]["join_keys"] >= 1


def test_healthcheck_warns_when_no_sources(tmp_path: Path):
    # Just create an empty generated/ dir.
    (tmp_path / "generated").mkdir(parents=True)
    client = RegistryClient(repo_path=tmp_path)
    info = client.healthcheck()
    assert info["ok"] is False
    assert any("only 0 sources loaded" in w for w in info["warnings"])


def test_healthcheck_warns_when_no_datasets_and_panel_source(tmp_path: Path):
    """A panel source (multi-dataset) WITHOUT catalog rows should warn.

    Single-dataset sources (corpus / registry / time-series) get surfaced
    as synthetic source-level datasets so a missing datasets.csv is not
    pathological for them. Panel sources do not get synthesized, so a
    missing catalog row IS a broken-registry signal.
    """
    generated = tmp_path / "generated"
    generated.mkdir(parents=True)
    (generated / "index.json").write_text(json.dumps([
        {
            "id": "fake-panel",
            "name": "Fake Panel",
            "domain": "academic",
            "entry_kind": "panel",  # panel sources do not get synthesized
            "description": "fake panel.",
            "join_keys": ["DOI"],
            "primary_keys": [],
            "geography": ["global"],
        }
    ]))
    (generated / "datasets.csv").write_text(
        "id,source_id,name,entry_level,entry_kind,route,data_endpoint,"
        "metadata_endpoint,time_index,time_grain,primary_keys,join_keys,"
        "field_schema,agent_use_cases\n"
    )
    (generated / "fields.csv").write_text(
        "source_id,dataset_id,field_name,type,role,join_key,unit,required,description\n"
    )
    (generated / "join-keys.csv").write_text(
        "join_key,entity_type,pattern,examples,description\n"
        "DOI,scholarly_work,^10\\..*,10.1038/x,DOI.\n"
    )

    client = RegistryClient(repo_path=tmp_path)
    info = client.healthcheck()
    assert info["ok"] is False
    assert any("datasets" in w for w in info["warnings"])


def test_healthcheck_warns_when_no_join_keys(tmp_path: Path):
    _write_min_registry(tmp_path, with_join_keys=False)
    client = RegistryClient(repo_path=tmp_path)
    info = client.healthcheck()
    assert info["ok"] is False
    assert any("join keys" in w for w in info["warnings"])


def test_healthcheck_warns_on_missing_commit_when_required(tmp_path: Path):
    # No .git → commit_hash returns None.
    _write_min_registry(tmp_path)
    client = RegistryClient(repo_path=tmp_path)
    client._versioning_cfg = {"require_commit_hash": True}
    info = client.healthcheck()
    assert info["ok"] is False
    assert any("commit hash" in w for w in info["warnings"])


def test_healthcheck_thresholds_are_tunable(tmp_path: Path):
    _write_min_registry(tmp_path)
    client = RegistryClient(repo_path=tmp_path)
    # The fixture has 1 source; requiring 100 should fail.
    info = client.healthcheck(min_sources=100)
    assert info["ok"] is False


# ---------------------------------------------------------------- CLI exit code


def test_cli_exit_zero_when_ok(tmp_path: Path):
    _write_min_registry(tmp_path)
    config = tmp_path / "config" / "datasources.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        f"datasources_repo:\n  path: '{tmp_path}'\nregistry_mode: local\n"
        "versioning:\n  require_commit_hash: false\n"
    )
    result = subprocess.run(
        ["deep-quant", "query-datasources", "--healthcheck", "--config", str(config)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "ok:                 True" in result.stdout


def test_cli_exit_nonzero_on_warnings(tmp_path: Path):
    # Populated repo but require commit hash without a git checkout.
    _write_min_registry(tmp_path)
    config = tmp_path / "config" / "datasources.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        f"datasources_repo:\n  path: '{tmp_path}'\nregistry_mode: local\n"
        "versioning:\n  require_commit_hash: true\n"
    )
    result = subprocess.run(
        ["deep-quant", "query-datasources", "--healthcheck", "--config", str(config)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "ok:                 False" in result.stdout
    assert "commit hash" in result.stderr.lower()
