# TestQL — Interface Query Language for Testing

TestQL with endpoint detection, OpenAPI generation, and AI echo

## Metadata

- **name**: `testql`
- **version**: `0.4.2`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **openapi_title**: testql API v1.0.0
- **generated_from**: pyproject.toml, Taskfile.yml, testql(74), openapi(7 ep), app.doql.less, app.doql.css, pyqual.yaml, goal.yaml, .env.example, src(11 mod), project/(10 analysis files)

## Intent

TestQL with endpoint detection, OpenAPI generation, and AI echo

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`, `app.doql.css`)

```less
// LESS format — define @variables here as needed

app {
  name: testql;
  version: 0.2.1;
}

interface[type="cli"] {
  framework: click;
}
interface[type="cli"] page[name="testql"] {

}

workflow[name="install"] {
  trigger: manual;
  step-1: run cmd=pip install -e .[dev];
}

workflow[name="quality"] {
  trigger: manual;
  step-1: run cmd=pyqual run;
}

workflow[name="quality:fix"] {
  trigger: manual;
  step-1: run cmd=pyqual run --fix;
}

workflow[name="quality:report"] {
  trigger: manual;
  step-1: run cmd=pyqual report;
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=pytest -q;
}

workflow[name="lint"] {
  trigger: manual;
  step-1: run cmd=ruff check .;
}

workflow[name="fmt"] {
  trigger: manual;
  step-1: run cmd=ruff format .;
}

workflow[name="build"] {
  trigger: manual;
  step-1: run cmd=python -m build;
}

workflow[name="clean"] {
  trigger: manual;
  step-1: run cmd=rm -rf build/ dist/ *.egg-info;
}

workflow[name="iql:run"] {
  trigger: manual;
  step-1: run cmd=testql run {{.CLI_ARGS}};
}

workflow[name="iql:shell"] {
  trigger: manual;
  step-1: run cmd=testql shell;
}

workflow[name="doql:adopt"] {
  trigger: manual;
  step-1: run cmd=if ! command -v {{.DOQL_CMD}} >/dev/null 2>&1; then
echo "⚠️  doql not installed. Install: pip install doql"
exit 1
fi;
  step-2: run cmd={{.DOQL_CMD}} adopt {{.PWD}} --output app.doql.css --force;
  step-3: run cmd={{.DOQL_CMD}} export --format less -o {{.DOQL_OUTPUT}};
  step-4: run cmd=echo "✅ Project structure captured in {{.DOQL_OUTPUT}}";
}

workflow[name="doql:validate"] {
  trigger: manual;
  step-1: run cmd=if [ ! -f "{{.DOQL_OUTPUT}}" ]; then
echo "❌ {{.DOQL_OUTPUT}} not found. Run: task doql:adopt"
exit 1
fi;
  step-2: run cmd={{.DOQL_CMD}} validate;
}

workflow[name="doql:doctor"] {
  trigger: manual;
  step-1: run cmd={{.DOQL_CMD}} doctor;
}

workflow[name="doql:build"] {
  trigger: manual;
  step-1: run cmd=if [ ! -f "{{.DOQL_OUTPUT}}" ]; then
echo "❌ {{.DOQL_OUTPUT}} not found. Run: task doql:adopt"
exit 1
fi;
  step-2: run cmd=# Regenerate LESS from CSS if CSS exists
if [ -f "app.doql.css" ]; then
{{.DOQL_CMD}} export --format less -o {{.DOQL_OUTPUT}}
fi;
  step-3: run cmd={{.DOQL_CMD}} build app.doql.css --out build/;
}

workflow[name="docker:build"] {
  trigger: manual;
  step-1: run cmd=docker-compose build;
}

workflow[name="docker:up"] {
  trigger: manual;
  step-1: run cmd=docker-compose up -d;
}

workflow[name="docker:down"] {
  trigger: manual;
  step-1: run cmd=docker-compose down;
}

