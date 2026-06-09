"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURE_ROOT = Path(__file__).parent / "fixtures"
REGISTRY_MINI = FIXTURE_ROOT / "registry-mini"


@pytest.fixture
def registry_mini_path() -> Path:
    """Path to the tiny three-source registry fixture."""
    return REGISTRY_MINI


@pytest.fixture
def client(registry_mini_path):
    """RegistryClient pointed at the fixture catalog."""
    from deep_quantitative_research.registry import RegistryClient

    return RegistryClient(repo_path=registry_mini_path)
