"""SQL DDL → TestPlan IR.

Reads one or more `CREATE TABLE` statements (via the SQL adapter's
`parse_ddl`) and emits a CRUD coverage scenario:

    * one schema fixture (`sql.schema`)
    * a `count(*)` query per table
    * a `select * limit 5` smoke query per table
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from testql.adapters.sql.ddl_parser import ParsedDDL, Table, parse_ddl
from testql.adapters.sql.fixtures import SchemaFixture
from testql.ir import Assertion, ScenarioMetadata, SqlStep, TestPlan

from .base import BaseSource, SourceLike


def _load_sql_text(source: SourceLike) -> str:
    if isinstance(source, dict):
        return str(source.get("sql", ""))
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    if "\n" not in source and Path(source).is_file():
        return Path(source).read_text(encoding="utf-8")
    return source


def _crud_steps(table: Table, dialect: Optional[str]) -> list[SqlStep]:
    count_step = SqlStep(
        name=f"count_{table.name}",
        query=f"SELECT COUNT(*) FROM {table.name}",
        dialect=dialect,
        asserts=[Assertion(field=f"count_{table.name}", op=">=", expected=0)],
    )
    sample_step = SqlStep(
        name=f"sample_{table.name}",
        query=f"SELECT * FROM {table.name} LIMIT 5",
        dialect=dialect,
        asserts=[Assertion(field=f"sample_{table.name}.length", op="<=", expected=5)],
    )
    return [count_step, sample_step]


def _schema_fixture_from_ddl(ddl: ParsedDDL) -> SchemaFixture:
    fx = SchemaFixture()
    for t in ddl.tables:
        fx.tables.append(t)
    return fx


@dataclass
class SqlSource(BaseSource):
    """`*.sql` DDL → TestPlan with CRUD coverage queries."""

    name: str = "sql"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (".sql", ".ddl"))
    dialect: Optional[str] = None

    def load(self, source: SourceLike) -> TestPlan:
        sql = _load_sql_text(source)
        ddl = parse_ddl(sql, dialect=self.dialect)
        plan = TestPlan(metadata=ScenarioMetadata(
            name=f"CRUD coverage ({len(ddl.tables)} tables)",
            type="sql",
            extra={"source": "sql", "dialect": self.dialect or "sqlite"},
        ))
        plan.fixtures.append(_schema_fixture_from_ddl(ddl).to_fixture())
        for table in ddl.tables:
            plan.steps.extend(_crud_steps(table, self.dialect))
        return plan


__all__ = ["SqlSource"]
