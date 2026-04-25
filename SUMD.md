# TestQL — Interface Query Language for Testing

TestQL — Multi-DSL Test Platform: TestTOON / NL / SQL / Proto / GraphQL adapters with Unified IR, generator engine, and meta-testing

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Code Analysis](#code-analysis)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [API Stubs](#api-stubs)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `testql`
- **version**: `1.2.5`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **openapi_title**: testql API v1.0.0
- **generated_from**: pyproject.toml, Taskfile.yml, testql(74), openapi(7 ep), app.doql.less, pyqual.yaml, goal.yaml, .env.example, src(15 mod), project/(2 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: testql;
  version: 1.2.5;
}

dependencies {
  runtime: "httpx>=0.27, click>=8.0, rich>=13.0, pyyaml>=6.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60, websockets>=13.0";
  dev: "pytest, pytest-asyncio, pytest-cov, fastapi, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60, sqlglot>=20.0, protobuf>=4.21, graphql-core>=3.2";
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
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

workflow[name="deps:update"] {
  trigger: manual;
  step-1: run cmd=PIP="pip"
[ -f "{{.PWD}}/.venv/bin/pip" ] && PIP="{{.PWD}}/.venv/bin/pip"
$PIP install --upgrade pip
OUTDATED=$($PIP list --outdated --format=columns 2>/dev/null | tail -n +3 | awk '{print $1}')
if [ -z "$OUTDATED" ]; then
  echo "✅ All packages are up to date."
else
  echo "📦 Upgrading: $OUTDATED"
  echo "$OUTDATED" | xargs $PIP install --upgrade
  echo "✅ Done."
fi;
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
  target: docker;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  python_version: >=3.10;
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
- `testql.pipeline`
- `testql.report_generator`
- `testql.runner`
- `testql.sumd_generator`
- `testql.sumd_parser`
- `testql.toon_parser`

## Interfaces

### CLI Entry Points

- `testql`

### REST API (from `openapi.yaml`)

```yaml markpact:openapi path=openapi.yaml
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

```toon markpact:testql path=testql/scenarios/generic/api-crud-template.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/c2004/smoke/api-health.testql.toon.yaml
# SCENARIO: api-health.testql.toon.yaml — basic health check for c2004
# TYPE: api
# VERSION: 1.0

# ── Wywołania API ─────────────────────────────────────
API[1]{method, endpoint, status, assert_key, assert_value}:
  GET,  /health,  200,  status,  ok
```

#### `testql/scenarios/c2004/smoke/api-smoke.testql.toon.yaml`

```toon markpact:testql path=testql/scenarios/c2004/smoke/api-smoke.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/generic/auth-login.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/diagnostics/backend-diagnostic.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-config-feature-flags.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-config-labels.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-config-settings.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-config-tables.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-config-theme.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-config-users.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-id-barcode.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-id-list.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-id-manual.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-id-qr.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-id-rfid.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-manager-activities.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-manager-intervals.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-manager-library.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-manager-scenarios.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-manager-test-types.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-reports-chart.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-reports-custom.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-reports-filter.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-reports-month.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-reports-quarter.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-reports-week.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-reports-year.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-test-devices-search.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-test-full-test.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-test-protocols.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-test-scenario-view.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-test-testing-barcode.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-test-testing-qr.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-test-testing-rfid.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-test-testing-search.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-workshop-dispositions-search.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-workshop-requests-search.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-workshop-services-search.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/connect-workshop-transport-search.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/c2004/gui/connect-workshop-transport.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/diagnostics/create-todays-reports.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/examples/device-identification.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/c2004/encoder/encoder-navigation.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/c2004/encoder/encoder-workshop.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/diagnostics/full-diagnostic.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/diagnostics/generate-test-reports.testql.toon.yaml
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

```toon markpact:testql path=testql-scenarios/generated-api-integration.testql.toon.yaml
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

```toon markpact:testql path=testql-scenarios/generated-api-smoke.testql.toon.yaml
# SCENARIO: Auto-generated API Smoke Tests
# TYPE: api
# GENERATED: true
# DETECTORS: FastAPIDetector, OpenAPIDetector

CONFIG[4]{key, value}:
  base_url, http://localhost:8101
  timeout_ms, 10000
  retry_count, 3
  detected_frameworks, FastAPIDetector, OpenAPIDetector

# REST API Endpoints (14 unique)
API[14]{method, endpoint, expected_status}:
  GET, /iql/files, 200
  GET, /iql/file, 200
  GET, /iql/tables, 200
  POST, /iql/run-line, 201
  POST, /iql/run-file, 201
  GET, /iql/logs, 200
  GET, /iql/log, 200
  GET, http://localhost:8101/iql/file, 200
  GET, http://localhost:8101/iql/files, 200
  GET, http://localhost:8101/iql/log, 200
  GET, http://localhost:8101/iql/logs, 200
  POST, http://localhost:8101/iql/run-file, 201
  POST, http://localhost:8101/iql/run-line, 201
  GET, http://localhost:8101/iql/tables, 200

ASSERT[2]{field, operator, expected}:
  status, <, 500
  response_time, <, 2000

# Summary by Framework:
#   fastapi: 7 endpoints
#   openapi: 7 endpoints
```

#### `testql-scenarios/generated-cli-tests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-cli-tests.testql.toon.yaml
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

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/generic/health-check.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/examples/quick-navigation.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/recordings/recorded-test-session.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/reproduce-view.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/views/run-all-views.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/run-mask-test-protocol.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/recordings/session-recording.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-api.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-app-lifecycle.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/examples/test-device-flow.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-devices-crud.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-dsl-objects.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-encoder.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-gui-all.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-gui-connect-config.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-gui-connect-id.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-gui-connect-manager.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-gui-connect-reports.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-gui-connect-test.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-gui-connect-workshop.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-mixed-workflow.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-protocol-flow.testql.toon.yaml
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

```toon markpact:testql path=testql/scenarios/tests/test-ui-navigation.testql.toon.yaml
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

```yaml markpact:taskfile path=Taskfile.yml
# Taskfile.yml — testql (Test Query Language) project runner
# https://taskfile.dev

version: "3"

vars:
  APP_NAME: testql
  DOQL_OUTPUT: app.doql.less
  DOQL_CMD: "{{if eq OS \"windows\"}}doql.exe{{else}}doql{{end}}"

env:
  PYTHONPATH: "{{.PWD}}"

tasks:
  # ─────────────────────────────────────────────────────────────────────────────
  # Development
  # ─────────────────────────────────────────────────────────────────────────────

  install:
    desc: Install Python dependencies (editable)
    cmds:
      - pip install -e .[dev]

  deps:update:
    desc: Upgrade all outdated Python packages in the active / project venv
    cmds:
      - |
        PIP="pip"
        [ -f "{{.PWD}}/.venv/bin/pip" ] && PIP="{{.PWD}}/.venv/bin/pip"
        $PIP install --upgrade pip
        OUTDATED=$($PIP list --outdated --format=columns 2>/dev/null | tail -n +3 | awk '{print $1}')
        if [ -z "$OUTDATED" ]; then
          echo "✅ All packages are up to date."
        else
          echo "📦 Upgrading: $OUTDATED"
          echo "$OUTDATED" | xargs $PIP install --upgrade
          echo "✅ Done."
        fi

  quality:
    desc: Run pyqual quality pipeline (test + lint + format check)
    cmds:
      - pyqual run

  quality:fix:
    desc: Run pyqual with auto-fix (format + lint fix)
    cmds:
      - pyqual run --fix

  quality:report:
    desc: Generate pyqual quality report
    cmds:
      - pyqual report

  test:
    desc: Run pytest suite
    cmds:
      - pytest -q

  lint:
    desc: Run ruff lint check
    cmds:
      - ruff check .

  fmt:
    desc: Auto-format with ruff
    cmds:
      - ruff format .

  build:
    desc: Build wheel + sdist
    cmds:
      - python -m build

  clean:
    desc: Remove build artefacts
    cmds:
      - rm -rf build/ dist/ *.egg-info

  all:
    desc: Run install, quality check, test
    cmds:
      - task: install
      - task: quality

  # ─────────────────────────────────────────────────────────────────────────────
  # IQL / Test Execution
  # ─────────────────────────────────────────────────────────────────────────────

  iql:run:
    desc: Run IQL scenario file
    cmds:
      - testql run {{.CLI_ARGS}}

  iql:shell:
    desc: Start IQL interactive shell
    cmds:
      - testql shell

  # ─────────────────────────────────────────────────────────────────────────────
  # Doql Integration
  # ─────────────────────────────────────────────────────────────────────────────

  doql:adopt:
    desc: Reverse-engineer testql project structure
    cmds:
      - |
        if ! command -v {{.DOQL_CMD}} >/dev/null 2>&1; then
          echo "⚠️  doql not installed. Install: pip install doql"
          exit 1
        fi
      - "{{.DOQL_CMD}} adopt {{.PWD}} --output app.doql.css --force"
      - "{{.DOQL_CMD}} export --format less -o {{.DOQL_OUTPUT}}"
      - echo "✅ Project structure captured in {{.DOQL_OUTPUT}}"

  doql:validate:
    desc: Validate app.doql.less syntax
    cmds:
      - |
        if [ ! -f "{{.DOQL_OUTPUT}}" ]; then
          echo "❌ {{.DOQL_OUTPUT}} not found. Run: task doql:adopt"
          exit 1
        fi
      - "{{.DOQL_CMD}} validate"

  doql:doctor:
    desc: Run doql health checks
    cmds:
      - "{{.DOQL_CMD}} doctor"

  doql:build:
    desc: Generate code from app.doql.less
    cmds:
      - |
        if [ ! -f "{{.DOQL_OUTPUT}}" ]; then
          echo "❌ {{.DOQL_OUTPUT}} not found. Run: task doql:adopt"
          exit 1
        fi
      - |
        # Regenerate LESS from CSS if CSS exists
        if [ -f "app.doql.css" ]; then
          {{.DOQL_CMD}} export --format less -o {{.DOQL_OUTPUT}}
        fi
      - "{{.DOQL_CMD}} build app.doql.css --out build/"

  analyze:
    desc: Full doql analysis (adopt + validate + doctor)
    cmds:
      - task: doql:adopt
      - task: doql:validate
      - task: doql:doctor

  # ─────────────────────────────────────────────────────────────────────────────
  # Docker & Deployment
  # ─────────────────────────────────────────────────────────────────────────────

  docker:build:
    desc: Build Docker image via docker-compose
    cmds:
      - docker-compose build

  docker:up:
    desc: Start Docker containers
    cmds:
      - docker-compose up -d

  docker:down:
    desc: Stop Docker containers
    cmds:
      - docker-compose down

  publish:
    desc: Build and publish package
    cmds:
      - task: build
      - twine upload dist/*

  # ─────────────────────────────────────────────────────────────────────────────
  # Utility
  # ─────────────────────────────────────────────────────────────────────────────

  help:
    desc: Show available tasks
    cmds:
      - task --list
```

## Quality Pipeline (`pyqual.yaml`)

```yaml markpact:pyqual path=pyqual.yaml
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
    coverage_min: 65     # baseline — increase as tests are added (currently 65%)

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
  version: 1.2.5
  env: local
```

## Dependencies

### Runtime

```text markpact:deps python
httpx>=0.27
click>=8.0
rich>=13.0
pyyaml>=6.0
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
websockets>=13.0
```

### Development

```text markpact:deps python scope=dev
pytest
pytest-asyncio
pytest-cov
fastapi
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
sqlglot>=20.0
protobuf>=4.21
graphql-core>=3.2
```

## Deployment

```bash markpact:run
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

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# testql | 303f 31420L | python:280,shell:19,less:4 | 2026-04-25
# stats: 649 func | 494 cls | 303 mod | CC̄=3.5 | critical:14 | cycles:0
# alerts[5]: CC parse_testtoon=14; CC _check_link_statuses=14; CC _action_type=14; CC suite=13; CC _check_asset_statuses=12
# hotspots[5]: watch fan=19; suite fan=19; main fan=18; analyze_topology fan=17; generate_topology fan=16
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[303]:
  TODO/testtoon_parser.py,142
  app.doql.less,167
  examples/api-testing/mock_server.py,51
  examples/api-testing/run.sh,28
  examples/artifact-bundle/generate_bundle.py,37
  examples/artifact-bundle/run.sh,19
  examples/browser-inspection/run.sh,65
  examples/discovery/discover-local.sh,15
  examples/discovery/inspect-web.sh,21
  examples/discovery/topology.sh,19
  examples/encoder-testing/run.sh,22
  examples/flow-control/run.sh,18
  examples/gui-testing/run.sh,23
  examples/project-echo/app.doql.less,37
  examples/project-echo/run.sh,38
  examples/run-all.sh,72
  examples/shell-testing/run.sh,17
  examples/testtoon-basics/run.sh,23
  examples/topology/run.sh,23
  examples/unit-testing/run.sh,24
  examples/web-inspection/run.sh,43
  examples/web-inspection-dot-testql/run.sh,14
  project.sh,50
  testql/__init__.py,10
  testql/__main__.py,7
  testql/_base_fallback.py,222
  testql/adapters/__init__.py,47
  testql/adapters/base.py,98
  testql/adapters/graphql/__init__.py,26
  testql/adapters/graphql/graphql_adapter.py,274
  testql/adapters/graphql/query_executor.py,77
  testql/adapters/graphql/schema_introspection.py,136
  testql/adapters/graphql/subscription_runner.py,41
  testql/adapters/nl/__init__.py,67
  testql/adapters/nl/entity_extractor.py,116
  testql/adapters/nl/grammar.py,108
  testql/adapters/nl/intent_recognizer.py,100
  testql/adapters/nl/lexicon/__init__.py,39
  testql/adapters/nl/llm_fallback.py,50
  testql/adapters/nl/nl_adapter.py,354
  testql/adapters/proto/__init__.py,54
  testql/adapters/proto/compatibility.py,144
  testql/adapters/proto/descriptor_loader.py,163
  testql/adapters/proto/message_validator.py,188
  testql/adapters/proto/proto_adapter.py,243
  testql/adapters/registry.py,88
  testql/adapters/sql/__init__.py,51
  testql/adapters/sql/ddl_parser.py,229
  testql/adapters/sql/dialect_resolver.py,89
  testql/adapters/sql/fixtures.py,106
  testql/adapters/sql/query_parser.py,96
  testql/adapters/sql/sql_adapter.py,334
  testql/adapters/testtoon_adapter.py,346
  testql/base.py,38
  testql/cli.py,56
  testql/commands/__init__.py,36
  testql/commands/discover_cmd.py,47
  testql/commands/echo/__init__.py,23
  testql/commands/echo/cli.py,40
  testql/commands/echo/context.py,55
  testql/commands/echo/formatters/__init__.py,10
  testql/commands/echo/formatters/text.py,96
  testql/commands/echo/parsers/__init__.py,11
  testql/commands/echo/parsers/doql.py,116
  testql/commands/echo/parsers/toon.py,77
  testql/commands/echo.py,25
  testql/commands/echo_helpers.py,69
  testql/commands/encoder_routes.py,478
  testql/commands/endpoints_cmd.py,137
  testql/commands/generate_cmd.py,171
  testql/commands/generate_ir_cmd.py,50
  testql/commands/generate_topology_cmd.py,59
  testql/commands/inspect_cmd.py,35
  testql/commands/misc_cmds.py,293
  testql/commands/run_cmd.py,57
  testql/commands/run_ir_cmd.py,66
  testql/commands/self_test_cmd.py,46
  testql/commands/suite/__init__.py,9
  testql/commands/suite/cli.py,101
  testql/commands/suite/collection.py,123
  testql/commands/suite/execution.py,74
  testql/commands/suite/listing.py,115
  testql/commands/suite/reports.py,90
  testql/commands/suite_cmd.py,13
  testql/commands/templates/__init__.py,19
  testql/commands/templates/content.py,167
  testql/commands/templates/templates.py,60
  testql/commands/topology_cmd.py,24
  testql/detectors/__init__.py,54
  testql/detectors/base.py,35
  testql/detectors/config_detector.py,87
  testql/detectors/django_detector.py,52
  testql/detectors/express_detector.py,60
  testql/detectors/fastapi_detector.py,154
  testql/detectors/flask_detector.py,122
  testql/detectors/graphql_detector.py,88
  testql/detectors/models.py,61
  testql/detectors/openapi_detector.py,91
  testql/detectors/test_detector.py,70
  testql/detectors/unified.py,138
  testql/detectors/websocket_detector.py,49
  testql/discovery/__init__.py,15
  testql/discovery/manifest.py,174
  testql/discovery/probes/__init__.py,6
  testql/discovery/probes/base.py,71
  testql/discovery/probes/browser/__init__.py,8
  testql/discovery/probes/browser/playwright_page.py,148
  testql/discovery/probes/filesystem/__init__.py,16
  testql/discovery/probes/filesystem/api_openapi.py,73
  testql/discovery/probes/filesystem/container_compose.py,45
  testql/discovery/probes/filesystem/container_dockerfile.py,42
  testql/discovery/probes/filesystem/package_node.py,55
  testql/discovery/probes/filesystem/package_python.py,201
  testql/discovery/probes/network/__init__.py,6
  testql/discovery/probes/network/http_endpoint.py,161
  testql/discovery/registry.py,60
  testql/discovery/source.py,34
  testql/doql_parser.py,173
  testql/echo_schemas.py,154
  testql/endpoint_detector.py,63
  testql/generator.py,62
  testql/generators/__init__.py,53
  testql/generators/analyzers.py,300
  testql/generators/base.py,60
  testql/generators/convenience.py,52
  testql/generators/generators.py,373
  testql/generators/llm/__init__.py,17
  testql/generators/llm/coverage_optimizer.py,33
  testql/generators/llm/edge_case_generator.py,27
  testql/generators/multi.py,106
  testql/generators/pipeline.py,96
  testql/generators/sources/__init__.py,52
  testql/generators/sources/base.py,33
  testql/generators/sources/graphql_source.py,67
  testql/generators/sources/nl_source.py,28
  testql/generators/sources/openapi_source.py,94
  testql/generators/sources/proto_source.py,91
  testql/generators/sources/sql_source.py,80
  testql/generators/sources/ui_source.py,82
  testql/generators/targets/__init__.py,37
  testql/generators/targets/base.py,22
  testql/generators/targets/nl_target.py,23
  testql/generators/targets/pytest_target.py,65
  testql/generators/targets/testtoon_target.py,24
  testql/generators/test_generator.py,107
  testql/interpreter/__init__.py,90
  testql/interpreter/_api_runner.py,187
  testql/interpreter/_assertions.py,104
  testql/interpreter/_converter.py,63
  testql/interpreter/_encoder.py,80
  testql/interpreter/_flow.py,137
  testql/interpreter/_gui.py,426
  testql/interpreter/_parser.py,34
  testql/interpreter/_shell.py,244
  testql/interpreter/_testtoon_parser.py,414
  testql/interpreter/_unit.py,268
  testql/interpreter/_websockets.py,173
  testql/interpreter/converter/__init__.py,20
  testql/interpreter/converter/core.py,59
  testql/interpreter/converter/dispatcher.py,50
  testql/interpreter/converter/handlers/__init__.py,31
  testql/interpreter/converter/handlers/api.py,32
  testql/interpreter/converter/handlers/assertions.py,35
  testql/interpreter/converter/handlers/encoder.py,48
  testql/interpreter/converter/handlers/flow.py,40
  testql/interpreter/converter/handlers/include.py,15
  testql/interpreter/converter/handlers/navigate.py,33
  testql/interpreter/converter/handlers/record.py,25
  testql/interpreter/converter/handlers/select.py,27
  testql/interpreter/converter/handlers/unknown.py,19
  testql/interpreter/converter/handlers/wait.py,23
  testql/interpreter/converter/models.py,21
  testql/interpreter/converter/parsers.py,94
  testql/interpreter/converter/renderer.py,65
  testql/interpreter/dispatcher.py,87
  testql/interpreter/interpreter.py,132
  testql/interpreter.py,28
  testql/ir/__init__.py,47
  testql/ir/assertions.py,34
  testql/ir/captures.py,38
  testql/ir/fixtures.py,34
  testql/ir/metadata.py,32
  testql/ir/plan.py,43
  testql/ir/steps.py,232
  testql/ir_runner/__init__.py,35
  testql/ir_runner/assertion_eval.py,125
  testql/ir_runner/context.py,43
  testql/ir_runner/engine.py,121
  testql/ir_runner/executors/__init__.py,52
  testql/ir_runner/executors/api.py,68
  testql/ir_runner/executors/base.py,69
  testql/ir_runner/executors/encoder.py,78
  testql/ir_runner/executors/graphql.py,60
  testql/ir_runner/executors/gui.py,31
  testql/ir_runner/executors/nl.py,25
  testql/ir_runner/executors/proto.py,88
  testql/ir_runner/executors/shell.py,47
  testql/ir_runner/executors/sql.py,66
  testql/ir_runner/executors/unit.py,43
  testql/ir_runner/interpolation.py,30
  testql/meta/__init__.py,42
  testql/meta/confidence_scorer.py,95
  testql/meta/coverage_analyzer.py,174
  testql/meta/mutator.py,220
  testql/meta/self_test.py,59
  testql/openapi_generator.py,445
  testql/pipeline.py,136
  testql/report_generator.py,251
  testql/reporters/__init__.py,7
  testql/reporters/console.py,39
  testql/reporters/json_reporter.py,34
  testql/reporters/junit.py,80
  testql/results/__init__.py,21
  testql/results/analyzer.py,491
  testql/results/artifacts.py,78
  testql/results/models.py,141
  testql/results/serializers.py,113
  testql/runner.py,372
  testql/runners/__init__.py,1
  testql/scenarios/c2004/c2004.testql.less,29
  testql/scenarios/config.testql.less,44
  testql/sumd_generator.py,209
  testql/sumd_parser.py,278
  testql/toon_parser.py,111
  testql/topology/__init__.py,22
  testql/topology/builder.py,143
  testql/topology/generator.py,242
  testql/topology/models.py,106
  testql/topology/serializers.py,52
  testql/topology/sitemap.py,120
  tests/fixtures/discovery/python_pkg/sample_api/__init__.py,2
  tests/fixtures/discovery/python_pkg/sample_api/main.py,8
  tests/test_adapter_capture_syntax.py,167
  tests/test_adapters_base.py,159
  tests/test_api_handler.py,90
  tests/test_browser_discovery.py,111
  tests/test_cli.py,98
  tests/test_converter.py,178
  tests/test_converter_handlers.py,352
  tests/test_detectors.py,331
  tests/test_discovery.py,106
  tests/test_dispatcher.py,140
  tests/test_doql_parser_sumd_gen.py,323
  tests/test_echo.py,227
  tests/test_echo_doql_parser.py,220
  tests/test_echo_schemas_helpers.py,214
  tests/test_encoder_routes.py,42
  tests/test_generate_cmd.py,95
  tests/test_generate_ir_cli.py,70
  tests/test_generators.py,111
  tests/test_graphql_adapter.py,197
  tests/test_gui_execution.py,130
  tests/test_interpreter.py,173
  tests/test_ir.py,194
  tests/test_ir_captures.py,51
  tests/test_ir_runner_assertion_eval.py,108
  tests/test_ir_runner_captures.py,153
  tests/test_ir_runner_engine.py,143
  tests/test_ir_runner_executors.py,174
  tests/test_ir_runner_interpolation.py,41
  tests/test_meta_confidence.py,97
  tests/test_meta_coverage.py,137
  tests/test_meta_mutator.py,190
  tests/test_meta_self_test.py,99
  tests/test_misc_cmds.py,111
  tests/test_network_discovery.py,133
  tests/test_nl_adapter.py,278
  tests/test_nl_entity_extractor.py,155
  tests/test_nl_grammar.py,101
  tests/test_nl_intent_recognizer.py,133
  tests/test_nl_scenarios_e2e.py,92
  tests/test_openapi_generator.py,344
  tests/test_pipeline.py,153
  tests/test_proto_adapter.py,128
  tests/test_proto_compatibility.py,159
  tests/test_proto_descriptor_loader.py,175
  tests/test_proto_graphql_scenarios_e2e.py,82
  tests/test_proto_message_validator.py,123
  tests/test_report_generator.py,169
  tests/test_reporters.py,317
  tests/test_results.py,120
  tests/test_run_ir_cli.py,66
  tests/test_runner.py,188
  tests/test_shell_execution.py,134
  tests/test_sources.py,284
  tests/test_sql_adapter.py,191
  tests/test_sql_ddl_parser.py,108
  tests/test_sql_dialect_resolver.py,75
  tests/test_sql_fixtures.py,73
  tests/test_sql_query_parser.py,67
  tests/test_sql_scenarios_e2e.py,71
  tests/test_suite_cmd_helpers.py,141
  tests/test_suite_execution.py,93
  tests/test_suite_listing.py,167
  tests/test_sumd_parser.py,206
  tests/test_targets.py,87
  tests/test_test_generator.py,118
  tests/test_testtoon_adapter.py,191
  tests/test_toon_parser.py,84
  tests/test_topology.py,88
  tests/test_topology_generator.py,162
  tests/test_unit_execution.py,113
  tree.sh,2
D:
  TODO/testtoon_parser.py:
    e: detect_separator,parse_value,parse_testtoon,validate,print_parsed,Section
    Section: to_dicts(0),validate(0)
    detect_separator(line)
    parse_value(v)
    parse_testtoon(text)
    validate(parsed)
    print_parsed(parsed)
  examples/api-testing/mock_server.py:
    e: health,devices,list_scenarios,create_scenario,get_scenario,update_scenario,delete_scenario,users
    health()
    devices()
    list_scenarios()
    create_scenario(body)
    get_scenario(sid)
    update_scenario(sid;body)
    delete_scenario(sid)
    users()
  examples/artifact-bundle/generate_bundle.py:
    e: main
    main()
  testql/__init__.py:
  testql/__main__.py:
  testql/_base_fallback.py:
    e: StepStatus,StepResult,ScriptResult,VariableStore,InterpreterOutput,BaseInterpreter,EventBridge
    StepStatus:
    StepResult:
    ScriptResult: passed(0),failed(0),summary(0)
    VariableStore: __init__(1),set(2),get(2),has(1),all(0),clear(0),interpolate(1)  # Simple key-value store with interpolation support.
    InterpreterOutput: __init__(1),emit(1),info(1),ok(1),fail(1),warn(1),error(1),step(2)  # Collects interpreter output lines for display or testing.
    BaseInterpreter: __init__(3),parse(2),execute(1),run(2),run_file(1),strip_comments(1)  # Abstract base for language interpreters.
    EventBridge: __init__(1),connect(0),disconnect(0),send_event(2),connected(0)  # Optional WebSocket bridge to DSL Event Server (port 8104).
  testql/adapters/__init__.py:
  testql/adapters/base.py:
    e: read_source,DSLDetectionResult,ValidationIssue,BaseDSLAdapter
    DSLDetectionResult:  # Outcome of `BaseDSLAdapter.detect()`.
    ValidationIssue:  # Single validation issue produced by `BaseDSLAdapter.validate
    BaseDSLAdapter: detect(1),parse(1),render(1),validate(1)  # Adapter contract.
    read_source(source)
  testql/adapters/graphql/__init__.py:
  testql/adapters/graphql/graphql_adapter.py:
    e: _config_section,_query_section,_mutation_section,_subscription_section,_assert_section,_toon_to_plan,_apply_section,_h_config,_h_query,_h_mutation,_h_subscription,_h_assert,_render_meta,_render_config,_format_variables,_render_operation_section,_render_asserts,_render_plan,parse,render,GraphQLDSLAdapter
    GraphQLDSLAdapter: detect(1),parse(1),render(1)  # Adapter for `*.graphql.testql.yaml` GraphQL contract scenari
    _config_section(section)
    _query_section(section;endpoint)
    _mutation_section(section;endpoint)
    _subscription_section(section;endpoint)
    _assert_section(section;steps)
    _toon_to_plan(toon)
    _apply_section(section;plan;gql_steps)
    _h_config(section;plan;gql_steps)
    _h_query(section;plan;gql_steps)
    _h_mutation(section;plan;gql_steps)
    _h_subscription(section;plan;gql_steps)
    _h_assert(section;plan;gql_steps)
    _render_meta(metadata)
    _render_config(plan)
    _format_variables(variables)
    _render_operation_section(plan;op;header)
    _render_asserts(plan)
    _render_plan(plan)
    parse(source)
    render(plan)
  testql/adapters/graphql/query_executor.py:
    e: classify_operation,parse_variables,_try_number,_is_quoted,_coerce_literal
    classify_operation(body)
    parse_variables(text)
    _try_number(raw)
    _is_quoted(raw)
    _coerce_literal(raw)
  testql/adapters/graphql/schema_introspection.py:
    e: _scan_balanced_braces,_kind_to_canonical,_extract_field_names,_parse_type_block,parse_schema,has_graphql_core,TypeDef
    TypeDef: to_dict(0)
    _scan_balanced_braces(text;start)
    _kind_to_canonical(kind)
    _extract_field_names(body)
    _parse_type_block(text;head_match)
    parse_schema(sdl)
    has_graphql_core()
  testql/adapters/graphql/subscription_runner.py:
    e: SubscriptionPlan
    SubscriptionPlan: to_dict(0)  # Declarative description of a subscription step.
  testql/adapters/nl/__init__.py:
  testql/adapters/nl/entity_extractor.py:
    e: first_quoted,all_quoted,first_backtick,all_backticked,first_path,first_selector,first_http_method,first_number,strip_quotes_and_backticks,split_on_preposition,trim_field_nouns
    first_quoted(text)
    all_quoted(text)
    first_backtick(text)
    all_backticked(text)
    first_path(text)
    first_selector(text)
    first_http_method(text)
    first_number(text)
    strip_quotes_and_backticks(text)
    split_on_preposition(text;prepositions)
    trim_field_nouns(text;nouns)
  testql/adapters/nl/grammar.py:
    e: is_step_line,strip_step_prefix,_apply_meta,_consume_line,split_header_and_body,normalize,Header
    Header: merged_extra(0)  # Parsed header of a `.nl.md` file.
    is_step_line(line)
    strip_step_prefix(line)
    _apply_meta(key;value;state)
    _consume_line(line;state;steps)
    split_header_and_body(text)
    normalize(text)
  testql/adapters/nl/intent_recognizer.py:
    e: _intent_table,recognize_intent,recognize_operator,IntentMatch
    IntentMatch:  # Outcome of `recognize_intent`.
    _intent_table(lexicon)
    recognize_intent(line;lexicon)
    recognize_operator(text;lexicon)
  testql/adapters/nl/lexicon/__init__.py:
    e: load_lexicon,available
    load_lexicon(lang)
    available()
  testql/adapters/nl/llm_fallback.py:
    e: get_resolver,set_resolver,LLMSuggestion,LLMResolver,NoOpLLMResolver
    LLMSuggestion:  # A best-guess intent + entities produced by an LLM fallback.
    LLMResolver: resolve(2)
    NoOpLLMResolver: resolve(2)  # Default resolver — always returns `None` (no fallback).
    get_resolver()
    set_resolver(resolver)
  testql/adapters/nl/nl_adapter.py:
    e: _build_navigate,_build_click,_build_input,_build_assert,_assert_field,_assert_expected,_build_wait,_api_status_part,_build_api,_build_sql,_resolve_encoder_action,_build_encoder,_build_step,_build_unresolved,_render_api,_render_sql,_render_encoder,_render_assert,_render_wait,_render_nl,_render_gui,_render_by_kind,_render_step,_metadata_from_header,parse,render,NLDSLAdapter
    NLDSLAdapter: detect(1),parse(1),render(1),_load_lexicon_safe(1)  # Adapter for `*.nl.md` natural-language scenarios.
    _build_navigate(match;line)
    _build_click(match;line)
    _build_input(match;line)
    _build_assert(match;line;lexicon)
    _assert_field(tail;lexicon)
    _assert_expected(tail)
    _build_wait(match;line)
    _api_status_part(status)
    _build_api(match;line)
    _build_sql(match;line)
    _resolve_encoder_action(verb)
    _build_encoder(match;line)
    _build_step(match;line;lexicon;lang)
    _build_unresolved(line;lang)
    _render_api(step;en)
    _render_sql(step;en)
    _render_encoder(step;en)
    _render_assert(step;en)
    _render_wait(step;en)
    _render_nl(step;en)
    _render_gui(step;en)
    _render_by_kind(step;en)
    _render_step(step;lang)
    _metadata_from_header(header;lang)
    parse(source)
    render(plan)
  testql/adapters/proto/__init__.py:
    e: has_protobuf
    has_protobuf()
  testql/adapters/proto/compatibility.py:
    e: _wire_compatible,_compare_field,_find_candidate_field,_compare_message,_scan_old_messages,_scan_new_messages,compare_schemas,CompatibilityIssue,CompatibilityReport
    CompatibilityIssue:
    CompatibilityReport: is_compatible(0),to_dict(0)
    _wire_compatible(a;b)
    _compare_field(old;new;message_name)
    _find_candidate_field(old_field;new_message)
    _compare_message(old;new)
    _scan_old_messages(old;new_messages;report)
    _scan_new_messages(old;new;report)
    compare_schemas(old;new)
  testql/adapters/proto/descriptor_loader.py:
    e: _strip_comments,_scan_balanced_braces,_parse_field,_parse_message,_iter_messages,parse_proto,load_proto_file,FieldDef,MessageDef,ProtoFile
    FieldDef: to_dict(0)
    MessageDef: field_by_name(1),field_by_number(1),to_dict(0)
    ProtoFile: message(1),to_dict(0)
    _strip_comments(text)
    _scan_balanced_braces(text;start)
    _parse_field(match)
    _parse_message(name;body)
    _iter_messages(text)
    parse_proto(text)
    load_proto_file(path)
  testql/adapters/proto/message_validator.py:
    e: parse_instance_fields,coerce_scalar,_validate_field_known,_validate_field_type,_validate_field_value,validate_message_instance,_row_issues,_missing_required,round_trip_equal,lookup_message,ValidationIssue,ValidationResult
    ValidationIssue:
    ValidationResult: ok(0),to_dict(0)
    parse_instance_fields(text)
    coerce_scalar(type_name;raw)
    _validate_field_known(name;message)
    _validate_field_type(name;declared;message)
    _validate_field_value(name;declared;raw)
    validate_message_instance(message;instance)
    _row_issues(name;declared;raw;message)
    _missing_required(message;seen)
    round_trip_equal(message;instance)
    lookup_message(proto;name)
  testql/adapters/proto/proto_adapter.py:
    e: _proto_section,_message_section,_assert_section,_toon_to_plan,_apply_section,_h_proto,_h_message,_h_assert,_render_meta,_render_proto_files,_render_messages,_render_asserts,_render_plan,parse,render,ProtoDSLAdapter
    ProtoDSLAdapter: detect(1),parse(1),render(1)  # Adapter for `*.proto.testql.yaml` Protocol Buffers contracts
    _proto_section(section)
    _message_section(section;schema_files)
    _assert_section(section;steps_by_name)
    _toon_to_plan(toon)
    _apply_section(section;plan;proto_steps;schema_files)
    _h_proto(section;plan;proto_steps;schema_files)
    _h_message(section;plan;proto_steps;schema_files)
    _h_assert(section;plan;proto_steps;schema_files)
    _render_meta(metadata)
    _render_proto_files(plan)
    _render_messages(plan)
    _render_asserts(plan)
    _render_plan(plan)
    parse(source)
    render(plan)
  testql/adapters/registry.py:
    e: get_registry,AdapterRegistry
    AdapterRegistry: __init__(0),register(1),unregister(1),clear(0),get(1),all(0),by_extension(1),detect(1)  # In-process registry of `BaseDSLAdapter` instances.
    get_registry()
  testql/adapters/sql/__init__.py:
  testql/adapters/sql/ddl_parser.py:
    e: _scan_balanced_parens,_iter_create_tables,_depth_delta,_split_top_level,_parse_column_line,_extract_default,_parse_table_regex,_parse_ddl_regex,_parse_ddl_sqlglot,_table_from_sqlglot,_column_from_sqlglot,parse_ddl,Column,Table,ParsedDDL
    Column: to_dict(0)
    Table: column(1),to_dict(0)
    ParsedDDL: table(1),to_dict(0)
    _scan_balanced_parens(sql;start)
    _iter_create_tables(sql)
    _depth_delta(ch)
    _split_top_level(body)
    _parse_column_line(line)
    _extract_default(rest)
    _parse_table_regex(name;body)
    _parse_ddl_regex(sql)
    _parse_ddl_sqlglot(sql;dialect)
    _table_from_sqlglot(stmt)
    _column_from_sqlglot(col)
    parse_ddl(sql;dialect;prefer_sqlglot)
  testql/adapters/sql/dialect_resolver.py:
    e: normalize_dialect,is_supported,has_sqlglot,transpile,SqlglotMissing
    SqlglotMissing:  # Raised when an operation requires sqlglot but it isn't insta
    normalize_dialect(name)
    is_supported(name)
    has_sqlglot()
    transpile(sql;source;target)
  testql/adapters/sql/fixtures.py:
    e: schema_fixture_from_rows,_truthy,_optional_str,ConnectionFixture,SchemaFixture
    ConnectionFixture: to_fixture(0)  # Declarative connection info parsed from CONFIG[connection_ur
    SchemaFixture: add_column(2),_ensure_table(1),to_fixture(0)  # Declarative schema collected from SCHEMA section rows.
    schema_fixture_from_rows(rows)
    _truthy(value;default)
    _optional_str(value)
  testql/adapters/sql/query_parser.py:
    e: classify,_analyze_with_sqlglot,_projection_columns,analyze_query,QueryInfo
    QueryInfo: to_dict(0)
    classify(sql)
    _analyze_with_sqlglot(sql;dialect)
    _projection_columns(tree)
    analyze_query(sql;dialect)
  testql/adapters/sql/sql_adapter.py:
    e: _config_section,_schema_section,_query_section,_row_query,_assert_section,_resolve_owner,_toon_to_plan,_apply_section,_h_config,_h_schema,_h_query,_h_assert,_h_capture,_render_meta,_render_config,_collect_schema_rows,_render_schema,_render_queries,_render_asserts,_render_captures,_render_plan,parse,render,SqlDSLAdapter
    SqlDSLAdapter: detect(1),parse(1),render(1)  # Adapter for `*.sql.testql.yaml` SQL contract scenarios.
    _config_section(section;dialect)
    _schema_section(section)
    _query_section(section;dialect)
    _row_query(row)
    _assert_section(section;steps_by_name)
    _resolve_owner(target;steps_by_name)
    _toon_to_plan(toon)
    _apply_section(section;plan;sql_steps;dialect)
    _h_config(section;plan;sql_steps;dialect)
    _h_schema(section;plan;sql_steps;dialect)
    _h_query(section;plan;sql_steps;dialect)
    _h_assert(section;plan;sql_steps;dialect)
    _h_capture(section;plan;sql_steps;dialect)
    _render_meta(metadata)
    _render_config(plan)
    _collect_schema_rows(plan)
    _render_schema(plan)
    _render_queries(plan)
    _render_asserts(plan)
    _render_captures(plan)
    _render_plan(plan)
    parse(source)
    render(plan)
  testql/adapters/testtoon_adapter.py:
    e: _config_to_dict,_api_section_to_steps,_navigate_section_to_steps,_encoder_section_to_steps,_assert_section_to_steps,_capture_section_apply,_resolve_capture_target,_generic_section_to_steps,_translate_section,_toon_to_plan,_render_meta,_render_config,_render_api_steps,_render_navigate_steps,_render_encoder_steps,_render_assertions,_render_captures,_render_plan,parse,render,TestToonAdapter
    TestToonAdapter: detect(1),parse(1),render(1)  # Adapter for the legacy `*.testql.toon.yaml` format (TestTOON
    _config_to_dict(section)
    _api_section_to_steps(section)
    _navigate_section_to_steps(section)
    _encoder_section_to_steps(section)
    _assert_section_to_steps(section)
    _capture_section_apply(section;plan)
    _resolve_capture_target(target;by_name;steps)
    _generic_section_to_steps(section)
    _translate_section(section)
    _toon_to_plan(toon)
    _render_meta(md)
    _render_config(config)
    _render_api_steps(steps)
    _render_navigate_steps(steps)
    _render_encoder_steps(steps)
    _render_assertions(steps)
    _render_captures(steps)
    _render_plan(plan)
    parse(source)
    render(plan)
  testql/base.py:
  testql/cli.py:
    e: cli,main
    cli()
    main()
  testql/commands/__init__.py:
  testql/commands/discover_cmd.py:
    e: discover,_print_summary
    discover(source;fmt;scan_network)
    _print_summary(manifest)
  testql/commands/echo/__init__.py:
  testql/commands/echo/cli.py:
    e: echo
    echo(path;fmt;no_toon;no_doql;output)
  testql/commands/echo/context.py:
    e: _find_doql_file,_find_toon_path,generate_context
    _find_doql_file(path)
    _find_toon_path(path)
    generate_context(path;include_toon;include_doql)
  testql/commands/echo/formatters/__init__.py:
  testql/commands/echo/formatters/text.py:
    e: _fmt_interfaces,_fmt_workflows,_fmt_contracts,_fmt_entities,_fmt_suggestions,_build_header,format_text_output
    _fmt_interfaces(context)
    _fmt_workflows(context)
    _fmt_contracts(context)
    _fmt_entities(context)
    _fmt_suggestions(context)
    _build_header(context)
    format_text_output(context)
  testql/commands/echo/parsers/__init__.py:
  testql/commands/echo/parsers/doql.py:
    e: _parse_kv_block,_parse_app_block,_parse_entities,_parse_interfaces,_parse_workflows,_parse_deploy,_parse_environment,_parse_integrations,parse_doql_less
    _parse_kv_block(body)
    _parse_app_block(content)
    _parse_entities(content)
    _parse_interfaces(content)
    _parse_workflows(content)
    _parse_deploy(content)
    _parse_environment(content)
    _parse_integrations(content)
    parse_doql_less(filepath)
  testql/commands/echo/parsers/toon.py:
    e: _extract_endpoint,_extract_assert,_parse_scenario,parse_toon_scenarios
    _extract_endpoint(method;value)
    _extract_assert(key;value)
    _parse_scenario(content;file;base_path)
    parse_toon_scenarios(path)
  testql/commands/echo.py:
  testql/commands/echo_helpers.py:
    e: _collect_toon_directory,collect_toon_data,collect_doql_data,render_echo
    _collect_toon_directory(toon_file_path;project_echo)
    collect_toon_data(toon_path;project_echo)
    collect_doql_data(doql_path;project_echo)
    render_echo(project_echo;fmt;project_path_obj)
  testql/commands/encoder_routes.py:
    e: _strip_path_segments,_migrate_legacy_extension,_remap_tests_prefix,_normalize_iql_path,_resolve_iql_path,_assert_bool_prop,_assert_count_prop,_assert_text_prop,_assert_classes_prop,_evaluate_assertion,_format_log_detail,_exec_encoder_cmd,_exec_browser_cmd,_exec_assert_cmd,_execute_iql_line,iql_list_files,iql_read_file,iql_list_tables,_extract_table_names,iql_run_line,iql_run_file,_run_iql_lines,_update_counters,_build_run_summary,_write_run_log,iql_list_logs,iql_read_log
    _strip_path_segments(candidate)
    _migrate_legacy_extension(candidate)
    _remap_tests_prefix(candidate)
    _normalize_iql_path(path)
    _resolve_iql_path(path)
    _assert_bool_prop(result;prop;expected)
    _assert_count_prop(result;expected)
    _assert_text_prop(result;expected)
    _assert_classes_prop(result;expected)
    _evaluate_assertion(result;prop;expected)
    _format_log_detail(cmd;result)
    _exec_encoder_cmd(cmd;arg)
    _exec_browser_cmd(cmd;arg;raw_arg)
    _exec_assert_cmd(raw_arg)
    _execute_iql_line(line)
    iql_list_files()
    iql_read_file(path)
    iql_list_tables(path)
    _extract_table_names(content)
    iql_run_line(req)
    iql_run_file(req)
    _run_iql_lines(lines;label)
    _update_counters(counters;result)
    _build_run_summary(normalized_path;requested_path;lines;results;counters)
    _write_run_log(normalized_path;lines;log_lines;summary)
    iql_list_logs()
    iql_read_log(name)
  testql/commands/endpoints_cmd.py:
    e: endpoints,_format_endpoints_json,_format_endpoints_csv,_format_endpoints_table,_format_endpoints,openapi
    endpoints(path;fmt;framework;endpoint_type;output)
    _format_endpoints_json(eps;target_path)
    _format_endpoints_csv(eps;target_path)
    _format_endpoints_table(eps;detector)
    _format_endpoints(eps;fmt;target_path;detector)
    openapi(path;output;format;title;version;contract_tests)
  testql/commands/generate_cmd.py:
    e: _is_workspace,_echo_analysis,_echo_generation,generate,_emit_ir_json,analyze,_count_routes_by,_print_routes_section,_print_scenarios_section
    _is_workspace(target_path)
    _echo_analysis(ctx;target_path)
    _echo_generation(ctx;generated)
    generate(path;output_dir;analyze_only;fmt;to_ir)
    _emit_ir_json(paths;fmt)
    analyze(path)
    _count_routes_by(routes;key)
    _print_routes_section(profile)
    _print_scenarios_section(profile)
  testql/commands/generate_ir_cmd.py:
    e: _split_from_arg,generate_ir
    _split_from_arg(value)
    generate_ir(from_;to_;out;no_llm)
  testql/commands/generate_topology_cmd.py:
    e: generate_topology,_pick_trace
    generate_topology(source;trace_id;output;fmt;scan_network)
    _pick_trace(topology;trace_id)
  testql/commands/inspect_cmd.py:
    e: inspect
    inspect(source;fmt;artifact;scan_network;browser;out_dir)
  testql/commands/misc_cmds.py:
    e: _create_templates,init,create,watch,from_sumd,report,echo
    _create_templates(templates_dir;project_type)
    init(path;name;project_type)
    create(name;test_type;module;output;force)
    watch(path;pattern;command;debounce)
    from_sumd(sumd_file;output;dry_run)
    report(data_json;output;example)
    echo(toon_path;doql_path;fmt;output;project_path)
  testql/commands/run_cmd.py:
    e: run
    run(file;url;dry_run;output;quiet)
  testql/commands/run_ir_cmd.py:
    e: _emit_json,_emit_console,run_ir
    _emit_json(result)
    _emit_console(result)
    run_ir(file;api_url;encoder_url;graphql_url;dry_run;output)
  testql/commands/self_test_cmd.py:
    e: _print_human,self_test
    _print_human(report)
    self_test(openapi;as_json)
  testql/commands/suite/__init__.py:
  testql/commands/suite/cli.py:
    e: suite,list_tests
    suite(suite_name;base_path;pattern;tags;test_types;parallel;fail_fast;output;report;url)
    list_tests(path;test_type;tag;fmt)
  testql/commands/suite/collection.py:
    e: _resolve_search_dir_and_pattern,_find_files,_collect_from_suite,_collect_by_pattern,_collect_recursive,_deduplicate_files,collect_test_files,collect_list_files
    _resolve_search_dir_and_pattern(base_dir;file_pattern)
    _find_files(base_dir;file_pattern)
    _collect_from_suite(target_path;suite_name;config)
    _collect_by_pattern(target_path;pattern)
    _collect_recursive(target_path)
    _deduplicate_files(files)
    collect_test_files(target_path;suite_name;pattern;config)
    collect_list_files(target_path)
  testql/commands/suite/execution.py:
    e: run_single_file,run_suite_files
    run_single_file(test_file;interp)
    run_suite_files(test_files;url;output;fail_fast;config)
  testql/commands/suite/listing.py:
    e: _parse_testtoon_header,_collect_meta_lines,_parse_yaml_meta_block,parse_meta,filter_tests,render_test_list
    _parse_testtoon_header(content)
    _collect_meta_lines(content)
    _parse_yaml_meta_block(content;yaml_module)
    parse_meta(tf;yaml_module)
    filter_tests(raw_files;target_path;test_type;tag;yaml_module)
    render_test_list(tests;fmt)
  testql/commands/suite/reports.py:
    e: build_report_data,_save_json_report,_build_junit_xml,save_report,print_summary
    build_report_data(suite_name;results;total_passed;total_failed;total_duration)
    _save_json_report(report_data;report_file)
    _build_junit_xml(report_data)
    save_report(report_data;report_file;output)
    print_summary(results;total_passed;total_failed;total_duration)
  testql/commands/suite_cmd.py:
  testql/commands/templates/__init__.py:
  testql/commands/templates/content.py:
    e: TestContentBuilder
    TestContentBuilder: build(5),_build_meta_header(4),_build_standard_vars(0),_build_gui(4),_build_api(4),_build_mixed(4),_build_performance(4),_build_workflow(4),_build_encoder(4)  # Builds test content for different test types.
  testql/commands/templates/templates.py:
  testql/commands/topology_cmd.py:
    e: topology
    topology(source;fmt;include_manifest;scan_network)
  testql/detectors/__init__.py:
  testql/detectors/base.py:
    e: BaseEndpointDetector
    BaseEndpointDetector: __init__(1),detect(0),_find_files(2)  # Base class for endpoint detectors.
  testql/detectors/config_detector.py:
    e: ConfigEndpointDetector
    ConfigEndpointDetector: detect(0),_analyze_docker_compose(1),_parse_port_mapping(1),_infer_protocol(1)  # Detect endpoints from configuration files.
  testql/detectors/django_detector.py:
    e: DjangoDetector
    DjangoDetector: detect(0),_analyze_urls_py(1)  # Detect Django URL patterns.
  testql/detectors/express_detector.py:
    e: ExpressDetector
    ExpressDetector: detect(0),_analyze_express_file(1),_extract_method_path(1)  # Detect Express.js routes from JavaScript/TypeScript files.
  testql/detectors/fastapi_detector.py:
    e: FastAPIDetector
    FastAPIDetector: detect(0),_analyze_file(1),_detect_router_assignment(2),_extract_router_prefix(1),_detect_app_assignment(1),_extract_include_router(1),_analyze_route_handler(4),_extract_route_info(1),_get_router_prefix(2),_extract_parameters(1),_get_annotation_name(1),_extract_docstring(1)  # Detect FastAPI endpoints using AST analysis.
  testql/detectors/flask_detector.py:
    e: FlaskDetector
    FlaskDetector: detect(0),_analyze_flask_file(1),_detect_blueprint(2),_extract_blueprint_prefix(1),_analyze_flask_route(4),_extract_flask_route_info(2),_extract_route_path(1),_extract_route_methods(1),_apply_blueprint_prefix(3)  # Detect Flask endpoints including Blueprints.
  testql/detectors/graphql_detector.py:
    e: GraphQLDetector
    GraphQLDetector: detect(0),_analyze_schema(1),_analyze_python_graphql(1)  # Detect GraphQL schemas and resolvers.
  testql/detectors/models.py:
    e: EndpointInfo,ServiceInfo
    EndpointInfo: to_testql_api_call(1),_infer_expected_status(0)  # Standardized endpoint information.
    ServiceInfo:  # Information about a service/application.
  testql/detectors/openapi_detector.py:
    e: OpenAPIDetector
    OpenAPIDetector: detect(0),_parse_spec(1),_extract_base_path(1)  # Detect endpoints from OpenAPI/Swagger specifications.
  testql/detectors/test_detector.py:
    e: TestEndpointDetector
    TestEndpointDetector: detect(0),_analyze_test_file(1),_extract_method_path(2)  # Detect API calls in test files to infer endpoints.
  testql/detectors/unified.py:
    e: detect_endpoints,UnifiedEndpointDetector
    UnifiedEndpointDetector: __init__(1),detect_all(0),_deduplicate_endpoints(1),get_endpoints_by_type(1),get_endpoints_by_framework(1),generate_testql_scenario(1),_rest_block(1),_graphql_block(1),_ws_block(1)  # Unified detector that runs all specialized detectors.
    detect_endpoints(project_path)
  testql/detectors/websocket_detector.py:
    e: WebSocketDetector
    WebSocketDetector: detect(0),_analyze_content(2)  # Detect WebSocket endpoints.
  testql/discovery/__init__.py:
  testql/discovery/manifest.py:
    e: _score_confidence,_merge_metadata,_dependencies_from_metadata,_interfaces_from_metadata,_unique,_dedupe_dicts,ManifestConfidence,Evidence,Dependency,Interface,BuildArtifact,ArtifactManifest
    ManifestConfidence:
    Evidence: to_dict(0)
    Dependency: to_dict(0)
    Interface: to_dict(0)
    BuildArtifact: to_dict(0)
    ArtifactManifest: from_probe_results(3),to_dict(1)
    _score_confidence(results)
    _merge_metadata(items)
    _dependencies_from_metadata(metadata)
    _interfaces_from_metadata(metadata)
    _unique(values)
    _dedupe_dicts(items)
  testql/discovery/probes/__init__.py:
  testql/discovery/probes/base.py:
    e: ProbeResult,Probe,BaseProbe
    ProbeResult: to_dict(0)
    Probe: applicable(1),probe(1)
    BaseProbe: applicable(1),no_match(0),result(5),evidence(3),source_roots(1)
  testql/discovery/probes/browser/__init__.py:
  testql/discovery/probes/browser/playwright_page.py:
    e: _link_kind,_asset_kind,PlaywrightPageProbe
    PlaywrightPageProbe: __init__(2),applicable(1),probe(1),evidence(3)
    _link_kind(base_url;href)
    _asset_kind(asset)
  testql/discovery/probes/filesystem/__init__.py:
  testql/discovery/probes/filesystem/api_openapi.py:
    e: _excluded,OpenAPIProbe
    OpenAPIProbe: probe(1),_find_specs(1),_load(1),_metadata(3)
    _excluded(path;root)
  testql/discovery/probes/filesystem/container_compose.py:
    e: DockerComposeProbe
    DockerComposeProbe: probe(1),_find_files(1),_metadata(1)
  testql/discovery/probes/filesystem/container_dockerfile.py:
    e: DockerfileProbe
    DockerfileProbe: probe(1),_find_files(1),_metadata(1)
  testql/discovery/probes/filesystem/package_node.py:
    e: NodePackageProbe
    NodePackageProbe: probe(1),_metadata(1)
  testql/discovery/probes/filesystem/package_python.py:
    e: _parse_pyproject,_parse_setup_cfg,_parse_setup_py,_parse_pyproject_dependencies,_parse_requirements,_dep,_section,_quoted_value,_plain_value,_call_kw,_dedupe_deps,_excluded,PythonPackageProbe
    PythonPackageProbe: probe(1),_find_manifests(1),_find_requirements(1),_find_python_files(1),_read_metadata(2),_looks_like_fastapi(2),_confidence(4)
    _parse_pyproject(text)
    _parse_setup_cfg(text)
    _parse_setup_py(text)
    _parse_pyproject_dependencies(text)
    _parse_requirements(text)
    _dep(value)
    _section(text;name)
    _quoted_value(text;key)
    _plain_value(text;key)
    _call_kw(text;key)
    _dedupe_deps(items)
    _excluded(path)
  testql/discovery/probes/network/__init__.py:
  testql/discovery/probes/network/http_endpoint.py:
    e: _fetch,_looks_textual,_metadata,_parse_html,_limit,_asset_kind,_link_kind,HTTPPageProbe,_PageParser
    HTTPPageProbe: __init__(1),applicable(1),probe(1),evidence(3)
    _PageParser: __init__(1),handle_starttag(2),handle_data(1),handle_endtag(1)
    _fetch(url;timeout)
    _looks_textual(content_type)
    _metadata(original_url;response;content_type;parsed)
    _parse_html(text;base_url)
    _limit(items;limit)
    _asset_kind(tag;attrs)
    _link_kind(base_url;href)
  testql/discovery/registry.py:
    e: default_probes,discover_path,_cost_key,ProbeRegistry
    ProbeRegistry: __init__(3),run(1),discover(1)
    default_probes(scan_network;use_browser)
    discover_path(path;scan_network;use_browser)
    _cost_key(probe)
  testql/discovery/source.py:
    e: SourceKind,ArtifactSource
    SourceKind:
    ArtifactSource: from_value(2),path(0),to_dict(0)
  testql/doql_parser.py:
    e: parse_doql_file,DoqlParser
    DoqlParser: __init__(0),parse_file(1),parse(1),_parse_app_block(1),_parse_entity_block(2),_parse_workflow_block(2),_parse_interface_block(2),_parse_deploy_block(1)  # Parser for doql LESS files.
    parse_doql_file(path)
  testql/echo_schemas.py:
    e: APIContract,Entity,Workflow,Interface,SystemModel,ProjectEcho
    APIContract:  # API contract layer from toon tests.
    Entity:  # Entity from doql model.
    Workflow:  # Workflow from doql.
    Interface:  # Interface from doql.
    SystemModel:  # System model from doql.
    ProjectEcho: to_dict(0),to_text(0)  # Combined project echo for LLM consumption.
  testql/endpoint_detector.py:
  testql/generator.py:
  testql/generators/__init__.py:
  testql/generators/analyzers.py:
    e: ProjectAnalyzer
    ProjectAnalyzer: _detect_web_frontend(1),_detect_python_type(1),_has_argparse_usage(0),_detect_hardware(0),detect_project_type(0),run_full_analysis(0),_scan_directory_structure(0),_collect_patterns_from_tree(3),_analyze_python_tests(0),_extract_test_pattern(4),_detect_pattern_type(2),_extract_commands_and_assertions(1),_analyze_config_files(0),_analyze_api_routes(0),_analyze_api_routes_fallback(0),_analyze_scenarios(0)  # Analyzes project structure to discover testable patterns.
  testql/generators/base.py:
    e: TestPattern,ProjectProfile,BaseAnalyzer
    TestPattern:  # Discovered test pattern from source code.
    ProjectProfile:  # Analyzed project profile.
    BaseAnalyzer: __init__(1),_get_exclude_dirs(0),_should_exclude_path(1)  # Base class for project analyzers.
  testql/generators/convenience.py:
    e: generate_for_project,generate_for_workspace
    generate_for_project(project_path)
    generate_for_workspace(workspace_path)
  testql/generators/generators.py:
    e: APIGeneratorMixin,PythonTestGeneratorMixin,ScenarioGeneratorMixin,SpecializedGeneratorMixin
    APIGeneratorMixin: _generate_api_tests(1),_build_api_test_header(1),_build_api_test_config(1),_build_rest_section(1),_build_graphql_section(1),_build_websocket_section(1),_build_api_test_endpoints(1),_deduplicate_rest_routes(1),_build_api_test_assertions(0),_build_api_test_summary(1)  # Mixin for generating API-focused test scenarios.
    PythonTestGeneratorMixin: _generate_from_python_tests(1)  # Mixin for generating tests from existing Python tests.
    ScenarioGeneratorMixin: _generate_from_scenarios(1)  # Mixin for generating tests from OQL/CQL scenarios.
    SpecializedGeneratorMixin: _generate_api_integration_tests(1),_generate_cli_tests(1),_generate_lib_tests(1),_generate_frontend_tests(1),_generate_hardware_tests(1)  # Mixin for generating specialized test types.
  testql/generators/llm/__init__.py:
  testql/generators/llm/coverage_optimizer.py:
    e: CoverageReport,CoverageOptimizer,NoOpCoverageOptimizer
    CoverageReport:
    CoverageOptimizer: analyse(1)
    NoOpCoverageOptimizer: analyse(1)  # Default — returns an empty report.
  testql/generators/llm/edge_case_generator.py:
    e: EdgeCaseGenerator,NoOpEdgeCaseGenerator
    EdgeCaseGenerator: enrich(1)
    NoOpEdgeCaseGenerator: enrich(1)  # Default — returns the plan unchanged.
  testql/generators/multi.py:
    e: MultiProjectTestGenerator
    MultiProjectTestGenerator: __init__(1),discover_projects(0),analyze_all(0),generate_all(0),generate_cross_project_tests(1)  # Generator that operates across multiple projects in a worksp
  testql/generators/pipeline.py:
    e: _resolve_source,_resolve_target,sorted_sources,sorted_targets,run,write,PipelineResult
    PipelineResult:
    _resolve_source(spec)
    _resolve_target(spec)
    sorted_sources()
    sorted_targets()
    run()
    write(result;out)
  testql/generators/sources/__init__.py:
    e: get_source,available_sources
    get_source(name)
    available_sources()
  testql/generators/sources/base.py:
    e: BaseSource
    BaseSource: load(1)  # Convert an external artifact (OpenAPI / SQL DDL / .proto / S
  testql/generators/sources/graphql_source.py:
    e: _load_sdl,_type_to_query,_is_smoke_target,GraphQLSource
    GraphQLSource: load(1)  # GraphQL SDL → TestPlan with one smoke query per top-level ty
    _load_sdl(source)
    _type_to_query(t;endpoint)
    _is_smoke_target(t)
  testql/generators/sources/nl_source.py:
    e: NLSource
    NLSource: load(1)  # Thin wrapper over `NLDSLAdapter.parse()`.
  testql/generators/sources/openapi_source.py:
    e: _load_spec,_pick_success_status,_operation_to_step,_iter_operations,OpenAPISource
    OpenAPISource: load(1)  # `openapi.yaml` / `openapi.json` → TestPlan.
    _load_spec(source)
    _pick_success_status(responses)
    _operation_to_step(method;path;op_spec)
    _iter_operations(paths)
  testql/generators/sources/proto_source.py:
    e: _load_proto_text,_sample_value_for,_sample_fields_blob,_message_to_step,ProtoSource
    ProtoSource: load(1)  # `.proto` file or text → TestPlan with one round-trip step pe
    _load_proto_text(source)
    _sample_value_for(type_name)
    _sample_fields_blob(message)
    _message_to_step(message;schema_file)
  testql/generators/sources/sql_source.py:
    e: _load_sql_text,_crud_steps,_schema_fixture_from_ddl,SqlSource
    SqlSource: load(1)  # `*.sql` DDL → TestPlan with CRUD coverage queries.
    _load_sql_text(source)
    _crud_steps(table;dialect)
    _schema_fixture_from_ddl(ddl)
  testql/generators/sources/ui_source.py:
    e: _load_html,_navigate_step,_input_steps,_button_steps,UISource
    UISource: load(1)  # HTML snapshot → smoke GUI scenario.
    _load_html(source)
    _navigate_step(url)
    _input_steps(html)
    _button_steps(html)
  testql/generators/targets/__init__.py:
    e: get_target,available_targets
    get_target(name)
    available_targets()
  testql/generators/targets/base.py:
    e: BaseTarget
    BaseTarget: render(1)
  testql/generators/targets/nl_target.py:
    e: NLTarget
    NLTarget: render(1)
  testql/generators/targets/pytest_target.py:
    e: _safe_ident,_step_summary,_emit_test,PytestTarget
    PytestTarget: render(1)
    _safe_ident(name;fallback)
    _step_summary(step)
    _emit_test(step;index)
  testql/generators/targets/testtoon_target.py:
    e: TestToonTarget
    TestToonTarget: render(1)
  testql/generators/test_generator.py:
    e: TestGenerator
    TestGenerator: analyze(0),generate_tests(1)  # Main test generator combining analysis and generation capabi
  testql/interpreter/__init__.py:
    e: main
    main()
  testql/interpreter/_api_runner.py:
    e: _resolve_length,_navigate_step,_navigate_json_path,ApiRunnerMixin
    ApiRunnerMixin: _do_http_request(3),_store_api_response(2),_record_api_success(3),_record_api_http_error(2),_record_api_error(2),_cmd_api(2),_cmd_capture(2)  # Mixin providing HTTP API execution commands: API, CAPTURE.
    _resolve_length(root;path)
    _navigate_step(obj;key)
    _navigate_json_path(root;path)
  testql/interpreter/_assertions.py:
    e: AssertionsMixin
    AssertionsMixin: _cmd_assert_status(2),_cmd_assert_ok(2),_cmd_assert_contains(2),_cmd_assert_json(2)  # Mixin providing ASSERT_STATUS, ASSERT_OK, ASSERT_CONTAINS, A
  testql/interpreter/_converter.py:
  testql/interpreter/_encoder.py:
    e: EncoderMixin
    EncoderMixin: _encoder_url(0),_encoder_do_http(4),_encoder_call(5),_cmd_encoder_on(2),_cmd_encoder_off(2),_cmd_encoder_scroll(2),_cmd_encoder_click(2),_cmd_encoder_dblclick(2),_cmd_encoder_focus(2),_cmd_encoder_status(2),_cmd_encoder_page_next(2),_cmd_encoder_page_prev(2)  # Mixin providing all ENCODER_* hardware control commands.
  testql/interpreter/_flow.py:
    e: FlowMixin
    FlowMixin: _cmd_wait_for(2),_cmd_wait(2),_cmd_log(2),_cmd_print(2),_cmd_include(2),_emit_event(3)  # Mixin providing: WAIT, LOG, PRINT, INCLUDE and _emit_event.
  testql/interpreter/_gui.py:
    e: GuiMixin
    GuiMixin: _init_gui_driver(0),_cmd_gui_start(2),_start_playwright(2),_start_selenium(2),_cmd_gui_click(2),_cmd_gui_input(2),_cmd_gui_assert_visible(2),_cmd_gui_assert_text(2),_cmd_gui_capture(2),_cmd_gui_stop(2)  # Mixin providing desktop GUI test commands using Playwright.
  testql/interpreter/_parser.py:
    e: parse_iql,IqlLine,IqlScript
    IqlLine:
    IqlScript:
    parse_iql(source;filename)
  testql/interpreter/_shell.py:
    e: ShellMixin
    ShellMixin: _cmd_shell(2),_cmd_exec(2),_cmd_run(2),_cmd_assert_exit_code(2),_cmd_assert_stdout_contains(2),_cmd_assert_stderr_contains(2)  # Mixin providing shell command execution: SHELL, EXEC, RUN, A
  testql/interpreter/_testtoon_parser.py:
    e: _detect_separator,_parse_inline_array,_parse_inline_dict,_parse_value,_make_section,_make_data_row,parse_testtoon,validate_testtoon,_expand_config,_append_api_asserts,_expand_api,_expand_navigate,_expand_encoder,_expand_select,_expand_assert,_expand_steps,_expand_flow,_expand_oql,_expand_wait,_expand_include,_expand_record,_expand_generic,testtoon_to_iql,ToonSection,ToonScript
    ToonSection: validate(0)
    ToonScript:
    _detect_separator(line)
    _parse_inline_array(v)
    _parse_inline_dict(v)
    _parse_value(v)
    _make_section(m)
    _make_data_row(raw;section)
    parse_testtoon(text;filename)
    validate_testtoon(script)
    _expand_config(section;lines;line_num)
    _append_api_asserts(row;lines;line_num)
    _expand_api(section;lines;line_num)
    _expand_navigate(section;lines;line_num)
    _expand_encoder(section;lines;line_num)
    _expand_select(section;lines;line_num)
    _expand_assert(section;lines;line_num)
    _expand_steps(section;lines;line_num)
    _expand_flow(section;lines;line_num)
    _expand_oql(section;lines;line_num)
    _expand_wait(section;lines;line_num)
    _expand_include(section;lines;line_num)
    _expand_record(section;lines;line_num)
    _expand_generic(section;lines;line_num)
    testtoon_to_iql(text;filename)
  testql/interpreter/_unit.py:
    e: UnitMixin
    UnitMixin: _parse_pytest_args(1),_extract_pytest_summary(1),_run_pytest_subprocess(3),_handle_pytest_dry_run(2),_handle_pytest_success(2),_handle_pytest_error(3),_cmd_unit_pytest(2),_cmd_unit_pytest_discover(2),_cmd_unit_import(2),_cmd_unit_assert(2)  # Mixin providing unit test execution: UNIT_PYTEST, UNIT_IMPOR
  testql/interpreter/_websockets.py:
    e: WebSocketMixin
    WebSocketMixin: __init_subclass__(1),_get_ws_context(0),_cmd_ws_connect(2),_cmd_ws_send(2),_ws_do_receive(4),_cmd_ws_receive(2),_cmd_ws_assert_msg(2),_cmd_ws_close(2)  # Mixin for WebSocket testing support.
  testql/interpreter/converter/__init__.py:
  testql/interpreter/converter/core.py:
    e: convert_iql_to_testtoon,convert_file,convert_directory
    convert_iql_to_testtoon(source;filename)
    convert_file(src)
    convert_directory(dir_path)
  testql/interpreter/converter/dispatcher.py:
    e: dispatch
    dispatch(filtered;i)
  testql/interpreter/converter/handlers/__init__.py:
  testql/interpreter/converter/handlers/api.py:
    e: handle_api
    handle_api(filtered;i)
  testql/interpreter/converter/handlers/assertions.py:
    e: collect_assert
    collect_assert(filtered;j)
  testql/interpreter/converter/handlers/encoder.py:
    e: _encoder_action_fields,_advance_past_wait,handle_encoder
    _encoder_action_fields(action;args)
    _advance_past_wait(filtered;i)
    handle_encoder(filtered;i)
  testql/interpreter/converter/handlers/flow.py:
    e: handle_flow
    handle_flow(filtered;i)
  testql/interpreter/converter/handlers/include.py:
    e: handle_include
    handle_include(filtered;i)
  testql/interpreter/converter/handlers/navigate.py:
    e: handle_navigate
    handle_navigate(filtered;i)
  testql/interpreter/converter/handlers/record.py:
    e: handle_record_start,handle_record_stop
    handle_record_start(filtered;i)
    handle_record_stop(filtered;i)
  testql/interpreter/converter/handlers/select.py:
    e: handle_select
    handle_select(filtered;i)
  testql/interpreter/converter/handlers/unknown.py:
    e: handle_unknown
    handle_unknown(filtered;i)
  testql/interpreter/converter/handlers/wait.py:
    e: handle_wait
    handle_wait(filtered;i)
  testql/interpreter/converter/models.py:
    e: Row,Section
    Row:  # A row of values in a section.
    Section:  # A section in the converted output.
  testql/interpreter/converter/parsers.py:
    e: parse_api_args,parse_meta_from_args,parse_target_from_args,parse_commands,detect_scenario_type,extract_scenario_name
    parse_api_args(args)
    parse_meta_from_args(args)
    parse_target_from_args(args)
    parse_commands(source)
    detect_scenario_type(commands)
    extract_scenario_name(comments;filename)
  testql/interpreter/converter/renderer.py:
    e: build_config_section,_render_section_header,render_sections,build_header
    build_config_section(commands)
    _render_section_header(sec)
    render_sections(sections)
    build_header(scenario_name;scenario_type)
  testql/interpreter/dispatcher.py:
    e: CommandDispatcher
    CommandDispatcher: __init__(1),_discover_handlers(0),register(2),dispatch(3),list_commands(0),has_command(1)  # Central command dispatcher with auto-discovery and better er
  testql/interpreter/interpreter.py:
    e: IqlInterpreter
    IqlInterpreter: __init__(6),parse(2),_is_testtoon(2),execute(1),_dispatch(3),_cmd_set(2),_cmd_get(2)  # IQL interpreter — runs .testql.toon.yaml / .iql / .tql scrip
  testql/interpreter.py:
  testql/ir/__init__.py:
  testql/ir/assertions.py:
    e: Assertion
    Assertion: to_dict(0)  # Single assertion against a step's outcome.
  testql/ir/captures.py:
    e: Capture
    Capture: to_dict(0)  # Bind a value at `from_path` inside a step's payload to `var_
  testql/ir/fixtures.py:
    e: Fixture
    Fixture: to_dict(0)  # Declarative setup/teardown for a TestPlan.
  testql/ir/metadata.py:
    e: ScenarioMetadata
    ScenarioMetadata: to_dict(0)  # Header-level metadata for a TestPlan.
  testql/ir/plan.py:
    e: TestPlan
    TestPlan: to_dict(0),name(0),type(0)  # Adapter-neutral representation of a single test scenario.
  testql/ir/steps.py:
    e: Step,ApiStep,GuiStep,EncoderStep,ShellStep,UnitStep,NlStep,SqlStep,ProtoStep,GraphqlStep
    Step: to_dict(0)  # Base step. Subclasses add typed fields; `kind` discriminator
    ApiStep: __post_init__(0),to_dict(0)
    GuiStep: __post_init__(0),to_dict(0)
    EncoderStep: __post_init__(0),to_dict(0)
    ShellStep: __post_init__(0),to_dict(0)
    UnitStep: __post_init__(0),to_dict(0)
    NlStep: __post_init__(0),to_dict(0)  # Raw natural-language line that has not yet been resolved to 
    SqlStep: __post_init__(0),to_dict(0)
    ProtoStep: __post_init__(0),to_dict(0)
    GraphqlStep: __post_init__(0),to_dict(0)
  testql/ir_runner/__init__.py:
  testql/ir_runner/assertion_eval.py:
    e: _next_segment,navigate,_op_contains,_op_matches,evaluate,evaluate_all,AssertionResult
    AssertionResult: to_dict(0)
    _next_segment(current;segment)
    navigate(payload;path)
    _op_contains(actual;expected)
    _op_matches(actual;expected)
    evaluate(assertion;payload)
    evaluate_all(assertions;payload)
  testql/ir_runner/context.py:
    e: ExecutionContext
    ExecutionContext: record(1)  # State container threaded through every executor call.
  testql/ir_runner/engine.py:
    e: load_plan,_apply_captures,_run_step,run_plan,IRRunner
    IRRunner: __init__(0),run(2)  # Execute a `TestPlan` step-by-step against an `ExecutionConte
    load_plan(source)
    _apply_captures(step;result;ctx)
    _run_step(step;ctx)
    run_plan(plan)
  testql/ir_runner/executors/__init__.py:
    e: get_executor,register,supported_kinds
    get_executor(kind)
    register(kind;executor)
    supported_kinds()
  testql/ir_runner/executors/api.py:
    e: _resolve_url,_parse_response,_do_request,_payload,execute
    _resolve_url(path;ctx)
    _parse_response(text)
    _do_request(method;url;body;headers)
    _payload(status;data;headers)
    execute(step;ctx)
  testql/ir_runner/executors/base.py:
    e: step_label,_aggregate_assertion_status,_compose_message,assemble_result,error_result,skipped_result,StepExecutor
    StepExecutor: __call__(2)  # Callable contract every executor must satisfy.
    step_label(step;prefix)
    _aggregate_assertion_status(passed;dry_run)
    _compose_message(base;failed_msgs)
    assemble_result(name;payload;assertions;dry_run;base_message)
    error_result(name;exc)
    skipped_result(name;reason)
  testql/ir_runner/executors/encoder.py:
    e: _request_body,_do_call,execute
    _request_body(action;value;target)
    _do_call(method;url;body)
    execute(step;ctx)
  testql/ir_runner/executors/graphql.py:
    e: _post_graphql,_resolve_endpoint,execute
    _post_graphql(url;query;variables)
    _resolve_endpoint(step;ctx)
    execute(step;ctx)
  testql/ir_runner/executors/gui.py:
    e: execute
    execute(step;ctx)
  testql/ir_runner/executors/nl.py:
    e: execute
    execute(step;ctx)
  testql/ir_runner/executors/proto.py:
    e: _resolve_source,_instance_tuples,_run_check,execute
    _resolve_source(step;ctx)
    _instance_tuples(step)
    _run_check(check;message;instance)
    execute(step;ctx)
  testql/ir_runner/executors/shell.py:
    e: _aggregate_status,_payload,execute
    _aggregate_status(returncode;expect_exit_code)
    _payload(returncode;stdout;stderr)
    execute(step;ctx)
  testql/ir_runner/executors/sql.py:
    e: _get_connection,_classify,_execute_query,execute
    _get_connection(ctx)
    _classify(query)
    _execute_query(conn;query)
    execute(step;ctx)
  testql/ir_runner/executors/unit.py:
    e: _payload,execute
    _payload(returncode;stdout;stderr)
    execute(step;ctx)
  testql/ir_runner/interpolation.py:
    e: interp_value
    interp_value(value;store)
  testql/meta/__init__.py:
  testql/meta/confidence_scorer.py:
    e: _is_llm_resolved,_score_assertions,_score_typed,_score_step,score_plan,StepConfidence,PlanConfidence
    StepConfidence: to_dict(0)
    PlanConfidence: to_dict(0)
    _is_llm_resolved(step)
    _score_assertions(step)
    _score_typed(step)
    _score_step(step)
    score_plan(plan)
  testql/meta/coverage_analyzer.py:
    e: _load_text,_load_yaml,_build_report,_openapi_endpoints,_plan_endpoints,coverage_vs_openapi,_sql_tables,_plan_sql_tables,_extract_table_names,coverage_vs_sql,_proto_messages,_plan_proto_messages,coverage_vs_proto,analyze,CoverageReport
    CoverageReport: percent(0),to_dict(0)
    _load_text(source)
    _load_yaml(source)
    _build_report(contract;declared;covered)
    _openapi_endpoints(spec)
    _plan_endpoints(plan)
    coverage_vs_openapi(plan;spec)
    _sql_tables(ddl)
    _plan_sql_tables(plan)
    _extract_table_names(sql)
    coverage_vs_sql(plan;ddl_source)
    _proto_messages(proto)
    _plan_proto_messages(plan)
    coverage_vs_proto(plan;proto_source)
    analyze(plan;contract;source)
  testql/meta/mutator.py:
    e: _flipped_op,mutations_flip_assertion_op,_next_status,_tweak_status_mutation,mutations_tweak_status,mutations_remove_step,_scrambled,mutations_scramble_assertion_value,mutate,run_mutation_test,Mutation,MutationReport
    Mutation: to_dict(0)  # One mutated plan plus a description of what changed.
    MutationReport: killed_ratio(0),to_dict(0)
    _flipped_op(op)
    mutations_flip_assertion_op(plan)
    _next_status(status)
    _tweak_status_mutation(plan;step_idx;step)
    mutations_tweak_status(plan)
    mutations_remove_step(plan)
    _scrambled(value)
    mutations_scramble_assertion_value(plan)
    mutate(plan)
    run_mutation_test(plan;executor)
  testql/meta/self_test.py:
    e: generate_self_test_plan,run_self_test,SelfTestReport
    SelfTestReport: is_release_ready(0),to_dict(0)
    generate_self_test_plan(openapi)
    run_self_test(openapi)
  testql/openapi_generator.py:
    e: _extract_path_params,_extract_ep_params,generate_openapi_spec,generate_contract_tests_from_spec,OpenAPISpec,OpenAPIGenerator,ContractTestGenerator
    OpenAPISpec: to_dict(0),to_json(1),to_yaml(0)  # OpenAPI specification container.
    OpenAPIGenerator: __init__(1),generate(2),_normalize_path(1),_build_operation(1),_infer_tags(1),_extract_parameters(1),_build_request_body(1),_build_responses(1),save(2)  # Generate OpenAPI specs from detected endpoints.
    ContractTestGenerator: __init__(1),_load_spec(1),generate_contract_tests(1),_get_expected_status(2),validate_response(3)  # Generate contract tests from OpenAPI specs.
    _extract_path_params(path)
    _extract_ep_params(ep_params;existing)
    generate_openapi_spec(project_path;output;format)
    generate_contract_tests_from_spec(spec_path;output)
  testql/pipeline.py:
    e: GenerationContext,GenerationPipeline
    GenerationContext:  # Data collected during the _collect phase.
    GenerationPipeline: __init__(1),_collect(0),_emit(2),_emit_workspace(2),_emit_single(2),run(0),_is_workspace(1)  # Orchestrate project analysis and scenario generation.
  testql/report_generator.py:
    e: _adapt_test_entry,generate_report,TestResult,TestSuiteReport,ReportDataParser,HTMLReportGenerator
    TestResult:  # Single test result.
    TestSuiteReport:  # Test suite report data.
    ReportDataParser: parse_testql_results(1),to_json(1)  # Parse test results into structured data.json format.
    HTMLReportGenerator: __init__(1),generate(2),_render_html(1),_render_test_row(1)  # Generate HTML reports from test data.
    _adapt_test_entry(t)
    generate_report(data_json;output_html)
  testql/reporters/__init__.py:
  testql/reporters/console.py:
    e: report_console
    report_console(result)
  testql/reporters/json_reporter.py:
    e: report_json
    report_json(result)
  testql/reporters/junit.py:
    e: report_junit,JUnitReporter
    JUnitReporter: generate(2),_add_testcase(3)  # Generate JUnit XML from a TestQL ScriptResult.
    report_junit(result;suite_name)
  testql/results/__init__.py:
  testql/results/analyzer.py:
    e: inspect_source,analyze_topology,_check_confidence,_check_nodes,_check_edges,_check_interfaces,_check_evidence,_crawl_checks,_check_link_statuses,_check_asset_statuses,_head_check_urls,_sitemap_checks,_browser_checks,_check_browser_render,_check_browser_console,_check_browser_network,_sitemap_node,_check_sitemap_crawl,_check_sitemap_broken,_check_sitemap_duplicates,_web_checks,_page_node,_check_web_status,_check_web_title,_check_web_links,_check_web_assets,_check_web_forms,_status_code,_findings_from_checks,_actions_from_findings,_status_from_checks,_likely_cause,_action_type,_action_summary,_topology_id,_run_id,_safe
    inspect_source(source;scan_network;use_browser)
    analyze_topology(topology;scan_network;use_browser)
    _check_confidence(topology)
    _check_nodes(topology)
    _check_edges(topology)
    _check_interfaces(topology)
    _check_evidence(topology)
    _crawl_checks(topology;scan_network)
    _check_link_statuses(metadata;node_id)
    _check_asset_statuses(metadata;node_id)
    _head_check_urls(urls)
    _sitemap_checks(topology)
    _browser_checks(topology;use_browser)
    _check_browser_render(node_id;metadata)
    _check_browser_console(node_id;metadata)
    _check_browser_network(node_id;metadata)
    _sitemap_node(topology)
    _check_sitemap_crawl(sitemap;subpages)
    _check_sitemap_broken(sitemap;subpages)
    _check_sitemap_duplicates(sitemap;subpages)
    _web_checks(topology)
    _page_node(topology)
    _check_web_status(node_id;metadata)
    _check_web_title(node_id;metadata)
    _check_web_links(node_id;metadata)
    _check_web_assets(node_id;metadata)
    _check_web_forms(node_id;metadata)
    _status_code(metadata)
    _findings_from_checks(checks)
    _actions_from_findings(findings;topology)
    _status_from_checks(checks)
    _likely_cause(check)
    _action_type(finding)
    _action_summary(finding)
    _topology_id(topology)
    _run_id(topology)
    _safe(value)
  testql/results/artifacts.py:
    e: write_inspection_artifacts,_write_group,_metadata
    write_inspection_artifacts(topology;envelope;plan;out_dir)
    _write_group(target;prefix;contents)
    _metadata(topology;envelope;plan;written)
  testql/results/models.py:
    e: CheckResult,FailureFinding,SuggestedAction,TestResultEnvelope,RefactorPlan
    CheckResult: to_dict(0)
    FailureFinding: to_dict(0)
    SuggestedAction: to_dict(0)
    TestResultEnvelope: to_dict(0)
    RefactorPlan: from_envelope(2),to_dict(0)
  testql/results/serializers.py:
    e: render_result_envelope,render_refactor_plan,render_inspection,_render_data,_render_toon,_render_nlp,_render_nlp_dict,_clean
    render_result_envelope(envelope;fmt)
    render_refactor_plan(plan;fmt)
    render_inspection(topology;envelope;plan;fmt)
    _render_data(data;fmt)
    _render_toon(data)
    _render_nlp(envelope;plan)
    _render_nlp_dict(result;plan)
    _clean(value)
  testql/runner.py:
    e: parse_line,parse_script,main,DslCommand,ExecutionResult,DslCliExecutor
    DslCommand:
    ExecutionResult:
    DslCliExecutor: __init__(2),execute(1),_dispatch(1),cmd_api(1),cmd_wait(1),cmd_log(1),cmd_print(1),cmd_store(1),cmd_env(1),cmd_assert_status(1),cmd_assert_json(1),cmd_set_header(1),cmd_set_base_url(1),run_script(2),_format_cmd(1)
    parse_line(line)
    parse_script(content)
    main()
  testql/runners/__init__.py:
  testql/sumd_generator.py:
    e: generate_sumd,_header_section,_metadata_section,_architecture_section,_doql_declaration_section,_api_contract_section,_workflows_table_section,_configuration_section,_llm_suggestions_section,_workflow_snippet,save_sumd
    generate_sumd(project_echo;project_path)
    _header_section(project_name;version)
    _metadata_section(project_name;version)
    _architecture_section()
    _doql_declaration_section(project_echo;project_name;version)
    _api_contract_section(project_echo)
    _workflows_table_section(project_echo)
    _configuration_section(project_echo;project_name;version)
    _llm_suggestions_section(project_echo)
    _workflow_snippet(workflows;name;comment;cmd)
    save_sumd(project_echo;project_path;output_path)
  testql/sumd_parser.py:
    e: _parse_block_interfaces,_parse_api_interfaces,parse_sumd_file,SumdMetadata,SumdInterface,SumdWorkflow,SumdDocument,SumdParser
    SumdMetadata:  # Metadata from SUMD.
    SumdInterface:  # Interface from SUMD.
    SumdWorkflow:  # Workflow from SUMD.
    SumdDocument:  # Parsed SUMD document.
    SumdParser: parse_file(1),parse(1),_parse_metadata(1),_parse_interfaces(1),_parse_workflows(1),_parse_testql_scenarios(1),_parse_architecture(1),_extract_section(2),generate_testql_scenarios(1)  # Parser for SUMD markdown files.
    _parse_block_interfaces(content)
    _parse_api_interfaces(content)
    parse_sumd_file(path)
  testql/toon_parser.py:
    e: parse_toon_file,ToonParser
    ToonParser: __init__(0),parse_file(1),parse(1),_parse_api_block(1),_parse_assert_block(1),_parse_log_block(1)  # Parser for toon test files.
    parse_toon_file(path)
  testql/topology/__init__.py:
  testql/topology/builder.py:
    e: build_topology,_source_location,_root_metadata,_default_trace,_safe_id,_protocol_for_interface,_protocol_for_evidence,TopologyBuilder
    TopologyBuilder: __init__(2),build(1),_add_type_nodes(3),_add_interface_nodes(3),_add_dependency_nodes(3),_add_evidence_nodes(3),_add_page_schema_nodes(3)
    build_topology(source;scan_network;use_browser)
    _source_location(source)
    _root_metadata(manifest)
    _default_trace(topology)
    _safe_id(value)
    _protocol_for_interface(interface_type)
    _protocol_for_evidence(evidence)
  testql/topology/generator.py:
    e: NodeMappingConfig,TopologyScenarioGenerator
    NodeMappingConfig:  # Controls how topology nodes are mapped to IR steps.
    TopologyScenarioGenerator: __init__(2),from_trace(1),from_path(1),to_testtoon(1),_node_to_step(1),_interface_to_step(2),_page_to_step(1),_link_to_step(1),_form_to_step(1),_asset_to_step(1),_dependency_to_step(1),_evidence_to_step(1),_attach_assertions(2),_outgoing_edges(1),_condition_to_assertion(1),_location(1),_protocol_for_node(1)  # Generate executable TestPlans from topology traversal traces
  testql/topology/models.py:
    e: Condition,TopologyNode,TopologyEdge,TraversalTrace,TopologyManifest
    Condition: to_dict(0)
    TopologyNode: to_dict(1)
    TopologyEdge: to_dict(0)
    TraversalTrace: to_dict(0)
    TopologyManifest: to_dict(1),node(1)
  testql/topology/serializers.py:
    e: render_topology,_render_toon,_source_location
    render_topology(topology;fmt;include_manifest)
    _render_toon(data)
    _source_location(source)
  testql/topology/sitemap.py:
    e: build_sitemap,_extract_internal_links,_resolve_urls,_crawl_subpage,_is_html,_add_sitemap_nodes,_looks_textual,_parse_subpage,_SubpageParser
    _SubpageParser: __init__(0),handle_starttag(2),handle_data(1),handle_endtag(1)
    build_sitemap(topology;max_pages;timeout)
    _extract_internal_links(page_node;max_pages)
    _resolve_urls(base_url;links)
    _crawl_subpage(url;base_url;timeout)
    _is_html(content_type;text)
    _add_sitemap_nodes(topology;base_url;crawled;max_pages)
    _looks_textual(content_type)
    _parse_subpage(text)
  tests/fixtures/discovery/python_pkg/sample_api/__init__.py:
  tests/fixtures/discovery/python_pkg/sample_api/main.py:
    e: health
    health()
  tests/test_adapter_capture_syntax.py:
    e: TestTestToonCaptureByIndex,TestTestToonCaptureByName,TestUnresolvedCaptureSilentlyDropped,TestSqlAdapterCapture,TestSqlCaptureExecutesEndToEnd
    TestTestToonCaptureByIndex: test_parse_attaches_capture_to_first_step(0),test_round_trip(0)
    TestTestToonCaptureByName: test_parse_attaches_via_step_name(0)
    TestUnresolvedCaptureSilentlyDropped: test_unknown_target_is_ignored(0)
    TestSqlAdapterCapture: test_parse_attaches_to_named_step(0),test_round_trip_emits_capture_section(0),test_unknown_query_is_ignored(0)
    TestSqlCaptureExecutesEndToEnd: test_parsed_capture_chains_through_runner(0)
  tests/test_adapters_base.py:
    e: _DummyAdapter,TestDSLDetectionResult,TestValidationIssue,TestReadSource,TestAdapterRegistry,TestDefaultRegistry,TestBaseAdapterDefaultValidate
    _DummyAdapter: detect(1),parse(1),render(1)
    TestDSLDetectionResult: test_defaults(0)
    TestValidationIssue: test_minimal(0)
    TestReadSource: test_string_passthrough(0),test_path_reads_file(1),test_string_pointing_to_file(1)
    TestAdapterRegistry: test_register_and_get(0),test_register_requires_name(0),test_unregister_and_clear(0),test_by_extension(1),test_by_extension_prefers_longest_match(0),test_detect_falls_back_to_content(0),test_detect_returns_none_when_no_match(0)
    TestDefaultRegistry: test_singleton(0),test_testtoon_preregistered(0)
    TestBaseAdapterDefaultValidate: test_validate_default_empty(0)
  tests/test_api_handler.py:
    e: TestCollectAssert,TestHandleApi
    TestCollectAssert: test_no_assert(0),test_assert_status(0),test_assert_status_invalid_defaults_200(0),test_assert_ok(0),test_assert_json_three_parts(0),test_assert_contains_one_part(0),test_multiple_asserts(0),test_stops_at_non_assert(0),test_empty(0)
    TestHandleApi: test_simple_get(0),test_post_with_assert_status(0),test_with_assert_json(0),test_multiple_api_calls(0),test_stops_at_non_api(0),test_columns_without_assert(0)
  tests/test_browser_discovery.py:
    e: mock_playwright,test_playwright_probe_collects_console_and_network,FakePlaywright,FakeBrowserLauncher,FakeBrowser,FakePage,FakePlaywrightImport
    FakePlaywright: __enter__(0),__exit__(0),chromium(0)
    FakeBrowserLauncher: launch(0)
    FakeBrowser: new_page(0),close(0)
    FakePage: __init__(0),on(2),goto(3),title(0),evaluate(1)
    FakePlaywrightImport: sync_playwright(0)
    mock_playwright()
    test_playwright_probe_collects_console_and_network(mock_playwright)
  tests/test_cli.py:
    e: TestCliHelp,TestSuiteCommand
    TestCliHelp: test_help(0),test_version(0),test_subcommands_listed(0),test_run_help(0),test_suite_help(0),test_list_help(0),test_generate_help(0),test_endpoints_help(0),test_init_help(0),test_echo_help(0)
    TestSuiteCommand: test_suite_no_files_exits_1(1),test_list_no_files(1),test_list_with_toon_file(1),test_list_format_simple(1),test_list_format_json(1)
  tests/test_converter.py:
    e: TestRow,TestSection,TestConvertIqlToTesttoon,TestConvertFile,TestConvertDirectory
    TestRow: test_row_creation(0),test_row_empty(0),test_row_multiple_fields(0)
    TestSection: test_section_creation(0),test_section_with_rows(0),test_section_with_comment(0)
    TestConvertIqlToTesttoon: test_navigate_command(0),test_scenario_name_from_filename(0),test_header_present(0),test_click_converts_to_flow(0),test_assert_text_converts(0),test_empty_source(0),test_get_request(0),test_default_filename(0),test_returns_string(0),test_multiline_script(0)
    TestConvertFile: test_creates_output_file(1),test_output_filename_pattern(1),test_iql_extension(1),test_output_is_in_same_dir(1),test_output_content_has_scenario(1),test_returns_path(1)
    TestConvertDirectory: test_empty_directory(1),test_converts_tql_files(1),test_converts_iql_files(1),test_converts_multiple_files(1),test_returns_list_of_paths(1),test_recursive_subdirectory(1),test_ignores_non_tql_files(1)
  tests/test_converter_handlers.py:
    e: TestParseApiArgs,TestParseTargetFromArgs,TestParseMetaFromArgs,TestParseCommands,TestDetectScenarioType,TestExtractScenarioName,TestHandleWait,TestHandleNavigate,TestHandleSelect,TestHandleEncoder,TestHandleFlow,TestHandleRecord,TestHandleInclude,TestHandleUnknown,TestDispatch
    TestParseApiArgs: test_method_and_path(0),test_quoted_path(0),test_no_args_defaults(0),test_strips_json_body(0),test_uppercases_method(0)
    TestParseTargetFromArgs: test_double_quoted(0),test_single_quoted(0),test_unquoted_first_token(0),test_empty(0)
    TestParseMetaFromArgs: test_json_dict(0),test_no_meta(0),test_raw_dict_fallback(0)
    TestParseCommands: test_navigate(0),test_comment_collected(0),test_blank_line(0),test_empty_source(0),test_uppercase_cmd(0)
    TestDetectScenarioType: test_api_only(0),test_gui_navigate(0),test_encoder(0),test_e2e(0),test_interaction_record(0)
    TestExtractScenarioName: test_from_comment(0),test_fallback_filename(0),test_skip_usage_comments(0)
    TestHandleWait: test_single_wait(0),test_multiple_waits(0),test_invalid_ms_defaults_100(0),test_stops_at_non_wait(0)
    TestHandleNavigate: test_single_navigate(0),test_navigate_with_wait(0),test_multiple_navigates(0),test_stops_at_non_navigate(0)
    TestHandleSelect: test_select_option(0),test_plain_select(0),test_multiple_selects(0),test_stops_at_non_select(0)
    TestHandleEncoder: test_encoder_focus(0),test_encoder_scroll(0),test_encoder_scroll_invalid_value(0),test_encoder_with_wait(0),test_multiple_encoder_commands(0)
    TestHandleFlow: test_app_start(0),test_session_start(0),test_multiple_flow_commands(0),test_stops_at_non_flow(0),test_flow_commands_frozenset(0)
    TestHandleRecord: test_record_start(0),test_record_stop(0)
    TestHandleInclude: test_include(0)
    TestHandleUnknown: test_unknown_command(0)
    TestDispatch: test_dispatches_navigate(0),test_dispatches_wait(0),test_dispatches_select(0),test_dispatches_encoder(0),test_dispatches_flow(0),test_dispatches_record_start(0),test_dispatches_record_stop(0),test_dispatches_include(0),test_dispatches_unknown(0)
  tests/test_detectors.py:
    e: _write,TestEndpointInfoModel,TestFastAPIDetector,TestFlaskDetector,TestUnifiedDetector,TestOpenAPIDetector,TestExpressDetector
    TestEndpointInfoModel: test_to_testql_api_call(1),test_defaults(1)
    TestFastAPIDetector: test_detects_route_decorator(1),test_empty_project(1),test_non_route_decorators_ignored(1)
    TestFlaskDetector: test_detects_route(1),test_empty_project(1)
    TestUnifiedDetector: test_returns_list(1),test_detects_fastapi(1),test_detectors_used_populated(1)
    TestOpenAPIDetector: test_empty_project(1),test_detects_yaml_spec(1),test_detects_json_spec(1),test_framework_is_openapi(1),test_base_path_from_servers(1),test_base_path_swagger2(1),test_x_extension_methods_skipped(1),test_invalid_yaml_skipped(1),test_spec_without_paths_skipped(1)
    TestExpressDetector: test_empty_project(1),test_detects_app_get(1),test_detects_router_post(1),test_framework_is_express(1),test_typescript_file_detected(1)
    _write(tmp_path;name;content)
  tests/test_discovery.py:
    e: TestDiscoveryCore,TestDiscoveryCli
    TestDiscoveryCore: test_empty_directory_is_inferred(1),test_python_package_probe_detects_fastapi(0),test_node_package_probe_detects_node_and_frontend_markers(0),test_openapi_probe_detects_openapi3_interface(0),test_dockerfile_probe_detects_container_metadata(0),test_compose_probe_detects_services(0),test_registry_returns_raw_probe_results(0),test_self_discovery_detects_current_project_root(0),test_self_discovery_detects_testql_package_directory(0)
    TestDiscoveryCli: test_discover_summary_output(0),test_discover_json_output(0),test_discover_manifest_output(0),test_discover_missing_path_exits_nonzero(0)
  tests/test_dispatcher.py:
    e: TestCommandDispatcher,TestDispatcherIntegration
    TestCommandDispatcher: interpreter(0),dispatcher(1),test_auto_discovery(1),test_has_command(1),test_dispatch_known_command(2),test_dispatch_unknown_command(2),test_dispatch_with_suggestion(2),test_register_custom_command(2),test_case_insensitive_dispatch(1)  # Test CommandDispatcher functionality.
    TestDispatcherIntegration: interpreter(0),test_interpreter_uses_dispatcher(1),test_dispatch_through_interpreter(1),test_all_mixin_commands_discovered(1)  # Test CommandDispatcher integration with IqlInterpreter.
  tests/test_doql_parser_sumd_gen.py:
    e: TestDoqlParser,TestHeaderSection,TestMetadataSection,TestArchitectureSection,TestGenerateSumd,TestApiContractSection,TestWorkflowsTableSection,TestConfigurationSection,TestLlmSuggestionsSection,TestSaveSumd
    TestDoqlParser: test_init(0),test_parse_empty(0),test_parse_app_block(0),test_parse_entities(0),test_entity_fields(0),test_entity_fields_contain_domain(0),test_parse_workflow(0),test_parse_interface(0),test_parse_resets_between_calls(0),test_parse_file(1),test_no_app_block(0)
    TestHeaderSection: test_contains_project_name(0),test_returns_list(0)
    TestMetadataSection: test_contains_name(0),test_contains_version(0)
    TestArchitectureSection: test_contains_code_block(0),test_mentions_doql(0)
    TestGenerateSumd: _make_echo(0),test_returns_string(1),test_contains_project_name(1),test_contains_version(1),test_contains_metadata_section(1),test_contains_architecture_section(1),test_uses_path_name_as_fallback(1),test_interfaces_included(1),test_entities_not_in_base_output(1),test_workflows_included(1)
    TestApiContractSection: test_no_endpoints_returns_empty(0),test_with_endpoints(0),test_endpoint_with_description(0)
    TestWorkflowsTableSection: test_no_workflows_returns_empty(0),test_with_workflows(0),test_long_command_truncated(0)
    TestConfigurationSection: test_basic(0),test_with_base_url(0)
    TestLlmSuggestionsSection: test_has_testql_commands(0),test_with_test_workflow(0),test_with_install_workflow(0)
    TestSaveSumd: test_saves_to_default_path(1),test_saves_to_custom_path(1)
  tests/test_echo.py:
    e: write_toon,TestFindDoqlFile,TestFindToonPath,TestGenerateContext,TestExtractEndpoint,TestExtractAssert,TestParseToonScenarios,TestFmtInterfaces,TestFmtWorkflows,TestFmtContracts,TestFmtEntities,TestFormatTextOutput
    TestFindDoqlFile: test_finds_less_file(1),test_prefers_less_over_css(1),test_returns_none_when_missing(1)
    TestFindToonPath: test_returns_testql_scenarios_if_exists(1),test_falls_back_to_path(1)
    TestGenerateContext: test_returns_dict_with_project(1),test_no_doql_when_excluded(1),test_no_toon_when_excluded(1),test_empty_contracts_when_no_toon_files(1)
    TestExtractEndpoint: test_dict_value(0),test_string_value(0)
    TestExtractAssert: test_basic(0)
    TestParseToonScenarios: test_empty_dir(1),test_parses_single_file(1),test_multiple_http_methods(1),test_skips_empty_files(1),test_assert_blocks_parsed(1)
    TestFmtInterfaces: test_empty_when_no_system_model(0),test_shows_interfaces(0),test_empty_interfaces_returns_empty(0)
    TestFmtWorkflows: test_empty_when_no_workflows(0),test_shows_workflow_name(0)
    TestFmtContracts: test_empty_when_no_contracts(0),test_shows_contract_name(0),test_truncates_long_endpoint_list(0)
    TestFmtEntities: test_empty_when_no_entities(0),test_shows_entity_count(0)
    TestFormatTextOutput: test_returns_string(1),test_contains_project_name(1)
    write_toon(tmp_path;name;content)
  tests/test_echo_doql_parser.py:
    e: TestParseKvBlock,TestParseAppBlock,TestParseEntities,TestParseInterfaces,TestParseWorkflows,TestParseDeploy,TestParseEnvironment,TestParseIntegrations,TestParseDoqlLess
    TestParseKvBlock: test_simple(0),test_empty(0),test_no_colon_line_ignored(0),test_strips_trailing_semicolon(0)
    TestParseAppBlock: test_parses_name_and_version(0),test_no_app_block_returns_empty(0)
    TestParseEntities: test_count(0),test_entity_name(0),test_annotations_extracted(0),test_fields_extracted(0),test_no_entities_returns_empty(0),test_entity_without_annotations(0)
    TestParseInterfaces: test_count(0),test_type(0),test_framework(0),test_no_interfaces(0)
    TestParseWorkflows: test_count(0),test_name(0),test_trigger(0),test_steps(0),test_annotations(0),test_no_workflows(0)
    TestParseDeploy: test_platform(0),test_no_deploy(0)
    TestParseEnvironment: test_name(0),test_host(0),test_no_environment(0)
    TestParseIntegrations: test_count(0),test_name(0),test_types_deduped(0),test_no_integrations(0)
    TestParseDoqlLess: test_returns_all_keys(1),test_app_name_in_result(1),test_entities_count(1)
  tests/test_echo_schemas_helpers.py:
    e: TestAPIContract,TestEntity,TestWorkflow,TestInterface,TestSystemModel,TestProjectEcho,TestEchoHelpers
    TestAPIContract: test_defaults(0)
    TestEntity: test_create(0),test_with_all_fields(0)
    TestWorkflow: test_defaults(0),test_with_values(0)
    TestInterface: test_create(0),test_no_framework(0)
    TestSystemModel: test_defaults(0)
    TestProjectEcho: _make_echo(0),test_to_dict_has_keys(0),test_to_dict_api_contract(0),test_to_dict_interfaces(0),test_to_dict_entities(0),test_to_dict_workflows(0),test_to_dict_is_json_serializable(0),test_to_text_contains_project_name(0),test_to_text_contains_interface(0),test_to_text_contains_workflow(0),test_to_text_contains_endpoints(0),test_to_text_docker_deploy(0),test_to_text_no_endpoints(0),test_to_text_empty_interfaces(0),test_to_dict_deploy_info(0)
    TestEchoHelpers: test_collect_toon_data_missing_path(2),test_collect_toon_data_single_file(2),test_collect_toon_data_directory(2),test_collect_doql_data_missing(2),test_render_echo_json(0),test_render_echo_text(0)
  tests/test_encoder_routes.py:
    e: test_normalize_legacy_test_path,test_normalize_legacy_view_path,test_normalize_testql_prefixed_path,test_normalize_passthrough_diagnostics_path,test_normalize_testtoon_path,test_resolve_new_format
    test_normalize_legacy_test_path()
    test_normalize_legacy_view_path()
    test_normalize_testql_prefixed_path()
    test_normalize_passthrough_diagnostics_path()
    test_normalize_testtoon_path()
    test_resolve_new_format()
  tests/test_generate_cmd.py:
    e: TestIsWorkspace,TestGenerateCommand
    TestIsWorkspace: test_has_pyproject_returns_false(1),test_has_setup_py_returns_false(1),test_workspace_dir_without_init(1),test_workspace_dir_with_init_returns_false(1),test_no_workspace_dirs_returns_false(1),test_multiple_workspace_dirs(1)
    TestGenerateCommand: _make_pipeline_ctx(1),test_analyze_only_single_project(1),test_analyze_only_workspace(1),test_generate_single_project(1),test_analyze_command(1)
  tests/test_generate_ir_cli.py:
    e: TestGenerateIRCLI
    TestGenerateIRCLI: test_command_exists(0),test_round_trip_to_stdout(1),test_writes_to_file(1),test_bad_from_arg_errors(0),test_legacy_generate_still_works(0)
  tests/test_generators.py:
    e: TestBaseAnalyzer,TestProjectAnalyzerDetectType,TestTestPattern
    TestBaseAnalyzer: test_init(1),test_get_exclude_dirs(1),test_should_exclude_path_venv(1),test_should_exclude_path_src(1)
    TestProjectAnalyzerDetectType: test_detect_python_api_fastapi(1),test_detect_python_api_flask(1),test_detect_python_cli(1),test_detect_python_lib(1),test_detect_hardware(1),test_detect_mixed_default(1),test_detect_web_frontend(1),test_detect_web_frontend_missing_e2e_markers(1)
    TestTestPattern: test_defaults(0),test_metadata(0)
  tests/test_graphql_adapter.py:
    e: TestClassifyOperation,TestParseVariables,TestParseSchema,TestSubscriptionPlan,TestAdapterDetect,TestAdapterParse,TestAdapterRender,TestRegistration,TestHasGraphQLCore
    TestClassifyOperation: test_query(0),test_mutation(0),test_subscription(0),test_default_query(0),test_empty(0)
    TestParseVariables: test_basic(0),test_no_braces(0),test_bool_null(0),test_float(0),test_empty(0)
    TestParseSchema: test_object_type(0),test_scalar(0),test_input_renamed_to_input_object(0),test_enum(0),test_empty(0)
    TestSubscriptionPlan: test_to_dict(0)
    TestAdapterDetect: test_by_extension(1),test_by_header(0),test_negative(0)
    TestAdapterParse: test_metadata(0),test_endpoint_in_config(0),test_query_step(0),test_mutation_step(0),test_subscription_step(0),test_asserts_attached(0)
    TestAdapterRender: test_round_trip_step_count(0)
    TestRegistration: test_registered(0)
    TestHasGraphQLCore: test_returns_bool(0)
  tests/test_gui_execution.py:
    e: TestGuiExecution,TestGuiDriverSelection
    TestGuiExecution: interpreter(0),test_gui_start_dry_run(1),test_gui_click_dry_run(1),test_gui_input_dry_run(1),test_gui_assert_visible_dry_run(1),test_gui_assert_text_dry_run(1),test_gui_capture_dry_run(1),test_gui_stop_dry_run(1),test_gui_click_no_session_error(1),test_gui_start_no_args_error(1)  # Test GUI commands in dry-run mode (full tests require Playwr
    TestGuiDriverSelection: interpreter(0),test_gui_driver_default_playwright(2),test_gui_driver_selenium_fallback(2)  # Test GUI driver selection and initialization.
  tests/test_interpreter.py:
    e: TestParseIql,TestParseTestTOON,TestTestTOONExpansion,TestIqlInterpreter
    TestParseIql: test_empty(0),test_comments_ignored(0),test_basic_commands(0)
    TestParseTestTOON: test_empty(0),test_meta(0),test_api_section(0),test_encoder_section(0),test_validation_pass(0),test_validation_fail(0)
    TestTestTOONExpansion: test_api_expansion(0),test_encoder_expansion(0),test_config_expansion(0),test_navigate_expansion(0)
    TestIqlInterpreter: test_dry_run_api(0),test_set_get(0),test_testtoon_dry_run(0)
  tests/test_ir.py:
    e: TestScenarioMetadata,TestAssertion,TestFixture,TestStepVariants,TestTestPlan
    TestScenarioMetadata: test_defaults(0),test_to_dict_minimal(0),test_to_dict_full(0)
    TestAssertion: test_defaults(0),test_to_dict_minimal(0),test_to_dict_full(0)
    TestFixture: test_defaults(0),test_to_dict(0)
    TestStepVariants: test_base_step_kind(0),test_api_step(0),test_gui_step(0),test_encoder_step(0),test_shell_step(0),test_unit_step(0),test_nl_step(0),test_sql_step(0),test_proto_step(0),test_graphql_step(0),test_step_with_asserts_and_wait(0)
    TestTestPlan: test_empty(0),test_name_and_type_shortcuts(0),test_to_dict_round_trip_shape(0)
  tests/test_ir_captures.py:
    e: TestCaptureDataclass,TestStepCapturesField
    TestCaptureDataclass: test_minimal(0),test_to_dict(0)
    TestStepCapturesField: test_default_empty(0),test_attaches_to_api_step(0),test_to_dict_omits_empty_captures(0),test_to_dict_includes_populated_captures(0),test_works_on_sql_step(0)
  tests/test_ir_runner_assertion_eval.py:
    e: TestNavigate,TestOperators,TestResultShape
    TestNavigate: test_empty_path_returns_payload(0),test_dotted_dict_path(0),test_list_index(0),test_missing_key(0),test_none_short_circuits(0),test_attribute_fallback(0)
    TestOperators: test_op(4),test_unknown_op(0),test_lt_with_none_actual(0)
    TestResultShape: test_message_on_fail(0),test_passing_has_no_message(0),test_to_dict(0),test_evaluate_all(0)
  tests/test_ir_runner_captures.py:
    e: _plan,TestSqlCaptures,TestShellCaptures,TestMissingPath,TestErrorAndSkippedSteps,TestChainedInterpolation
    TestSqlCaptures: test_capture_from_first_row(0),test_capture_chains_into_next_step(0)
    TestShellCaptures: test_capture_returncode(0)
    TestMissingPath: test_unknown_path_warns_but_passes(0)
    TestErrorAndSkippedSteps: test_error_step_does_not_capture(0)
    TestChainedInterpolation: test_captured_value_interpolated_in_subsequent_step(0)
    _plan()
  tests/test_ir_runner_engine.py:
    e: _plan,TestLoadPlan,TestSupportedKinds,TestEngineDryRun,TestEngineSqlEndToEnd,TestEngineShell,TestEngineUnknownKind,TestRegisterCustomExecutor,TestRunnerVariables
    TestLoadPlan: test_passthrough_testplan(0),test_unknown_source(0)
    TestSupportedKinds: test_all_step_kinds_have_executor(0)
    TestEngineDryRun: test_api_dry_run_does_not_call_network(0),test_summary_format(0)
    TestEngineSqlEndToEnd: test_sqlite_in_memory_round_trip(0),test_failing_assertion_makes_plan_not_ok(0)
    TestEngineShell: test_echo_succeeds(0),test_expect_exit_code(0)
    TestEngineUnknownKind: test_unknown_kind_records_error(0)
    TestRegisterCustomExecutor: test_register_custom_kind(0)
    TestRunnerVariables: test_variables_persist_across_steps(0)
    _plan()
  tests/test_ir_runner_executors.py:
    e: TestSqlExecutor,TestShellExecutor,TestProtoExecutor,TestSkippedExecutors,TestDryRunExecutors
    TestSqlExecutor: test_dry_run(0),test_select_returns_columns(0),test_invalid_sql_returns_error(0)
    TestShellExecutor: test_zero_exit(0),test_nonzero_warning(0),test_assertion_drives_status(0)
    TestProtoExecutor: test_round_trip(1),test_unknown_message(1),test_no_source(0)
    TestSkippedExecutors: test_nl_skipped(0),test_gui_skipped(0),test_gui_dry_run_passes(0)
    TestDryRunExecutors: test_unit_dry_run(0),test_unit_empty_target_errors(0),test_encoder_dry_run(0),test_encoder_unknown_action(0),test_graphql_dry_run(0),test_graphql_subscription_skipped(0),test_api_dry_run_url_resolution(0)
  tests/test_ir_runner_interpolation.py:
    e: _store,TestInterpValue
    TestInterpValue: test_string_brace_form(0),test_string_dollar_form(0),test_unset_passthrough(0),test_dict_recursion(0),test_list_recursion(0),test_nested(0),test_non_string_passthrough(0)
    _store()
  tests/test_meta_confidence.py:
    e: TestPlanConfidence,TestStepReasons
    TestPlanConfidence: test_empty_plan_zero(0),test_strong_step_high_score(0),test_step_without_asserts_lower(0),test_nl_unresolved_lower(0),test_nl_llm_resolved_lowest(0),test_multi_assert_bonus(0),test_per_step_scores_recorded(0),test_clamping(0),test_to_dict(0)
    TestStepReasons: test_reasons_explain_score(0),test_llm_reason(0)
  tests/test_meta_coverage.py:
    e: TestOpenAPICoverage,TestSqlCoverage,TestProtoCoverage,TestAnalyze,TestReportShape
    TestOpenAPICoverage: test_full(0),test_partial(0),test_empty_plan(0),test_empty_spec(0),test_load_dict(0)
    TestSqlCoverage: test_table_in_select(0),test_partial(0)
    TestProtoCoverage: test_full(0),test_partial(0)
    TestAnalyze: test_openapi_dispatch(0),test_unknown_contract(0)
    TestReportShape: test_to_dict(0)
  tests/test_meta_mutator.py:
    e: _sample_plan,TestFlipOp,TestTweakStatus,TestRemoveStep,TestScrambleValue,TestMutate,TestMutationHarness,TestReportShape
    TestFlipOp: test_flips_eq_to_ne(0),test_flip_does_not_mutate_original(0),test_unknown_op_skipped(0)
    TestTweakStatus: test_one_per_api_step(0),test_status_assertion_also_updated(0),test_skips_non_api(0)
    TestRemoveStep: test_one_mutation_per_step(0),test_each_mutation_has_one_fewer_step(0)
    TestScrambleValue: test_skips_status_assertions(0),test_int_increments(0),test_bool_negated(0),test_string_suffixed(0),test_unscrambleable_skipped(0)
    TestMutate: test_combines_all_mutators(0)
    TestMutationHarness: test_perfect_executor_kills_all(0),test_weak_executor_lets_mutations_survive(0),test_failing_baseline_returns_empty(0)
    TestReportShape: test_to_dict(0)
    _sample_plan()
  tests/test_meta_self_test.py:
    e: TestGenerateSelfTestPlan,TestRunSelfTest,TestSelfTestCLI,TestAgainstFrameworkOwnSpec
    TestGenerateSelfTestPlan: test_loads_from_path(1)
    TestRunSelfTest: test_returns_report(1),test_release_ready_when_full_coverage(1),test_to_dict_shape(1)
    TestSelfTestCLI: test_help(0),test_human_output(1),test_json_output(1)
    TestAgainstFrameworkOwnSpec: test_real_openapi_yaml(0)  # Plan gate: testql exercising its own openapi.yaml hits the 1
  tests/test_misc_cmds.py:
    e: TestInitCommand,TestCreateCommand
    TestInitCommand: test_creates_dirs_and_config(1),test_config_contains_project_name(1),test_api_type_creates_api_template(1),test_gui_type_creates_gui_template(1),test_encoder_type_creates_encoder_template(1),test_all_type_creates_all_templates(1),test_existing_config_not_overwritten(1),test_default_path_is_current_dir(1)
    TestCreateCommand: test_creates_test_file(1),test_file_contains_name(1),test_fails_if_exists_without_force(1),test_force_overwrites_existing(1),test_api_type(1),test_with_module(1),test_creates_output_dir_if_missing(1)
  tests/test_network_discovery.py:
    e: test_discover_url_requires_scan_network_for_match,test_topology_url_builds_page_schema_nodes,test_inspect_url_nlp_passes_with_mocked_network,test_inspect_cli_url_json_with_scan_network,test_inspect_url_reports_http_failure,test_inspect_url_builds_sitemap_with_mocked_network,FakeClient,FakeErrorClient
    FakeClient: __init__(0),__enter__(0),__exit__(3),get(1),head(1)
    FakeErrorClient:
    test_discover_url_requires_scan_network_for_match(monkeypatch)
    test_topology_url_builds_page_schema_nodes(monkeypatch)
    test_inspect_url_nlp_passes_with_mocked_network(monkeypatch)
    test_inspect_cli_url_json_with_scan_network(monkeypatch)
    test_inspect_url_reports_http_failure(monkeypatch)
    test_inspect_url_builds_sitemap_with_mocked_network(monkeypatch)
  tests/test_nl_adapter.py:
    e: TestDetect,TestParseHeader,TestParsePolishLoginScenario,TestParseEnglishApiScenario,TestParseUnresolved,TestSqlAndEncoder,TestRender,TestAdapterRegistration,TestDeterministicCoverage
    TestDetect: test_detect_by_extension(1),test_detect_by_header(0),test_negative(0)
    TestParseHeader: test_metadata(0),test_default_lang_when_missing(0),test_default_type_when_missing(0)
    TestParsePolishLoginScenario: plan(0),test_step_count(1),test_navigate(1),test_input_email(1),test_input_password(1),test_click(1),test_assert_visible(1),test_assert_url_contains(1)
    TestParseEnglishApiScenario: plan(0),test_count(1),test_get(1),test_status_assert(1),test_post(1),test_wait(1)
    TestParseUnresolved: test_unknown_line_becomes_nl_step(0),test_llm_fallback_when_resolver_set(0)
    TestSqlAndEncoder: test_sql_intent(0),test_encoder_on(0),test_encoder_click(0)
    TestRender: test_round_trip_preserves_intents(0),test_render_includes_header(0)
    TestAdapterRegistration: test_registered(0),test_extension_lookup(1)
    TestDeterministicCoverage: test_polish_coverage(0)  # Plan gate: ≥95% of intent-bearing lines resolve deterministi
  tests/test_nl_entity_extractor.py:
    e: TestQuoted,TestBacktick,TestPath,TestSelector,TestHttpMethod,TestNumber,TestStripQuotesAndBackticks,TestSplitOnPreposition,TestTrimFieldNouns
    TestQuoted: test_double_quoted(0),test_single_quoted(0),test_no_match(0),test_all_quoted(0)
    TestBacktick: test_first(0),test_all(0),test_none(0)
    TestPath: test_backticked_path(0),test_quoted_path(0),test_raw_path(0),test_path_with_query(0),test_no_path(0),test_does_not_match_word_with_slash(0)
    TestSelector: test_attribute_selector(0),test_id_selector(0),test_class_selector(0),test_raw_selector(0),test_skips_path(0),test_none(0)
    TestHttpMethod: test_get(0),test_lowercase(0),test_no_method(0)
    TestNumber: test_simple(0),test_negative_not_supported(0),test_no_number(0)
    TestStripQuotesAndBackticks: test_removes_all(0)
    TestSplitOnPreposition: test_polish_do(0),test_english_into(0),test_no_preposition(0),test_picks_earliest(0),test_empty_prepositions(0)
    TestTrimFieldNouns: test_trims_pole(0),test_trims_pola(0),test_does_not_trim_other_words(0),test_empty(0)
  tests/test_nl_grammar.py:
    e: TestStepDetection,TestStripPrefix,TestSplitHeaderAndBody,TestNormalize
    TestStepDetection: test_numbered_dot(0),test_numbered_paren(0),test_dash_bullet(0),test_star_bullet(0),test_indented_bullet(0),test_not_a_step(0)
    TestStripPrefix: test_dot(0),test_paren(0),test_dash(0),test_idempotent_for_non_steps(0)
    TestSplitHeaderAndBody: test_basic(0),test_handles_hash_prefix_meta(0),test_empty(0),test_only_steps_no_header(0),test_skips_blank_and_unknown_lines(0)
    TestNormalize: test_lowers_and_collapses_whitespace(0),test_idempotent(0)
  tests/test_nl_intent_recognizer.py:
    e: pl,en,TestRecognizeIntentPolish,TestRecognizeIntentEnglish,TestLongestMatchWins,TestRecognizeOperator
    TestRecognizeIntentPolish: test_navigate(1),test_navigate_multi_word(1),test_click(1),test_input(1),test_assert(1),test_wait(1),test_api(1),test_sql(1),test_encoder(1),test_unknown(1)
    TestRecognizeIntentEnglish: test_navigate(1),test_navigate_multi_word(1),test_click(1),test_input(1),test_api(1),test_assert(1)
    TestLongestMatchWins: test_wykonaj_zapytanie_sql_beats_wykonaj(1)
    TestRecognizeOperator: test_equal_pl(1),test_contains(1),test_greater(1),test_no_operator(1),test_not_equal_takes_precedence_over_equal_when_same_position(1),test_english_equal(1)
    pl()
    en()
  tests/test_nl_scenarios_e2e.py:
    e: _scenario_files,scenario,TestScenarioFilesParse,TestSpecificScenarios
    TestScenarioFilesParse: test_scenario_dir_not_empty(0),test_parse_succeeds(1),test_no_unresolved_nl_steps(1),test_round_trip_preserves_step_count(1)
    TestSpecificScenarios: test_login_pl(0),test_api_smoke_pl(0),test_encoder_flow_pl(0),test_login_en(0)
    _scenario_files()
    scenario(request)
  tests/test_openapi_generator.py:
    e: _make_ep,TestOpenAPISpec,TestOpenAPIGenerator,TestContractTestGenerator,TestConvenienceFunctions
    TestOpenAPISpec: test_defaults(0),test_to_dict_has_keys(0),test_to_json(0),test_to_yaml(0)
    TestOpenAPIGenerator: test_init(1),test_generate_empty_project(1),test_generate_title(1),test_generate_default_title_from_path(1),test_generate_version(1),test_generate_servers_present(1),test_generate_components_schemas(1),test_normalize_path_prepends_slash(1),test_normalize_path_preserves_existing_slash(1),test_build_operation_get(1),test_build_operation_post(1),test_build_operation_delete(1),test_build_operation_with_summary(1),test_build_operation_with_description(1),test_build_operation_with_handler_name(1),test_extract_parameters_path_param(1),test_extract_parameters_id_is_string(1),test_extract_parameters_with_query_param(1),test_infer_tags_from_api_path(1),test_infer_tags_from_direct_resource(1),test_build_request_body_create_handler(1),test_build_request_body_update_handler(1),test_save_yaml(1),test_save_json(1),test_save_default_path(1),test_generate_with_fastapi_project(1)
    TestContractTestGenerator: _make_spec(0),test_init_with_dict(0),test_init_with_openapi_spec(0),test_init_with_yaml_file(1),test_init_with_json_file(1),test_generate_contract_tests(1),test_contract_tests_content(1),test_get_expected_status_get(1),test_get_expected_status_post(1),test_get_expected_status_fallback(1),test_validate_response_missing_endpoint(0),test_validate_response_missing_method(0),test_validate_response_valid(0),test_validate_response_wrong_status(0),test_validate_response_bad_content_type(0)
    TestConvenienceFunctions: test_generate_openapi_spec(1),test_generate_openapi_spec_json(1),test_generate_contract_tests_from_spec(1)
    _make_ep(path;method;framework;handler_name;summary;description;parameters;tags;deprecated;endpoint_type;tmp_path)
  tests/test_pipeline.py:
    e: TestRegistries,TestResolution,TestMatrix,TestLLMEnrichmentOptIn,TestWrite
    TestRegistries: test_sorted_sources(0),test_sorted_targets(0)
    TestResolution: test_unknown_source_raises(0),test_unknown_target_raises(0)
    TestMatrix: test_run_returns_result(2),test_output_non_empty(2),test_plan_has_metadata(2)
    TestLLMEnrichmentOptIn: test_default_runs_without_llm(0),test_no_op_enricher_is_pure(0),test_custom_enricher_invoked(0),test_custom_optimizer_attached_to_metadata(0)
    TestWrite: test_writes_to_file(1),test_writes_to_directory_with_derived_name(1)
  tests/test_proto_adapter.py:
    e: TestDetect,TestParseMetadata,TestParseSchemas,TestParseMessages,TestParseAsserts,TestRender,TestRegistration
    TestDetect: test_by_extension(1),test_by_header(0),test_negative(0)
    TestParseMetadata: test_name_type_version(0)
    TestParseSchemas: test_proto_files_become_fixture(0)
    TestParseMessages: test_step_count(0),test_message_names(0),test_schema_file_propagated(0),test_fields_blob_preserved(0)
    TestParseAsserts: test_assertions_attach_to_message(0),test_orphan_assert(0)
    TestRender: test_round_trip_step_count(0),test_render_includes_meta(0)
    TestRegistration: test_registered(0)
  tests/test_proto_compatibility.py:
    e: TestIdentitySchemas,TestRemovedField,TestAddedField,TestTypeChange,TestTagChange,TestRename,TestRemovedMessage,TestAddedMessage,TestReportShape
    TestIdentitySchemas: test_no_issues(0)
    TestRemovedField: test_breaking(0)
    TestAddedField: test_safe(0)
    TestTypeChange: test_incompatible_breaking(0),test_string_to_int_breaking(0),test_int32_to_uint32_safe(0)
    TestTagChange: test_breaking(0)
    TestRename: test_rename_is_warning(0)
    TestRemovedMessage: test_breaking(0)
    TestAddedMessage: test_info_only(0)
    TestReportShape: test_to_dict(0)
  tests/test_proto_descriptor_loader.py:
    e: TestParseHeader,TestParseMessages,TestLabelsAndDefaults,TestComments,TestLookups,TestLoadProtoFile,TestScalarTypes,TestToDict
    TestParseHeader: test_syntax(0),test_package(0),test_default_syntax(0)
    TestParseMessages: test_two_messages(0),test_field_count(0),test_field_types(0),test_field_numbers_unique(0)
    TestLabelsAndDefaults: test_required(0),test_optional_with_default(0),test_repeated(0)
    TestComments: test_line_comments_stripped(0),test_block_comments_stripped(0)
    TestLookups: test_field_by_name(0),test_field_by_number(0),test_field_by_name_missing(0),test_message_missing(0)
    TestLoadProtoFile: test_round_trip(1)
    TestScalarTypes: test_includes_canonical_proto_scalars(0)
    TestToDict: test_round_trip_shape(0)
  tests/test_proto_graphql_scenarios_e2e.py:
    e: _proto_scenarios,_graphql_scenarios,proto_scenario,graphql_scenario,TestProtoScenarios,TestGraphQLScenarios
    TestProtoScenarios: test_dir_not_empty(0),test_parse(1),test_round_trip_step_count(1)
    TestGraphQLScenarios: test_dir_not_empty(0),test_parse(1),test_endpoint_propagated(1),test_round_trip_step_count(1)
    _proto_scenarios()
    _graphql_scenarios()
    proto_scenario(request)
    graphql_scenario(request)
  tests/test_proto_message_validator.py:
    e: TestParseInstanceFields,TestCoerceScalar,TestValidateMessageInstance,TestRoundTrip
    TestParseInstanceFields: test_basic(0),test_quoted_value(0),test_empty(0)
    TestCoerceScalar: test_int(0),test_float(0),test_bool(0),test_string_passthrough(0),test_bytes(0),test_unknown_type_returns_string(0)
    TestValidateMessageInstance: test_ok(0),test_unknown_field(0),test_type_mismatch(0),test_value_coercion_failure(0),test_required_missing(0),test_to_dict(0)
    TestRoundTrip: test_clean_round_trip(0),test_round_trip_failure_on_invalid_value(0)
  tests/test_report_generator.py:
    e: _make_report,TestTestResult,TestTestSuiteReport,TestReportDataParser,TestHTMLReportGenerator
    TestTestResult: test_create(0),test_create_with_failures(0)
    TestTestSuiteReport: test_create(0),test_zero_report(0)
    TestReportDataParser: test_parse_testql_results_returns_report(1),test_to_json_is_valid_json(0),test_to_json_includes_tests(0),test_to_json_empty_suite(0)
    TestHTMLReportGenerator: test_generate_creates_file(1),test_html_contains_suite_name(1),test_html_contains_stats(1),test_html_contains_test_names(1),test_success_rate_zero_total(1),test_html_is_valid_start(1),test_custom_template_dir(1),test_render_html_returns_string(0),test_render_html_failed_test_name(0),test_render_html_failure_message(0)
    _make_report()
  tests/test_reporters.py:
    e: make_result,make_step,TestConsoleReporter,TestJsonReporter,TestJunitReporter,TestVariableStore,TestInterpreterOutput,TestScriptResultHelpers
    TestConsoleReporter: test_returns_string(0),test_contains_source(0),test_passed_step_shows_checkmark(0),test_failed_step_shows_cross(0),test_error_step_shows_explosion(0),test_skipped_step_shows_icon(0),test_step_message_shown(0),test_errors_section_shown(0),test_summary_line_counts(0),test_duration_in_output(0)
    TestJsonReporter: test_returns_valid_json(0),test_has_required_fields(0),test_source_matches(0),test_step_fields(0),test_counts(0),test_errors_included(0),test_warnings_included(0)
    TestJunitReporter: test_returns_string(0),test_valid_xml(0),test_testsuite_element(0),test_testcase_per_step(0),test_failure_element_for_failed_step(0)
    TestVariableStore: test_set_get(0),test_default_if_missing(0),test_has(0),test_all(0),test_clear(0),test_interpolate_curly(0),test_interpolate_dollar(0),test_interpolate_missing_left_unchanged(0),test_interpolate_no_vars(0),test_initial_values(0)
    TestInterpreterOutput: test_emit_stores_line(0),test_ok_prefix(0),test_fail_prefix(0),test_warn_prefix(0),test_info_prefix(0),test_error_prefix(0),test_step_with_icon(0),test_not_quiet_prints(1)
    TestScriptResultHelpers: test_passed_count(0),test_failed_count(0),test_summary_ok(0),test_summary_fail(0)
    make_result(source;ok;steps;errors;warnings;duration_ms)
    make_step(name;status;message;duration_ms)
  tests/test_results.py:
    e: TestResultEnvelope,TestResultSerializers,TestInspectCli,TestDotTestqlArtifacts
    TestResultEnvelope: test_analyze_topology_passes_for_openapi_fixture(0),test_analyze_topology_warns_for_empty_directory(1),test_inspect_source_returns_refactor_plan(1)
    TestResultSerializers: test_render_result_json(0),test_render_refactor_yaml(1),test_render_inspection_toon(1),test_render_inspection_nlp(1)
    TestInspectCli: test_inspect_default_toon_output(0),test_inspect_json_result_artifact(0),test_inspect_refactor_plan_nlp_for_empty_dir(1),test_inspect_missing_path_exits_nonzero(0)
    TestDotTestqlArtifacts: test_write_inspection_artifacts_creates_dot_testql_bundle(1),test_inspect_cli_out_dir_writes_bundle(1)
  tests/test_run_ir_cli.py:
    e: _write,TestRunIrCLI
    TestRunIrCLI: test_help(0),test_dry_run_console(1),test_json_output(1),test_actual_sqlite_run(1)
    _write(tmp_path;name;content)
  tests/test_runner.py:
    e: TestDslCommand,TestExecutionResult,TestParseLine,TestParseScript,TestDslCliExecutor
    TestDslCommand: test_create_minimal(0),test_create_full(0)
    TestExecutionResult: test_success(0),test_failure(0)
    TestParseLine: test_empty_returns_none(0),test_comment_returns_none(0),test_blank_line_returns_none(0),test_api_get(0),test_api_post_with_body(0),test_api_with_expected(0),test_api_with_comment(0),test_wait_command(0),test_wait_with_comment(0),test_general_command_with_quotes(0),test_simple_command(0),test_api_patch(0),test_api_delete(0)
    TestParseScript: test_empty_script(0),test_comments_and_blanks_skipped(0),test_multiline_script(0),test_mixed_content(0)
    TestDslCliExecutor: test_init_defaults(0),test_init_custom_url(0),test_browser_command_skipped(0),test_semantic_command_logged(0),test_browser_command_verbose(1),test_semantic_command_verbose(1),test_execute_unknown_command_returns_result(0),test_execute_returns_duration(0),test_wait_command_via_execute(0)
  tests/test_shell_execution.py:
    e: TestShellExecution,TestShellDryRun
    TestShellExecution: interpreter(1),test_shell_echo_command(2),test_shell_with_exit_code(1),test_assert_exit_code_success(1),test_assert_exit_code_failure(1),test_assert_stdout_contains_success(1),test_assert_stdout_contains_failure(1),test_shell_timeout(1),test_shell_no_previous_command_warning(1)  # Test SHELL, EXEC, RUN commands and assertions.
    TestShellDryRun: interpreter(0),test_shell_dry_run(1)  # Test shell commands in dry-run mode.
  tests/test_sources.py:
    e: TestRegistry,TestOpenAPISource,TestSqlSource,TestProtoSource,TestGraphQLSource,TestNLSource,TestUISource
    TestRegistry: test_six_builtin_sources(0),test_get_source(1),test_get_unknown(0)
    TestOpenAPISource: test_paths_become_api_steps(0),test_status_picks_lowest_2xx(0),test_default_status_when_unspecified(0),test_base_url_from_servers(0),test_metadata_from_info(0),test_load_from_path(1),test_load_from_dict(0)
    TestSqlSource: test_two_tables_yield_four_steps(0),test_count_step_has_assert(0),test_schema_fixture_emitted(0),test_dialect_propagates(0),test_load_from_path(1)
    TestProtoSource: test_one_step_per_message(0),test_sample_fields_blob(0),test_round_trip_assertion(0),test_schema_fixture(0)
    TestGraphQLSource: test_one_step_per_object_type(0),test_endpoint_set_in_config(0),test_query_body_uses_field_list(0)
    TestNLSource: test_delegates_to_adapter(0)
    TestUISource: test_navigate_first(0),test_inputs_extracted(0),test_buttons_extracted(0)
  tests/test_sql_adapter.py:
    e: TestDetect,TestParseMetadata,TestParseConfig,TestParseSchema,TestParseQueries,TestParseAsserts,TestRender,TestRegistration
    TestDetect: test_by_extension(1),test_by_header(0),test_negative(0)
    TestParseMetadata: test_name(0),test_type(0),test_dialect_in_extra(0),test_default_dialect(0)
    TestParseConfig: test_config_dict(0),test_connection_fixture_added(0)
    TestParseSchema: test_schema_fixture(0)
    TestParseQueries: test_count_and_steps(0),test_query_text(0),test_dialect_propagated(0)
    TestParseAsserts: test_assert_attached_to_query(0),test_dotted_assert_attaches_to_base_query(0),test_orphan_asserts_become_assert_step(0)
    TestRender: test_round_trip_step_count(0),test_render_includes_meta(0),test_render_includes_schema(0),test_render_empty_plan(0)
    TestRegistration: test_auto_registered(0),test_extension_lookup(1),test_extension_does_not_collide_with_testtoon(1)
  tests/test_sql_ddl_parser.py:
    e: TestRegexFallback,TestSqlglotPath,TestTableHelpers
    TestRegexFallback: test_single_table(0),test_column_types(0),test_primary_key_flag(0),test_not_null_flag(0),test_unique_flag(0),test_default_extracted(0),test_multi_table(0),test_empty_input(0),test_to_dict(0)
    TestSqlglotPath: test_picks_sqlglot_by_default(0),test_falls_back_on_unparseable(0)
    TestTableHelpers: test_column_lookup_case_insensitive(0),test_to_dict_round_trip(0)
  tests/test_sql_dialect_resolver.py:
    e: TestNormalize,TestIsSupported,TestSupportedDialectsConstant,TestTranspile
    TestNormalize: test_default_when_empty(0),test_lowercases(0),test_aliases(0),test_unknown_passthrough(0)
    TestIsSupported: test_known(0),test_unknown(0),test_empty_returns_false_or_default(0)
    TestSupportedDialectsConstant: test_includes_canonical_names(0)
    TestTranspile: test_raises_when_sqlglot_missing(1),test_round_trip_select(0),test_passthrough_same_dialect(0)
  tests/test_sql_fixtures.py:
    e: TestConnectionFixture,TestSchemaFixtureFromRows
    TestConnectionFixture: test_to_fixture(0)
    TestSchemaFixtureFromRows: test_basic(0),test_skips_empty_rows(0),test_truthy_flags(0),test_default_dash_treated_as_none(0),test_default_value_preserved(0),test_to_fixture_shape(0)
  tests/test_sql_query_parser.py:
    e: TestClassify,TestAnalyzeQueryRegexFallback,TestAnalyzeQuerySqlglot
    TestClassify: test_select(0),test_with_cte(0),test_insert(0),test_update(0),test_delete(0),test_merge(0),test_other(0),test_empty(0)
    TestAnalyzeQueryRegexFallback: test_basic_kind_set(0)
    TestAnalyzeQuerySqlglot: test_extracts_tables(0),test_extracts_columns(0),test_formatted_present(0),test_returns_kind_only_on_unparseable(0)
  tests/test_sql_scenarios_e2e.py:
    e: _scenarios,scenario,TestScenarios,TestSpecificScenarios
    TestScenarios: test_dir_not_empty(0),test_parse_succeeds(1),test_has_sql_steps(1),test_round_trip_preserves_step_count(1),test_dialect_propagates_to_steps(1)
    TestSpecificScenarios: test_users_contract_postgres(0),test_orders_sqlite(0)
    _scenarios()
    scenario(request)
  tests/test_suite_cmd_helpers.py:
    e: _collect_test_files,TestFindFiles,TestCollectFromSuite,TestCollectByPattern,TestCollectRecursive,TestCollectTestFiles
    TestFindFiles: test_returns_empty_for_missing_dir(1),test_finds_matching_files(1),test_finds_files_in_subdirs(1),test_path_with_separator(1),test_path_with_missing_subdir(1)
    TestCollectFromSuite: test_named_suite(1),test_string_pattern_in_suite(1),test_missing_suite_name(1),test_uses_parent_when_file(1)
    TestCollectByPattern: test_finds_matching(1),test_no_match(1)
    TestCollectRecursive: test_finds_testql_files(1),test_empty_project(1)
    TestCollectTestFiles: test_single_file_target(1),test_suite_takes_priority(1),test_pattern_used_when_no_suite(1),test_deduplication(1),test_nonexistent_files_excluded(1)
    _collect_test_files(target_path;suite_name;pattern;config)
  tests/test_suite_execution.py:
    e: FakeResult,TestRunSingleFile,TestRunSuiteFiles
    FakeResult: __init__(5)
    TestRunSingleFile: test_ok_result(0),test_fail_result(0),test_exception_returns_error_dict(0)
    TestRunSuiteFiles: test_empty_files(0),test_all_pass(0),test_one_fail_continues(0),test_fail_fast_stops(0),test_uses_config_default_url(0)
  tests/test_suite_listing.py:
    e: TestParseTesttoonHeader,TestParseYamlMetaBlock,TestParseMeta,TestFilterTests,TestRenderTestList
    TestParseTesttoonHeader: test_returns_none_for_no_header(0),test_parses_scenario_header(0),test_parses_type_without_scenario(0),test_returns_none_for_plain_content(0),test_tags_default_empty(0)
    TestParseYamlMetaBlock: test_returns_none_without_meta(0),test_parses_meta_block(0),test_meta_with_tags(0),test_empty_meta_block(0)
    TestParseMeta: test_default_meta_from_stem(1),test_uses_header_when_present(1),test_uses_yaml_meta_when_no_header(1),test_returns_default_on_missing_file(1)
    TestFilterTests: _make_files(1),test_filter_all(1),test_filter_by_type(1),test_filter_by_tag(1),test_empty_input(1),test_result_has_required_keys(1)
    TestRenderTestList: test_render_json(1),test_render_simple(1),test_render_table(1),test_render_table_empty_tags(1)
  tests/test_sumd_parser.py:
    e: TestSumdMetadata,TestSumdParser
    TestSumdMetadata: test_defaults(0)
    TestSumdParser: test_parse_returns_document(0),test_parse_metadata_name(0),test_parse_metadata_version(0),test_parse_metadata_ecosystem(0),test_parse_metadata_ai_model(0),test_parse_metadata_fallback_header(0),test_parse_architecture(0),test_parse_empty_architecture(0),test_parse_interface_rest(0),test_parse_workflow(0),test_extract_section(0),test_extract_section_missing(0),test_generate_testql_scenarios(0),test_parse_file(1),test_parse_toon_testql_block_with_api_entries(0),test_parse_toon_code_block_scenario(0),test_generate_testql_scenarios_with_testql_scenarios(0),test_generate_testql_scenarios_empty_interfaces_and_scenarios(0),test_parse_toon_api_block_with_comment_and_blank_lines(0),test_parse_toon_scenario_with_type_meta_comment(0)
  tests/test_targets.py:
    e: _sample_plan,TestRegistry,TestTestToonTarget,TestNLTarget,TestPytestTarget
    TestRegistry: test_three_builtin_targets(0),test_get(1),test_get_unknown(0)
    TestTestToonTarget: test_extension(0),test_render_includes_meta(0)
    TestNLTarget: test_extension(0),test_render(0)
    TestPytestTarget: test_extension(0),test_emits_one_test_per_step(0),test_safe_idents(0),test_summary_in_docstring(0),test_handles_unnamed_steps(0)
    _sample_plan()
  tests/test_test_generator.py:
    e: TestTestGeneratorAnalyze,TestTestGeneratorGenerateTests
    TestTestGeneratorAnalyze: test_analyze_returns_profile(1),test_analyze_empty_project_mixed_type(1),test_analyze_fastapi_project(1),test_analyze_cli_project(1),test_analyze_argparse_cli_project(1),test_analyze_typer_cli_project(1),test_analyze_sets_project_path(1)
    TestTestGeneratorGenerateTests: test_generate_empty_project_returns_empty_list(1),test_generate_creates_output_dir(1),test_generate_default_output_dir(1),test_generate_auto_analyzes_if_not_analyzed(1),test_generate_returns_list(1),test_generate_with_python_tests(1),test_generate_accepts_string_output_dir(1),test_generate_with_discovered_routes(1)
  tests/test_testtoon_adapter.py:
    e: TestDetect,TestParse,TestRender,TestAdapterRegistration,TestBackwardCompatibility
    TestDetect: test_detect_by_extension(1),test_detect_by_metadata_header(0),test_detect_negative(0),test_detect_section_header(0)
    TestParse: test_parse_string(0),test_parse_file(1),test_api_steps(0),test_api_step_has_status_assert(0),test_navigate_step(0),test_encoder_step(0),test_assert_section(0),test_unknown_section_falls_through_to_generic(0)
    TestRender: test_render_round_trip_basic(0),test_render_includes_metadata(0),test_render_includes_config(0),test_render_empty_plan(0)
    TestAdapterRegistration: test_adapter_registered_in_default_registry(0),test_extensions_match(0)
    TestBackwardCompatibility: test_legacy_parser_imports(0),test_interpreter_package_reexports(0)  # The legacy parser must still work unchanged after Phase 0.
  tests/test_toon_parser.py:
    e: TestToonParser
    TestToonParser: test_init(0),test_parse_empty(0),test_parse_api_get(0),test_parse_api_post(0),test_parse_api_no_status_defaults_200(0),test_parse_assert_block(0),test_parse_log_block_sets_base_url(0),test_parse_multiple_api_blocks(0),test_parse_resets_contract_between_calls(0),test_parse_file(1)
  tests/test_topology.py:
    e: TestTopologyBuilder,TestTopologySerializers,TestTopologyCli
    TestTopologyBuilder: test_builds_root_type_dependency_and_evidence_nodes(0),test_builds_interface_node_for_openapi(0),test_to_dict_can_embed_manifest(0)
    TestTopologySerializers: test_render_json(0),test_render_yaml(0),test_render_toon(0)
    TestTopologyCli: test_topology_help_is_available(0),test_topology_default_toon_output(0),test_topology_json_output(0),test_topology_missing_path_exits_nonzero(0)
  tests/test_topology_generator.py:
    e: _manifest,TestNodeToStepMapping,TestFromTrace,TestToTesttoon,TestConfigOverride
    TestNodeToStepMapping: test_interface_http_becomes_api_step(0),test_page_becomes_gui_navigate(0),test_link_becomes_api_get(0),test_form_post_becomes_api_post(0),test_dependency_becomes_shell_step(0),test_evidence_becomes_shell_file_check(0),test_unsupported_node_returns_none(0)
    TestFromTrace: test_trace_produces_plan_with_steps(0),test_plan_skips_missing_nodes(0),test_assertions_from_edge_conditions(0)
    TestToTesttoon: test_round_trip_contains_expected_sections(0)
    TestConfigOverride: test_custom_http_method(0)
    _manifest()
  tests/test_unit_execution.py:
    e: TestUnitExecution,TestUnitDryRun
    TestUnitExecution: interpreter(0),test_unit_import_success(1),test_unit_import_failure(1),test_unit_assert_success(1),test_unit_assert_failure(1),test_unit_assert_builtin_function(1),test_unit_pytest_no_args(1),test_unit_pytest_dry_run(1)  # Test UNIT_PYTEST, UNIT_IMPORT, UNIT_ASSERT commands.
    TestUnitDryRun: interpreter(0),test_unit_import_dry_run(1),test_unit_pytest_discover_dry_run(1)  # Test unit commands in dry-run mode.
```

## Source Map

*Top 5 modules by symbol density — signatures for LLM orientation.*

### `testql._base_fallback` (`testql/_base_fallback.py`)

```python
class StepStatus:
class StepResult:
class ScriptResult:
    def passed()  # CC=3
    def failed()  # CC=3
    def summary()  # CC=2
class VariableStore:  # Simple key-value store with interpolation support.
    def __init__(initial)  # CC=1
    def set(key, value)  # CC=1
    def get(key, default)  # CC=1
    def has(key)  # CC=1
    def all()  # CC=1
    def clear()  # CC=1
    def interpolate(text)  # CC=1
class InterpreterOutput:  # Collects interpreter output lines for display or testing.
    def __init__(quiet)  # CC=1
    def emit(msg)  # CC=2
    def info(msg)  # CC=1
    def ok(msg)  # CC=1
    def fail(msg)  # CC=1
    def warn(msg)  # CC=1
    def error(msg)  # CC=1
    def step(icon, msg)  # CC=1
class BaseInterpreter:  # Abstract base for language interpreters.
    def __init__(variables, quiet, bridge_url)  # CC=1
    def parse(source, filename)  # CC=1
    def execute(parsed)  # CC=1
    def run(source, filename)  # CC=1
    def run_file(path)  # CC=1
    def strip_comments(lines)  # CC=3
class EventBridge:  # Optional WebSocket bridge to DSL Event Server (port 8104).
    def __init__(url)  # CC=1
    def connect()  # CC=2
    def disconnect()  # CC=3
    def send_event(event_type, payload)  # CC=4
    def connected()  # CC=1
```

### `testql.openapi_generator` (`testql/openapi_generator.py`)

```python
def _extract_path_params(path)  # CC=4, fan=3
def _extract_ep_params(ep_params, existing)  # CC=7, fan=4
def generate_openapi_spec(project_path, output, format)  # CC=1, fan=3
def generate_contract_tests_from_spec(spec_path, output)  # CC=1, fan=2
class OpenAPISpec:  # OpenAPI specification container.
    def to_dict()  # CC=1
    def to_json(indent)  # CC=1
    def to_yaml()  # CC=1
class OpenAPIGenerator:  # Generate OpenAPI specs from detected endpoints.
    def __init__(project_path)  # CC=3
    def generate(title, version)  # CC=5
    def _normalize_path(path)  # CC=2
    def _build_operation(ep)  # CC=7
    def _infer_tags(ep)  # CC=7
    def _extract_parameters(ep)  # CC=1
    def _build_request_body(ep)  # CC=6
    def _build_responses(ep)  # CC=3
    def save(output_path, format)  # CC=3
class ContractTestGenerator:  # Generate contract tests from OpenAPI specs.
    def __init__(spec)  # CC=3
    def _load_spec(path)  # CC=2
    def generate_contract_tests(output_file)  # CC=6
    def _get_expected_status(method, operation)  # CC=4
    def validate_response(endpoint, method, response)  # CC=11 ⚠
```

### `testql.runner` (`testql/runner.py`)

```python
def parse_line(line)  # CC=9, fan=8
def parse_script(content)  # CC=3, fan=2
def main()  # CC=10, fan=14 ⚠
class DslCommand:
class ExecutionResult:
class DslCliExecutor:
    def __init__(base_url, verbose)  # CC=1
    def execute(cmd)  # CC=2
    def _dispatch(cmd)  # CC=6
    def cmd_api(cmd)  # CC=7
    def cmd_wait(cmd)  # CC=1
    def cmd_log(cmd)  # CC=2
    def cmd_print(cmd)  # CC=2
    def cmd_store(cmd)  # CC=2
    def cmd_env(cmd)  # CC=2
    def cmd_assert_status(cmd)  # CC=2
    def cmd_assert_json(cmd)  # CC=12 ⚠
    def cmd_set_header(cmd)  # CC=2
    def cmd_set_base_url(cmd)  # CC=1
    def run_script(content, stop_on_error)  # CC=11 ⚠
    def _format_cmd(cmd)  # CC=2
```

### `testql.sumd_parser` (`testql/sumd_parser.py`)

```python
def _parse_block_interfaces(content)  # CC=3, fan=5
def _parse_api_interfaces(content)  # CC=8, fan=7
def parse_sumd_file(path)  # CC=1, fan=2
class SumdMetadata:  # Metadata from SUMD.
class SumdInterface:  # Interface from SUMD.
class SumdWorkflow:  # Workflow from SUMD.
class SumdDocument:  # Parsed SUMD document.
class SumdParser:  # Parser for SUMD markdown files.
    def parse_file(path)  # CC=1
    def parse(content)  # CC=1
    def _parse_metadata(content)  # CC=8
    def _parse_interfaces(content)  # CC=1
    def _parse_workflows(content)  # CC=4
    def _parse_testql_scenarios(content)  # CC=11 ⚠
    def _parse_architecture(content)  # CC=3
    def _extract_section(content, section_name)  # CC=2
    def generate_testql_scenarios(doc)  # CC=5
```

### `testql.sumd_generator` (`testql/sumd_generator.py`)

```python
def generate_sumd(project_echo, project_path)  # CC=4, fan=10
def _header_section(project_name, version)  # CC=1, fan=1
def _metadata_section(project_name, version)  # CC=1, fan=0
def _architecture_section()  # CC=1, fan=0
def _doql_declaration_section(project_echo, project_name, version)  # CC=7, fan=1
def _api_contract_section(project_echo)  # CC=6, fan=4
def _workflows_table_section(project_echo)  # CC=5, fan=2
def _configuration_section(project_echo, project_name, version)  # CC=2, fan=1
def _llm_suggestions_section(project_echo)  # CC=4, fan=3
def _workflow_snippet(workflows, name, comment, cmd)  # CC=4, fan=1
def save_sumd(project_echo, project_path, output_path)  # CC=2, fan=2
```

## Call Graph

*534 nodes · 500 edges · 111 modules · CC̄=2.1*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `_render_toon` *(in testql.results.serializers)* | 6 | 1 | 46 | **47** |
| `print` *(in examples.browser-inspection.run)* | 0 | 37 | 0 | **37** |
| `list` *(in code2llm_output.map.toon)* | 0 | 31 | 0 | **31** |
| `write_inspection_artifacts` *(in testql.results.artifacts)* | 1 | 2 | 28 | **30** |
| `inspect` *(in testql.commands.inspect_cmd)* | 6 | 0 | 24 | **24** |
| `generate_topology` *(in testql.commands.generate_topology_cmd)* | 5 | 0 | 24 | **24** |
| `_print_routes_section` *(in testql.commands.generate_cmd)* | 10 ⚠ | 1 | 23 | **24** |
| `interp_value` *(in testql.ir_runner.interpolation)* | 6 | 16 | 7 | **23** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/oqlos/testql
# nodes: 534 | edges: 500 | modules: 111
# CC̄=2.1

HUBS[20]:
  testql.results.serializers._render_toon
    CC=6  in:1  out:46  total:47
  examples.browser-inspection.run.print
    CC=0  in:37  out:0  total:37
  code2llm_output.map.toon.list
    CC=0  in:31  out:0  total:31
  testql.results.artifacts.write_inspection_artifacts
    CC=1  in:2  out:28  total:30
  testql.commands.inspect_cmd.inspect
    CC=6  in:0  out:24  total:24
  testql.commands.generate_topology_cmd.generate_topology
    CC=5  in:0  out:24  total:24
  testql.commands.generate_cmd._print_routes_section
    CC=10  in:1  out:23  total:24
  testql.ir_runner.interpolation.interp_value
    CC=6  in:16  out:7  total:23
  testql.commands.echo.parsers.doql._parse_workflows
    CC=7  in:1  out:22  total:23
  testql.adapters.testtoon_adapter._render_plan
    CC=9  in:4  out:19  total:23
  testql.commands.encoder_routes._run_iql_lines
    CC=6  in:1  out:22  total:23
  testql._base_fallback.VariableStore.set
    CC=1  in:22  out:0  total:22
  testql.commands.misc_cmds.report
    CC=4  in:0  out:22  total:22
  testql.runner.parse_line
    CC=9  in:2  out:20  total:22
  testql.adapters.sql.fixtures.schema_fixture_from_rows
    CC=4  in:1  out:20  total:21
  testql.commands.endpoints_cmd.endpoints
    CC=9  in:0  out:20  total:20
  testql.adapters.base.read_source
    CC=5  in:11  out:9  total:20
  testql.commands.misc_cmds.echo
    CC=4  in:0  out:20  total:20
  testql.runner.DslCliExecutor.run_script
    CC=11  in:0  out:20  total:20
  testql.commands.misc_cmds.init
    CC=4  in:0  out:20  total:20

MODULES:
  TODO.testtoon_parser  [2 funcs]
    print_parsed  CC=8  out:12
    validate  CC=2  out:2
  code2llm_output.map.toon  [13 funcs]
    _navigate_json_path  CC=0  out:0
    format_text_output  CC=0  out:0
    generate_context  CC=0  out:0
    generate_report  CC=0  out:0
    generate_sumd  CC=0  out:0
    list  CC=0  out:0
    parse_doql_file  CC=0  out:0
    parse_doql_less  CC=0  out:0
    parse_iql  CC=0  out:0
    parse_script  CC=0  out:0
  examples.artifact-bundle.generate_bundle  [1 funcs]
    main  CC=2  out:10
  examples.browser-inspection.run  [1 funcs]
    print  CC=0  out:0
  project.map.toon  [2 funcs]
    build_topology  CC=0  out:0
    run_self_test  CC=0  out:0
  testql._base_fallback  [4 funcs]
    emit  CC=2  out:2
    all  CC=1  out:1
    has  CC=1  out:0
    set  CC=1  out:0
  testql.adapters.base  [1 funcs]
    read_source  CC=5  out:9
  testql.adapters.graphql.graphql_adapter  [20 funcs]
    detect  CC=4  out:6
    parse  CC=1  out:3
    render  CC=1  out:1
    _apply_section  CC=2  out:6
    _assert_section  CC=4  out:11
    _config_section  CC=3  out:4
    _format_variables  CC=3  out:2
    _h_assert  CC=1  out:2
    _h_config  CC=1  out:2
    _h_mutation  CC=2  out:5
  testql.adapters.graphql.query_executor  [5 funcs]
    _coerce_literal  CC=3  out:2
    _is_quoted  CC=3  out:1
    _try_number  CC=3  out:2
    classify_operation  CC=3  out:3
    parse_variables  CC=6  out:7
  testql.adapters.graphql.schema_introspection  [5 funcs]
    to_dict  CC=1  out:1
    _kind_to_canonical  CC=1  out:2
    _parse_type_block  CC=4  out:12
    _scan_balanced_braces  CC=5  out:1
    parse_schema  CC=4  out:6
  testql.adapters.nl.entity_extractor  [5 funcs]
    all_backticked  CC=2  out:2
    first_backtick  CC=2  out:2
    first_path  CC=6  out:6
    first_quoted  CC=3  out:4
    first_selector  CC=7  out:7
  testql.adapters.nl.grammar  [6 funcs]
    _apply_meta  CC=2  out:0
    _consume_line  CC=5  out:13
    is_step_line  CC=1  out:2
    normalize  CC=1  out:3
    split_header_and_body  CC=2  out:4
    strip_step_prefix  CC=1  out:2
  testql.adapters.nl.intent_recognizer  [3 funcs]
    _intent_table  CC=5  out:8
    recognize_intent  CC=4  out:11
    recognize_operator  CC=6  out:8
  testql.adapters.nl.lexicon  [1 funcs]
    load_lexicon  CC=3  out:5
  testql.adapters.nl.llm_fallback  [1 funcs]
    get_resolver  CC=1  out:0
  testql.adapters.nl.nl_adapter  [18 funcs]
    _load_lexicon_safe  CC=4  out:3
    detect  CC=6  out:6
    parse  CC=3  out:8
    render  CC=5  out:8
    _api_status_part  CC=2  out:3
    _assert_expected  CC=4  out:3
    _assert_field  CC=7  out:7
    _build_api  CC=6  out:8
    _build_assert  CC=2  out:5
    _build_encoder  CC=2  out:5
  testql.adapters.proto.compatibility  [7 funcs]
    _compare_field  CC=5  out:8
    _compare_message  CC=2  out:3
    _find_candidate_field  CC=6  out:2
    _scan_new_messages  CC=4  out:2
    _scan_old_messages  CC=3  out:5
    _wire_compatible  CC=4  out:1
    compare_schemas  CC=2  out:3
  testql.adapters.proto.descriptor_loader  [7 funcs]
    _iter_messages  CC=3  out:4
    _parse_field  CC=3  out:9
    _parse_message  CC=2  out:3
    _scan_balanced_braces  CC=5  out:1
    _strip_comments  CC=1  out:2
    load_proto_file  CC=1  out:3
    parse_proto  CC=4  out:9
  testql.adapters.proto.message_validator  [9 funcs]
    _missing_required  CC=4  out:1
    _row_issues  CC=3  out:4
    _validate_field_known  CC=2  out:2
    _validate_field_type  CC=3  out:2
    _validate_field_value  CC=3  out:2
    coerce_scalar  CC=5  out:6
    parse_instance_fields  CC=7  out:10
    round_trip_equal  CC=6  out:4
    validate_message_instance  CC=5  out:7
  testql.adapters.proto.proto_adapter  [16 funcs]
    detect  CC=5  out:6
    parse  CC=1  out:3
    render  CC=1  out:1
    _apply_section  CC=2  out:6
    _assert_section  CC=5  out:12
    _h_assert  CC=3  out:2
    _h_message  CC=1  out:3
    _h_proto  CC=1  out:4
    _message_section  CC=5  out:8
    _proto_section  CC=3  out:7
  testql.adapters.registry  [3 funcs]
    all  CC=1  out:2
    detect  CC=9  out:8
    get_registry  CC=1  out:0
  testql.adapters.sql.ddl_parser  [12 funcs]
    _column_from_sqlglot  CC=4  out:11
    _depth_delta  CC=3  out:0
    _extract_default  CC=2  out:2
    _iter_create_tables  CC=3  out:4
    _parse_column_line  CC=3  out:12
    _parse_ddl_regex  CC=2  out:3
    _parse_ddl_sqlglot  CC=5  out:7
    _parse_table_regex  CC=4  out:3
    _scan_balanced_parens  CC=5  out:1
    _split_top_level  CC=7  out:8
  testql.adapters.sql.dialect_resolver  [4 funcs]
    has_sqlglot  CC=2  out:0
    is_supported  CC=2  out:2
    normalize_dialect  CC=2  out:3
    transpile  CC=4  out:5
  testql.adapters.sql.fixtures  [1 funcs]
    schema_fixture_from_rows  CC=4  out:20
  testql.adapters.sql.query_parser  [5 funcs]
    to_dict  CC=1  out:2
    _analyze_with_sqlglot  CC=5  out:9
    _projection_columns  CC=5  out:5
    analyze_query  CC=3  out:4
    classify  CC=2  out:4
  testql.adapters.sql.sql_adapter  [21 funcs]
    detect  CC=5  out:6
    parse  CC=1  out:3
    render  CC=1  out:1
    _apply_section  CC=2  out:6
    _assert_section  CC=4  out:12
    _collect_schema_rows  CC=6  out:3
    _config_section  CC=5  out:10
    _h_assert  CC=3  out:2
    _h_config  CC=1  out:3
    _h_query  CC=1  out:3
  testql.adapters.testtoon_adapter  [11 funcs]
    detect  CC=9  out:12
    parse  CC=1  out:3
    render  CC=1  out:1
    _capture_section_apply  CC=8  out:12
    _config_to_dict  CC=3  out:3
    _render_config  CC=3  out:3
    _render_meta  CC=5  out:4
    _render_plan  CC=9  out:19
    _resolve_capture_target  CC=4  out:3
    _toon_to_plan  CC=6  out:12
  testql.cli  [2 funcs]
    cli  CC=1  out:2
    main  CC=1  out:1
  testql.commands.discover_cmd  [1 funcs]
    discover  CC=5  out:17
  testql.commands.echo.cli  [1 funcs]
    echo  CC=3  out:17
  testql.commands.echo.context  [3 funcs]
    _find_doql_file  CC=4  out:5
    _find_toon_path  CC=2  out:1
    generate_context  CC=4  out:5
  testql.commands.echo.formatters.text  [7 funcs]
    _build_header  CC=1  out:4
    _fmt_contracts  CC=5  out:8
    _fmt_entities  CC=4  out:10
    _fmt_interfaces  CC=3  out:5
    _fmt_suggestions  CC=6  out:8
    _fmt_workflows  CC=3  out:6
    format_text_output  CC=1  out:7
  testql.commands.echo.parsers.doql  [9 funcs]
    _parse_app_block  CC=2  out:3
    _parse_deploy  CC=2  out:3
    _parse_entities  CC=7  out:16
    _parse_environment  CC=2  out:3
    _parse_integrations  CC=4  out:12
    _parse_interfaces  CC=2  out:4
    _parse_kv_block  CC=3  out:6
    _parse_workflows  CC=7  out:22
    parse_doql_less  CC=1  out:8
  testql.commands.echo.parsers.toon  [2 funcs]
    _parse_scenario  CC=5  out:15
    parse_toon_scenarios  CC=3  out:5
  testql.commands.echo_helpers  [4 funcs]
    _collect_toon_directory  CC=8  out:9
    collect_doql_data  CC=2  out:5
    collect_toon_data  CC=3  out:7
    render_echo  CC=3  out:4
  testql.commands.encoder_routes  [25 funcs]
    _assert_bool_prop  CC=2  out:5
    _assert_classes_prop  CC=2  out:1
    _assert_count_prop  CC=2  out:2
    _assert_text_prop  CC=2  out:2
    _build_run_summary  CC=2  out:1
    _evaluate_assertion  CC=6  out:6
    _exec_assert_cmd  CC=7  out:11
    _exec_browser_cmd  CC=9  out:10
    _exec_encoder_cmd  CC=6  out:4
    _execute_iql_line  CC=10  out:13
  testql.commands.endpoints_cmd  [5 funcs]
    _format_endpoints  CC=3  out:3
    _format_endpoints_csv  CC=5  out:7
    _format_endpoints_json  CC=3  out:3
    _format_endpoints_table  CC=5  out:8
    endpoints  CC=9  out:20
  testql.commands.generate_cmd  [4 funcs]
    _count_routes_by  CC=2  out:3
    _echo_analysis  CC=4  out:17
    _print_routes_section  CC=10  out:23
    generate  CC=5  out:17
  testql.commands.generate_ir_cmd  [2 funcs]
    _split_from_arg  CC=2  out:6
    generate_ir  CC=2  out:12
  testql.commands.generate_topology_cmd  [2 funcs]
    _pick_trace  CC=5  out:1
    generate_topology  CC=5  out:24
  testql.commands.inspect_cmd  [1 funcs]
    inspect  CC=6  out:24
  testql.commands.misc_cmds  [4 funcs]
    _create_templates  CC=4  out:4
    echo  CC=4  out:20
    init  CC=4  out:20
    report  CC=4  out:22
  testql.commands.run_ir_cmd  [2 funcs]
    _emit_json  CC=2  out:4
    run_ir  CC=3  out:13
  testql.commands.self_test_cmd  [2 funcs]
    _print_human  CC=4  out:6
    self_test  CC=2  out:8
  testql.commands.suite.cli  [1 funcs]
    list_tests  CC=2  out:13
  testql.commands.suite.collection  [8 funcs]
    _collect_by_pattern  CC=2  out:3
    _collect_from_suite  CC=4  out:7
    _collect_recursive  CC=4  out:3
    _deduplicate_files  CC=5  out:5
    _find_files  CC=6  out:7
    _resolve_search_dir_and_pattern  CC=4  out:2
    collect_list_files  CC=4  out:5
    collect_test_files  CC=5  out:7
  testql.commands.suite.execution  [2 funcs]
    run_single_file  CC=3  out:7
    run_suite_files  CC=5  out:11
  testql.commands.suite.listing  [6 funcs]
    _collect_meta_lines  CC=7  out:6
    _parse_testtoon_header  CC=6  out:8
    _parse_yaml_meta_block  CC=5  out:4
    filter_tests  CC=6  out:9
    parse_meta  CC=6  out:6
    render_test_list  CC=6  out:9
  testql.commands.suite.reports  [3 funcs]
    _build_junit_xml  CC=5  out:8
    _save_json_report  CC=1  out:3
    save_report  CC=3  out:5
  testql.commands.topology_cmd  [1 funcs]
    topology  CC=3  out:13
  testql.detectors.unified  [2 funcs]
    _deduplicate_endpoints  CC=3  out:4
    detect_all  CC=4  out:6
  testql.discovery.manifest  [8 funcs]
    from_probe_results  CC=8  out:6
    to_dict  CC=9  out:11
    _dedupe_dicts  CC=4  out:8
    _dependencies_from_metadata  CC=4  out:7
    _interfaces_from_metadata  CC=5  out:7
    _merge_metadata  CC=10  out:7
    _score_confidence  CC=5  out:1
    _unique  CC=3  out:3
  testql.discovery.probes.base  [1 funcs]
    to_dict  CC=3  out:4
  testql.discovery.probes.filesystem.api_openapi  [2 funcs]
    _find_specs  CC=9  out:11
    _excluded  CC=4  out:3
  testql.discovery.probes.filesystem.package_python  [13 funcs]
    _find_python_files  CC=7  out:6
    _read_metadata  CC=8  out:13
    _call_kw  CC=2  out:3
    _dedupe_deps  CC=4  out:5
    _dep  CC=3  out:4
    _parse_pyproject  CC=7  out:12
    _parse_pyproject_dependencies  CC=6  out:15
    _parse_requirements  CC=4  out:5
    _parse_setup_cfg  CC=3  out:6
    _parse_setup_py  CC=3  out:4
  testql.discovery.probes.network.http_endpoint  [9 funcs]
    probe  CC=6  out:14
    handle_starttag  CC=10  out:14
    _asset_kind  CC=8  out:2
    _fetch  CC=1  out:2
    _limit  CC=1  out:0
    _link_kind  CC=4  out:4
    _looks_textual  CC=2  out:2
    _metadata  CC=1  out:10
    _parse_html  CC=2  out:5
  testql.discovery.registry  [3 funcs]
    __init__  CC=2  out:1
    default_probes  CC=3  out:9
    discover_path  CC=1  out:2
  testql.generators.base  [1 funcs]
    _should_exclude_path  CC=1  out:3
  testql.generators.generators  [1 funcs]
    _deduplicate_rest_routes  CC=4  out:3
  testql.generators.multi  [1 funcs]
    generate_cross_project_tests  CC=3  out:11
  testql.generators.pipeline  [6 funcs]
    _resolve_source  CC=3  out:4
    _resolve_target  CC=3  out:4
    run  CC=5  out:13
    sorted_sources  CC=1  out:1
    sorted_targets  CC=1  out:1
    write  CC=5  out:9
  testql.generators.sources  [2 funcs]
    available_sources  CC=1  out:2
    get_source  CC=2  out:3
  testql.generators.sources.graphql_source  [4 funcs]
    load  CC=3  out:7
    _is_smoke_target  CC=3  out:2
    _load_sdl  CC=5  out:9
    _type_to_query  CC=3  out:5
  testql.generators.sources.openapi_source  [4 funcs]
    load  CC=7  out:13
    _iter_operations  CC=6  out:5
    _operation_to_step  CC=3  out:7
    _pick_success_status  CC=7  out:7
  testql.generators.sources.proto_source  [5 funcs]
    load  CC=3  out:8
    _load_proto_text  CC=5  out:12
    _message_to_step  CC=2  out:3
    _sample_fields_blob  CC=3  out:3
    _sample_value_for  CC=1  out:1
  testql.generators.sources.sql_source  [4 funcs]
    load  CC=3  out:10
    _crud_steps  CC=1  out:4
    _load_sql_text  CC=5  out:9
    _schema_fixture_from_ddl  CC=2  out:2
  testql.generators.sources.ui_source  [4 funcs]
    load  CC=1  out:12
    _button_steps  CC=2  out:4
    _input_steps  CC=2  out:2
    _load_html  CC=5  out:12
  testql.generators.targets  [2 funcs]
    available_targets  CC=1  out:2
    get_target  CC=2  out:3
  testql.generators.targets.pytest_target  [4 funcs]
    render  CC=3  out:3
    _emit_test  CC=2  out:3
    _safe_ident  CC=5  out:4
    _step_summary  CC=3  out:2
  testql.interpreter._api_runner  [4 funcs]
    _cmd_capture  CC=3  out:13
    _navigate_json_path  CC=5  out:5
    _navigate_step  CC=4  out:4
    _resolve_length  CC=4  out:6
  testql.interpreter._assertions  [1 funcs]
    _cmd_assert_json  CC=6  out:17
  testql.interpreter._flow  [1 funcs]
    _cmd_include  CC=7  out:17
  testql.interpreter._testtoon_parser  [10 funcs]
    _append_api_asserts  CC=8  out:10
    _detect_separator  CC=2  out:0
    _expand_api  CC=2  out:5
    _make_data_row  CC=2  out:6
    _make_section  CC=4  out:9
    _parse_inline_array  CC=2  out:2
    _parse_inline_dict  CC=3  out:4
    _parse_value  CC=8  out:10
    parse_testtoon  CC=8  out:15
    testtoon_to_iql  CC=2  out:4
  testql.interpreter.converter.core  [3 funcs]
    convert_directory  CC=4  out:7
    convert_file  CC=1  out:3
    convert_iql_to_testtoon  CC=5  out:10
  testql.interpreter.converter.dispatcher  [1 funcs]
    dispatch  CC=3  out:3
  testql.interpreter.converter.handlers.api  [1 funcs]
    handle_api  CC=6  out:7
  testql.interpreter.converter.handlers.assertions  [1 funcs]
    collect_assert  CC=9  out:9
  testql.interpreter.converter.handlers.encoder  [3 funcs]
    _advance_past_wait  CC=4  out:2
    _encoder_action_fields  CC=5  out:4
    handle_encoder  CC=3  out:8
  testql.interpreter.converter.handlers.flow  [1 funcs]
    handle_flow  CC=3  out:6
  testql.interpreter.converter.handlers.include  [1 funcs]
    handle_include  CC=1  out:2
  testql.interpreter.converter.handlers.navigate  [1 funcs]
    handle_navigate  CC=6  out:8
  testql.interpreter.converter.handlers.record  [1 funcs]
    handle_record_start  CC=1  out:2
  testql.interpreter.converter.handlers.select  [1 funcs]
    handle_select  CC=3  out:8
  testql.interpreter.converter.handlers.unknown  [1 funcs]
    handle_unknown  CC=3  out:4
  testql.interpreter.converter.parsers  [6 funcs]
    detect_scenario_type  CC=11  out:6
    extract_scenario_name  CC=6  out:8
    parse_api_args  CC=5  out:9
    parse_commands  CC=5  out:10
    parse_meta_from_args  CC=4  out:6
    parse_target_from_args  CC=4  out:9
  testql.interpreter.converter.renderer  [4 funcs]
    _render_section_header  CC=3  out:2
    build_config_section  CC=6  out:6
    build_header  CC=1  out:0
    render_sections  CC=7  out:12
  testql.interpreter.dispatcher  [1 funcs]
    dispatch  CC=5  out:13
  testql.interpreter.interpreter  [3 funcs]
    __init__  CC=2  out:4
    execute  CC=4  out:16
    parse  CC=2  out:3
  testql.ir.metadata  [1 funcs]
    to_dict  CC=3  out:2
  testql.ir.steps  [1 funcs]
    to_dict  CC=3  out:4
  testql.ir_runner.assertion_eval  [4 funcs]
    _next_segment  CC=6  out:7
    evaluate  CC=3  out:6
    evaluate_all  CC=2  out:1
    navigate  CC=3  out:2
  testql.ir_runner.engine  [5 funcs]
    run  CC=5  out:9
    _apply_captures  CC=6  out:5
    _run_step  CC=4  out:12
    load_plan  CC=4  out:8
    run_plan  CC=1  out:2
  testql.ir_runner.executors  [1 funcs]
    get_executor  CC=1  out:1
  testql.ir_runner.executors.base  [6 funcs]
    _aggregate_assertion_status  CC=3  out:0
    _compose_message  CC=3  out:1
    assemble_result  CC=5  out:6
    error_result  CC=1  out:2
    skipped_result  CC=1  out:1
    step_label  CC=2  out:0
  testql.ir_runner.executors.encoder  [3 funcs]
    _do_call  CC=5  out:7
    _request_body  CC=5  out:2
    execute  CC=5  out:11
  testql.ir_runner.executors.gui  [1 funcs]
    execute  CC=2  out:3
  testql.ir_runner.executors.nl  [1 funcs]
    execute  CC=1  out:2
  testql.ir_runner.executors.proto  [3 funcs]
    _instance_tuples  CC=2  out:3
    _resolve_source  CC=3  out:6
    _run_check  CC=6  out:3
  testql.ir_runner.interpolation  [1 funcs]
    interp_value  CC=6  out:7
  testql.meta.confidence_scorer  [6 funcs]
    to_dict  CC=1  out:2
    _is_llm_resolved  CC=3  out:1
    _score_assertions  CC=3  out:2
    _score_step  CC=3  out:9
    _score_typed  CC=2  out:1
    score_plan  CC=4  out:5
  testql.meta.coverage_analyzer  [14 funcs]
    to_dict  CC=1  out:2
    _build_report  CC=1  out:6
    _extract_table_names  CC=3  out:4
    _load_text  CC=4  out:6
    _load_yaml  CC=3  out:3
    _openapi_endpoints  CC=6  out:7
    _plan_endpoints  CC=3  out:1
    _plan_proto_messages  CC=4  out:1
    _plan_sql_tables  CC=3  out:4
    _proto_messages  CC=2  out:0
  testql.meta.mutator  [9 funcs]
    _flipped_op  CC=1  out:1
    _next_status  CC=2  out:0
    _scrambled  CC=5  out:4
    _tweak_status_mutation  CC=4  out:3
    mutate  CC=2  out:2
    mutations_flip_assertion_op  CC=5  out:6
    mutations_scramble_assertion_value  CC=6  out:6
    mutations_tweak_status  CC=4  out:4
    run_mutation_test  CC=4  out:8
  testql.openapi_generator  [5 funcs]
    _load_spec  CC=2  out:3
    _extract_parameters  CC=1  out:3
    _infer_tags  CC=7  out:9
    _extract_ep_params  CC=7  out:8
    _extract_path_params  CC=4  out:4
  testql.results.analyzer  [37 funcs]
    _action_summary  CC=1  out:0
    _action_type  CC=14  out:0
    _actions_from_findings  CC=4  out:6
    _browser_checks  CC=3  out:4
    _check_asset_statuses  CC=12  out:16
    _check_browser_console  CC=3  out:5
    _check_browser_network  CC=3  out:5
    _check_browser_render  CC=3  out:4
    _check_confidence  CC=2  out:2
    _check_edges  CC=2  out:3
  testql.results.artifacts  [2 funcs]
    _write_group  CC=2  out:3
    write_inspection_artifacts  CC=1  out:28
  testql.results.models  [4 funcs]
    to_dict  CC=3  out:2
    to_dict  CC=3  out:2
    from_envelope  CC=3  out:3
    to_dict  CC=2  out:2
  testql.results.serializers  [7 funcs]
    _render_data  CC=7  out:11
    _render_nlp  CC=1  out:3
    _render_nlp_dict  CC=5  out:14
    _render_toon  CC=6  out:46
    render_inspection  CC=2  out:5
    render_refactor_plan  CC=1  out:2
    render_result_envelope  CC=1  out:2
  testql.runner  [6 funcs]
    _dispatch  CC=6  out:6
    cmd_log  CC=2  out:3
    cmd_print  CC=2  out:4
    run_script  CC=11  out:20
    parse_line  CC=9  out:20
    parse_script  CC=3  out:2
  testql.sumd_generator  [11 funcs]
    _api_contract_section  CC=6  out:11
    _architecture_section  CC=1  out:0
    _configuration_section  CC=2  out:1
    _doql_declaration_section  CC=7  out:5
    _header_section  CC=1  out:1
    _llm_suggestions_section  CC=4  out:5
    _metadata_section  CC=1  out:0
    _workflow_snippet  CC=4  out:1
    _workflows_table_section  CC=5  out:3
    generate_sumd  CC=4  out:10
  testql.sumd_parser  [3 funcs]
    _parse_interfaces  CC=1  out:2
    _parse_api_interfaces  CC=8  out:13
    _parse_block_interfaces  CC=3  out:7
  testql.topology.serializers  [1 funcs]
    render_topology  CC=4  out:5

EDGES:
  examples.artifact-bundle.generate_bundle.main → examples.browser-inspection.run.print
  examples.artifact-bundle.generate_bundle.main → testql.results.analyzer.inspect_source
  examples.artifact-bundle.generate_bundle.main → testql.results.artifacts.write_inspection_artifacts
  TODO.testtoon_parser.print_parsed → examples.browser-inspection.run.print
  TODO.testtoon_parser.print_parsed → TODO.testtoon_parser.validate
  testql.cli.main → testql.cli.cli
  testql.runner.parse_line → examples.browser-inspection.run.print
  testql.runner.parse_script → testql.runner.parse_line
  testql.runner.DslCliExecutor._dispatch → examples.browser-inspection.run.print
  testql.runner.DslCliExecutor.cmd_log → examples.browser-inspection.run.print
  testql.runner.DslCliExecutor.cmd_print → examples.browser-inspection.run.print
  testql.runner.DslCliExecutor.run_script → code2llm_output.map.toon.parse_script
  testql.runner.DslCliExecutor.run_script → examples.browser-inspection.run.print
  testql.openapi_generator.OpenAPIGenerator._infer_tags → code2llm_output.map.toon.list
  testql.openapi_generator.OpenAPIGenerator._infer_tags → testql._base_fallback.VariableStore.set
  testql.openapi_generator.OpenAPIGenerator._extract_parameters → testql.openapi_generator._extract_path_params
  testql.openapi_generator.OpenAPIGenerator._extract_parameters → testql.openapi_generator._extract_ep_params
  testql._base_fallback.InterpreterOutput.emit → examples.browser-inspection.run.print
  testql.sumd_generator.generate_sumd → testql.sumd_generator._header_section
  testql.sumd_generator.generate_sumd → testql.sumd_generator._metadata_section
  testql.sumd_generator.generate_sumd → testql.sumd_generator._architecture_section
  testql.sumd_generator.generate_sumd → testql.sumd_generator._doql_declaration_section
  testql.sumd_generator.generate_sumd → testql.sumd_generator._api_contract_section
  testql.sumd_generator.generate_sumd → testql.sumd_generator._workflows_table_section
  testql.sumd_generator.generate_sumd → testql.sumd_generator._configuration_section
  testql.sumd_generator.generate_sumd → testql.sumd_generator._llm_suggestions_section
  testql.sumd_generator._llm_suggestions_section → testql.sumd_generator._workflow_snippet
  testql.sumd_generator.save_sumd → testql.sumd_generator.generate_sumd
  testql.sumd_parser.SumdParser._parse_interfaces → testql.sumd_parser._parse_block_interfaces
  testql.sumd_parser.SumdParser._parse_interfaces → testql.sumd_parser._parse_api_interfaces
  testql.commands.self_test_cmd.self_test → project.map.toon.run_self_test
  testql.commands.self_test_cmd.self_test → testql.commands.self_test_cmd._print_human
  testql.commands.discover_cmd.discover → testql.discovery.registry.discover_path
  testql.commands.generate_cmd.generate → testql.commands.generate_cmd._echo_analysis
  testql.commands.generate_cmd._print_routes_section → testql.commands.generate_cmd._count_routes_by
  testql.commands.topology_cmd.topology → project.map.toon.build_topology
  testql.commands.topology_cmd.topology → testql.topology.serializers.render_topology
  testql.commands.misc_cmds.init → testql.commands.misc_cmds._create_templates
  testql.commands.misc_cmds.report → code2llm_output.map.toon.generate_report
  testql.commands.misc_cmds.echo → testql.commands.echo_helpers.render_echo
  testql.commands.misc_cmds.echo → testql.commands.echo_helpers.collect_toon_data
  testql.commands.run_ir_cmd.run_ir → testql.ir_runner.engine.run_plan
  testql.commands.run_ir_cmd.run_ir → testql.commands.run_ir_cmd._emit_json
  testql.commands.encoder_routes._normalize_iql_path → testql.commands.encoder_routes._strip_path_segments
  testql.commands.encoder_routes._normalize_iql_path → testql.commands.encoder_routes._migrate_legacy_extension
  testql.commands.encoder_routes._normalize_iql_path → testql.commands.encoder_routes._remap_tests_prefix
  testql.commands.encoder_routes._resolve_iql_path → testql.commands.encoder_routes._normalize_iql_path
  testql.commands.encoder_routes._evaluate_assertion → testql.commands.encoder_routes._assert_bool_prop
  testql.commands.encoder_routes._evaluate_assertion → testql.commands.encoder_routes._assert_count_prop
  testql.commands.encoder_routes._evaluate_assertion → testql.commands.encoder_routes._assert_text_prop
```

## API Stubs

*testql API v1.0.0 — auto-generated stubs from `openapi.yaml`.*

```python markpact:openapi path=openapi.yaml
# fastapi
def iql_read_file() -> Response:  # Read a TestQL file content (.testql.toon.yaml / .iql / .tql).
    "GET /iql/file"
def iql_list_files() -> Response:  # List all .testql.toon.yaml files in the project (with .iql/.tql fallback).
    "GET /iql/files"
def iql_read_log() -> Response:  # Read a specific log file.
    "GET /iql/log"
def iql_list_logs() -> Response:  # List available log files.
    "GET /iql/logs"
def iql_run_file() -> Response:  # Run an entire IQL file with validation. Returns structured results + saves log.
    "POST /iql/run-file"
def iql_run_line() -> Response:  # Execute a single IQL command line via the encoder bridge.
    "POST /iql/run-line"
def iql_list_tables() -> Response:  # Extract table names from an IQL file.
    "GET /iql/tables"

```

**Schemas**: `Error`, `HealthCheck`

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Api (17)

**`api-crud-template.testql.toon.yaml — generic CRUD test template`**

**`api-health.testql.toon.yaml — basic health check for c2004`**
- `GET /health` → `200`

**`api-smoke.testql.toon.yaml — smoke test for all main c2004 API endpoints`**
- `GET /health` → `200`
- `GET /api/v3/version` → `200`
- `GET /api/v3/data/devices` → `200`

**`auth-login.testql.toon.yaml — generic authentication login test template`**
- `POST /api/v3/auth/login"` → `200`

**`Backend Diagnostic Tests`**
- `GET /api/v3/health` → `200`
- `GET /api/v3/template-json` → `200`
- `GET /api/v3/template-json/default` → `200`

**`API Integration Tests`**
- `GET /health` → `200`
- `GET /api/v1/status` → `200`
- `POST /api/v1/test` → `201`
- assert `status == ok`
- assert `response_time < 1000`

**`Auto-generated API Smoke Tests`**
- `GET /iql/files` → `200`
- `GET /iql/file` → `200`
- `GET /iql/tables` → `200`
- assert `status < 500`
- assert `response_time < 2000`
- detectors: FastAPIDetector, OpenAPIDetector

**`health-check.testql.toon.yaml — generic health check scenario`**
- `GET /health` → `200`
- `GET /api/v3/version` → `200`

**`run-all-views.testql.toon.yaml — Master runner for all per-view IQL tests`**

**`=============================================================================`**
- `GET /api/v3/scenarios/scn-drager-fps-7000-maska-nadcisnieniowa?include_content=true` → `200`
- `POST /api/v3/protocols"` → `200`

**`Example DSL Script - API Testing`**
- `GET /api/v3/data/devices?limit=5` → `200`
- `GET /api/v3/data/customers?limit=5` → `200`
- `GET /api/v3/data/intervals?limit=5` → `200`

**`DSL Script - Application Lifecycle Test`**
- `GET /api/v3/data/protocols?limit=3` → `200`
- `GET /api/v3/data/test_scenarios?limit=3` → `200`

**`Example DSL Script - Devices CRUD Operations`**
- `GET /api/v3/data/devices?limit=10` → `200`
- `GET /api/v3/data/customers?limit=5` → `200`
- `GET /api/v3/data/intervals?limit=10` → `200`

**`Example DSL Script - DSL Objects Test`**
- `GET /api/v3/data/dsl_objects?limit=100` → `200`
- `GET /api/v3/data/dsl_functions?limit=100` → `200`
- `GET /api/v3/data/dsl_params?limit=100` → `200`

**`test-gui-all.testql.toon.yaml — Master GUI test suite — runs all module GUI tests`**

**`Example DSL Script - Protocol Flow Test (Read-Only)`**
- `GET /api/v3/data/devices?limit=5` → `200`
- `GET /api/v3/data/customers?limit=5` → `200`
- `GET /api/v3/data/test_scenarios?limit=10` → `200`

**`Example DSL Script - API Endpoints Test`**
- `GET /api/v3/data/devices?limit=5` → `200`
- `GET /api/v3/data/customers?limit=5` → `200`
- `GET /api/v3/data/protocols?limit=10` → `200`

### Cli (1)

**`CLI Command Tests`**

### E2E (1)

**`DSL Mixed Workflow Example`**
- `GET /api/v3/data/devices?limit=3` → `200`
- `GET /api/v3/data/customers?limit=3` → `200`
- `GET /api/v3/data/intervals?limit=3` → `200`

### Gui (51)

**`connect-config-feature-flags.testql.toon.yaml — Test: Konfiguracja > Feature Flags`**

**`connect-config-labels.testql.toon.yaml — Test: Konfiguracja > Etykiety`**

**`connect-config-settings.testql.toon.yaml — Test: Konfiguracja > Ustawienia`**

**`connect-config-tables.testql.toon.yaml — Test: Konfiguracja > Tabele`**

**`connect-config-theme.testql.toon.yaml — Test: Konfiguracja > Motyw`**

**`connect-config-users.testql.toon.yaml — Test: Konfiguracja > Użytkownicy`**

**`connect-id-barcode.testql.toon.yaml — Test: Identyfikacja > Barcode`**

**`connect-id-list.testql.toon.yaml — Test: Identyfikacja > Lista użytkowników`**

**`connect-id-manual.testql.toon.yaml — Test: Identyfikacja > Logowanie ręczne`**

**`connect-id-qr.testql.toon.yaml — Test: Identyfikacja > QR Code`**

**`connect-id-rfid.testql.toon.yaml — Test: Identyfikacja > RFID`**

**`connect-manager-activities.testql.toon.yaml — Test: Manager > Czynności`**

**`connect-manager-intervals.testql.toon.yaml — Test: Manager > Interwały`**

**`connect-manager-library.testql.toon.yaml — Test: Manager > Biblioteka`**

**`connect-manager-scenarios.testql.toon.yaml — Test: Manager > Scenariusze`**

**`connect-manager-test-types.testql.toon.yaml — Test: Manager > Rodzaj Testu`**

**`connect-reports-chart.testql.toon.yaml — Test: Raporty > Wykres`**

**`connect-reports-custom.testql.toon.yaml — Test: Raporty > Niestandardowy`**

**`connect-reports-filter.testql.toon.yaml — Test: Raporty > Filtruj`**

**`connect-reports-month.testql.toon.yaml — Test: Raporty > Miesiąc`**

**`connect-reports-quarter.testql.toon.yaml — Test: Raporty > Kwartał`**

**`connect-reports-week.testql.toon.yaml — Test: Raporty > Tydzień`**

**`connect-reports-year.testql.toon.yaml — Test: Raporty > Rok`**

**`connect-test-devices-search.testql.toon.yaml — Test: Testowanie > Wyszukiwanie urządzeń`**

**`connect-test-full-test.testql.toon.yaml — Test: Testowanie > Test automatyczny`**

**`connect-test-protocols.testql.toon.yaml — Test: Testowanie > Raporty (protokoły)`**

**`connect-test-scenario-view.testql.toon.yaml — Test: Testowanie > Scenariusz/Interwały`**

**`connect-test-testing-barcode.testql.toon.yaml — Test: Testowanie > Barcode`**

**`connect-test-testing-qr.testql.toon.yaml — Test: Testowanie > QR`**

**`connect-test-testing-rfid.testql.toon.yaml — Test: Testowanie > RFID`**

**`connect-test-testing-search.testql.toon.yaml — Test: Testowanie > Wyszukiwanie testów`**

**`connect-workshop-dispositions-search.testql.toon.yaml — Test: Warsztat > Dyspozycje`**

**`connect-workshop-requests-search.testql.toon.yaml — Test: Warsztat > Zgłoszenia`**

**`connect-workshop-services-search.testql.toon.yaml — Test: Warsztat > Serwisy`**

**`connect-workshop-transport-search.testql.toon.yaml — Test: Warsztat > Transport`**

**`connect-workshop-transport.testql.toon.yaml — GUI test for workshop transport view`**

**`Create Today's Reports`**

**`Device Identification Example`**

**`encoder-navigation.testql.toon.yaml — encoder hardware navigation test`**

**`encoder-workshop.testql.toon.yaml — encoder navigation in workshop context`**

**`Full System Diagnostic - API + Routes + DSL`**
- `GET /api/v3/health` → `200`
- `GET /api/v3/auth/session` → `200`
- `GET /api/v3/config/system` → `200`

**`Quick Navigation Example`**

**`DSL Session Recording`**

**`Reproduce View - Connect Manager with Scenario Selection`**

**`test-encoder.testql.toon.yaml — Encoder navigation tests via IQL`**

**`test-gui-connect-config.testql.toon.yaml — GUI tests for Connect Config module`**
- `GET /api/v3/config/settings` → `200`
- `GET /api/v3/feature-flags` → `200`

**`test-gui-connect-id.testql.toon.yaml — GUI tests for Connect ID module`**
- `GET /api/v3/auth/users` → `200`

**`test-gui-connect-manager.testql.toon.yaml — GUI tests for Connect Manager module`**
- `GET /api/v3/data/test_scenarios?limit=5` → `200`
- `GET /api/v3/data/intervals?limit=5` → `200`
- `GET /api/v3/activities?limit=5` → `200`

**`test-gui-connect-reports.testql.toon.yaml — GUI tests for Connect Reports module`**
- `GET /api/v3/data/protocols?limit=5` → `200`

**`test-gui-connect-test.testql.toon.yaml — GUI tests for Connect Test module`**
- `GET /api/v3/data/devices?limit=5` → `200`
- `GET /api/v3/data/test_scenarios?limit=5` → `200`
- `GET /api/v3/data/protocols?limit=5` → `200`

**`test-gui-connect-workshop.testql.toon.yaml — GUI tests for Connect Workshop module`**
- `GET /api/v3/data/customers?limit=5` → `200`

### Integration (1)

**`Auto-generated from Python Tests`**

### Interaction (3)

**`Generate Test Reports Scenario`**

**`Session Recording Example`**

**`DSL Example: Complete Device Test Flow`**

## Intent

TestQL — Multi-DSL Test Platform: TestTOON / NL / SQL / Proto / GraphQL adapters with Unified IR, generator engine, and meta-testing
