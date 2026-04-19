# TestQL — Interface Query Language for Testing


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.6.4-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$3.00-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-17.2h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $3.0000 (20 commits)
- 👤 **Human dev:** ~$1715 (17.2h @ $100/h, 30min dedup)

Generated on 2026-04-19 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

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
testql scenarios/tests/test-api.testql.toon.yaml --url http://localhost:8101

# Dry-run (parse + validate only)
testql scenarios/views/connect-id-barcode.testql.toon.yaml --dry-run

# JSON output for CI integration
testql scenarios/tests/test-api.testql.toon.yaml --output json

# Run with verbose logging
testql scenarios/tests/test-api.testql.toon.yaml --verbose
```

## API Endpoint Detection

TestQL includes advanced endpoint detection for multiple frameworks:

```bash
# List all detected endpoints in a project
testql endpoints ./my-project
testql endpoints ./my-project --format json
testql endpoints ./my-project --framework fastapi

# Analyze project structure and generate tests
testql analyze ./my-project
testql generate ./my-project
```

### Supported Frameworks

- **FastAPI** — Detects routers, decorators, include_router patterns
- **Flask** — Blueprints, MethodView, route decorators
- **Django** — URL patterns from urls.py
- **Express.js** — JavaScript/TypeScript route definitions
- **OpenAPI/Swagger** — Spec file parsing (JSON/YAML)
- **GraphQL** — Schema and resolver detection
- **WebSocket** — WS endpoint detection

### Endpoint Detection Features

- **Framework Detection**: Automatically identifies the web framework
- **Handler Names**: Extracts function/method names for documentation
- **Parameters**: Detects path/query/body parameters
- **Docstrings**: Uses function docstrings for test descriptions
- **Test Inference**: Analyzes existing tests to discover endpoints

## OpenAPI Generation

Generate OpenAPI 3.0 specifications from your code:

```bash
# Generate OpenAPI spec (YAML format)
testql openapi ./my-project
testql openapi ./my-project --format json

# Generate with contract tests
testql openapi ./my-project --contract-tests

# Custom output file
testql openapi ./my-project -o ./docs/api-spec.yaml --title "My API"
```

### Contract Testing

TestQL generates contract tests from OpenAPI specs:

```yaml
# Auto-generated from openapi.yaml
API[25]{method, endpoint, expected_status}:
  GET, /api/v1/users, 200
  POST, /api/v1/users, 201
  ...

ASSERT[3]{field, operator, expected}:
  content_type, ==, application/json
  schema_valid, ==, true
  status, <, 500
```

## Project Echo (AI Context)

Generate AI-friendly project metadata by combining TESTQL scenarios with DOQL system models:

```bash
# Generate unified project context
testql echo --toon-path testql-scenarios/ --doql-path app.doql.less

# JSON output for LLM consumption
testql echo --toon-path ./tests --doql-path ./app.doql.less --format json -o context.json

# Text output (human-readable)
testql echo --doql-path ./app.doql.less --format text
```

### Echo Layers

| Layer | Source | Content |
|-------|--------|---------|
| **API Contract** | `*.testql.toon.yaml` | Endpoints, methods, assertions |
| **System Model** | `*.doql.less` | Entities, workflows, interfaces |
| **Unified Context** | Combined | Complete project metadata for AI |

### Example Output

```
📦 Project: weboql (0.1.2)

🧠 Type:
  • API (fastapi)

🛠️ Workflows:
  • install: pip install -e .
  • test: pytest
  • run: HARDWARE_MODE=mock weboql-server

🌐 API scenarios:
  • API Health Check (api) - 4 endpoint(s)

💡 LLM suggestions:
  • Run tests: task test
  • Start server: task run
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
INCLUDE "common-setup.testql.toon.yaml"

# Include relative paths
INCLUDE "../helpers/auth.testql.toon.yaml"
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

TestQL scenarios use two formats:
- `*.testql.toon.yaml` — TestTOON tabular format for test sequences (preserves order)
- `*.testql.less` — LESS format for shared test configuration (variables, mixins)

| Directory | Purpose | Example |
|-----------|---------|----------|
| `scenarios/tests/` | API/integration tests | `test-api.testql.toon.yaml` |
| `scenarios/views/` | GUI view tests | `connect-id-barcode.testql.toon.yaml` |
| `scenarios/diagnostics/` | System checks | `health-check.testql.toon.yaml` |
| `scenarios/examples/` | Learning samples | `device-identification.testql.toon.yaml` |
| `scenarios/recordings/` | Recorded sessions | `session-recording.testql.toon.yaml` |

### TestTOON Format

Test files use the tabular TestTOON format where each section declares its schema:

```testtoon
# SCENARIO: API Smoke Test
# TYPE: api
# VERSION: 1.0

API[3]{method, endpoint, status}:
  GET,  /api/v3/health,   200
  GET,  /api/v3/devices,  200
  POST, /api/v3/start,    201

ASSERT[2]{field, op, expected}:
  status,  ==, ok
  count,   >,  0
```

### LESS Configuration

Shared test configuration uses LESS for variables and mixins:

```less
// config.testql.less
@api_url: http://localhost:8101;
@timeout_ms: 30000;

.api-test(@method, @endpoint) {
  method: @method;
  endpoint: @endpoint;
  expect_status: 200;
}
```

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

```testtoon
# scenarios/tests/test-api.testql.toon.yaml
# SCENARIO: Device API Test
# TYPE: api
# VERSION: 1.0

CONFIG[1]{key, value}:
  base_url,  http://localhost:8101

API[2]{method, endpoint, status}:
  GET,   /api/v3/data/devices,   200
  POST,  /api/v3/scenarios,      201

ASSERT[2]{field, op, expected}:
  data.length,  >,   0
  data.id,      !=,  null
```

## Documentation

- [TestQL Specification](docs/testql-spec.md) — Complete language reference
- [Recipes](docs/recipes/) — Common testing patterns and examples

## License

Licensed under Apache-2.0.
