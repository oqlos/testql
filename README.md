# TestQL — Interface Query Language for Testing

TestQL is a declarative DSL for testing GUI, REST API, and hardware encoder interfaces.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Run a scenario
testql scenarios/tests/test-api.tql --url http://localhost:8101

# Dry-run (parse + validate only)
testql scenarios/views/connect-id-barcode.tql --dry-run

# JSON output
testql scenarios/tests/test-api.tql --output json
```

## Language Reference

```
# Variables
SET <name> <value>
GET <name>

# Logging
LOG <message>

# API calls
API GET "/path"
API POST "/path" {"key": "value"}
ASSERT_STATUS <code>
ASSERT_OK
ASSERT_CONTAINS "<text>"
ASSERT_JSON <path> <op> <value>

# Navigation (GUI)
NAVIGATE <path>
WAIT <ms>
CLICK <selector>
INPUT <selector> <text>

# Encoder
ENCODER_ON / ENCODER_OFF / ENCODER_SCROLL / ENCODER_CLICK / ENCODER_STATUS

# Script composition
INCLUDE <file>
```

## Scenarios

Scenarios are `.tql` files organized by category:

- `scenarios/tests/` — automated test suites
- `scenarios/views/` — GUI view tests
- `scenarios/diagnostics/` — system diagnostic scripts
- `scenarios/examples/` — usage examples
- `scenarios/recordings/` — recorded sessions