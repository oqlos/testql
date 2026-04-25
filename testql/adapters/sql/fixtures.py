"""SQL fixture helpers — connection settings + schema declarations.

These are *declarative*: they describe the desired state, not how to reach it.
Execution wiring belongs to a future `testql.interpreter._sql` mixin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from testql.ir import Fixture

from .ddl_parser import Column, Table


@dataclass
class ConnectionFixture:
    """Declarative connection info parsed from CONFIG[connection_url]."""

    url: str
    dialect: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def to_fixture(self) -> Fixture:
        return Fixture(
            name="sql.connection",
            setup={"url": self.url, "dialect": self.dialect, **self.extra},
            scope="session",
        )


@dataclass
class SchemaFixture:
    """Declarative schema collected from SCHEMA section rows."""

    tables: list[Table] = field(default_factory=list)

    def add_column(self, table_name: str, column: Column) -> None:
        table = self._ensure_table(table_name)
        table.columns.append(column)

    def _ensure_table(self, name: str) -> Table:
        for t in self.tables:
            if t.name.lower() == name.lower():
                return t
        new = Table(name=name)
        self.tables.append(new)
        return new

    def to_fixture(self) -> Fixture:
        return Fixture(
            name="sql.schema",
            setup={"tables": [t.to_dict() for t in self.tables]},
            scope="scenario",
        )


def schema_fixture_from_rows(rows: Iterable[dict]) -> SchemaFixture:
    """Build a `SchemaFixture` from SCHEMA[table, column, type, ...] rows."""
    fx = SchemaFixture()
    for row in rows:
        table_name = str(row.get("table", "")).strip()
        col_name = str(row.get("column", "")).strip()
        col_type = str(row.get("type", "")).strip()
        if not (table_name and col_name):
            continue
        fx.add_column(table_name, Column(
            name=col_name,
            type=col_type,
            nullable=_truthy(row.get("nullable"), default=True),
            primary_key=_truthy(row.get("primary_key"), default=False),
            unique=_truthy(row.get("unique"), default=False),
            default=_optional_str(row.get("default")),
        ))
    return fx


def _truthy(value, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in {"true", "yes", "y", "1"}:
        return True
    if s in {"false", "no", "n", "0", "-"}:
        return False
    return default


def _optional_str(value) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s or s == "-":
        return None
    return s


__all__ = [
    "ConnectionFixture",
    "SchemaFixture",
    "schema_fixture_from_rows",
]
