"""Compatibility tests for legacy c2004 OQL path mapping and new .testql.toon.yaml format."""

from __future__ import annotations


from testql.commands.encoder_routes import OQL_DIR, _normalize_oql_path, _resolve_oql_path


def test_normalize_legacy_test_path():
    result = _normalize_oql_path("db/dsl/oql/tests/test-api.oql")
    # May map to .testql.toon.yaml if available on disk
    assert result.startswith("c2004/views/test-api")


def test_normalize_legacy_view_path():
    result = _normalize_oql_path("db/dsl/oql/tests/views/connect-id-barcode.oql")
    assert result.startswith("c2004/views/views/connect-id-barcode")


def test_normalize_testql_prefixed_path():
    result = _normalize_oql_path("testql/scenarios/c2004/views/test-api.oql")
    assert result.startswith("c2004/views/test-api")


def test_normalize_passthrough_diagnostics_path():
    result = _normalize_oql_path("diagnostics/full-diagnostic.oql")
    # May resolve to .testql.toon.yaml if file exists
    assert result.startswith("diagnostics/full-diagnostic")


def test_normalize_testtoon_path():
    """New format paths should pass through unchanged."""
    result = _normalize_oql_path("diagnostics/backend-diagnostic.testql.toon.yaml")
    assert result == "diagnostics/backend-diagnostic.testql.toon.yaml"


def test_resolve_new_format():
    """Verify .testql.toon.yaml files are discoverable."""
    normalized_path, resolved_path = _resolve_oql_path("diagnostics/backend-diagnostic.testql.toon.yaml")
    assert normalized_path == "diagnostics/backend-diagnostic.testql.toon.yaml"
    assert resolved_path == (OQL_DIR / normalized_path).resolve()
    assert resolved_path.is_file()