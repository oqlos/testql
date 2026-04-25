"""Executor for `SqlStep` — runs a query against an in-memory SQLite database.

The first run per `ExecutionContext` lazily creates a single shared `sqlite3`
connection and applies every `SchemaFixture` attached to `plan.fixtures`. After
that, subsequent steps can `SELECT`, `INSERT`, `UPDATE`, `DELETE` against the
same DB.

For more advanced needs (Postgres, MySQL) wire in a custom `connection_factory`
on the context — this module only handles the default SQLite path.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from testql.base import StepResult, StepStatus
from testql.ir import SqlStep

from ..context import ExecutionContext
from ..interpolation import interp_value
from .base import assemble_result, error_result, step_label


def _get_connection(ctx: ExecutionContext) -> sqlite3.Connection:
    """Lazy-init a shared in-memory SQLite connection."""
    conn = ctx.vars.get("_sql_conn")
    if conn is None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        ctx.vars.set("_sql_conn", conn)
    return conn


def _classify(query: str) -> str:
    head = query.strip().split(None, 1)[0].lower() if query.strip() else ""
    return head


def _execute_query(conn: sqlite3.Connection, query: str) -> dict:
    cur = conn.execute(query)
    if _classify(query) in ("select", "with", "pragma"):
        rows = [dict(r) for r in cur.fetchall()]
        return {"rows": rows, "rowcount": len(rows),
                "columns": [c[0] for c in cur.description or []]}
    conn.commit()
    return {"rows": [], "rowcount": cur.rowcount, "columns": []}


def execute(step: SqlStep, ctx: ExecutionContext) -> StepResult:
    label = step_label(step, "SQL")
    query: Any = interp_value(step.query, ctx.vars)
    if ctx.dry_run:
        return StepResult(name=label, status=StepStatus.PASSED,
                          details={"dry_run": True, "query": query})
    try:
        conn = _get_connection(ctx)
        payload = _execute_query(conn, query)
    except Exception as e:
        return error_result(label, e)
    ctx.last_response = payload
    return assemble_result(label, payload, step.asserts, ctx.dry_run)


__all__ = ["execute"]
