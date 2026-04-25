"""SqlDSLAdapter — `*.sql.testql.yaml` scenarios → Unified IR.

The on-disk format is a TestTOON variant with SQL-specific sections:

    # SCENARIO: User contract
    # TYPE: sql
    # DIALECT: postgres

    CONFIG[1]{key, value}:
      connection_url, postgresql://localhost/test_db

    SCHEMA[3]{table, column, type}:
      users, id, INT
      users, email, VARCHAR(255)
      users, created_at, TIMESTAMP

    QUERY[2]{name, sql}:
      count_users, SELECT COUNT(*) FROM users
      active_users, SELECT id FROM users WHERE active = true

    ASSERT[3]{query, op, expected}:
      count_users, ==, 100
      active_users.length, >, 0
      active_users[0].id, !=, null

The adapter uses the existing TestTOON parser to do the lexical work, then
translates the section rows into IR nodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from testql.interpreter._testtoon_parser import (
    ToonScript,
    ToonSection,
    parse_testtoon as _parse_testtoon,
)
from testql.ir import Assertion, Capture, Fixture, ScenarioMetadata, SqlStep, Step, TestPlan

from ..base import BaseDSLAdapter, DSLDetectionResult, SourceLike, read_source
from .dialect_resolver import DEFAULT_DIALECT, normalize_dialect
from .fixtures import ConnectionFixture, schema_fixture_from_rows


# ── Section translators ─────────────────────────────────────────────────────


def _config_section(section: ToonSection, dialect: Optional[str]) -> tuple[dict, list[Fixture]]:
    """CONFIG → (config-dict, [ConnectionFixture])."""
    config: dict = {}
    fixtures: list[Fixture] = []
    for row in section.rows:
        key = str(row.get("key", "")).strip()
        value = row.get("value")
        if not key:
            continue
        config[key] = value
    url = config.get("connection_url") or config.get("url")
    if url:
        fixtures.append(ConnectionFixture(url=str(url), dialect=dialect).to_fixture())
    return config, fixtures


def _schema_section(section: ToonSection) -> Fixture:
    return schema_fixture_from_rows(section.rows).to_fixture()


def _query_section(section: ToonSection, dialect: str) -> list[SqlStep]:
    steps: list[SqlStep] = []
    for row in section.rows:
        name = str(row.get("name", "")).strip() or "query"
        sql = _row_query(row)
        if not sql:
            continue
        steps.append(SqlStep(name=name, query=sql, dialect=dialect))
    return steps


def _row_query(row: dict) -> str:
    sql = row.get("sql") or row.get("query") or ""
    return str(sql).strip()


def _assert_section(section: ToonSection, steps_by_name: dict[str, SqlStep]) -> list[Step]:
    """ASSERT[query, op, expected] → asserts attached to matching SqlStep.

    Asserts whose `query` doesn't match any declared query become a synthetic
    `kind=assert` step so they're still represented in the IR.
    """
    orphan_asserts: list[Assertion] = []
    for row in section.rows:
        target = str(row.get("query", "")).strip()
        op = str(row.get("op", "==")).strip()
        expected = row.get("expected")
        assertion = Assertion(field=target, op=op, expected=expected)
        owner = _resolve_owner(target, steps_by_name)
        if owner is not None:
            owner.asserts.append(assertion)
        else:
            orphan_asserts.append(assertion)
    if orphan_asserts:
        return [Step(kind="assert", name="ASSERT", asserts=orphan_asserts)]
    return []


def _resolve_owner(target: str, steps_by_name: dict[str, SqlStep]) -> Optional[SqlStep]:
    """Pick the SqlStep matching the assert's `query` reference.

    Supports `name`, `name.length`, and `name[i].field` styles — only the
    leading identifier needs to match a declared query name.
    """
    base = target.split(".", 1)[0].split("[", 1)[0].strip()
    return steps_by_name.get(base)


# ── ToonScript → TestPlan ───────────────────────────────────────────────────


def _toon_to_plan(toon: ToonScript) -> TestPlan:
    dialect = normalize_dialect(toon.meta.get("dialect")) if toon.meta.get("dialect") else DEFAULT_DIALECT
    metadata = ScenarioMetadata(
        name=toon.meta.get("scenario", ""),
        type=toon.meta.get("type", "sql"),
        version=toon.meta.get("version"),
        extra={k: v for k, v in toon.meta.items()
               if k not in {"scenario", "type", "version", "dialect"}},
    )
    metadata.extra["dialect"] = dialect
    plan = TestPlan(metadata=metadata)
    sql_steps: list[SqlStep] = []
    for section in toon.sections:
        _apply_section(section, plan, sql_steps, dialect)
    # ASSERT sections were collected last; if not yet handled, scan again.
    return plan


def _apply_section(section: ToonSection, plan: TestPlan,
                   sql_steps: list[SqlStep], dialect: str) -> None:
    handler = _SECTION_HANDLERS.get(section.type)
    if handler is None:
        plan.steps.append(Step(kind=section.type.lower(), name=section.type,
                               extra={"rows": list(section.rows)}))
        return
    handler(section, plan, sql_steps, dialect)


def _h_config(section: ToonSection, plan: TestPlan,
              sql_steps: list[SqlStep], dialect: str) -> None:
    cfg, fixtures = _config_section(section, dialect)
    plan.config.update(cfg)
    plan.fixtures.extend(fixtures)


def _h_schema(section: ToonSection, plan: TestPlan,
              sql_steps: list[SqlStep], dialect: str) -> None:
    plan.fixtures.append(_schema_section(section))


def _h_query(section: ToonSection, plan: TestPlan,
             sql_steps: list[SqlStep], dialect: str) -> None:
    new_steps = _query_section(section, dialect)
    sql_steps.extend(new_steps)
    plan.steps.extend(new_steps)


def _h_assert(section: ToonSection, plan: TestPlan,
              sql_steps: list[SqlStep], dialect: str) -> None:
    plan.steps.extend(_assert_section(section, {s.name: s for s in sql_steps if s.name}))


def _h_capture(section: ToonSection, plan: TestPlan,
               sql_steps: list[SqlStep], dialect: str) -> None:
    """Attach `Capture`s to SqlSteps by `query` name (matches assert lookup style)."""
    by_name = {s.name: s for s in sql_steps if s.name}
    for row in section.rows:
        target = str(row.get("query", "") or row.get("step", "")).strip()
        var = str(row.get("var", "")).strip()
        from_path = str(row.get("from", "")).strip()
        owner = by_name.get(target)
        if owner is not None and var and from_path:
            owner.captures.append(Capture(var_name=var, from_path=from_path))


_SECTION_HANDLERS = {
    "CONFIG": _h_config,
    "SCHEMA": _h_schema,
    "QUERY": _h_query,
    "ASSERT": _h_assert,
    "CAPTURE": _h_capture,
}


# ── Renderer (IR → SQL TestTOON) ────────────────────────────────────────────


def _render_meta(metadata: ScenarioMetadata) -> list[str]:
    out = []
    if metadata.name:
        out.append(f"# SCENARIO: {metadata.name}")
    out.append(f"# TYPE: {metadata.type or 'sql'}")
    dialect = metadata.extra.get("dialect")
    if dialect:
        out.append(f"# DIALECT: {dialect}")
    if metadata.version:
        out.append(f"# VERSION: {metadata.version}")
    return out


def _render_config(plan: TestPlan) -> list[str]:
    if not plan.config:
        return []
    lines = [f"CONFIG[{len(plan.config)}]" + "{key, value}:"]
    for k, v in plan.config.items():
        lines.append(f"  {k}, {v}")
    return lines


def _collect_schema_rows(plan: TestPlan) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for fx in plan.fixtures:
        if fx.name != "sql.schema":
            continue
        for table in (fx.setup or {}).get("tables", []):
            for col in table.get("columns", []):
                rows.append((table["name"], col["name"], col["type"]))
    return rows


def _render_schema(plan: TestPlan) -> list[str]:
    rows = _collect_schema_rows(plan)
    if not rows:
        return []
    lines = [f"SCHEMA[{len(rows)}]" + "{table, column, type}:"]
    lines.extend(f"  {t}, {c}, {ty}" for t, c, ty in rows)
    return lines


def _render_queries(plan: TestPlan) -> list[str]:
    sql_steps = [s for s in plan.steps if isinstance(s, SqlStep)]
    if not sql_steps:
        return []
    lines = [f"QUERY[{len(sql_steps)}]" + "{name, sql}:"]
    for s in sql_steps:
        lines.append(f"  {s.name or 'query'}, {s.query}")
    return lines


def _render_asserts(plan: TestPlan) -> list[str]:
    rows: list[tuple[str, str, object]] = []
    for s in plan.steps:
        for a in s.asserts:
            rows.append((a.field, a.op, a.expected))
    if not rows:
        return []
    lines = [f"ASSERT[{len(rows)}]" + "{query, op, expected}:"]
    for q, op, exp in rows:
        lines.append(f"  {q}, {op}, {exp}")
    return lines


def _render_captures(plan: TestPlan) -> list[str]:
    """Emit `CAPTURE[N]{query, var, from}` rows referencing the SqlStep name."""
    rows: list[tuple[str, str, str]] = []
    for s in plan.steps:
        if not isinstance(s, SqlStep) or not s.name:
            continue
        for c in s.captures:
            rows.append((s.name, c.var_name, c.from_path))
    if not rows:
        return []
    lines = [f"CAPTURE[{len(rows)}]" + "{query, var, from}:"]
    for q, var, frm in rows:
        lines.append(f"  {q}, {var}, {frm}")
    return lines


def _render_plan(plan: TestPlan) -> str:
    parts = _render_meta(plan.metadata)
    if parts:
        parts.append("")
    parts.extend(_render_config(plan))
    parts.extend(_render_schema(plan))
    parts.extend(_render_queries(plan))
    parts.extend(_render_asserts(plan))
    parts.extend(_render_captures(plan))
    return "\n".join(parts) + ("\n" if parts else "")


# ── Adapter ─────────────────────────────────────────────────────────────────


@dataclass
class SqlDSLAdapter(BaseDSLAdapter):
    """Adapter for `*.sql.testql.yaml` SQL contract scenarios."""

    name: str = "sql"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (
        ".sql.testql.yaml",
        ".sql.testql.yml",
    ))

    def detect(self, source: SourceLike) -> DSLDetectionResult:
        text, filename = read_source(source)
        for ext in self.file_extensions:
            if filename.lower().endswith(ext):
                return DSLDetectionResult(matches=True, confidence=0.95, reason=f"extension {ext}")
        if "# TYPE: sql" in text or "# DIALECT:" in text:
            return DSLDetectionResult(matches=True, confidence=0.7, reason="SQL header")
        return DSLDetectionResult(matches=False, confidence=0.0, reason="no SQL markers")

    def parse(self, source: SourceLike) -> TestPlan:
        text, filename = read_source(source)
        toon = _parse_testtoon(text, filename=filename)
        return _toon_to_plan(toon)

    def render(self, plan: TestPlan) -> str:
        return _render_plan(plan)


# ── Convenience module-level helpers ─────────────────────────────────────


def parse(source: SourceLike) -> TestPlan:
    return SqlDSLAdapter().parse(source)


def render(plan: TestPlan) -> str:
    return SqlDSLAdapter().render(plan)


__all__ = ["SqlDSLAdapter", "parse", "render"]
