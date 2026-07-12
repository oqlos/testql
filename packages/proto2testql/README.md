# proto2testql

Protocol Buffers contract adapter and generator source for
[TestQL](../../README.md), packaged as a standalone plugin.

## What it provides

- **`proto` DSL adapter** — parses and renders `*.proto.testql.yaml`
  contract scenarios (message validation, round-trips, compatibility).
  Registered automatically through the `testql.plugins` entry point.
- **`proto` generator source** — converts a `.proto` schema into a TestPlan
  (one validation step per message). Registered through the `testql.sources`
  entry point and resolved lazily by
  `testql.generators.sources.get_source("proto")`.
- **Schema compatibility checks** — `compare_schemas` reports breaking
  changes between two `.proto` revisions.

The dependency-free `.proto` descriptor parser and message validator live in
core (`testql.proto_schema`), because the IR runner executes `ProtoStep`s
even without this adapter installed.

## Install

```bash
pip install proto2testql             # adapter + source
pip install proto2testql[protobuf]   # + protobuf runtime for binary serialisation
```

No imports or configuration needed — installing the package is enough for
`testql` to pick up the adapter and source.

## Development

```bash
pip install -e packages/proto2testql
pytest packages/proto2testql/tests
```
