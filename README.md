# TestQL — Interface Query Language for Testing

TestQL is a declarative DSL (Domain Specific Language) for testing GUI, REST API, and hardware encoder interfaces. It provides a simple, readable syntax for writing automated tests without programming overhead.

## Installation

```bash
# Install from source
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Requirements

- Python 3.10+
- HTTPX for API testing
- Playwright for GUI testing (optional)

## Quick Start

```bash
# Run a test scenario
testql scenarios/tests/test-api.tql --url http://localhost:8101

# Dry-run (parse + validate only)
testql scenarios/views/connect-id-barcode.tql --dry-run

# JSON output for CI integration
testql scenarios/tests/test-api.tql --output json

# Run with verbose logging
testql scenarios/tests/test-api.tql --verbose
```

## Language Reference

### Variables

```testql
SET api_url "http://localhost:8101"
SET timeout 5000
GET api_url              # Prints variable value
```

Variables support `${var}` and `$var` interpolation:

```testql
SET base_url "http://localhost:8101"
API GET "${base_url}/api/devices"
```

### Logging

```testql
LOG "Starting test suite"
LOG "Current value: ${var}"
```

### API Commands

```testql
# HTTP methods
API GET "/api/v3/data/devices"
API POST "/api/v3/scenarios" {"id": "ts1", "name": "Test"}
API PUT "/api/v3/devices/123" {"status": "active"}
API DELETE "/api/v3/scenarios/old"
```

### Assertions

```testql
# Status code assertions
ASSERT_STATUS 200
ASSERT_OK                  # Shorthand for 2xx status

# Content assertions
ASSERT_CONTAINS "device"
ASSERT_CONTAINS "status": "ok"

# JSON path assertions
ASSERT_JSON data.length > 0
ASSERT_JSON devices[0].id == "dev-001"
ASSERT_JSON status != "error"
```

**Operators:** `==`, `!=`, `>`, `>=`, `<`, `<=`

### GUI Navigation (Playwright)

```testql
# Navigation
NAVIGATE "/connect-workshop"
NAVIGATE "${base_url}/devices"

# Interaction
WAIT 500
CLICK "[data-action='search']"
INPUT "#search-input" "drager"
CLICK "button[type='submit']"

# Assertions
ASSERT_VISIBLE "[data-testid='results']"
ASSERT_TEXT "#status" "Connected"
```

### Hardware Encoder Commands

```testql
ENCODER_ON                    # Activate encoder mode
ENCODER_FOCUS column1         # Focus specific column
ENCODER_SCROLL 3              # Scroll 3 steps
ENCODER_CLICK                 # Confirm (single click)
ENCODER_DBLCLICK              # Cancel (double click)
ENCODER_PAGE_NEXT             # Next page
ENCODER_PAGE_PREV             # Previous page
ENCODER_STATUS                # Print current encoder state
ENCODER_OFF                   # Deactivate encoder mode
```

### Script Composition

```testql
# Include common setup
INCLUDE "common-setup.tql"

# Include relative paths
INCLUDE "../helpers/auth.tql"
```

### Control Flow (Planned)

```testql
IF status == "ready"
  LOG "System ready"
ELSE ERROR "System not ready"

LABEL start
REPEAT 3 {
  API GET "/api/ping"
}
GOTO start
```

## Project Structure

```
testql/
├── testql/
│   ├── cli.py           # Command-line interface
│   ├── base.py          # Base test runner
│   ├── commands/        # Command implementations
│   ├── runners/         # Test execution runners
│   └── reporters/       # Output formatters
├── scenarios/           # Sample test scenarios
│   ├── tests/          # Automated test suites
│   ├── views/          # GUI view tests
│   ├── diagnostics/    # System diagnostic scripts
│   ├── examples/       # Usage examples
│   └── recordings/     # Recorded test sessions
├── docs/
│   ├── testql-spec.md  # Full language specification
│   └── recipes/        # Common testing patterns
└── tests/              # Unit tests
```

## Scenario Organization

TestQL scenarios are `.tql` files organized by category:

| Directory | Purpose | Example |
|-----------|---------|---------|
| `scenarios/tests/` | API/integration tests | `test-api.tql` |
| `scenarios/views/` | GUI view tests | `connect-id-barcode.tql` |
| `scenarios/diagnostics/` | System checks | `health-check.tql` |
| `scenarios/examples/` | Learning samples | `hello-world.tql` |
| `scenarios/recordings/` | Recorded sessions | `user-flow-1.tql` |

## CLI Options

```bash
testql <file> [options]

Options:
  --url <url>         Base URL for API tests (default: http://localhost:8101)
  --dry-run           Parse and validate only, don't execute
  --output <format>   Output format: text (default), json, junit
  --verbose           Enable verbose logging
  --timeout <ms>      Default timeout for operations
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=testql

# Run specific test file
pytest tests/test_runner.py -v
```

## Example Scenario

```testql
# scenarios/tests/test-api.tql

SET base_url "http://localhost:8101"
LOG "Testing device API"

# Test GET endpoint
API GET "${base_url}/api/v3/data/devices"
ASSERT_OK
ASSERT_JSON data.length > 0

# Test POST endpoint
API POST "${base_url}/api/v3/scenarios" {"name": "Test Scenario"}
ASSERT_STATUS 201
ASSERT_JSON data.id != null

LOG "All tests passed!"
```

## Documentation

- [TestQL Specification](docs/testql-spec.md) — Complete language reference
- [Recipes](docs/recipes/) — Common testing patterns and examples

## License

Apache-2.0