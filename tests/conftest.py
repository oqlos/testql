"""Shared pytest fixtures for the TestQL test suite.

Provides session-scoped caches for repeated expensive operations such as
self-discovery against the project root and the ``testql`` package
directory. Multiple tests call ``discover_path(ROOT)`` which walks the
entire project tree (~1s each); caching keeps the behavior identical
but avoids redundant walks.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from testql.discovery import discover_path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TESTQL_PKG = PROJECT_ROOT / "testql"


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def testql_pkg_dir() -> Path:
    return TESTQL_PKG


@pytest.fixture(scope="session")
def project_root_manifest():
    """Cached discovery manifest for the project root.

    ``discover_path`` is pure over a static directory tree, so session-wide
    caching is safe and trims several seconds from the full test run.
    """
    return discover_path(PROJECT_ROOT)


@pytest.fixture(scope="session")
def testql_pkg_manifest():
    """Cached discovery manifest for the ``testql`` package subdirectory."""
    return discover_path(TESTQL_PKG)
