"""Tests for the provenance / PIT discipline:

- Target.revisions_possible and Target.point_in_time_safe surface as
  checks in the validation report when true / false.
- RegistryClient.snapshot() records remote_url + dirty_tree warnings.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from deep_quantitative_research.registry import RegistryClient
from deep_quantitative_research.research.signal_spec import (
    FeatureGridSpec,
    HypothesisBlock,
    Predictor,
    SignalSpec,
    Target,
    ValidationSpec,
    load_signal_spec,
)
from deep_quantitative_research.validation import Check
from deep_quantitative_research.validation.gate import assemble


# ---------------------------------------------------------------- signal spec


def test_target_carries_revisions_possible_field(tmp_path: Path):
    spec_yaml = """
signal_id: test
signal_name: Test
hypothesis:
  statement: x predicts y
  target_variable: y
target:
  dataset_id: target-ds
  field: y
  cadence: monthly
  revisions_possible: true
  point_in_time_safe: false
predictors:
  - dataset_id: pred-ds
    field: x
    cadence: monthly
feature_grid:
  mode: controlled
  max_features: 10
  max_lags: 2
validation:
  train_period: 2020-01-31/2021-12-31
  test_period: 2022-01-31/2022-12-31
outputs:
  signal_card: true
"""
    path = tmp_path / "spec.yaml"
    path.write_text(spec_yaml)
    spec = load_signal_spec(path)
    assert spec.target.revisions_possible is True
    assert spec.target.point_in_time_safe is False


def test_target_revisions_possible_defaults_to_none(tmp_path: Path):
    spec_yaml = """
signal_id: test
signal_name: Test
hypothesis:
  statement: x predicts y
  target_variable: y
target:
  dataset_id: target-ds
  field: y
  cadence: monthly
predictors:
  - dataset_id: pred-ds
    field: x
    cadence: monthly
feature_grid:
  mode: controlled
  max_features: 10
  max_lags: 2
validation:
  train_period: 2020-01-31/2021-12-31
  test_period: 2022-01-31/2022-12-31
outputs:
  signal_card: true
"""
    path = tmp_path / "spec.yaml"
    path.write_text(spec_yaml)
    spec = load_signal_spec(path)
    assert spec.target.revisions_possible is None
    assert spec.target.point_in_time_safe is None


# ---------------------------------------------------------------- snapshot


def _init_repo(repo_path: Path, *, remote_url: str | None = None, with_dirty_file: bool = False) -> None:
    """Init a git repo, stage all current files, and commit them.

    Generated/ files are written before this helper is called, so the
    initial commit captures them and the working tree is clean unless
    ``with_dirty_file`` is set.
    """
    subprocess.run(["git", "init", "--quiet"], cwd=repo_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit",
         "-m", "init", "--quiet", "--allow-empty"],
        cwd=repo_path, check=True,
    )
    if remote_url:
        subprocess.run(
            ["git", "remote", "add", "origin", remote_url],
            cwd=repo_path, check=True,
        )
    if with_dirty_file:
        (repo_path / "dirty.txt").write_text("uncommitted change")


def _write_min_generated(repo_path: Path) -> None:
    generated = repo_path / "generated"
    generated.mkdir(parents=True)
    (generated / "index.json").write_text("[]")
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
    )


def test_snapshot_records_remote_url(tmp_path: Path):
    _write_min_generated(tmp_path)
    _init_repo(tmp_path, remote_url="https://example.com/repo.git")
    client = RegistryClient(repo_path=tmp_path)
    snap = client.snapshot([])
    assert snap["remote_url"] == "https://example.com/repo.git"
    assert snap["dirty_tree"] is False
    assert snap["warnings"] == []


def test_snapshot_warns_on_dirty_tree(tmp_path: Path):
    _write_min_generated(tmp_path)
    _init_repo(tmp_path, remote_url="https://example.com/repo.git", with_dirty_file=True)
    client = RegistryClient(repo_path=tmp_path)
    snap = client.snapshot([])
    assert snap["dirty_tree"] is True
    assert any("uncommitted changes" in w for w in snap["warnings"])


def test_snapshot_warns_when_no_remote(tmp_path: Path):
    _write_min_generated(tmp_path)
    _init_repo(tmp_path, remote_url=None)
    client = RegistryClient(repo_path=tmp_path)
    snap = client.snapshot([])
    assert snap["remote_url"] is None
    assert any("no remote configured" in w for w in snap["warnings"])


def test_snapshot_dataset_ids_recorded(tmp_path: Path):
    _write_min_generated(tmp_path)
    _init_repo(tmp_path, remote_url="https://example.com/repo.git")
    client = RegistryClient(repo_path=tmp_path)
    snap = client.snapshot(["dataset-a", "dataset-b"])
    assert {d["dataset_id"] for d in snap["datasets"]} == {"dataset-a", "dataset-b"}