workflow[name="publish"] {
  trigger: manual;
  step-1: run cmd=twine upload dist/*;
}

workflow[name="help"] {
  trigger: manual;
  step-1: run cmd=task --list;
}

deploy {
  target: docker-compose;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
}
```

```css
app {
  name: "testql";
  version: "0.2.1";
}

interface[type="cli"] {
  framework: click;
}
interface[type="cli"] page[name="testql"] {

}

workflow[name="install"] {
  trigger: "manual";
  step-1: run cmd=pip install -e .[dev];
}

workflow[name="quality"] {
  trigger: "manual";
  step-1: run cmd=pyqual run;
}

workflow[name="quality:fix"] {
  trigger: "manual";
  step-1: run cmd=pyqual run --fix;
}

workflow[name="quality:report"] {
  trigger: "manual";
  step-1: run cmd=pyqual report;
}

workflow[name="test"] {
  trigger: "manual";
  step-1: run cmd=pytest -q;
}

workflow[name="lint"] {
  trigger: "manual";
  step-1: run cmd=ruff check .;
}

workflow[name="fmt"] {
  trigger: "manual";
  step-1: run cmd=ruff format .;
}

workflow[name="build"] {
  trigger: "manual";
  step-1: run cmd=python -m build;
}

workflow[name="clean"] {
  trigger: "manual";
  step-1: run cmd=rm -rf build/ dist/ *.egg-info;
}

workflow[name="iql:run"] {
  trigger: "manual";
  step-1: run cmd=testql run {{.CLI_ARGS}};
}

workflow[name="iql:shell"] {
  trigger: "manual";
  step-1: run cmd=testql shell;
}

workflow[name="doql:adopt"] {
  trigger: "manual";
  step-1: run cmd=if ! command -v {{.DOQL_CMD}} >/dev/null 2>&1; then
  echo "⚠️  doql not installed. Install: pip install doql"
  exit 1
fi;
  step-2: run cmd={{.DOQL_CMD}} adopt {{.PWD}} --output app.doql.css --force;
  step-3: run cmd={{.DOQL_CMD}} export --format less -o {{.DOQL_OUTPUT}};
  step-4: run cmd=echo "✅ Project structure captured in {{.DOQL_OUTPUT}}";
}

workflow[name="doql:validate"] {
  trigger: "manual";
  step-1: run cmd=if [ ! -f "{{.DOQL_OUTPUT}}" ]; then
  echo "❌ {{.DOQL_OUTPUT}} not found. Run: task doql:adopt"
  exit 1
fi;
  step-2: run cmd={{.DOQL_CMD}} validate;
}

workflow[name="doql:doctor"] {
  trigger: "manual";
  step-1: run cmd={{.DOQL_CMD}} doctor;
}

workflow[name="doql:build"] {
  trigger: "manual";
  step-1: run cmd=if [ ! -f "{{.DOQL_OUTPUT}}" ]; then
  echo "❌ {{.DOQL_OUTPUT}} not found. Run: task doql:adopt"
  exit 1
fi;
  step-2: run cmd=# Regenerate LESS from CSS if CSS exists
if [ -f "app.doql.css" ]; then
  {{.DOQL_CMD}} export --format less -o {{.DOQL_OUTPUT}}
fi;
  step-3: run cmd={{.DOQL_CMD}} build app.doql.css --out build/;
}

workflow[name="docker:build"] {
  trigger: "manual";
  step-1: run cmd=docker-compose build;
}

workflow[name="docker:up"] {
  trigger: "manual";
  step-1: run cmd=docker-compose up -d;
}

workflow[name="docker:down"] {
  trigger: "manual";
  step-1: run cmd=docker-compose down;
}

workflow[name="publish"] {
  trigger: "manual";
  step-1: run cmd=twine upload dist/*;
}

workflow[name="help"] {
  trigger: "manual";
  step-1: run cmd=task --list;
}

deploy {
  target: docker-compose;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: ".env";
}
```

### Source Modules

- `testql._base_fallback`
- `testql.base`
- `testql.cli`
- `testql.doql_parser`
- `testql.echo_schemas`
- `testql.endpoint_detector`
- `testql.generator`
- `testql.interpreter`
- `testql.openapi_generator`
- `testql.runner`
- `testql.toon_parser`

## Interfaces

### CLI Entry Points

- `testql`

### REST API (from `openapi.yaml`)

```yaml
components:
  schemas:
    Error:
      properties:
        code:
          type: integer
        error:
          type: string
        message:
          type: string
      type: object
    HealthCheck:
      properties:
        status:
          enum:
          - ok
          - error
          type: string
        timestamp:
          format: date-time
          type: string
        version:
          type: string
      type: object
info:
  description: Auto-generated OpenAPI spec for testql
  title: testql API
  version: 1.0.0
openapi: 3.0.3
paths:
  /iql/file:
    get:
      operationId: iql_read_file
      parameters:
      - in: query
        name: path
        required: false
        schema:
          type: str
      responses:
        '200': &id001
          content:
            application/json:
              schema:
                type: object
          description: Success
        '401': &id002
          description: Unauthorized
        '404': &id003
          description: Not Found
        '500': &id004
          description: Internal Server Error
      summary: Read a TestQL file content (.testql.toon.yaml / .iql / .tql).
      tags:
      - fastapi
      - iql
  /iql/files:
    get:
      operationId: iql_list_files
      responses:
        '200': *id001
        '401': *id002
        '404': *id003
        '500': *id004
      summary: List all .testql.toon.yaml files in the project (with .iql/.tql fallback).
      tags:
      - fastapi
      - iql
  /iql/log:
    get:
      operationId: iql_read_log
      parameters:
      - in: query
        name: name
        required: false
        schema:
          type: str
      responses:
        '200': *id001
        '401': *id002
        '404': *id003
        '500': *id004
      summary: Read a specific log file.
      tags:
      - fastapi
      - iql
  /iql/logs:
    get:
      operationId: iql_list_logs
      responses:
        '200': *id001
        '401': *id002
        '404': *id003
        '500': *id004
      summary: List available log files.
      tags:
      - fastapi
      - iql
  /iql/run-file:
    post:
      operationId: iql_run_file
      requestBody:
        content:
          application/json:
            schema:
              type: object
        required: true
      responses:
        '201': &id005
          content:
            application/json:
              schema:
                type: object
          description: Created
        '400': &id006
          content:
            application/json:
              schema:
                properties:
                  detail:
                    type: string
                  error:
                    type: string
                type: object
          description: Bad Request
        '401': *id002
        '404': *id003
        '500': *id004
      summary: Run an entire IQL file with validation. Returns structured results
        + saves log.
      tags:
      - fastapi
      - iql
  /iql/run-line:
    post:
      operationId: iql_run_line
      requestBody:
        content:
          application/json:
            schema:
              type: object
        required: true
      responses:
        '201': *id005
        '400': *id006
        '401': *id002
        '404': *id003
        '500': *id004
      summary: Execute a single IQL command line via the encoder bridge.
      tags:
      - fastapi
      - iql
  /iql/tables:
    get:
      operationId: iql_list_tables
      parameters:
      - in: query
        name: path
        required: false
        schema:
          type: str
      responses:
        '200': *id001
        '401': *id002
        '404': *id003
        '500': *id004
      summary: Extract table names from an IQL file.
      tags:
      - fastapi
      - iql
servers:
- description: Local development
  url: http://localhost:8101
- description: Relative
  url: /
```

### testql Scenarios

#### `testql/scenarios/generic/api-crud-template.testql.toon.yaml`

```toon
# SCENARIO: api-crud-template.testql.toon.yaml — generic CRUD test template
# TYPE: api
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[2]{key, value}:
  entity,  items
  base_path,  /api/v3/data/items

# ── Wywołania API ─────────────────────────────────────
API[3]{method, endpoint, status}:
  GET,  $,  200
  POST,  $,  200
  GET,  $,  200
```

#### `testql/scenarios/c2004/smoke/api-health.testql.toon.yaml`

```toon
# SCENARIO: api-health.testql.toon.yaml — basic health check for c2004
# TYPE: api
# VERSION: 1.0

# ── Wywołania API ─────────────────────────────────────
API[1]{method, endpoint, status, assert_key, assert_value}:
  GET,  /health,  200,  status,  ok
```

#### `testql/scenarios/c2004/smoke/api-smoke.testql.toon.yaml`

```toon
# SCENARIO: api-smoke.testql.toon.yaml — smoke test for all main c2004 API endpoints
# TYPE: api
# VERSION: 1.0

# ── Wywołania API ─────────────────────────────────────
API[5]{method, endpoint, status}:
  GET,  /health,  200
  GET,  /api/v3/version,  200
  GET,  /api/v3/data/devices,  200
  GET,  /api/v3/data/users,  200
  GET,  /api/v3/data/scenarios,  200
```

#### `testql/scenarios/generic/auth-login.testql.toon.yaml`

```toon
# SCENARIO: auth-login.testql.toon.yaml — generic authentication login test template
# TYPE: api
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  api_url,  $TARGET_URL

# ── Wywołania API ─────────────────────────────────────
API[1]{method, endpoint, status, assert_key, assert_value}:
  POST,  /api/v3/auth/login",  200,  "token",  -
```

#### `testql/scenarios/diagnostics/backend-diagnostic.testql.toon.yaml`

```toon
# SCENARIO: Backend Diagnostic Tests
# TYPE: api
# VERSION: 1.0

# ── Wywołania API ─────────────────────────────────────
API[16]{method, endpoint, status}:
  GET,  /api/v3/health,  200
  GET,  /api/v3/template-json,  200
  GET,  /api/v3/template-json/default,  200
  GET,  /api/v3/data/report_templates,  200
  GET,  /api/v3/devices,  200
  GET,  /api/v3/customers,  200
  GET,  /api/v3/dsl/objects,  200
  GET,  /api/v3/dsl/functions,  200
  GET,  /api/v3/dsl/params,  200
  GET,  /api/v3/dsl/units,  200
  GET,  /api/v3/config/system,  200
  GET,  /api/v3/schema/devices,  200
  GET,  /api/v3/schema/customers,  200
  GET,  /api/v3/schema/protocols,  200
  GET,  /api/v3/data/protocols,  200
  GET,  /api/v3/auth/session,  200
```

#### `testql/scenarios/tests/views/connect-config-feature-flags.testql.toon.yaml`

```toon
# SCENARIO: connect-config-feature-flags.testql.toon.yaml — Test: Konfiguracja > Feature Flags
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-config-feature-flags,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[7]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-config-labels.testql.toon.yaml`

```toon
# SCENARIO: connect-config-labels.testql.toon.yaml — Test: Konfiguracja > Etykiety
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-config-labels,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[8]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  300
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-config-settings.testql.toon.yaml`

```toon
# SCENARIO: connect-config-settings.testql.toon.yaml — Test: Konfiguracja > Ustawienia
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-config-settings,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[7]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-config-tables.testql.toon.yaml`

```toon
# SCENARIO: connect-config-tables.testql.toon.yaml — Test: Konfiguracja > Tabele
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-config-tables,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[7]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-config-theme.testql.toon.yaml`

```toon
# SCENARIO: connect-config-theme.testql.toon.yaml — Test: Konfiguracja > Motyw
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-config-theme,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[7]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-config-users.testql.toon.yaml`

```toon
# SCENARIO: connect-config-users.testql.toon.yaml — Test: Konfiguracja > Użytkownicy
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-config-users,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[7]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-id-barcode.testql.toon.yaml`

```toon
# SCENARIO: connect-id-barcode.testql.toon.yaml — Test: Identyfikacja > Barcode
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-id/barcode,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[7]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-id-list.testql.toon.yaml`

```toon
# SCENARIO: connect-id-list.testql.toon.yaml — Test: Identyfikacja > Lista użytkowników
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-id/list,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[8]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  300
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-id-manual.testql.toon.yaml`

```toon
# SCENARIO: connect-id-manual.testql.toon.yaml — Test: Identyfikacja > Logowanie ręczne
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-id/manual,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[7]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-id-qr.testql.toon.yaml`

```toon
# SCENARIO: connect-id-qr.testql.toon.yaml — Test: Identyfikacja > QR Code
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-id/qr,  500

FLOW[1]{command, target, meta}:
  click,  #btn-simulate-qr,  -

WAIT[1]{ms}:
  300

FLOW[1]{command, target, meta}:
  click,  #btn-simulate-qr,  -

WAIT[1]{ms}:
  200

# ── Encoder HW ────────────────────────────────────────
ENCODER[8]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  300
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-id-rfid.testql.toon.yaml`

```toon
# SCENARIO: connect-id-rfid.testql.toon.yaml — Test: Identyfikacja > RFID
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-id/rfid,  800

FLOW[1]{command, target, meta}:
  assert,  #top-bar-section-title,  -

FLOW[1]{command, target, meta}:
  assert,  .module-main-content,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[2]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200

FLOW[1]{command, target, meta}:
  assert,  [data-enc-zone='col3'],  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[3]{action, target, value, wait_ms}:
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[4]{action, target, value, wait_ms}:
  click,  -,  -,  300
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -
```

#### `testql/scenarios/tests/views/connect-manager-activities.testql.toon.yaml`

```toon
# SCENARIO: connect-manager-activities.testql.toon.yaml — Test: Manager > Czynności
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-manager/activities,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[8]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  300
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-manager-intervals.testql.toon.yaml`

```toon
# SCENARIO: connect-manager-intervals.testql.toon.yaml — Test: Manager > Interwały
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-manager/intervals,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[8]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  300
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-manager-library.testql.toon.yaml`

```toon
# SCENARIO: connect-manager-library.testql.toon.yaml — Test: Manager > Biblioteka
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-manager/library,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[6]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-manager-scenarios.testql.toon.yaml`

```toon
# SCENARIO: connect-manager-scenarios.testql.toon.yaml — Test: Manager > Scenariusze
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-manager/scenarios,  800

FLOW[1]{command, target, meta}:
  assert,  #top-bar-section-title,  -

FLOW[1]{command, target, meta}:
  assert,  .module-main-content,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[5]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[3]{action, target, value, wait_ms}:
  click,  -,  -,  300
  dblclick,  -,  -,  200
  off,  -,  -,  200

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -
```

#### `testql/scenarios/tests/views/connect-manager-test-types.testql.toon.yaml`

```toon
# SCENARIO: connect-manager-test-types.testql.toon.yaml — Test: Manager > Rodzaj Testu
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-manager/test-types,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[6]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-reports-chart.testql.toon.yaml`

```toon
# SCENARIO: connect-reports-chart.testql.toon.yaml — Test: Raporty > Wykres
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-reports/chart?filter=all,  800

FLOW[1]{command, target, meta}:
  assert,  #top-bar-section-title,  -

FLOW[1]{command, target, meta}:
  assert,  .bar,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[2]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200

FLOW[1]{command, target, meta}:
  assert,  [data-enc-zone='col3'],  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[3]{action, target, value, wait_ms}:
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[2]{action, target, value, wait_ms}:
  dblclick,  -,  -,  200
  off,  -,  -,  200

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -
```

#### `testql/scenarios/tests/views/connect-reports-custom.testql.toon.yaml`

```toon
# SCENARIO: connect-reports-custom.testql.toon.yaml — Test: Raporty > Niestandardowy
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-reports/custom?filter=all,  800

FLOW[1]{command, target, meta}:
  assert,  #top-bar-section-title,  -

FLOW[1]{command, target, meta}:
  assert,  .custom-filters-panel,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[2]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200

FLOW[1]{command, target, meta}:
  assert,  [data-enc-zone='col3'],  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[8]{action, target, value, wait_ms}:
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -
```

#### `testql/scenarios/tests/views/connect-reports-filter.testql.toon.yaml`

```toon
# SCENARIO: connect-reports-filter.testql.toon.yaml — Test: Raporty > Filtruj
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-reports/filter?filter=all,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[7]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-reports-month.testql.toon.yaml`

```toon
# SCENARIO: connect-reports-month.testql.toon.yaml — Test: Raporty > Miesiąc
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-reports/month?filter=all,  800

FLOW[1]{command, target, meta}:
  assert,  #top-bar-section-title,  -

FLOW[1]{command, target, meta}:
  assert,  .calendar-grid,  -

FLOW[1]{command, target, meta}:
  assert,  .day-cell,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[2]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200

FLOW[1]{command, target, meta}:
  assert,  [data-enc-zone='col3'],  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[3]{action, target, value, wait_ms}:
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[2]{action, target, value, wait_ms}:
  dblclick,  -,  -,  200
  off,  -,  -,  200

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -
```

#### `testql/scenarios/tests/views/connect-reports-quarter.testql.toon.yaml`

```toon
# SCENARIO: connect-reports-quarter.testql.toon.yaml — Test: Raporty > Kwartał
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-reports/quarter?filter=all,  800

FLOW[1]{command, target, meta}:
  assert,  #top-bar-section-title,  -

FLOW[1]{command, target, meta}:
  assert,  .month-table-card,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[2]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200

FLOW[1]{command, target, meta}:
  assert,  [data-enc-zone='col3'],  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[3]{action, target, value, wait_ms}:
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[2]{action, target, value, wait_ms}:
  dblclick,  -,  -,  200
  off,  -,  -,  200

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -
```

#### `testql/scenarios/tests/views/connect-reports-week.testql.toon.yaml`

```toon
# SCENARIO: connect-reports-week.testql.toon.yaml — Test: Raporty > Tydzień
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-reports/week?filter=all,  800

FLOW[1]{command, target, meta}:
  assert,  #top-bar-section-title,  -

FLOW[1]{command, target, meta}:
  assert,  #week-grid,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[2]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200

FLOW[1]{command, target, meta}:
  assert,  [data-enc-zone='col3'],  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[3]{action, target, value, wait_ms}:
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[3]{action, target, value, wait_ms}:
  click,  -,  -,  300
  dblclick,  -,  -,  200
  off,  -,  -,  200

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -
```

#### `testql/scenarios/tests/views/connect-reports-year.testql.toon.yaml`

```toon
# SCENARIO: connect-reports-year.testql.toon.yaml — Test: Raporty > Rok
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-reports/year?filter=all,  1500

FLOW[1]{command, target, meta}:
  assert,  #top-bar-section-title,  -

FLOW[1]{command, target, meta}:
  assert,  .quarter-card,  -

FLOW[1]{command, target, meta}:
  assert,  .year-summary,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[2]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200

FLOW[1]{command, target, meta}:
  assert,  [data-enc-zone='col3'],  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[3]{action, target, value, wait_ms}:
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -

# ── Encoder HW ────────────────────────────────────────
ENCODER[6]{action, target, value, wait_ms}:
  click,  -,  -,  300
  dblclick,  -,  -,  200
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200

FLOW[1]{command, target, meta}:
  assert,  .encoder-focus,  -
```

#### `testql/scenarios/tests/views/connect-test-devices-search.testql.toon.yaml`

```toon
# SCENARIO: connect-test-devices-search.testql.toon.yaml — Test: Testowanie > Wyszukiwanie urządzeń
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/device-devices-search,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[9]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  300
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-test-full-test.testql.toon.yaml`

```toon
# SCENARIO: connect-test-full-test.testql.toon.yaml — Test: Testowanie > Test automatyczny
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/full-test,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[7]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-test-protocols.testql.toon.yaml`

```toon
# SCENARIO: connect-test-protocols.testql.toon.yaml — Test: Testowanie > Raporty (protokoły)
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/protocols,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[9]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  300
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-test-scenario-view.testql.toon.yaml`

```toon
# SCENARIO: connect-test-scenario-view.testql.toon.yaml — Test: Testowanie > Scenariusz/Interwały
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/scenario-view,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[6]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-test-testing-barcode.testql.toon.yaml`

```toon
# SCENARIO: connect-test-testing-barcode.testql.toon.yaml — Test: Testowanie > Barcode
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/testing-barcode,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[6]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-test-testing-qr.testql.toon.yaml`

```toon
# SCENARIO: connect-test-testing-qr.testql.toon.yaml — Test: Testowanie > QR
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/testing-qr,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[6]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-test-testing-rfid.testql.toon.yaml`

```toon
# SCENARIO: connect-test-testing-rfid.testql.toon.yaml — Test: Testowanie > RFID
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/testing-rfid,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[7]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-test-testing-search.testql.toon.yaml`

```toon
# SCENARIO: connect-test-testing-search.testql.toon.yaml — Test: Testowanie > Wyszukiwanie testów
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/testing-search,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[9]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  300
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-workshop-dispositions-search.testql.toon.yaml`

```toon
# SCENARIO: connect-workshop-dispositions-search.testql.toon.yaml — Test: Warsztat > Dyspozycje
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-workshop/dispositions-search,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[7]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-workshop-requests-search.testql.toon.yaml`

```toon
# SCENARIO: connect-workshop-requests-search.testql.toon.yaml — Test: Warsztat > Zgłoszenia
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-workshop/requests-search,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[8]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  300
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-workshop-services-search.testql.toon.yaml`

```toon
# SCENARIO: connect-workshop-services-search.testql.toon.yaml — Test: Warsztat > Serwisy
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-workshop/services-search,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[8]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  300
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/tests/views/connect-workshop-transport-search.testql.toon.yaml`

```toon
# SCENARIO: connect-workshop-transport-search.testql.toon.yaml — Test: Warsztat > Transport
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-workshop/transport-search,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[7]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col3,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  off,  -,  -,  200
```

#### `testql/scenarios/c2004/gui/connect-workshop-transport.testql.toon.yaml`

```toon
# SCENARIO: connect-workshop-transport.testql.toon.yaml — GUI test for workshop transport view
# TYPE: gui
# VERSION: 1.0

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-workshop-transport,  500

FLOW[1]{command, target, meta}:
  assert_visible,  [data-view='workshop-transport'],  -

FLOW[1]{command, target, meta}:
  click,  [data-action='search'],  -

WAIT[1]{ms}:
  300
```

#### `testql/scenarios/diagnostics/create-todays-reports.testql.toon.yaml`

```toon
# SCENARIO: Create Today's Reports
# TYPE: gui
# VERSION: 1.0

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/testing,  300

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  device,  d-morning-001,  {type:MSA_G1, serial:MRN001}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[5]{command, target, meta}:
  start_test,  ts-inspection,  {name:Poranna inspekcja MSA}
  protocol_created,  pro-today-001,  {device_id:d-morning-001, status:executed, scheduled_date:today_08:30}
  step_complete,  step-1,  {name:Kontrola wizualna, status:passed}
  step_complete,  step-2,  {name:Test funkcjonalny, status:passed}
  protocol_finalize,  pro-today-001,  {status:executed}

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  device,  d-midday-001,  {type:PSS_7000, serial:MID001}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[6]{command, target, meta}:
  start_test,  ts-calibration,  {name:Kalibracja PSS}
  protocol_created,  pro-today-002,  {device_id:d-midday-001, status:executed, scheduled_date:today_12:00}
  step_complete,  step-1,  {name:Zerowanie, status:passed}
  step_complete,  step-2,  {name:Kalibracja ciśnienia, status:passed}
  step_complete,  step-3,  {name:Weryfikacja, status:passed}
  protocol_finalize,  pro-today-002,  {status:executed}

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  device,  d-afternoon-001,  {type:REG_3000, serial:AFT001}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[2]{command, target, meta}:
  start_test,  ts-maintenance,  {name:Konserwacja regulatora}
  protocol_created,  pro-today-003,  {device_id:d-afternoon-001, status:planned, scheduled_date:today_14:30}

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  device,  d-evening-001,  {type:MSA_G1, serial:EVN001}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[2]{command, target, meta}:
  start_test,  ts-pressure,  {name:Test ciśnienia wieczorny}
  protocol_created,  pro-today-004,  {device_id:d-evening-001, status:overdue, scheduled_date:today_16:00}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-reports,  300

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  emit,  reports.refresh_requested,  {view:week}
```

#### `testql/scenarios/examples/device-identification.testql.toon.yaml`

```toon
# SCENARIO: Device Identification Example
# TYPE: gui
# VERSION: 1.0

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-id/device-rfid,  300

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  device,  d-msa-001,  {type:MSA_G1, serial:AO73138, customer:cu-acme-001}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  emit,  ui.device_details_shown,  {deviceId:d-msa-001, panel:device-info}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/testing,  300
```

#### `testql/scenarios/c2004/encoder/encoder-navigation.testql.toon.yaml`

```toon
# SCENARIO: encoder-navigation.testql.toon.yaml — encoder hardware navigation test
# TYPE: gui
# VERSION: 1.0

# ── Encoder HW ────────────────────────────────────────
ENCODER[9]{action, target, value, wait_ms}:
  on,  -,  -,  200
  status,  -,  -,  -
  scroll,  -,  1,  100
  scroll,  -,  1,  100
  click,  -,  -,  -
  page_next,  -,  -,  200
  page_prev,  -,  -,  200
  dblclick,  -,  -,  -
  off,  -,  -,  -
```

#### `testql/scenarios/c2004/encoder/encoder-workshop.testql.toon.yaml`

```toon
# SCENARIO: encoder-workshop.testql.toon.yaml — encoder navigation in workshop context
# TYPE: gui
# VERSION: 1.0

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-workshop,  500

# ── Encoder HW ────────────────────────────────────────
ENCODER[9]{action, target, value, wait_ms}:
  on,  -,  -,  200
  scroll,  -,  1,  100
  click,  -,  -,  300
  scroll,  -,  1,  100
  scroll,  -,  1,  100
  scroll,  -,  1,  100
  click,  -,  -,  300
  dblclick,  -,  -,  200
  off,  -,  -,  -
```

#### `testql/scenarios/diagnostics/full-diagnostic.testql.toon.yaml`

```toon
# SCENARIO: Full System Diagnostic - API + Routes + DSL
# TYPE: gui
# VERSION: 1.0

# ── Wywołania API ─────────────────────────────────────
API[23]{method, endpoint, status}:
  GET,  /api/v3/health,  200
  GET,  /api/v3/auth/session,  200
  GET,  /api/v3/config/system,  200
  GET,  /api/v3/data/devices,  200
  GET,  /api/v3/data/customers,  200
  GET,  /api/v3/data/protocols,  200
  GET,  /api/v3/data/report_templates,  200
  GET,  /api/v3/data/test_scenarios,  200
  GET,  /api/v3/data/workshops,  200
  GET,  /api/v3/schema/devices,  200
  GET,  /api/v3/schema/customers,  200
  GET,  /api/v3/schema/protocols,  200
  GET,  /api/v3/dsl/objects,  200
  GET,  /api/v3/dsl/functions,  200
  GET,  /api/v3/dsl/params,  200
  GET,  /api/v3/dsl/units,  200
  GET,  /api/v3/template-json,  200
  GET,  /api/v3/template-json/default,  200
  GET,  /api/v3/customers,  200
  GET,  /api/v3/devices,  200
  GET,  /api/v1/data/devices,  200
  GET,  /api/v1/data/customers,  200
  GET,  /api/v1/schema/devices,  200

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test,  100

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  emit,  diagnostic.test,  {status:running}

FLOW[1]{command, target, meta}:
  layout,  default,  -

FLOW[1]{command, target, meta}:
  state_save,  diagnostic-checkpoint,  -

FLOW[1]{command, target, meta}:
  process_start,  diagnostic-process,  {step:1}

FLOW[1]{command, target, meta}:
  process_next,  {"step":,  {step:2}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[14]{path, wait_ms}:
  /connect-id,  300
  /connect-test,  300
  /connect-test-device,  300
  /connect-test-protocol,  300
  /connect-test-full,  300
  /connect-data,  300
  /connect-workshop,  300
  /connect-config,  300
  /connect-reports,  300
  /connect-manager,  300
  /connect-scenario,  300
  /connect-template2,  300
  /connect-menu-editor,  300
  /connect-router,  300
```

#### `testql/scenarios/diagnostics/generate-test-reports.testql.toon.yaml`

```toon
# SCENARIO: Generate Test Reports Scenario
# TYPE: interaction
# VERSION: 1.0

# ── Nagrywanie sesji ──────────────────────────────────
RECORD_START[1]{session_id}:
  report-generation

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-id/device-rfid,  300

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  device,  d-msa-7000,  {type:MSA_G1, serial:AO73138}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/testing,  300

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  interval,  3m,  {code:periodic_3m}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[3]{command, target, meta}:
  start_test,  ts-pressure,  {name:Test ciśnienia MSA, steps:3}
  protocol_created,  pro-msa-001,  {device_id:d-msa-7000, status:IN_PROGRESS}
  step_complete,  step-1,  {name:Inicjalizacja, status:passed}

WAIT[1]{ms}:
  200

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-2,  {name:Test ciśnienia 15 mbar, status:passed, value:15.2 mbar}

WAIT[1]{ms}:
  200

# ── Kroki semantyczne ─────────────────────────────────
FLOW[2]{command, target, meta}:
  step_complete,  step-3,  {name:Weryfikacja, status:passed}
  protocol_finalize,  pro-msa-001,  {"status": "COMPLETED", "summary": {"passed": 3, "failed": 0}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-id/device-rfid,  300

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  device,  d-pss-5000,  {type:PSS_5000, serial:PS12345}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/testing,  300

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  interval,  6m,  {code:periodic_6m}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[3]{command, target, meta}:
  start_test,  ts-flow,  {name:Test przepływu PSS, steps:4}
  protocol_created,  pro-pss-001,  {device_id:d-pss-5000, status:IN_PROGRESS}
  step_complete,  step-1,  {name:Kalibracja, status:passed}

WAIT[1]{ms}:
  200

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-2,  {name:Test przepływu min, status:passed, value:2.5 l/min}

WAIT[1]{ms}:
  200

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-3,  {name:Test przepływu max, status:passed, value:15.0 l/min}

WAIT[1]{ms}:
  200

# ── Kroki semantyczne ─────────────────────────────────
FLOW[2]{command, target, meta}:
  step_complete,  step-4,  {name:Finalizacja, status:passed}
  protocol_finalize,  pro-pss-001,  {"status": "COMPLETED", "summary": {"passed": 4, "failed": 0}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-id/device-rfid,  300

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  device,  d-reg-001,  {type:REG_3000, serial:RG98765}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/testing,  300

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  interval,  12m,  {code:annual}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[3]{command, target, meta}:
  start_test,  ts-maintenance,  {name:Konserwacja regulatora, steps:5}
  protocol_created,  pro-reg-001,  {device_id:d-reg-001, status:IN_PROGRESS}
  step_complete,  step-1,  {name:Kontrola wizualna, status:passed}

WAIT[1]{ms}:
  200

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-2,  {name:Czyszczenie, status:passed}

WAIT[1]{ms}:
  200

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-3,  {name:Wymiana uszczelek, status:passed}

WAIT[1]{ms}:
  200

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-4,  {name:Test szczelności, status:passed, value:OK}

WAIT[1]{ms}:
  200

# ── Kroki semantyczne ─────────────────────────────────
FLOW[2]{command, target, meta}:
  step_complete,  step-5,  {name:Dokumentacja, status:passed}
  protocol_finalize,  pro-reg-001,  {"status": "COMPLETED", "summary": {"passed": 5, "failed": 0}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-reports,  500

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  emit,  reports.refresh_requested,  {view:week, filter:executed}

RECORD_STOP:
```

#### `testql-scenarios/generated-api-integration.testql.toon.yaml`

```toon
# SCENARIO: API Integration Tests
# TYPE: api
# GENERATED: true

CONFIG[3]{key, value}:
  base_url, http://localhost:8101
  timeout_ms, 30000
  retry_count, 3

API[4]{method, endpoint, expected_status}:
  GET, /health, 200
  GET, /api/v1/status, 200
  POST, /api/v1/test, 201
  GET, /api/v1/docs, 200

ASSERT[2]{field, operator, expected}:
  status, ==, ok
  response_time, <, 1000
```

#### `testql-scenarios/generated-api-smoke.testql.toon.yaml`

```toon
# SCENARIO: Auto-generated API Smoke Tests
# TYPE: api
# GENERATED: true
# DETECTORS: FastAPIDetector

CONFIG[4]{key, value}:
  base_url, http://localhost:8101
  timeout_ms, 10000
  retry_count, 3
  detected_frameworks, FastAPIDetector

# REST API Endpoints (7 unique)
API[7]{method, endpoint, expected_status}:
  GET, /iql/files, 200  # iql_list_files - List all .testql.toon.yaml files in the project (w
  GET, /iql/file, 200  # iql_read_file - Read a TestQL file content (.testql.toon.yaml / .i
  GET, /iql/tables, 200  # iql_list_tables - Extract table names from an IQL file.
  POST, /iql/run-line, 201  # iql_run_line - Execute a single IQL command line via the encoder 
  POST, /iql/run-file, 201  # iql_run_file - Run an entire IQL file with validation. Returns st
  GET, /iql/logs, 200  # iql_list_logs - List available log files.
  GET, /iql/log, 200  # iql_read_log - Read a specific log file.

ASSERT[2]{field, operator, expected}:
  status, <, 500
  response_time, <, 2000

# Summary by Framework:
#   fastapi: 7 endpoints
```

#### `testql-scenarios/generated-cli-tests.testql.toon.yaml`

```toon
# SCENARIO: CLI Command Tests
# TYPE: cli
# GENERATED: true

CONFIG[2]{key, value}:
  cli_command, python -mtestql
  timeout_ms, 10000

LOG[3]{message}:
  "Test CLI help command"
  "Test CLI version command"
  "Test CLI main workflow"
```

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon
# SCENARIO: Auto-generated from Python Tests
# TYPE: integration
# GENERATED: true

LOG[20]{message}:
  "Test: TestParseIql_test_basic_commands"
  "Test: TestParseTestTOON_test_api_section"
  "Test: TestTestTOONExpansion_test_api_expansion"
  "Test: TestTestTOONExpansion_test_config_expansion"
  "Test: TestIqlInterpreter_test_dry_run_api"
  "Test: test_basic_commands"
  "Test: test_api_section"
  "Test: test_api_expansion"
  "Test: test_config_expansion"
  "Test: test_dry_run_api"
```

#### `testql/scenarios/generic/health-check.testql.toon.yaml`

```toon
# SCENARIO: health-check.testql.toon.yaml — generic health check scenario
# TYPE: api
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  api_url,  $TARGET_URL

# ── Wywołania API ─────────────────────────────────────
API[2]{method, endpoint, status, assert_key, assert_value}:
  GET,  /health,  200,  status,  ok
  GET,  /api/v3/version,  200,  -,  -
```

#### `testql/scenarios/examples/quick-navigation.testql.toon.yaml`

```toon
# SCENARIO: Quick Navigation Example
# TYPE: gui
# VERSION: 1.0

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[5]{path, wait_ms}:
  /,  300
  /connect-id,  300
  /connect-test,  300
  /connect-data,  300
  /connect-reports,  300
```

#### `testql/scenarios/recordings/recorded-test-session.testql.toon.yaml`

```toon
# SCENARIO: DSL Session Recording
# TYPE: gui
# VERSION: 1.0

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test-device,  500

FLOW[1]{command, target, meta}:
  click,  [data-id='d-001'] .btn-test-item,  {label:🧪}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  open_interval_dialog,  d-001,  {customerId:cu-001}

WAIT[1]{ms}:
  300

# ── Wybory domenowe ───────────────────────────────────
SELECT[2]{action, id, meta}:
  select,  #interval-select,  {value:36m, text:36 miesięcy}
  interval,  36m,  {deviceId:d-001}

FLOW[1]{command, target, meta}:
  click,  #interval-start,  {action:confirm_interval}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  start_test,  ts-c20,  {interval:36m, deviceId:d-001, deviceType:MSA_G1}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test-protocol?protocol=pro-example123&step=1,  500

FLOW[1]{command, target, meta}:
  click,  .btn.btn-primary,  {label:OK}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-1,  {name:Wytworzyć podciśnienie, status:passed}

FLOW[1]{command, target, meta}:
  click,  .btn.btn-primary,  {label:OK}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[2]{command, target, meta}:
  step_complete,  final,  {name:Uwagi końcowe, status:passed}
  protocol_finalize,  pro-example123,  {status:executed}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/reports?protocol=pro-example123,  300
```

#### `testql/scenarios/tests/reproduce-view.testql.toon.yaml`

```toon
# SCENARIO: Reproduce View - Connect Manager with Scenario Selection
# TYPE: gui
# VERSION: 1.0

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-manager,  300

FLOW[1]{command, target, meta}:
  click,  #sidebar-col-2,  -

WAIT[2]{ms}:
  200
  500

FLOW[1]{command, target, meta}:
  click,  #scenario-list-body,  -

WAIT[1]{ms}:
  200

FLOW[1]{command, target, meta}:
  click,  .scenario-header,  -

WAIT[1]{ms}:
  100
```

#### `testql/scenarios/tests/views/run-all-views.testql.toon.yaml`

```toon
# SCENARIO: run-all-views.testql.toon.yaml — Master runner for all per-view IQL tests
# TYPE: api
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

INCLUDE[1]{file}:
  connect-id-rfid.testql.toon.yaml

INCLUDE[1]{file}:
  connect-id-qr.testql.toon.yaml

INCLUDE[1]{file}:
  connect-id-manual.testql.toon.yaml

INCLUDE[1]{file}:
  connect-id-list.testql.toon.yaml

INCLUDE[1]{file}:
  connect-id-barcode.testql.toon.yaml

INCLUDE[1]{file}:
  connect-test-devices-search.testql.toon.yaml

INCLUDE[1]{file}:
  connect-test-testing-search.testql.toon.yaml

INCLUDE[1]{file}:
  connect-test-testing-rfid.testql.toon.yaml

INCLUDE[1]{file}:
  connect-test-testing-qr.testql.toon.yaml

INCLUDE[1]{file}:
  connect-test-testing-barcode.testql.toon.yaml

INCLUDE[1]{file}:
  connect-test-full-test.testql.toon.yaml

INCLUDE[1]{file}:
  connect-test-scenario-view.testql.toon.yaml

INCLUDE[1]{file}:
  connect-test-protocols.testql.toon.yaml

INCLUDE[1]{file}:
  connect-workshop-requests-search.testql.toon.yaml

INCLUDE[1]{file}:
  connect-workshop-services-search.testql.toon.yaml

INCLUDE[1]{file}:
  connect-workshop-transport-search.testql.toon.yaml

INCLUDE[1]{file}:
  connect-workshop-dispositions-search.testql.toon.yaml

INCLUDE[1]{file}:
  connect-manager-scenarios.testql.toon.yaml

INCLUDE[1]{file}:
  connect-manager-activities.testql.toon.yaml

INCLUDE[1]{file}:
  connect-manager-intervals.testql.toon.yaml

INCLUDE[1]{file}:
  connect-manager-test-types.testql.toon.yaml

INCLUDE[1]{file}:
  connect-manager-library.testql.toon.yaml

INCLUDE[1]{file}:
  connect-reports-week.testql.toon.yaml

INCLUDE[1]{file}:
  connect-reports-month.testql.toon.yaml

INCLUDE[1]{file}:
  connect-reports-quarter.testql.toon.yaml

INCLUDE[1]{file}:
  connect-reports-year.testql.toon.yaml

INCLUDE[1]{file}:
  connect-reports-chart.testql.toon.yaml

INCLUDE[1]{file}:
  connect-reports-custom.testql.toon.yaml

INCLUDE[1]{file}:
  connect-reports-filter.testql.toon.yaml

INCLUDE[1]{file}:
  connect-config-settings.testql.toon.yaml

INCLUDE[1]{file}:
  connect-config-theme.testql.toon.yaml

INCLUDE[1]{file}:
  connect-config-labels.testql.toon.yaml

INCLUDE[1]{file}:
  connect-config-users.testql.toon.yaml

INCLUDE[1]{file}:
  connect-config-tables.testql.toon.yaml

INCLUDE[1]{file}:
  connect-config-feature-flags.testql.toon.yaml
```

#### `testql/scenarios/tests/run-mask-test-protocol.testql.toon.yaml`

```toon
# SCENARIO: =============================================================================
# TYPE: api
# VERSION: 1.0

# ── Wywołania API ─────────────────────────────────────
API[2]{method, endpoint, status}:
  GET,  /api/v3/scenarios/scn-drager-fps-7000-maska-nadcisnieniowa?include_content=true,  200
  POST,  /api/v3/protocols",  200

WAIT[1]{ms}:
  1000
```

#### `testql/scenarios/recordings/session-recording.testql.toon.yaml`

```toon
# SCENARIO: Session Recording Example
# TYPE: interaction
# VERSION: 1.0

# ── Nagrywanie sesji ──────────────────────────────────
RECORD_START[1]{session_id}:
  demo-session-001

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-id/device-rfid,  300

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  device,  d-demo-001,  {type:PSS-7000, serial:PS12345}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/testing,  300

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  interval,  3m,  {code:periodic_3m, description:3 miesiące}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[2]{command, target, meta}:
  start_test,  ts-demo,  {name:Demo Test, steps:3}
  step_complete,  step-1,  {name:Initialization, status:passed}

WAIT[1]{ms}:
  200

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-2,  {name:Pressure Check, status:passed, value:15.2 mbar}

WAIT[1]{ms}:
  200

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-3,  {name:Finalization, status:passed}

RECORD_STOP:
```

#### `testql/scenarios/tests/test-api.testql.toon.yaml`

```toon
# SCENARIO: Example DSL Script - API Testing
# TYPE: api
# VERSION: 1.0

# ── Wywołania API ─────────────────────────────────────
API[4]{method, endpoint, status}:
  GET,  /api/v3/data/devices?limit=5,  200
  GET,  /api/v3/data/customers?limit=5,  200
  GET,  /api/v3/data/intervals?limit=5,  200
  GET,  /api/v3/data/test_scenarios?limit=5,  200

WAIT[1]{ms}:
  100

# ── Wywołania API ─────────────────────────────────────
API[1]{method, endpoint, status}:
  GET,  /api/v3/menu/configurations?limit=10,  200
```

#### `testql/scenarios/tests/test-app-lifecycle.testql.toon.yaml`

```toon
# SCENARIO: DSL Script - Application Lifecycle Test
# TYPE: api
# VERSION: 1.0

# ── Kroki semantyczne ─────────────────────────────────
FLOW[18]{command, target, meta}:
  app_start,  C2004 Connect System,  {phase:startup}
  app_init,  shell,  {step:mounted}
  app_init,  modules,  {step:registered, count:7}
  app_init,  menu,  {step:configured}
  app_init,  router,  {step:configured, routes:12}
  app_ready,  C2004 Connect System,  {status:initialized}
  module_load,  connect-test,  {path:/connect-test, status:starting}
  module_ready,  connect-test,  {title:Testowanie, status:rendered}
  module_load,  connect-reports,  {path:/connect-reports, status:starting}
  module_ready,  connect-reports,  {title:Raporty, status:rendered}
  page_setup,  reports,  {action:initialize}
  page_render,  reports,  {template:c10, items:25}
  page_setup,  protocol-steps,  {action:initialize}
  page_render,  protocol-steps,  {steps:5, status:pending}
  report_autoopen,  check,  {protocolId:pro-123456}
  report_fetch,  pro-123456,  {status:found}
  report_open,  pro-123456,  {action:modal}
  report_print,  pro-123456,  {template:c10, format:pdf}

# ── Wywołania API ─────────────────────────────────────
API[2]{method, endpoint, status}:
  GET,  /api/v3/data/protocols?limit=3,  200
  GET,  /api/v3/data/test_scenarios?limit=3,  200
```

#### `testql/scenarios/examples/test-device-flow.testql.toon.yaml`

```toon
# SCENARIO: DSL Example: Complete Device Test Flow
# TYPE: interaction
# VERSION: 1.0

# ── Nagrywanie sesji ──────────────────────────────────
RECORD_START[1]{session_id}:
  operator1

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-id/device-rfid,  300

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  device,  d-001,  {type:MSA_G1, serial:AO73138, customer:cu-001}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/testing,  300

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  emit,  test.interval_dialog_opened,  {deviceId:d-001}

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  interval,  3m,  {code:periodic_3m, description:3 miesiące}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[2]{command, target, meta}:
  start_test,  ts-c20,  {name:C20 Standard, steps:5}
  protocol_created,  pro-example-001,  {via:cqrs, deviceId:d-001}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test-protocol?protocol=pro-example-001&step=1,  300

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-1,  {name:Sprawdzenie ciśnienia, status:passed, value:15.2 mbar}

WAIT[1]{ms}:
  500

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-2,  {name:Test szczelności, status:passed, value:OK}

WAIT[1]{ms}:
  500

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-3,  {name:Kontrola wizualna, status:passed, note:Brak uszkodzeń}

WAIT[1]{ms}:
  500

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-4,  {name:Test funkcjonalny, status:passed}

WAIT[1]{ms}:
  500

# ── Kroki semantyczne ─────────────────────────────────
FLOW[2]{command, target, meta}:
  step_complete,  step-5,  {name:Weryfikacja końcowa, status:passed}
  protocol_finalize,  pro-example-001,  {"status": "executed", "summary": {"passed": 5, "failed": 0}

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/reports?protocol=pro-example-001,  300

RECORD_STOP:
```

#### `testql/scenarios/tests/test-devices-crud.testql.toon.yaml`

```toon
# SCENARIO: Example DSL Script - Devices CRUD Operations
# TYPE: api
# VERSION: 1.0

# ── Wywołania API ─────────────────────────────────────
API[4]{method, endpoint, status}:
  GET,  /api/v3/data/devices?limit=10,  200
  GET,  /api/v3/data/customers?limit=5,  200
  GET,  /api/v3/data/intervals?limit=10,  200
  GET,  /api/v3/data/scenario_goal_intervals?limit=10,  200
```

#### `testql/scenarios/tests/test-dsl-objects.testql.toon.yaml`

```toon
# SCENARIO: Example DSL Script - DSL Objects Test
# TYPE: api
# VERSION: 1.0

# ── Wywołania API ─────────────────────────────────────
API[6]{method, endpoint, status}:
  GET,  /api/v3/data/dsl_objects?limit=100,  200
  GET,  /api/v3/data/dsl_functions?limit=100,  200
  GET,  /api/v3/data/dsl_params?limit=100,  200
  GET,  /api/v3/data/dsl_units?limit=100,  200
  GET,  /api/v3/data/dsl_object_functions?limit=1000,  200
  GET,  /api/v3/data/dsl_param_units?limit=1000,  200
```

#### `testql/scenarios/tests/test-encoder.testql.toon.yaml`

```toon
# SCENARIO: test-encoder.testql.toon.yaml — Encoder navigation tests via IQL
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  http://localhost:8105

# ── Encoder HW ────────────────────────────────────────
ENCODER[31]{action, target, value, wait_ms}:
  on,  -,  -,  300
  status,  -,  -,  -
  focus,  col1,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  page_next,  -,  -,  300
  status,  -,  -,  -
  page_prev,  -,  -,  300
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  dblclick,  -,  -,  300
  status,  -,  -,  -
  dblclick,  -,  -,  300
  status,  -,  -,  -
  dblclick,  -,  -,  300
  status,  -,  -,  -
  off,  -,  -,  200
  status,  -,  -,  -
```

#### `testql/scenarios/tests/test-gui-all.testql.toon.yaml`

```toon
# SCENARIO: test-gui-all.testql.toon.yaml — Master GUI test suite — runs all module GUI tests
# TYPE: api
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[2]{key, value}:
  encoder_url,  http://localhost:8105
  api_url,  http://localhost:8101

INCLUDE[1]{file}:
  test-gui-connect-id.testql.toon.yaml

INCLUDE[1]{file}:
  test-gui-connect-test.testql.toon.yaml

INCLUDE[1]{file}:
  test-gui-connect-workshop.testql.toon.yaml

INCLUDE[1]{file}:
  test-gui-connect-manager.testql.toon.yaml

INCLUDE[1]{file}:
  test-gui-connect-config.testql.toon.yaml

INCLUDE[1]{file}:
  test-gui-connect-reports.testql.toon.yaml
```

#### `testql/scenarios/tests/test-gui-connect-config.testql.toon.yaml`

```toon
# SCENARIO: test-gui-connect-config.testql.toon.yaml — GUI tests for Connect Config module
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[2]{key, value}:
  encoder_url,  http://localhost:8105
  api_url,  http://localhost:8101

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[10]{path, wait_ms}:
  /connect-config,  500
  /connect-config/system,  300
  /connect-config/devices,  300
  /connect-config/security,  300
  /connect-config/theme,  300
  /connect-config/labels,  300
  /connect-config/feature-flags,  300
  /connect-config/tables,  300
  /connect-config/sitemap,  300
  /connect-config/module-registry,  300

# ── Encoder HW ────────────────────────────────────────
ENCODER[21]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col1,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  dblclick,  -,  -,  200
  dblclick,  -,  -,  200
  off,  -,  -,  200

# ── Wywołania API ─────────────────────────────────────
API[2]{method, endpoint, status}:
  GET,  /api/v3/config/settings,  200
  GET,  /api/v3/feature-flags,  200
```

#### `testql/scenarios/tests/test-gui-connect-id.testql.toon.yaml`

```toon
# SCENARIO: test-gui-connect-id.testql.toon.yaml — GUI tests for Connect ID module
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[2]{key, value}:
  encoder_url,  http://localhost:8105
  api_url,  http://localhost:8101

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[2]{path, wait_ms}:
  /connect-id,  500
  /connect-id/rfid,  300

FLOW[1]{command, target, meta}:
  click,  #btn-simulate-scan,  -

WAIT[1]{ms}:
  200

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[3]{path, wait_ms}:
  /connect-id/qr,  300
  /connect-id/manual,  300
  /connect-id/list,  300

FLOW[1]{command, target, meta}:
  input,  #add-name,  -

FLOW[1]{command, target, meta}:
  input,  #add-id,  -

WAIT[1]{ms}:
  100

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-id/barcode,  300

# ── Encoder HW ────────────────────────────────────────
ENCODER[25]{action, target, value, wait_ms}:
  on,  -,  -,  300
  status,  -,  -,  -
  focus,  col1,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  300
  status,  -,  -,  -
  dblclick,  -,  -,  200
  status,  -,  -,  -
  dblclick,  -,  -,  200
  status,  -,  -,  -
  dblclick,  -,  -,  200
  status,  -,  -,  -
  off,  -,  -,  200

# ── Wywołania API ─────────────────────────────────────
API[1]{method, endpoint, status}:
  GET,  /api/v3/auth/users,  200
```

#### `testql/scenarios/tests/test-gui-connect-manager.testql.toon.yaml`

```toon
# SCENARIO: test-gui-connect-manager.testql.toon.yaml — GUI tests for Connect Manager module
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[2]{key, value}:
  encoder_url,  http://localhost:8105
  api_url,  http://localhost:8101

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[7]{path, wait_ms}:
  /connect-manager,  500
  /connect-manager/scenario-editor,  300
  /connect-manager/activities,  300
  /connect-manager/test-types,  300
  /connect-manager/intervals,  300
  /connect-manager/library,  300
  /connect-manager/variables,  300

# ── Encoder HW ────────────────────────────────────────
ENCODER[20]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col1,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  dblclick,  -,  -,  200
  dblclick,  -,  -,  200
  dblclick,  -,  -,  200
  off,  -,  -,  200

# ── Wywołania API ─────────────────────────────────────
API[3]{method, endpoint, status}:
  GET,  /api/v3/data/test_scenarios?limit=5,  200
  GET,  /api/v3/data/intervals?limit=5,  200
  GET,  /api/v3/activities?limit=5,  200
```

#### `testql/scenarios/tests/test-gui-connect-reports.testql.toon.yaml`

```toon
# SCENARIO: test-gui-connect-reports.testql.toon.yaml — GUI tests for Connect Reports module
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[2]{key, value}:
  encoder_url,  http://localhost:8105
  api_url,  http://localhost:8101

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[8]{path, wait_ms}:
  /connect-reports,  500
  /connect-reports/week,  300
  /connect-reports/month,  300
  /connect-reports/quarter,  300
  /connect-reports/year,  300
  /connect-reports/custom,  300
  /connect-reports/filter,  300
  /connect-reports/chart,  300

# ── Encoder HW ────────────────────────────────────────
ENCODER[22]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col1,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  page_next,  -,  -,  300
  status,  -,  -,  -
  page_prev,  -,  -,  300
  dblclick,  -,  -,  200
  dblclick,  -,  -,  200
  dblclick,  -,  -,  200
  off,  -,  -,  200

# ── Wywołania API ─────────────────────────────────────
API[1]{method, endpoint, status}:
  GET,  /api/v3/data/protocols?limit=5,  200
```

#### `testql/scenarios/tests/test-gui-connect-test.testql.toon.yaml`

```toon
# SCENARIO: test-gui-connect-test.testql.toon.yaml — GUI tests for Connect Test module
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[2]{key, value}:
  encoder_url,  http://localhost:8105
  api_url,  http://localhost:8101

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[4]{path, wait_ms}:
  /connect-test,  500
  /connect-test/testing-rfid,  300
  /connect-test/testing-qr,  300
  /connect-test/testing-search,  300

FLOW[1]{command, target, meta}:
  click,  [data-action='search-devices'],  -

WAIT[1]{ms}:
  500

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[5]{path, wait_ms}:
  /connect-test/testing-barcode,  300
  /connect-test/devices-search,  300
  /connect-test/scenario-view,  300
  /connect-test/test-run,  300
  /connect-test/protocols,  300

# ── Encoder HW ────────────────────────────────────────
ENCODER[23]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col1,  -,  200
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  300
  status,  -,  -,  -
  click,  -,  -,  300
  dblclick,  -,  -,  200
  dblclick,  -,  -,  200
  dblclick,  -,  -,  200
  status,  -,  -,  -
  off,  -,  -,  200

# ── Wywołania API ─────────────────────────────────────
API[3]{method, endpoint, status}:
  GET,  /api/v3/data/devices?limit=5,  200
  GET,  /api/v3/data/test_scenarios?limit=5,  200
  GET,  /api/v3/data/protocols?limit=5,  200
```

#### `testql/scenarios/tests/test-gui-connect-workshop.testql.toon.yaml`

```toon
# SCENARIO: test-gui-connect-workshop.testql.toon.yaml — GUI tests for Connect Workshop module
# TYPE: gui
# VERSION: 1.0

# ── Konfiguracja ──────────────────────────────────────
CONFIG[2]{key, value}:
  encoder_url,  http://localhost:8105
  api_url,  http://localhost:8101

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[2]{path, wait_ms}:
  /connect-workshop,  500
  /connect-workshop/requests-search,  300

FLOW[1]{command, target, meta}:
  click,  [data-action='requests-search'],  -

WAIT[1]{ms}:
  300

FLOW[1]{command, target, meta}:
  click,  [data-action='filters-apply'],  -

WAIT[1]{ms}:
  200

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[4]{path, wait_ms}:
  /connect-workshop/services-search,  300
  /connect-workshop/transport-search,  300
  /connect-workshop/dispositions-search,  300
  /connect-workshop/requests-new-request,  300

# ── Encoder HW ────────────────────────────────────────
ENCODER[26]{action, target, value, wait_ms}:
  on,  -,  -,  300
  focus,  col1,  -,  200
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  500
  status,  -,  -,  -
  scroll,  -,  1,  150
  scroll,  -,  1,  150
  status,  -,  -,  -
  click,  -,  -,  300
  status,  -,  -,  -
  page_next,  -,  -,  300
  status,  -,  -,  -
  page_prev,  -,  -,  300
  status,  -,  -,  -
  dblclick,  -,  -,  200
  dblclick,  -,  -,  200
  dblclick,  -,  -,  200
  status,  -,  -,  -
  off,  -,  -,  200

# ── Wywołania API ─────────────────────────────────────
API[1]{method, endpoint, status}:
  GET,  /api/v3/data/customers?limit=5,  200
```

#### `testql/scenarios/tests/test-mixed-workflow.testql.toon.yaml`

```toon
# SCENARIO: DSL Mixed Workflow Example
# TYPE: e2e
# VERSION: 1.0

# ── Wywołania API ─────────────────────────────────────
API[3]{method, endpoint, status}:
  GET,  /api/v3/data/devices?limit=3,  200
  GET,  /api/v3/data/customers?limit=3,  200
  GET,  /api/v3/data/intervals?limit=3,  200

# ── Nawigacja UI ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test-device,  500

FLOW[1]{command, target, meta}:
  click,  [data-id='d-001'] .btn-test,  -

WAIT[1]{ms}:
  300

# ── Wybory domenowe ───────────────────────────────────
SELECT[1]{action, id, meta}:
  select,  #interval-select,  {value:36m}

FLOW[1]{command, target, meta}:
  click,  #interval-start,  -

# ── Wybory domenowe ───────────────────────────────────
SELECT[2]{action, id, meta}:
  device,  d-001,  {serial:AO73138, type:MSA_G1}
  interval,  36m,  {label:36 miesięcy}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[1]{command, target, meta}:
  start_test,  ts-c20,  {scenario:C20 standard}

# ── Wywołania API ─────────────────────────────────────
API[2]{method, endpoint, status}:
  GET,  /api/v3/data/protocols?limit=3,  200
  GET,  /api/v3/data/test_scenarios?limit=3,  200
```

#### `testql/scenarios/tests/test-protocol-flow.testql.toon.yaml`

```toon
# SCENARIO: Example DSL Script - Protocol Flow Test (Read-Only)
# TYPE: api
# VERSION: 1.0

# ── Wywołania API ─────────────────────────────────────
API[6]{method, endpoint, status}:
  GET,  /api/v3/data/devices?limit=5,  200
  GET,  /api/v3/data/customers?limit=5,  200
  GET,  /api/v3/data/test_scenarios?limit=10,  200
  GET,  /api/v3/data/intervals?limit=10,  200
  GET,  /api/v3/data/scenario_goal_intervals?limit=20,  200
  GET,  /api/v3/data/protocols?limit=10,  200

# ── Wybory domenowe ───────────────────────────────────
SELECT[2]{action, id, meta}:
  device,  d-001,  {type:MSA_G1, serial:AO73138}
  interval,  36m,  {code:periodic_36m}

# ── Kroki semantyczne ─────────────────────────────────
FLOW[4]{command, target, meta}:
  start_test,  ts-c20,  {scenario:C20 standard}
  protocol_created,  pro-example,  {via:cqrs}
  step_complete,  step-1,  {name:Test ciśnienia, status:passed}
  protocol_finalize,  pro-example,  {status:executed}
```

#### `testql/scenarios/tests/test-ui-navigation.testql.toon.yaml`

```toon
# SCENARIO: Example DSL Script - API Endpoints Test
# TYPE: api
# VERSION: 1.0

# ── Wywołania API ─────────────────────────────────────
API[7]{method, endpoint, status}:
  GET,  /api/v3/data/devices?limit=5,  200
  GET,  /api/v3/data/customers?limit=5,  200
  GET,  /api/v3/data/protocols?limit=10,  200
  GET,  /api/v3/data/test_scenarios?limit=10,  200
  GET,  /api/v3/data/intervals?limit=10,  200
  GET,  /api/v3/data/scenario_goal_intervals?limit=10,  200
  GET,  /api/v3/data/labels?limit=10,  200
```

## Workflows

### Taskfile Tasks (`Taskfile.yml`)

```yaml
tasks:
  install:
    desc: "Install Python dependencies (editable)"
    cmds:
      - pip install -e .[dev]
  quality:
    desc: "Run pyqual quality pipeline (test + lint + format check)"
    cmds:
      - pyqual run
  quality:fix:
    desc: "Run pyqual with auto-fix (format + lint fix)"
    cmds:
      - pyqual run --fix
  quality:report:
    desc: "Generate pyqual quality report"
    cmds:
      - pyqual report
  test:
    desc: "Run pytest suite"
    cmds:
      - pytest -q
  lint:
    desc: "Run ruff lint check"
    cmds:
      - ruff check .
  fmt:
    desc: "Auto-format with ruff"
    cmds:
      - ruff format .
  build:
    desc: "Build wheel + sdist"
    cmds:
      - python -m build
  clean:
    desc: "Remove build artefacts"
    cmds:
      - rm -rf build/ dist/ *.egg-info
  all:
    desc: "Run install, quality check, test"
  iql:run:
    desc: "Run IQL scenario file"
    cmds:
      - testql run {{.CLI_ARGS}}
  iql:shell:
    desc: "Start IQL interactive shell"
    cmds:
      - testql shell
  doql:adopt:
    desc: "Reverse-engineer testql project structure"
    cmds:
      - if ! command -v {{.DOQL_CMD}} >/dev/null 2>&1; then
  echo "⚠️  doql not installed. Install: pip install doql"
  exit 1
fi
  doql:validate:
    desc: "Validate app.doql.less syntax"
    cmds:
      - if [ ! -f "{{.DOQL_OUTPUT}}" ]; then
  echo "❌ {{.DOQL_OUTPUT}} not found. Run: task doql:adopt"
  exit 1
fi
  doql:doctor:
    desc: "Run doql health checks"
    cmds:
      - {{.DOQL_CMD}} doctor
  doql:build:
    desc: "Generate code from app.doql.less"
    cmds:
      - if [ ! -f "{{.DOQL_OUTPUT}}" ]; then
  echo "❌ {{.DOQL_OUTPUT}} not found. Run: task doql:adopt"
  exit 1
fi
  analyze:
    desc: "Full doql analysis (adopt + validate + doctor)"
  docker:build:
    desc: "Build Docker image via docker-compose"
    cmds:
      - docker-compose build
  docker:up:
    desc: "Start Docker containers"
    cmds:
      - docker-compose up -d
  docker:down:
    desc: "Stop Docker containers"
    cmds:
      - docker-compose down
  publish:
    desc: "Build and publish package"
    cmds:
      - twine upload dist/*
  help:
    desc: "Show available tasks"
    cmds:
      - task --list
```

## Quality Pipeline (`pyqual.yaml`)

```yaml
pipeline:
  name: quality-loop

  # Quickstart: replace all of this with a single profile line:
  #   profile: python-minimal   # analyze → validate → lint → fix → test
  #   profile: python-publish   # + git-push and make-publish
  #   profile: python-secure    # + pip-audit, bandit, detect-secrets
  #   profile: python           # standard (needs manual stage config)
  #   profile: ci               # CI-only, no fix
  # See: pyqual profiles

  # Quality gates — pipeline iterates until ALL pass
  metrics:
    cc_max: 10           # cyclomatic complexity per function
    vallm_pass_min: 60   # actual: 64.6%
    # coverage_min: 80  # disabled - pytest_cov reports null

  # Pipeline stages — use 'tool:' for built-in presets or 'run:' for custom commands
  # See all presets: pyqual tools
  # when: any_stage_fail    — run only when a prior stage in this iteration failed
  # when: metrics_fail      — run only when quality gates are not yet passing
  # when: first_iteration   — run only on iteration 1 (skip re-runs after fix)
  # when: after_fix         — run only after the fix stage ran in this iteration
  stages:
    - name: analyze
      tool: code2llm-filtered   # uses sensible exclude defaults

    - name: validate
      tool: vallm-filtered      # uses sensible exclude defaults

    - name: prefact
      tool: prefact
      optional: true
      when: any_stage_fail
      timeout: 900

    - name: fix
      tool: llx-fix
      optional: true
      when: any_stage_fail
      timeout: 1800

    - name: security
      tool: bandit
      optional: true
      timeout: 120

    - name: typecheck
      tool: mypy
      timeout: 300

    - name: test
      tool: pytest
      timeout: 600

    - name: push
      tool: git-push            # built-in: git add + commit + push
      optional: true
      timeout: 120

  # Loop behavior
  loop:
    max_iterations: 3
    on_fail: report      # report | create_ticket | block
    ticket_backends:     # backends to sync when on_fail = create_ticket
      - markdown        # TODO.md (default)
      # - github        # GitHub Issues (requires GITHUB_TOKEN)

  # Environment (optional)
  env:
    LLM_MODEL: openrouter/qwen/qwen3-coder-next
```

## Configuration

```yaml
project:
  name: testql
  version: 0.4.2
  env: local
```

## Dependencies

### Runtime

- `httpx>=0.27`
- `click>=8.0`
- `rich>=13.0`
- `pyyaml>=6.0`
- `goal>=2.1.0`
- `costs>=0.1.20`
- `pfix>=0.1.60`
- `websockets>=13.0`

### Development

- `pytest`
- `pytest-asyncio`
- `fastapi`
- `goal>=2.1.0`
- `costs>=0.1.20`
- `pfix>=0.1.60`

## Deployment

```bash
pip install testql

# development install
pip install -e .[dev]
```

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `*(not set)*` | Required: OpenRouter API key (https://openrouter.ai/keys) |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` | Model (default: openrouter/qwen/qwen3-coder-next) |
| `PFIX_AUTO_APPLY` | `true` | true = apply fixes without asking |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | true = auto pip/uv install |
| `PFIX_AUTO_RESTART` | `false` | true = os.execv restart after fix |
| `PFIX_MAX_RETRIES` | `3` |  |
| `PFIX_DRY_RUN` | `false` |  |
| `PFIX_ENABLED` | `true` |  |
| `PFIX_GIT_COMMIT` | `false` | true = auto-commit fixes |
| `PFIX_GIT_PREFIX` | `pfix:` | commit message prefix |
| `PFIX_CREATE_BACKUPS` | `false` | false = disable .pfix_backups/ directory |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`testql`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `testql/__init__.py:__version__`

## Code Analysis

### `project/analysis.toon.yaml`

```toon
# code2llm | 0f 0L | unknown | 2026-04-18
# CC̄=0.0 | critical:0/0 | dups:0 | cycles:0

HEALTH[0]: ok

REFACTOR[0]: none needed

PIPELINES[0]: none detected

LAYERS:

COUPLING: no cross-package imports detected

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### `project/project.toon.yaml`

```toon
# testql | 0 func | 0f | 4929L | unknown | 2026-04-18

HEALTH:
  CC̄=0.0  critical=0 (limit:10)  dup=0  cycles=0

MODULES[0] (top by size):

EVOLUTION:
  2026-04-18 CC̄=0.0 crit=0 4929L // Automated analysis
```

### `project/evolution.toon.yaml`

```toon
# code2llm/evolution | 0 func | 1f | 2026-04-18

NEXT[2] (ranked by impact):
  [1] !! SPLIT           testql/cli.py
      WHY: 887L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0

  [2] !! SPLIT           testql/generator.py
      WHY: 645L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[2]:
  ⚠ Splitting testql/cli.py may break 0 import paths
  ⚠ Splitting testql/generator.py may break 0 import paths

METRICS-TARGET:
  CC̄:          0.0 → ≤0.0
  max-CC:      0 → ≤0
  god-modules: 2 → 0
  high-CC(≥15): 0 → ≤0
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=0.0 → now CC̄=0.0
```

### `project/map.toon.yaml`

```toon
# testql | 0f 0L | unknown | 2026-04-18
# stats: 0 func | 0 cls | 0 mod | CC̄=0.0 | critical:0 | cycles:0
# alerts[0]: none
# hotspots[0]: none
# evolution: CC̄ 0.0→0.0 (flat 0.0)
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[0]:
D:
```

### `project/duplication.toon.yaml`

```toon
# redup/duplication | 0 groups | 0f 0L | 2026-04-18

SUMMARY:
  files_scanned: 0
  total_lines:   0
  dup_groups:    0
  dup_fragments: 0
  saved_lines:   0
  scan_ms:       4002
```

### `project/validation.toon.yaml`

```toon
# vallm batch | 65f | 42✓ 5⚠ 0✗ | 2026-04-18

SUMMARY:
  scanned: 65  passed: 42 (64.6%)  warnings: 5  errors: 0  unsupported: 23

WARNINGS[5]{path,score}:
  testql/cli.py,0.80
    issues[12]{rule,severity,message,line}:
      complexity.cyclomatic,warning,analyze has cyclomatic complexity 16 (max: 15),125
      complexity.cyclomatic,warning,endpoints has cyclomatic complexity 21 (max: 15),201
      complexity.cyclomatic,warning,suite has cyclomatic complexity 47 (max: 15),671
      complexity.cyclomatic,warning,list has cyclomatic complexity 21 (max: 15),862
      complexity.cyclomatic,warning,echo has cyclomatic complexity 16 (max: 15),941
      complexity.maintainability,warning,Low maintainability index: 8.8 (threshold: 20),
      complexity.lizard_cc,warning,analyze: CC=16 exceeds limit 15,125
      complexity.lizard_cc,warning,endpoints: CC=21 exceeds limit 15,201
      complexity.lizard_cc,warning,suite: CC=43 exceeds limit 15,671
      complexity.lizard_length,warning,suite: 120 lines exceeds limit 100,671
      complexity.lizard_cc,warning,list: CC=21 exceeds limit 15,862
      complexity.lizard_cc,warning,echo: CC=16 exceeds limit 15,941
  testql/commands/echo.py,0.93
    issues[4]{rule,severity,message,line}:
      complexity.cyclomatic,warning,parse_doql_less has cyclomatic complexity 29 (max: 15),14
      complexity.cyclomatic,warning,format_text_output has cyclomatic complexity 19 (max: 15),175
      complexity.lizard_cc,warning,parse_doql_less: CC=29 exceeds limit 15,14
      complexity.lizard_cc,warning,format_text_output: CC=19 exceeds limit 15,175
  testql/interpreter/_converter.py,0.93
    issues[3]{rule,severity,message,line}:
      complexity.cyclomatic,warning,convert_iql_to_testtoon has cyclomatic complexity 66 (max: 15),100
      complexity.lizard_cc,warning,convert_iql_to_testtoon: CC=66 exceeds limit 15,100
      complexity.lizard_length,warning,convert_iql_to_testtoon: 280 lines exceeds limit 100,100
  testql/endpoint_detector.py,0.96
    issues[2]{rule,severity,message,line}:
      complexity.cyclomatic,warning,generate_testql_scenario has cyclomatic complexity 16 (max: 15),768
      complexity.maintainability,warning,Low maintainability index: 6.6 (threshold: 20),
  testql/generator.py,0.96
    issues[3]{rule,severity,message,line}:
      complexity.cyclomatic,warning,_generate_api_tests has cyclomatic complexity 26 (max: 15),342
      complexity.maintainability,warning,Low maintainability index: 14.4 (threshold: 20),
      complexity.lizard_cc,warning,_generate_api_tests: CC=26 exceeds limit 15,342

UNSUPPORTED[4]{bucket,count}:
  *.md,8
  *.txt,1
  *.yml,2
  other,12
```

### `project/compact_flow.mmd`

```mermaid
flowchart TD
```

### `project/calls.mmd`

```mermaid
flowchart LR
```

### `project/flow.mmd`

```mermaid
flowchart TD

    %% Entry points (blue)
    classDef entry fill:#4dabf7,stroke:#1971c2,color:#fff
```

### `project/context.md`

# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/oqlos/testql
- **Primary Language**: unknown
- **Languages**: 
- **Analysis Mode**: static
- **Total Functions**: 0
- **Total Classes**: 0
- **Modules**: 0
- **Entry Points**: 0

## Architecture by Module

## Key Entry Points

Main execution flows into the system:

## Process Flows

Key execution flows identified:

## Data Transformation Functions

Key functions that process and transform data:

## Public API Surface

Functions exposed as public API (no underscore prefix):


## System Interactions

How components interact:

```mermaid
graph TD
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.
