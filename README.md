# TestQL — Interface Query Language for Testing


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.31-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$7.50-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-36.5h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $7.5000 (62 commits)
- 👤 **Human dev:** ~$3650 (36.5h @ $100/h, 30min dedup)

Generated on 2026-04-26 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-testql-blue) ![Version](https://img.shields.io/badge/version-1.2.17-blue) ![Python](https://img.shields.io/badge/python-3.10+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)

TestQL is a declarative DSL (Domain Specific Language) for testing GUI, REST API, and hardware encoder interfaces. It provides a simple, readable syntax for writing automated tests without programming overhead.

### What's new in 0.6.18

- **Executor Refactoring**: Complete implementation of CLI/Shell, GUI, and Unit test execution
- **CommandDispatcher**: New centralized command dispatcher with auto-discovery and better error messages
- **Test Coverage**: Increased from 16% to 65% (target: ≥50% achieved)
- **Code Quality**: All CC hotspots resolved, god modules eliminated
- **New Test Mixins**: Shell, GUI, and Unit execution mixins with 39 new tests

### Recent Improvements (0.6.7 - 0.6.17)

- **CLI/Shell Execution**: `SHELL`, `EXEC`, `RUN` commands with exit code and stdout/stderr assertions
- **GUI Execution**: Playwright/Selenium support with `GUI_START`, `GUI_CLICK`, `GUI_INPUT`, etc.
- **Unit Test Execution**: `UNIT_PYTEST`, `UNIT_ASSERT`, `UNIT_IMPORT` for Python test integration
- **Architecture**: Modular interpreter structure with auto-discovery of command handlers
- **OpenAPI**: 7 endpoints auto-generated with FastAPI integration
- **Quality Pipeline**: pyqual.yaml with 65% coverage target, vallm validation at 64.6%



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


## Artifact Discovery, Topology, and Web Inspection

TestQL can now inspect codebases, manifests, and opt-in live URLs, then write structured topology and result artifacts for humans, CI, and LLM workflows.

```bash
# Discover local artifact types
python3 -m testql.cli discover ./testql --format json

# Build a topology graph from discovered artifacts
python3 -m testql.cli topology ./testql --format toon

# Inspect a live web page and write all data/metadata to .testql
python3 -m testql.cli inspect https://tom.sapletta.com/ \
  --scan-network \
  --out-dir .testql
```

The `.testql/` artifact bundle contains:

```text
metadata.json
topology.{json,yaml,toon.yaml}
result.{json,yaml,toon.yaml}
refactor-plan.{json,yaml,toon.yaml}
inspection.{json,yaml,toon.yaml}
summary.md
```

Live URL inspection currently extracts:

- **HTTP metadata**: status code, final URL, content type.
- **Page schema**: title, links, assets, forms.
- **Topology graph**: page, link, asset, form, interface, evidence nodes.
- **Structured results**: web checks for status, title, links, assets, forms.
- **Reports**: TOON/YAML/JSON plus NLP summary.

Example:

```bash
examples/web-inspection-dot-testql/run.sh https://tom.sapletta.com/
```

Current capabilities:

- **Asset classification**: script, stylesheet, image, icon, preload, link.
- **Bounded link validation**: HEAD checks for all internal links (up to 100).
- **Bounded asset validation**: HEAD checks for all extracted assets.
- **Broken resource detection**: assets or links returning error status are flagged as findings.
- **Bounded sitemap crawl**: fetches up to 10 internal subpages, extracts titles and link counts, adds `subpage` nodes to the topology.
- **Sitemap checks**: crawl coverage, broken subpage detection, duplicate title warnings.
- **Playwright browser inspection** (`--browser`): renders the page in a headless browser, captures console errors, network calls (REST/GraphQL/WebSocket), and JS-rendered DOM.
- **Browser checks**: render detection, console error count, network call capture, title extraction, link/asset/form enumeration.

Current limitations:

- Per-resource validation uses HEAD requests only; full page content is not fetched for linked pages.
- Screenshots, performance metrics, accessibility checks, and auth flows are planned next.

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

### Generate from Topology

Generate executable scenarios from discovered topology paths:

```bash
# Generate TestTOON from the first topology trace
testql generate-topology ./project

# Generate IR JSON from a specific trace
testql generate-topology ./project --trace-id trace.001 --format ir-json

# Write to file with live network scanning
testql generate-topology ./project --scan-network -o scenario.testql.toon.yaml
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

## Examples

| Example | Description |
|---------|-------------|
| [API Testing](examples/api-testing/) | REST API testing with `API GET/POST` and assertions |
| [Artifact Bundle](examples/artifact-bundle/) | Generate `.testql/` bundles via CLI or Python script |
| [Browser Inspection](examples/browser-inspection/) | Headless browser inspection with Playwright |
| [Discovery](examples/discovery/) | Discover artifacts and build project topology |
| [GUI Testing](examples/gui-testing/) | Playwright-based GUI navigation and assertions |
| [Project Echo](examples/project-echo/) | Generate AI context from TestQL + DOQL models |
| [Shell Testing](examples/shell-testing/) | Run shell commands and assert exit codes/output |
| [TestTOON Basics](examples/testtoon-basics/) | Tabular TestTOON format walkthrough |
| [Topology](examples/topology/) | Generate topology graphs from codebases |
| [Web Inspection](examples/web-inspection/) | Inspect live URLs and generate structured reports |
| [Web Inspection + Bundle](examples/web-inspection-dot-testql/) | Full web inspection writing `.testql` artifact bundle |

## Documentation

- [TestQL Specification](docs/testql-spec.md) — Complete language reference
- [Recipes](docs/recipes/) — Common testing patterns and examples

## License

Licensed under Apache-2.0.
