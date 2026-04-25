"""Tests for `testql.adapters.sql.dialect_resolver`."""

from __future__ import annotations

import pytest

from testql.adapters.sql.dialect_resolver import (
    DEFAULT_DIALECT,
    SUPPORTED_DIALECTS,
    SqlglotMissing,
    has_sqlglot,
    is_supported,
    normalize_dialect,
    transpile,
)


class TestNormalize:
    def test_default_when_empty(self):
        assert normalize_dialect(None) == DEFAULT_DIALECT
        assert normalize_dialect("") == DEFAULT_DIALECT

    def test_lowercases(self):
        assert normalize_dialect("Postgres") == "postgres"

    def test_aliases(self):
        assert normalize_dialect("postgresql") == "postgres"
        assert normalize_dialect("pg") == "postgres"
        assert normalize_dialect("tsql") == "mssql"
        assert normalize_dialect("mariadb") == "mysql"

    def test_unknown_passthrough(self):
        assert normalize_dialect("crystaldb") == "crystaldb"


class TestIsSupported:
    def test_known(self):
        assert is_supported("postgres")
        assert is_supported("PostgreSQL")
        assert is_supported("sqlite")

    def test_unknown(self):
        assert not is_supported("crystaldb")

    def test_empty_returns_false_or_default(self):
        # Default dialect is sqlite which IS in the supported set.
        assert is_supported(None) is True


class TestSupportedDialectsConstant:
    def test_includes_canonical_names(self):
        for name in ("postgres", "sqlite", "mysql", "mssql"):
            assert name in SUPPORTED_DIALECTS


class TestTranspile:
    def test_raises_when_sqlglot_missing(self, monkeypatch):
        monkeypatch.setattr(
            "testql.adapters.sql.dialect_resolver.has_sqlglot", lambda: False
        )
        with pytest.raises(SqlglotMissing):
            transpile("SELECT 1", "postgres", "sqlite")

    @pytest.mark.skipif(not has_sqlglot(), reason="sqlglot not installed")
    def test_round_trip_select(self):
        out = transpile("SELECT 1", "postgres", "sqlite")
        assert "select" in out.lower()

    @pytest.mark.skipif(not has_sqlglot(), reason="sqlglot not installed")
    def test_passthrough_same_dialect(self):
        sql = "SELECT id FROM users"
        out = transpile(sql, "postgres", "postgres")
        # Either identical or canonicalised; must still be a SELECT.
        assert "SELECT" in out.upper()
