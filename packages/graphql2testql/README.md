# graphql2testql

GraphQL contract adapter and SDL generator source for [TestQL](../../README.md),
packaged as a standalone plugin.

## What it provides

- **`graphql` DSL adapter** — parses and renders `*.graphql.testql.yaml`
  contract scenarios (queries, mutations, subscriptions). Registered
  automatically through the `testql.plugins` entry point.
- **`graphql` generator source** — converts a GraphQL SDL schema into a
  TestPlan of smoke queries (one per top-level type). Registered through the
  `testql.sources` entry point and resolved lazily by
  `testql.generators.sources.get_source("graphql")`.

## Install

```bash
pip install graphql2testql          # adapter + source
pip install graphql2testql[sdl]     # + graphql-core for canonical SDL parsing
```

No imports or configuration needed — installing the package is enough for
`testql` to pick up the adapter and source.

## Development

```bash
pip install -e packages/graphql2testql
pytest packages/graphql2testql/tests
```
