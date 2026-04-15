"""Compatibility tests for legacy c2004 IQL path mapping."""

from __future__ import annotations

from pathlib import Path

from testql.commands.encoder_routes import IQL_DIR, _normalize_iql_path, _resolve_iql_path


def test_normalize_legacy_test_path():
    assert _normalize_iql_path("db/dsl/iql/tests/test-api.iql") == "c2004/views/test-api.iql"


def test_normalize_legacy_view_path():
    assert _normalize_iql_path("db/dsl/iql/tests/views/connect-id-barcode.iql") == "c2004/views/views/connect-id-barcode.iql"


def test_normalize_testql_prefixed_path():
    assert _normalize_iql_path("testql/scenarios/c2004/views/test-api.iql") == "c2004/views/test-api.iql"


def test_normalize_passthrough_diagnostics_path():
    assert _normalize_iql_path("diagnostics/full-diagnostic.iql") == "diagnostics/full-diagnostic.iql"


def test_resolve_legacy_path_to_canonical_file():
    normalized_path, resolved_path = _resolve_iql_path("tests/test-api.iql")

    assert normalized_path == "c2004/views/test-api.iql"
    assert resolved_path == (IQL_DIR / normalized_path).resolve()
    assert resolved_path == Path(IQL_DIR / "c2004/views/test-api.iql").resolve()
    assert resolved_path.is_file()