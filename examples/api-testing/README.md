# API Testing with TestQL

This example demonstrates REST API testing using TestQL's TestTOON tabular format.

## Files

- `health-check.testql.toon.yaml` — Basic API health check with assertions
- `crud-workflow.testql.toon.yaml` — Full CRUD workflow example
- `run.sh` — Execute the scenarios

## Usage

```bash
# Run with default URL (http://localhost:8101)
./run.sh

# Run against a specific API
./run.sh http://localhost:3000
```

## Concepts demonstrated

- **Variables**: `SET base_url`, `${base_url}` interpolation
- **HTTP methods**: GET, POST, PUT, DELETE
- **Assertions**: status code, JSON path, contains
- **Capture**: store response values for chaining
