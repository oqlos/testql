# TestQL Language Specification v1.0

## Overview

TestQL (Test Query Language) is a declarative DSL for testing GUI, REST API, and hardware encoder interfaces. Files use the `.testql.toon.yaml` extension (TestTOON tabular format) and `.testql.less` for shared configuration. Legacy formats: `.tql`, `.oql`.

## Variables

```
SET <name> <value>        # SET api_url "http://localhost:8101"
GET <name>                # Print variable value
```

Variables support `${var}` and `$var` interpolation in all arguments.

## Logging

```
LOG <message>             # LOG "test started"
```

## API Commands

```
API GET <url>             # API GET "/api/v3/data/devices"
API POST <url> <json>     # API POST "/api/v3/scenarios" {"id": "ts1"}
API PUT <url> <json>
API DELETE <url>
```

## Assertions

```
ASSERT_STATUS <code>      # ASSERT_STATUS 200
ASSERT_OK                 # Shorthand for 2xx status
ASSERT_CONTAINS "<text>"  # Search in JSON response
ASSERT_JSON <path> <op> <value>  # ASSERT_JSON data.length > 0
```

Operators: `==`, `!=`, `>`, `>=`, `<`, `<=`

## Navigation (GUI)

```
NAVIGATE <path>           # NAVIGATE "/connect-workshop"
WAIT <ms>                 # WAIT 500
CLICK <selector>          # CLICK "[data-action='search']"
INPUT <selector> <text>   # INPUT "#search-input" "drager"
ASSERT_VISIBLE <selector>
ASSERT_TEXT <selector> <text>
```

## Encoder Commands

```
ENCODER_ON                # Activate encoder mode
ENCODER_OFF               # Deactivate
ENCODER_FOCUS <col>       # Focus specific column
ENCODER_SCROLL <n>        # Scroll by n steps
ENCODER_CLICK             # Confirm (single click)
ENCODER_DBLCLICK          # Cancel (double click)
ENCODER_PAGE_NEXT         # Next page
ENCODER_PAGE_PREV         # Previous page
ENCODER_STATUS            # Print current state
```

## Script Composition

```
INCLUDE <file>            # INCLUDE "common-setup.testql.toon.yaml"
```

## Control Flow (planned)

```
IF <condition>
ELSE ERROR <msg>
GOTO <label>
LABEL <name>
REPEAT <n> { ... }
```

## CLI Commands

### Project Echo (AI Context)

Generate AI-friendly project metadata combining TESTQL scenarios with DOQL system models:

```bash
# Generate unified project context
testql echo --toon-path testql-scenarios/ --doql-path app.doql.less

# JSON output for LLM consumption
testql echo --toon-path ./tests --doql-path ./app.doql.less --format json -o context.json

# Text output (human-readable)
testql echo --doql-path ./app.doql.less --format text
```

**Echo Layers:**

| Layer | Source | Content |
|-------|--------|---------|
| API Contract | `*.testql.toon.yaml` | Endpoints, methods, assertions |
| System Model | `*.doql.less` | Entities, workflows, interfaces |
| Unified Context | Combined | Complete metadata for AI |

### Other CLI Commands

```bash
# Run test scenarios
testql run scenario.testql.toon.yaml --url http://localhost:8101
testql suite smoke                          # Run suite from testql.yaml
testql list                                 # List all test files

# Generate and analyze
testql endpoints ./my-project               # Detect API endpoints
testql analyze ./my-project                 # Project structure analysis
testql openapi ./my-project -o spec.yaml    # Generate OpenAPI spec
testql generate ./my-project                # Generate test scenarios

# Initialize project
testql init --type api                      # Create testql.yaml and templates
testql create my-test --type api            # Create new test file
```
