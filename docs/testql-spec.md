# TestQL Language Specification v1.0

## Overview

TestQL (Test Query Language) is a declarative DSL for testing GUI, REST API, and hardware encoder interfaces. Files use the `.testql.toon.yaml` extension (TestTOON tabular format) and `.testql.less` for shared configuration. Legacy formats: `.tql`, `.oql`.

## Variables

```
SET <name> <value>        # SET api_url "http://localhost:8101"
GET <name>                # Print variable value
GETENV <env> [name]       # Read a non-secret environment variable
GETENV_SECRET <env> [name] # Read a secret; redact it from logs and results
```

Variables support `${var}` and `$var` interpolation in all arguments.
Use `GETENV_SECRET` for passwords and API tokens. Secret variables are returned as
`***REDACTED***` in result metadata, and GUI input logging never includes their value.

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

## Native Desktop Commands (Linux)

Control the real OS desktop: monitors, windows, mirror capture, OCR. See [DESKTOP_GUI_E2E.md](./DESKTOP_GUI_E2E.md).

```
DESKTOP_MONITORS
DESKTOP_LIST
DESKTOP_INSPECT "inspect.png"
DESKTOP_CAPTURE "shot.png" [monitor]     # monitor: primary | DP-2 | 0
DESKTOP_DESCRIBE "shot.png"
DESKTOP_ANALYZE "shot.png" [out.json]
DESKTOP_ASSERT_WINDOW "title"
DESKTOP_ASSERT_TEXT "needle" ["shot.png"]
DESKTOP_ASSERT_ELEMENTS 1 ["shot.png"]
DESKTOP_CLICK_TEXT "label" ["shot.png"]
DESKTOP_FOCUS "title"
DESKTOP_CLICK x y
DESKTOP_TYPE "text"
DESKTOP_KEY Return
DESKTOP_LAUNCH "/usr/bin/app" [args]
DESKTOP_STOP
```

On GNOME/Wayland, `DESKTOP_CAPTURE` uses **vdisplay mirror→Xvfb** (no screenshot portal). Metadata: `shot.png.vdisplay.json`.

## Modbus Commands (RTU probe + wizard API)

```
MODBUS probe                                    # use MODBUS_* env (see testql-modbus-probe.py)
MODBUS probe serial=/dev/ttyACM1 baud=9600 device_ids=1,2
MODBUS skip_if_no_port serial=/dev/ttyACM1      # sets modbus_skip_probe when port missing
MODBUS api plan                                 # GET connect-scenario wizard plan (:8096)
MODBUS api runtime-status                       # GET runtime status via scenario proxy
```

After `MODBUS probe`, use `ASSERT_JSON ok == true` and `ASSERT_JSON results.length > 0`.
Set `TESTQL_MODBUS_SKIP=1` to skip failed probes (CI without bench hardware).

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
