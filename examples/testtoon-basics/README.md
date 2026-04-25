# TestTOON Format Basics

This example demonstrates the TestTOON tabular format used by TestQL.

## Files

- `minimal.testql.toon.yaml` — Minimal valid TestTOON file
- `variables.testql.toon.yaml` — Using variables and interpolation
- `assertions.testql.toon.yaml` — Different assertion types
- `run.sh` — Execute the scenarios

## Format Rules

1. Each section declares its count: `SECTION[N]{column1, column2}`
2. Rows are comma-separated values aligned with columns
3. Comments start with `#`
4. `CONFIG` section holds key-value pairs for variables
