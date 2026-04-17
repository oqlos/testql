"""Compatibility tests for legacy c2004 IQL path mapping and new .testql.toon.yaml format."""

from __future__ import annotations

from pathlib import Path

from testql.commands.encoder_routes import IQL_DIR, _normalize_iql_path, _resolve_iql_path


def test_normalize_legacy_test_path():
    result = _normalize_iql_path("db/dsl/iql/tests/test-api.iql")
    # May map to .testql.toon.yaml if available on disk
    assert result.startswith("c2004/views/test-api")


def test_normalize_legacy_view_path():
    result = _normalize_iql_path("db/dsl/iql/tests/views/connect-id-barcode.iql")
    assert result.startswith("c2004/views/views/connect-id-barcode")


def test_normalize_testql_prefixed_path():
    result = _normalize_iql_path("testql/scenarios/c2004/views/test-api.iql")
    assert result.startswith("c2004/views/test-api")


def test_normalize_passthrough_diagnostics_path():
    result = _normalize_iql_path("diagnostics/full-diagnostic.iql")
    # May resolve to .testql.toon.yaml if file exists
    assert result.startswith("diagnostics/full-diagnostic")


def test_normalize_testtoon_path():
    """New format paths should pass through unchanged."""
    result = _normalize_iql_path("diagnostics/backend-diagnostic.testql.toon.yaml")
    assert result == "diagnostics/backend-diagnostic.testql.toon.yaml"


def test_resolve_new_format():
    """Verify .testql.toon.yaml files are discoverable."""
    normalized_path, resolved_path = _resolve_iql_path("diagnostics/backend-diagnostic.testql.toon.yaml")
    assert normalized_path == "diagnostics/backend-diagnostic.testql.toon.yaml"
    assert resolved_path == (IQL_DIR / normalized_path).resolve()
    assert resolved_path.is_file()