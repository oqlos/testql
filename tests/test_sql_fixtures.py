"""Tests for `testql.adapters.sql.fixtures`."""

from __future__ import annotations

from testql.adapters.sql.fixtures import (
    ConnectionFixture,
    SchemaFixture,
    schema_fixture_from_rows,
)


class TestConnectionFixture:
    def test_to_fixture(self):
        c = ConnectionFixture(url="postgresql://x", dialect="postgres",
                              extra={"timeout": 5})
        f = c.to_fixture()
        assert f.name == "sql.connection"
        assert f.scope == "session"
        assert f.setup["url"] == "postgresql://x"
        assert f.setup["dialect"] == "postgres"
        assert f.setup["timeout"] == 5


class TestSchemaFixtureFromRows:
    def test_basic(self):
        fx = schema_fixture_from_rows([
            {"table": "users", "column": "id", "type": "INT"},
            {"table": "users", "column": "email", "type": "VARCHAR(255)"},
            {"table": "orders", "column": "id", "type": "INT"},
        ])
        assert len(fx.tables) == 2
        users = next(t for t in fx.tables if t.name == "users")
        assert len(users.columns) == 2
        assert users.columns[0].name == "id"

    def test_skips_empty_rows(self):
        fx = schema_fixture_from_rows([
            {"table": "", "column": "id", "type": "INT"},
            {"table": "users", "column": "", "type": "INT"},
            {"table": "users", "column": "id", "type": "INT"},
        ])
        assert len(fx.tables) == 1
        assert fx.tables[0].columns[0].name == "id"

    def test_truthy_flags(self):
        fx = schema_fixture_from_rows([
            {"table": "t", "column": "a", "type": "INT",
             "nullable": "false", "primary_key": "true", "unique": "yes"},
        ])
        col = fx.tables[0].columns[0]
        assert col.nullable is False
        assert col.primary_key is True
        assert col.unique is True

    def test_default_dash_treated_as_none(self):
        fx = schema_fixture_from_rows([
            {"table": "t", "column": "a", "type": "INT", "default": "-"},
        ])
        assert fx.tables[0].columns[0].default is None

    def test_default_value_preserved(self):
        fx = schema_fixture_from_rows([
            {"table": "t", "column": "a", "type": "TIMESTAMP", "default": "now()"},
        ])
        assert fx.tables[0].columns[0].default == "now()"

    def test_to_fixture_shape(self):
        fx = schema_fixture_from_rows([{"table": "t", "column": "a", "type": "INT"}])
        f = fx.to_fixture()
        assert f.name == "sql.schema"
        assert f.scope == "scenario"
        assert f.setup["tables"][0]["name"] == "t"
