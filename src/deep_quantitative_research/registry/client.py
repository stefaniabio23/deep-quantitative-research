"""RegistryClient: load config, open the datasources catalog, expose typed access.

Reads the generated/ artefacts in the sibling datasources repo. CSV-native,
no DuckDB required at runtime. If catalog.duckdb appears in the future, the
client can grow a fast path; the read API stays identical.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from functools import cached_property
from pathlib import Path
from typing import Any

import yaml

from .types import Dataset, Field, JoinKey, Source


class RegistryError(RuntimeError):
    """Raised when the registry cannot be located, loaded, or queried."""


def _split_list(raw: str | None, sep: str = ";") -> list[str]:
    if not raw:
        return []
    return [piece.strip() for piece in raw.split(sep) if piece.strip()]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"yes", "true", "1"}


class RegistryClient:
    """Read-only client over the datasources repo's generated catalog."""

    def __init__(
        self,
        config_path: Path | str | None = None,
        repo_path: Path | str | None = None,
    ) -> None:
        if repo_path is not None:
            self.repo_path = Path(repo_path).resolve()
            self.config_path = None
            self._versioning_cfg: dict[str, Any] = {}
        else:
            config_path = Path(config_path or "config/datasources.yaml")
            if not config_path.exists():
                raise RegistryError(
                    f"Config not found at {config_path}. "
                    "Run deep-quant from the repo root or pass --config."
                )
            cfg = yaml.safe_load(config_path.read_text()) or {}
            repo_cfg = cfg.get("datasources_repo") or {}
            raw_path = repo_cfg.get("path", "../datasources")
            self.config_path = config_path
            env_override = os.environ.get("DATASOURCES_PATH")
            # Convention: relative `path` in config is resolved from the repo
            # root (the parent of `config/`), so `path: "../datasources"` points
            # at a sibling repo regardless of CWD. Absolute paths win as-is.
            raw = Path(raw_path)
            if env_override:
                base = Path(env_override)
            elif raw.is_absolute():
                base = raw
            else:
                config_parent = config_path.resolve().parent
                repo_root = config_parent.parent if config_parent.name == "config" else config_parent
                base = repo_root / raw
            self.repo_path = base.resolve()
            self._versioning_cfg = cfg.get("versioning", {}) or {}

        self.generated_path = self.repo_path / "generated"
        if not self.generated_path.exists():
            raise RegistryError(
                f"datasources/generated not found at {self.generated_path}. "
                "Run `python3 scripts/generate.py` in the datasources repo."
            )

    # ---------------------------------------------------------------- loaders

    @cached_property
    def _index_entries(self) -> list[dict[str, Any]]:
        path = self.generated_path / "index.json"
        if not path.exists():
            return []
        return json.loads(path.read_text())

    @cached_property
    def _datasets_csv(self) -> list[dict[str, str]]:
        return _read_csv(self.generated_path / "datasets.csv")

    @cached_property
    def _fields_csv(self) -> list[dict[str, str]]:
        return _read_csv(self.generated_path / "fields.csv")

    @cached_property
    def _join_keys_csv(self) -> list[dict[str, str]]:
        return _read_csv(self.generated_path / "join-keys.csv")

    # ---------------------------------------------------------------- caches

    @cached_property
    def sources(self) -> dict[str, Source]:
        out: dict[str, Source] = {}
        for entry in self._index_entries:
            sid = entry.get("id")
            if not sid:
                continue
            out[sid] = Source(
                id=sid,
                name=entry.get("name") or sid,
                domain=entry.get("domain") or "",
                entry_kind=entry.get("entry_kind") or "",
                description=entry.get("description") or "",
                join_keys=list(entry.get("join_keys") or []),
                primary_keys=list(entry.get("primary_keys") or []),
                geography=list(entry.get("geography") or []),
                raw=entry,
            )
        return out

    @cached_property
    def datasets(self) -> dict[str, Dataset]:
        out: dict[str, Dataset] = {}

        for row in self._datasets_csv:
            ds_id = row.get("id")
            if not ds_id:
                continue
            out[ds_id] = Dataset(
                id=ds_id,
                source_id=row.get("source_id") or "",
                name=row.get("name") or ds_id,
                entry_kind=row.get("entry_kind") or "",
                time_index=row.get("time_index") or None,
                time_grain=_split_list(row.get("time_grain")),
                primary_keys=_split_list(row.get("primary_keys")),
                join_keys=_split_list(row.get("join_keys")),
                field_schema=row.get("field_schema") or None,
                is_catalog=True,
                raw=dict(row),
            )

        # For sources that are single-dataset (corpus / registry / time-series /
        # dataset-dump) and have no catalog rows, surface the source itself as a
        # dataset. The source_id == dataset_id in this case. Skip multi-dataset
        # providers (panel sources, or any source that already has catalog rows
        # under it).
        sources_with_catalog = {ds.source_id for ds in out.values()}
        for sid, source in self.sources.items():
            if sid in out:
                continue
            if source.entry_kind == "panel":
                continue
            if sid in sources_with_catalog:
                continue
            out[sid] = Dataset(
                id=sid,
                source_id=sid,
                name=source.name,
                entry_kind=source.entry_kind,
                time_index=None,
                time_grain=[],
                primary_keys=source.primary_keys,
                join_keys=source.join_keys,
                field_schema=None,
                is_catalog=False,
                raw=source.raw,
            )
        return out

    @cached_property
    def fields_by_dataset(self) -> dict[str, list[Field]]:
        out: dict[str, list[Field]] = {}
        for row in self._fields_csv:
            ds_id = row.get("dataset_id") or ""
            out.setdefault(ds_id, []).append(
                Field(
                    source_id=row.get("source_id") or "",
                    dataset_id=ds_id,
                    name=row.get("field_name") or "",
                    type=row.get("type") or None,
                    role=row.get("role") or None,
                    join_key=row.get("join_key") or None,
                    unit=row.get("unit") or None,
                    required=_truthy(row.get("required")),
                    description=row.get("description") or None,
                )
            )
        return out

    @cached_property
    def join_keys(self) -> dict[str, JoinKey]:
        out: dict[str, JoinKey] = {}
        for row in self._join_keys_csv:
            name = row.get("join_key")
            if not name:
                continue
            out[name] = JoinKey(
                name=name,
                entity_type=row.get("entity_type") or None,
                pattern=row.get("pattern") or None,
                examples=_split_list(row.get("examples")),
                description=row.get("description") or None,
            )
        return out

    # ---------------------------------------------------------------- meta

    def commit_hash(self) -> str | None:
        """Return the datasources repo HEAD commit, or None if git is unavailable."""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def remote_url(self) -> str | None:
        """Return ``origin``'s remote URL, or None when unavailable."""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def is_dirty(self) -> bool | None:
        """Return True when the registry working tree has uncommitted changes.

        Returns None when git is unavailable. A True value combined with a
        commit hash means the locked commit does not represent what the run
        actually saw.
        """
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            return bool(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def healthcheck(
        self,
        *,
        min_sources: int = 1,
        min_datasets: int = 1,
        min_join_keys: int = 1,
    ) -> dict[str, Any]:
        """Single-call diagnostic for `deep-quant query-datasources --healthcheck`.

        Returns counts, registry commit, and an explicit ``warnings`` list
        plus an ``ok`` flag. Empties masquerade as a passing healthcheck if
        callers only look at the count totals; the warnings catch the
        common failure modes:

        - No sources loaded at all (registry repo missing or generate.py
          never run).
        - Sources present but datasets / join-keys empty (catalog generation
          half-finished, or the registry moved to a sources-only schema
          without the downstream consumer being told).
        - ``require_commit_hash: true`` configured but the datasources
          repo isn't a git checkout, so a research run cannot be locked.
        """
        commit = self.commit_hash()
        counts = {
            "sources": len(self.sources),
            "datasets": len(self.datasets),
            "fields": sum(len(v) for v in self.fields_by_dataset.values()),
            "join_keys": len(self.join_keys),
        }
        warnings_list: list[str] = []

        if counts["sources"] < min_sources:
            warnings_list.append(
                f"only {counts['sources']} sources loaded (expected >= {min_sources}); "
                "check that the datasources repo exists at the configured path and "
                "scripts/generate.py has been run."
            )
        else:
            # Sources are present; partial / empty downstream tables suggest
            # a half-built or stale catalog.
            if counts["datasets"] < min_datasets:
                warnings_list.append(
                    f"{counts['sources']} sources loaded but only {counts['datasets']} "
                    "datasets; the catalog may be incomplete or generated/datasets.csv "
                    "may be missing."
                )
            if counts["join_keys"] < min_join_keys:
                warnings_list.append(
                    f"{counts['sources']} sources loaded but only {counts['join_keys']} "
                    "join keys; generated/join-keys.csv may be missing or empty."
                )

        requires_commit = bool(self._versioning_cfg.get("require_commit_hash"))
        if requires_commit and not commit:
            warnings_list.append(
                "config requires a datasources registry commit hash, but the "
                "datasources repo is not a git checkout. Research runs cannot be "
                "locked or reproduced."
            )

        return {
            "config_path": str(self.config_path) if self.config_path else None,
            "repo_path": str(self.repo_path),
            "generated_path": str(self.generated_path),
            "registry_commit": commit,
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "counts": counts,
            "requires_commit_hash": requires_commit,
            "warnings": warnings_list,
            "ok": not warnings_list,
        }

    def snapshot(self, dataset_ids: list[str]) -> dict[str, Any]:
        """Build a registry-lock.yaml block for a research run.

        Records enough provenance for another machine to reproduce the run:
        commit hash, remote URL, and whether the working tree was dirty when
        the snapshot was taken. A hash against an unpushed local commit is
        not reproducible; surfacing remote_url + dirty_tree makes that
        explicit instead of silent.
        """
        commit = self.commit_hash()
        remote = self.remote_url()
        dirty = self.is_dirty()
        if self._versioning_cfg.get("require_commit_hash") and not commit:
            raise RegistryError(
                "config requires datasources commit hash but git is unavailable "
                f"at {self.repo_path}. Initialise the repo as a git checkout."
            )
        warnings: list[str] = []
        if commit and dirty:
            warnings.append(
                "datasources working tree had uncommitted changes when this run "
                "was locked; the recorded commit does not represent what the run "
                "actually saw."
            )
        if commit and not remote:
            warnings.append(
                "datasources repo has no remote configured; the commit hash is "
                "only meaningful on this machine."
            )
        return {
            "repo": "datasources",
            "path": str(self.repo_path),
            "remote_url": remote,
            "commit": commit,
            "dirty_tree": dirty,
            "snapshot_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "warnings": warnings,
            "datasets": [
                {"dataset_id": did, "registry_commit": commit}
                for did in dataset_ids
            ],
        }


_DEFAULT_CLIENT: RegistryClient | None = None


def get_client(
    config_path: Path | str | None = None,
    repo_path: Path | str | None = None,
    *,
    refresh: bool = False,
) -> RegistryClient:
    """Return a cached default RegistryClient.

    Pass `refresh=True` to force reloading; pass an explicit `repo_path` or
    `config_path` to bypass the cache.
    """
    global _DEFAULT_CLIENT
    if config_path is None and repo_path is None and not refresh and _DEFAULT_CLIENT is not None:
        return _DEFAULT_CLIENT
    client = RegistryClient(config_path=config_path, repo_path=repo_path)
    if config_path is None and repo_path is None:
        _DEFAULT_CLIENT = client
    return client
