# Unit Testing with TestQL

This example demonstrates running Python unit tests using TestQL's unit test execution commands.

## Files

- `test-math.oql` — Basic UNIT_ASSERT and UNIT_IMPORT examples
- `test-pytest.oql` — Run pytest suites and check results
- `run.sh` — Execute the scenarios

## Usage

```bash
# Dry-run (no Python execution)
make dry-run

# Run unit tests
make run
```

## Concepts demonstrated

- `UNIT_IMPORT` — Verify module importability
- `UNIT_ASSERT` — Inline Python assertions
- `UNIT_PYTEST` — Run pytest suites
- Variable interpolation for module paths
