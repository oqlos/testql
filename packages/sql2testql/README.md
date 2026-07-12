# sql2testql

SQL contract adapter and generator source for [TestQL](../../README.md),
packaged as a standalone plugin.

## What it provides

- **`sql` DSL adapter** — parses and renders `*.sql.testql.yaml` contract
  scenarios (queries, captures, schema/connection fixtures). Registered
  automatically through the `testql.plugins` entry point.
- **`sql` generator source** — converts a DDL script into a TestPlan (one
  smoke query per table plus a schema fixture). Registered through the
  `testql.sources` entry point and resolved lazily by
  `testql.generators.sources.get_source("sql")`.
- **Query analysis** — `analyze_query`/`classify` extract tables, columns,
  and statement kinds from raw SQL.

DDL parsing and dialect resolution live in core (`testql.sql_schema`),
because the meta coverage analyzer works even without this adapter installed.

## Install

```bash
pip install sql2testql            # adapter + source
pip install sql2testql[sqlglot]   # + sqlglot for AST parsing and transpilation
```

No imports or configuration needed — installing the package is enough for
`testql` to pick up the adapter and source.

## Development

```bash
pip install -e packages/sql2testql
pytest packages/sql2testql/tests
```
