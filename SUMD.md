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
- [Makefile Targets](#makefile-targets)
- [Code Analysis](#code-analysis)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [API Stubs](#api-stubs)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `testql`
- **version**: `1.2.54`
- **python_requires**: `>=3.10`
- **license**: {'text': 'Apache-2.0'}
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **openapi_title**: testql API v1.0.0
- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, testql(77), openapi(7 ep), app.doql.less, pyqual.yaml, goal.yaml, .env.example, src(16 mod), project/(3 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: testql;
  version: 1.2.54;
}

dependencies {
  runtime: "httpx>=0.27, click>=8.0, rich>=13.0, pyyaml>=6.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60, websockets>=13.0, pytest-cov>=7.0, fastapi>=0.100";
  dev: "pytest, pytest-asyncio, pytest-cov, mcp>=1.0, fastapi, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60, sqlglot>=20.0, protobuf>=4.21, graphql-core>=3.2";
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
  step-1: run cmd=echo "📦 Installing testql...";
  step-2: run cmd=if command -v uv > /dev/null 2>&1; then \;
  step-3: run cmd=uv pip install -e .; \;
  step-4: run cmd=else \;
  step-5: run cmd=pip install -e .; \;
  step-6: run cmd=fi;
  step-7: run cmd=echo "✅ Installation completed!";
}

workflow[name="install-dev"] {
  trigger: manual;
  step-1: run cmd=echo "📦 Installing testql with dev dependencies...";
  step-2: run cmd=if command -v uv > /dev/null 2>&1; then \;
  step-3: run cmd=uv pip install -e ".[dev]"; \;
  step-4: run cmd=else \;
  step-5: run cmd=pip install -e ".[dev]"; \;
  step-6: run cmd=fi;
  step-7: run cmd=echo "✅ Dev installation completed!";
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=echo "🧪 Running tests...";
  step-2: run cmd=.venv/bin/python -m pytest tests/ -v --tb=short;
}

workflow[name="test-cov"] {
  trigger: manual;
  step-1: run cmd=echo "🧪 Running tests with coverage...";
  step-2: run cmd=.venv/bin/python -m pytest tests/ -v --cov=testql --cov-report=term-missing --cov-report=json;
}

workflow[name="lint"] {
  trigger: manual;
  step-1: run cmd=echo "🔍 Running linting with ruff...";
  step-2: run cmd=.venv/bin/python -m ruff check testql/;
  step-3: run cmd=.venv/bin/python -m ruff check tests/;
}

workflow[name="format"] {
  trigger: manual;
  step-1: run cmd=echo "📝 Formatting code with ruff...";
  step-2: run cmd=.venv/bin/python -m ruff format testql/;
  step-3: run cmd=.venv/bin/python -m ruff format tests/;
}

workflow[name="clean"] {
  trigger: manual;
  step-1: run cmd=echo "🧹 Cleaning temporary files...";
  step-2: run cmd=find . -type f -name "*.pyc" -delete;
  step-3: run cmd=find . -type d -name "__pycache__" -delete;
  step-4: run cmd=find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true;
  step-5: run cmd=rm -rf build/ dist/ .coverage htmlcov/ coverage.json;
  step-6: run cmd=echo "✅ Clean completed!";
}

workflow[name="publish"] {
  trigger: manual;
  step-1: run cmd=echo "📦 Publishing to PyPI...";
  step-2: run cmd=command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build);
  step-3: run cmd=rm -rf dist/ build/ *.egg-info/;
  step-4: run cmd=.venv/bin/python -m build;
  step-5: run cmd=.venv/bin/twine check dist/*;
  step-6: run cmd=echo "⚡ Ready to upload. Run: make publish-confirm to upload to PyPI";
}

workflow[name="publish-confirm"] {
  trigger: manual;
  step-1: run cmd=echo "🚀 Uploading to PyPI...";
  step-2: run cmd=.venv/bin/twine upload dist/*;
}

workflow[name="publish-test"] {
  trigger: manual;
  step-1: run cmd=echo "📦 Publishing to TestPyPI...";
  step-2: run cmd=command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build);
  step-3: run cmd=rm -rf dist/ build/ *.egg-info/;
  step-4: run cmd=.venv/bin/python -m build;
  step-5: run cmd=.venv/bin/twine upload --repository testpypi dist/*;
}

workflow[name="version"] {
  trigger: manual;
  step-1: run cmd=echo "📦 Version information...";
  step-2: run cmd=cat VERSION;
  step-3: run cmd=.venv/bin/python -c "from importlib.metadata import version; print(f'Installed version: {version(\"testql\")}')";
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

workflow[name="fmt"] {
  trigger: manual;
  step-1: run cmd=ruff format .;
}

workflow[name="build"] {
  trigger: manual;
  step-1: run cmd=python -m build;
}

workflow[name="oql:run"] {
  trigger: manual;
  step-1: run cmd=testql run {{.CLI_ARGS}};
}

workflow[name="oql:shell"] {
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

environment[name="testql.autoloop.example"] {
  runtime: docker-compose;
  env_file: .env.testql.autoloop.example;
}
```

### Source Modules

- `testql._base_fallback`
- `testql.autoloop_runner`
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
  /oql/file:
    get:
      operationId: oql_read_file
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
      summary: Read a TestQL file content (.testql.toon.yaml / .oql / .tql).
      tags:
      - fastapi
      - oql
  /oql/files:
    get:
      operationId: oql_list_files
      responses:
        '200': *id001
        '401': *id002
        '404': *id003
        '500': *id004
      summary: List all .testql.toon.yaml files in the project (with .oql/.tql fallback).
      tags:
      - fastapi
      - oql
  /oql/log:
    get:
      operationId: oql_read_log
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
      - oql
  /oql/logs:
    get:
      operationId: oql_list_logs
      responses:
        '200': *id001
        '401': *id002
        '404': *id003
        '500': *id004
      summary: List available log files.
      tags:
      - fastapi
      - oql
  /oql/run-file:
    post:
      operationId: oql_run_file
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
      summary: Run an entire OQL file with validation. Returns structured results
        + saves log.
      tags:
      - fastapi
      - oql
  /oql/run-line:
    post:
      operationId: oql_run_line
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
      summary: Execute a single OQL command line via the encoder bridge.
      tags:
      - fastapi
      - oql
  /oql/tables:
    get:
      operationId: oql_list_tables
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
      summary: Extract table names from an OQL file.
      tags:
      - fastapi
      - oql
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

# ── Configuration ──────────────────────────────────────
CONFIG[2]{key, value}:
  entity,  items
  base_path,  /api/v3/data/items

# ── API Calls ─────────────────────────────────────
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

# ── Configuration ──────────────────────────────────────
CONFIG[1]{key, value}:
  api_url,  $TARGET_URL

# ── API Calls ─────────────────────────────────────
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

# ── UI Navigation ──────────────────────────────────────
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
  GET, /oql/files, 200
  GET, /oql/file, 200
  GET, /oql/tables, 200
  POST, /oql/run-line, 201
  POST, /oql/run-file, 201
  GET, /oql/logs, 200
  GET, /oql/log, 200
  GET, http://localhost:8101/oql/file, 200
  GET, http://localhost:8101/oql/files, 200
  GET, http://localhost:8101/oql/log, 200
  GET, http://localhost:8101/oql/logs, 200
  POST, http://localhost:8101/oql/run-file, 201
  POST, http://localhost:8101/oql/run-line, 201
  GET, http://localhost:8101/oql/tables, 200

ASSERT[2]{field, operator, expected}:
  status, <, 500
  response_time, <, 2000

# Summary by Framework:
#   fastapi: 7 endpoints
#   openapi: 7 endpoints
```

#### `testql-scenarios/generated-asset-assert.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-asset-assert.testql.toon.yaml
# SCENARIO: Internal Asset Availability (excluding known-external 403s)
# TYPE: web
# GENERATED: true
# ITERATION: 2
# FOCUS: page.root, asset nodes
# OPEN_FAILURES: finding.web.asset_status

CONFIG[3]{key, value}:
  base_url, https://tom.sapletta.com
  timeout_ms, 8000
  retry_count, 1

# Internal assets only — external CDN/third-party excluded
API[5]{method, endpoint, expected_status}:
  GET, /, 200
  GET, /favicon.ico, 200
  GET, /robots.txt, 200
  HEAD, /, 200
  HEAD, /sitemap.xml, 200

ASSERT[2]{field, operator, expected}:
  status, <, 500
  response_time, <, 3000
```

#### `testql-scenarios/generated-cli-extended.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-cli-extended.testql.toon.yaml
# SCENARIO: Extended CLI Smoke Tests
# TYPE: cli
# GENERATED: true
# ITERATION: 3
# FOCUS: page.root CLI paths, coverage gap closure

CONFIG[2]{key, value}:
  cli_command, venv/bin/python3.13 -m testql
  timeout_ms, 15000

# Core CLI subcommands — must exit cleanly with --help
SHELL[8]{command, exit_code}:
  venv/bin/python3.13 -m testql --help, 0
  venv/bin/python3.13 -m testql --version, 0
  venv/bin/python3.13 -m testql topology --help, 0
  venv/bin/python3.13 -m testql run --help, 0
  venv/bin/python3.13 -m testql discover --help, 0
  venv/bin/python3.13 -m testql generate --help, 0
  venv/bin/python3.13 -m testql inspect --help, 0
  venv/bin/python3.13 -m testql mcp --help, 0

ASSERT[1]{field, operator, expected}:
  exit_code, ==, 0
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
# ITERATION: 3 (fix_test — replaced LOG stubs with UNIT steps)

CONFIG[2]{key, value}:
  runner, pytest
  flags, --no-cov -q

UNIT[10]{target}:
  tests/test_cli.py
  tests/test_mcp_autoloop.py
  tests/test_cli_no_block.py
  tests/test_smoke_decisions.py
  tests/test_interpreter.py
  tests/test_runner.py
  tests/test_detectors.py
  tests/test_generators.py
  tests/test_discovery.py
  tests/test_pipeline.py

ASSERT[1]{field, operator, expected}:
  exit_code, ==, 0
```

#### `testql-scenarios/generated-sitemap-assert.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-sitemap-assert.testql.toon.yaml
# SCENARIO: Sitemap Uniqueness and Asset Availability
# TYPE: web
# GENERATED: true
# ITERATION: 2
# FOCUS: sitemap.root, page.root
# OPEN_FAILURES: finding.sitemap.duplicates, finding.web.asset_status

CONFIG[3]{key, value}:
  base_url, https://tom.sapletta.com
  timeout_ms, 10000
  retry_count, 2

# Sitemap subpages (must return 200)
API[7]{method, endpoint, expected_status}:
  GET, /sitemap.xml, 200
  GET, /pl/, 200
  GET, /de/, 200
  GET, /ru/, 200
  GET, /, 200
  GET, /idea/, 200
  GET, /about/, 200

ASSERT[2]{field, operator, expected}:
  status, <, 500
  response_time, <, 5000

# External 403s (xmlrpc.php, sharethis, fonts.googleapis.com) are infra_blocked — not asserted
LOG[1]{message}:
  "SKIP external 403s: xmlrpc.php, sharethis, fonts.googleapis.com — infra_blocked per iter-1"
```

#### `testql/scenarios/generic/health-check.testql.toon.yaml`

```toon markpact:testql path=testql/scenarios/generic/health-check.testql.toon.yaml
# SCENARIO: health-check.testql.toon.yaml — generic health check scenario
# TYPE: api
# VERSION: 1.0

# ── Configuration ──────────────────────────────────────
CONFIG[1]{key, value}:
  api_url,  $TARGET_URL

# ── API Calls ─────────────────────────────────────
API[2]{method, endpoint, status, assert_key, assert_value}:
  GET,  /health,  200,  status,  ok
  GET,  /api/v3/version,  200,  -,  -
```

#### `testql/scenarios/examples/quick-navigation.testql.toon.yaml`

```toon markpact:testql path=testql/scenarios/examples/quick-navigation.testql.toon.yaml
# SCENARIO: Quick Navigation Example
# TYPE: gui
# VERSION: 1.0

# ── UI Navigation ──────────────────────────────────────
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

# ── UI Navigation ──────────────────────────────────────
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
# SCENARIO: run-all-views.testql.toon.yaml — Master runner for all per-view OQL tests
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

# ── API Calls ─────────────────────────────────────
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

# ── API Calls ─────────────────────────────────────
API[4]{method, endpoint, status}:
  GET,  /api/v3/data/devices?limit=5,  200
  GET,  /api/v3/data/customers?limit=5,  200
  GET,  /api/v3/data/intervals?limit=5,  200
  GET,  /api/v3/data/test_scenarios?limit=5,  200

WAIT[1]{ms}:
  100

# ── API Calls ─────────────────────────────────────
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

# ── API Calls ─────────────────────────────────────
API[2]{method, endpoint, status}:
  GET,  /api/v3/data/protocols?limit=3,  200
  GET,  /api/v3/data/test_scenarios?limit=3,  200
```

#### `testql/scenarios/examples/test-device-flow.testql.toon.yaml`

```toon markpact:testql path=testql/scenarios/examples/test-device-flow.testql.toon.yaml
# SCENARIO: DSL Example: Complete Device Test Flow
# TYPE: interaction
# VERSION: 1.0

# ── Session Recording ──────────────────────────────────
RECORD_START[1]{session_id}:
  operator1

# ── UI Navigation ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-id/device-rfid,  300

# ── Domain Selections ───────────────────────────────────
SELECT[1]{action, id, meta}:
  device,  d-001,  {type:MSA_G1, serial:AO73138, customer:cu-001}

# ── UI Navigation ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/testing,  300

# ── Semantic Steps ─────────────────────────────────
FLOW[1]{command, target, meta}:
  emit,  test.interval_dialog_opened,  {deviceId:d-001}

# ── Domain Selections ───────────────────────────────────
SELECT[1]{action, id, meta}:
  interval,  3m,  {code:periodic_3m, description:3 months}

# ── Semantic Steps ─────────────────────────────────
FLOW[2]{command, target, meta}:
  start_test,  ts-c20,  {name:C20 Standard, steps:5}
  protocol_created,  pro-example-001,  {via:cqrs, deviceId:d-001}

# ── UI Navigation ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test-protocol?protocol=pro-example-001&step=1,  300

# ── Semantic Steps ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-1,  {name:Pressure check, status:passed, value:15.2 mbar}

WAIT[1]{ms}:
  500

# ── Semantic Steps ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-2,  {name:Leak test, status:passed, value:OK}

WAIT[1]{ms}:
  500

# ── Semantic Steps ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-3,  {name:Visual inspection, status:passed, note:No damage}

WAIT[1]{ms}:
  500

# ── Semantic Steps ─────────────────────────────────
FLOW[1]{command, target, meta}:
  step_complete,  step-4,  {name:Functional test, status:passed}

WAIT[1]{ms}:
  500

# ── Semantic Steps ─────────────────────────────────
FLOW[2]{command, target, meta}:
  step_complete,  step-5,  {name:Final verification, status:passed}
  protocol_finalize,  pro-example-001,  {"status": "executed", "summary": {"passed": 5, "failed": 0}

# ── UI Navigation ──────────────────────────────────────
NAVIGATE[1]{path, wait_ms}:
  /connect-test/reports?protocol=pro-example-001,  300

RECORD_STOP:
```

#### `testql/scenarios/tests/test-devices-crud.testql.toon.yaml`

```toon markpact:testql path=testql/scenarios/tests/test-devices-crud.testql.toon.yaml
# SCENARIO: Example DSL Script - Devices CRUD Operations
# TYPE: api
# VERSION: 1.0

# ── API Calls ─────────────────────────────────────
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

# ── API Calls ─────────────────────────────────────
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
# SCENARIO: test-encoder.testql.toon.yaml — Encoder navigation tests via OQL
# TYPE: gui
# VERSION: 1.0

# ── Configuration ──────────────────────────────────────
CONFIG[1]{key, value}:
  encoder_url,  ${ENCODER_URL:-http://localhost:8105}

# ── Encoder Hardware ────────────────────────────────────────
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

# ── Configuration ──────────────────────────────────────
CONFIG[2]{key, value}:
  encoder_url,  ${ENCODER_URL:-http://localhost:8105}
  api_url,  ${API_URL:-http://localhost:8101}

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

# ── API Calls ─────────────────────────────────────
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

# ── UI Navigation ──────────────────────────────────────
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

# ── API Calls ─────────────────────────────────────
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

# ── API Calls ─────────────────────────────────────
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

# ── API Calls ─────────────────────────────────────
API[1]{method, endpoint, status}:
  GET,  /api/v3/data/protocols?limit=5,  200
```

#### `testql/scenarios/tests/test-gui-connect-test.testql.toon.yaml`

```toon markpact:testql path=testql/scenarios/tests/test-gui-connect-test.testql.toon.yaml
# SCENARIO: test-gui-connect-test.testql.toon.yaml — GUI tests for Connect Test module
# TYPE: gui
# VERSION: 1.0

# ── Configuration ──────────────────────────────────────
CONFIG[2]{key, value}:
  encoder_url,  ${ENCODER_URL:-http://localhost:8105}
  api_url,  ${API_URL:-http://localhost:8101}

# ── UI Navigation ──────────────────────────────────────
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

# ── Encoder Hardware ────────────────────────────────────────
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

# ── API Calls ─────────────────────────────────────
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

# ── Encoder Hardware ────────────────────────────────────────
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

# ── API Calls ─────────────────────────────────────
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

# ── API Calls ─────────────────────────────────────
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

# ── Semantic Steps ─────────────────────────────────
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

# ── API Calls ─────────────────────────────────────
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
  # OQL / Test Execution
  # ─────────────────────────────────────────────────────────────────────────────

  oql:run:
    desc: Run OQL scenario file
    cmds:
      - testql run {{.CLI_ARGS}}

  oql:shell:
    desc: Start OQL interactive shell
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
  version: 1.2.54
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
pytest-cov>=7.0
fastapi>=0.100
```

### Development

```text markpact:deps python scope=dev
pytest
pytest-asyncio
pytest-cov
mcp>=1.0
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

## Makefile Targets

- `help` — Default target
- `install` — Installation
- `install-dev`
- `test` — Testing
- `test-cov`
- `lint` — Code quality
- `format`
- `clean` — Utilities
- `publish` — Release helpers
- `publish-confirm`
- `publish-test`
- `version`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# testql | 372f 45261L | python:344,shell:24,less:4 | 2026-06-06
# stats: 913 func | 602 cls | 372 mod | CC̄=3.7 | critical:36 | cycles:0
# alerts[5]: CC main=15; CC parse_testtoon=14; CC watchdog=14; CC _filter_commands=14; CC _expand_flow=14
# hotspots[5]: generate_from_page fan=19; heal_scenario fan=19; watch fan=19; suite fan=19; watchdog fan=19
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[372]:
  TODO/testtoon_parser.py,142
  app.doql.less,237
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
  examples/web-inspection/c2004-localhost/run-matrix.sh,102
  examples/web-inspection/c2004-localhost/run.sh,73
  examples/web-inspection/run.sh,43
  examples/web-inspection-dot-testql/run.sh,14
  project.sh,50
  scripts/install_testql_autoloop.sh,157
  scripts/setup_mcp_windsurf.sh,92
  scripts/smoke_manifest_flow.sh,71
  test_autoloop_api.py,453
  test_autoloop_mcp.py,519
  test_manifest_and_generators.py,526
  testql/__init__.py,10
  testql/__main__.py,7
  testql/_base_fallback.py,233
  testql/adapters/__init__.py,54
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
  testql/adapters/nlp2dsl/__init__.py,22
  testql/adapters/nlp2dsl/client.py,63
  testql/adapters/nlp2dsl/live_llm.py,91
  testql/adapters/nlp2dsl/llm_provider.py,43
  testql/adapters/nlp2dsl/mock_llm.py,47
  testql/adapters/nlp2dsl/nlp2dsl_adapter.py,82
  testql/adapters/proto/__init__.py,54
  testql/adapters/proto/compatibility.py,144
  testql/adapters/proto/descriptor_loader.py,163
  testql/adapters/proto/message_validator.py,188
  testql/adapters/proto/proto_adapter.py,243
  testql/adapters/registry.py,151
  testql/adapters/scenario_yaml.py,507
  testql/adapters/sql/__init__.py,51
  testql/adapters/sql/ddl_parser.py,229
  testql/adapters/sql/dialect_resolver.py,89
  testql/adapters/sql/fixtures.py,106
  testql/adapters/sql/query_parser.py,96
  testql/adapters/sql/sql_adapter.py,334
  testql/adapters/testtoon_adapter.py,743
  testql/artifacts/__init__.py,18
  testql/artifacts/base.py,25
  testql/artifacts/email_checker.py,45
  testql/artifacts/file_checker.py,43
  testql/artifacts/registry.py,36
  testql/autoloop_runner.py,1
  testql/base.py,38
  testql/cli.py,107
  testql/commands/__init__.py,36
  testql/commands/auto_cmd.py,203
  testql/commands/conversation_cmd.py,109
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
  testql/commands/generate_cmd.py,172
  testql/commands/generate_from_page_cmd.py,100
  testql/commands/generate_ir_cmd.py,50
  testql/commands/generate_topology_cmd.py,59
  testql/commands/heal_scenario_cmd.py,308
  testql/commands/inspect_cmd.py,35
  testql/commands/misc_cmds.py,293
  testql/commands/run_cmd.py,161
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
  testql/commands/watchdog_cmd.py,283
  testql/conversation/__init__.py,6
  testql/conversation/runner.py,287
  testql/detectors/__init__.py,54
  testql/detectors/base.py,35
  testql/detectors/config_detector.py,219
  testql/detectors/django_detector.py,52
  testql/detectors/express_detector.py,60
  testql/detectors/fastapi_detector.py,154
  testql/detectors/flask_detector.py,122
  testql/detectors/graphql_detector.py,88
  testql/detectors/models.py,61
  testql/detectors/openapi_detector.py,91
  testql/detectors/test_detector.py,70
  testql/detectors/unified.py,240
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
  testql/generators/analyzers.py,310
  testql/generators/api_generator.py,299
  testql/generators/base.py,60
  testql/generators/convenience.py,52
  testql/generators/conversation_generator.py,70
  testql/generators/generators.py,31
  testql/generators/llm/__init__.py,17
  testql/generators/llm/coverage_optimizer.py,33
  testql/generators/llm/edge_case_generator.py,27
  testql/generators/multi.py,106
  testql/generators/page_analyzer.py,527
  testql/generators/pipeline.py,96
  testql/generators/pytest_generator.py,148
  testql/generators/scenario_generator.py,88
  testql/generators/sources/__init__.py,86
  testql/generators/sources/base.py,33
  testql/generators/sources/config_source.py,306
  testql/generators/sources/conversation.py,36
  testql/generators/sources/graphql_source.py,67
  testql/generators/sources/nl_source.py,28
  testql/generators/sources/openapi_source.py,94
  testql/generators/sources/oql_models.py,31
  testql/generators/sources/oql_parser.py,268
  testql/generators/sources/oql_source.py,307
  testql/generators/sources/page_source.py,173
  testql/generators/sources/proto_source.py,91
  testql/generators/sources/pytest_source.py,390
  testql/generators/sources/sql_source.py,80
  testql/generators/sources/ui_source.py,82
  testql/generators/specialized_generator.py,171
  testql/generators/targets/__init__.py,37
  testql/generators/targets/base.py,22
  testql/generators/targets/nl_target.py,23
  testql/generators/targets/pytest_target.py,65
  testql/generators/targets/testtoon_target.py,24
  testql/generators/test_generator.py,107
  testql/integrations/planfile_hook.py,116
  testql/interpreter/__init__.py,92
  testql/interpreter/_api_runner.py,303
  testql/interpreter/_assertions.py,305
  testql/interpreter/_converter.py,63
  testql/interpreter/_dom_scan.py,41
  testql/interpreter/_encoder.py,101
  testql/interpreter/_flow.py,166
  testql/interpreter/_gui.py,709
  testql/interpreter/_hardware.py,110
  testql/interpreter/_modbus.py,233
  testql/interpreter/_parser.py,34
  testql/interpreter/_shell.py,261
  testql/interpreter/_testtoon_parser.py,565
  testql/interpreter/_unit.py,268
  testql/interpreter/_validation.py,154
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
  testql/interpreter/dom_scan_formatters.py,85
  testql/interpreter/dom_scan_mixin.py,319
  testql/interpreter/dom_scan_models.py,54
  testql/interpreter/dom_scanner.py,419
  testql/interpreter/interpreter.py,160
  testql/interpreter/testtoon_models.py,34
  testql/interpreter/testtoon_parser.py,297
  testql/interpreter.py,28
  testql/ir/__init__.py,55
  testql/ir/assertions.py,34
  testql/ir/captures.py,38
  testql/ir/fixtures.py,34
  testql/ir/metadata.py,32
  testql/ir/plan.py,43
  testql/ir/steps.py,319
  testql/ir_runner/__init__.py,35
  testql/ir_runner/assertion_eval.py,125
  testql/ir_runner/context.py,43
  testql/ir_runner/engine.py,137
  testql/ir_runner/executors/__init__.py,54
  testql/ir_runner/executors/api.py,68
  testql/ir_runner/executors/assert_json.py,31
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
  testql/mcp/__init__.py,34
  testql/mcp/server.py,160
  testql/meta/__init__.py,42
  testql/meta/confidence_scorer.py,95
  testql/meta/coverage_analyzer.py,174
  testql/meta/mutator.py,220
  testql/meta/self_test.py,59
  testql/openapi_generator.py,445
  testql/pipeline.py,146
  testql/report_generator.py,251
  testql/reporters/__init__.py,7
  testql/reporters/console.py,39
  testql/reporters/json_reporter.py,34
  testql/reporters/junit.py,80
  testql/results/__init__.py,21
  testql/results/analyzer.py,505
  testql/results/artifacts.py,145
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
  tests/conftest.py,60
  tests/fixtures/discovery/python_pkg/sample_api/__init__.py,2
  tests/fixtures/discovery/python_pkg/sample_api/main.py,8
  tests/test_adapter_capture_syntax.py,167
  tests/test_adapters_base.py,159
  tests/test_api_handler.py,90
  tests/test_browser_discovery.py,111
  tests/test_cli.py,98
  tests/test_cli_no_block.py,104
  tests/test_conversation_live_llm.py,83
  tests/test_conversation_nlp2dsl.py,158
  tests/test_converter.py,178
  tests/test_converter_handlers.py,352
  tests/test_detectors.py,389
  tests/test_discovery.py,104
  tests/test_dispatcher.py,140
  tests/test_doql_parser_sumd_gen.py,323
  tests/test_echo.py,227
  tests/test_echo_doql_parser.py,220
  tests/test_echo_schemas_helpers.py,214
  tests/test_encoder_routes.py,42
  tests/test_generate_cmd.py,95
  tests/test_generate_from_page_cli.py,280
  tests/test_generate_ir_cli.py,151
  tests/test_generators.py,238
  tests/test_graphql_adapter.py,197
  tests/test_gui_execution.py,130
  tests/test_interpreter.py,224
  tests/test_ir.py,217
  tests/test_ir_captures.py,51
  tests/test_ir_runner_assertion_eval.py,108
  tests/test_ir_runner_captures.py,153
  tests/test_ir_runner_engine.py,143
  tests/test_ir_runner_executors.py,174
  tests/test_ir_runner_interpolation.py,41
  tests/test_mcp_autoloop.py,202
  tests/test_meta_confidence.py,97
  tests/test_meta_coverage.py,137
  tests/test_meta_mutator.py,190
  tests/test_meta_self_test.py,99
  tests/test_misc_cmds.py,111
  tests/test_modbus_commands.py,46
  tests/test_navigate_json_path.py,161
  tests/test_network_discovery.py,163
  tests/test_nl_adapter.py,278
  tests/test_nl_entity_extractor.py,155
  tests/test_nl_grammar.py,101
  tests/test_nl_intent_recognizer.py,133
  tests/test_nl_scenarios_e2e.py,92
  tests/test_openapi_generator.py,344
  tests/test_page_analyzer.py,246
  tests/test_pipeline.py,153
  tests/test_plugin_registry.py,120
  tests/test_proto_adapter.py,128
  tests/test_proto_compatibility.py,159
  tests/test_proto_descriptor_loader.py,175
  tests/test_proto_graphql_scenarios_e2e.py,82
  tests/test_proto_message_validator.py,123
  tests/test_report_generator.py,169
  tests/test_reporters.py,317
  tests/test_results.py,124
  tests/test_run_cmd.py,114
  tests/test_run_ir_cli.py,66
  tests/test_runner.py,188
  tests/test_scenario_yaml_adapter.py,208
  tests/test_shell_execution.py,134
  tests/test_smoke_decisions.py,160
  tests/test_sources.py,497
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
  tests/test_test_generator.py,121
  tests/test_testtoon_adapter.py,412
  tests/test_toon_parser.py,84
  tests/test_topology.py,88
  tests/test_topology_generator.py,162
  tests/test_unit_execution.py,113
  tests/test_validation.py,185
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
  test_autoloop_api.py:
    e: add_colors,ok,fail,warn,info,header,step_import_testql,step_mcp_check,step_discovery,step_topology,step_inspect,step_generate_tests,step_run_scenario,step_run_tests,step_generate_llm_decision,step_save_artifacts,run_iteration,main
    add_colors()
    ok(msg)
    fail(msg)
    warn(msg)
    info(msg)
    header(msg)
    step_import_testql()
    step_mcp_check()
    step_discovery(project_path)
    step_topology(project_path)
    step_inspect(project_path)
    step_generate_tests(project_path)
    step_run_scenario(scenario_path)
    step_run_tests(scenarios)
    step_generate_llm_decision(iteration;discovery;topology;inspection;test_results)
    step_save_artifacts(output_dir;discovery;topology;inspection;test_results;llm_decision)
    run_iteration(project_path;iteration;output_dir)
    main()
  test_autoloop_mcp.py:
    e: ok,fail,warn,info,header,step_generate_topology,step_generate_tests,step_run_tests,step_generate_llm_prompt,step_check_mcp_windsurf,run_autoloop,main,C
    C:
    ok(msg)
    fail(msg)
    warn(msg)
    info(msg)
    header(msg)
    step_generate_topology(project_path;output_dir)
    step_generate_tests(project_path;output_dir)
    step_run_tests(scenarios;output_dir)
    step_generate_llm_prompt(topology;test_results;iteration;output_dir;simulate_llm)
    step_check_mcp_windsurf(output_dir)
    run_autoloop(project_path;max_iterations;simulate_llm)
    main()
  test_manifest_and_generators.py:
    e: log_ok,log_fail,log_warn,log_info,generate_report,main,Colors,ManifestProbeTester,GeneratorTester,MCPWindsurfChecker
    Colors:
    ManifestProbeTester: run_all(0),_test_probe(2)  # Test all discovery probe types.
    GeneratorTester: run_all(0),_test_api_generator(0),_test_python_test_generator(0),_test_scenario_generator(0),_test_round_trip(0)  # Test all test generation capabilities.
    MCPWindsurfChecker: run_all(0),_check_cli(0),_check_json_output(0),_check_discover_command(0),_check_generate_command(0)  # Check MCP Windsurf integration compatibility.
    log_ok(msg)
    log_fail(msg)
    log_warn(msg)
    log_info(msg)
    generate_report(all_results;output_path)
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
  testql/adapters/nlp2dsl/__init__.py:
  testql/adapters/nlp2dsl/client.py:
    e: Nlp2DslResponse,Nlp2DslClient
    Nlp2DslResponse: ok(0)
    Nlp2DslClient: __init__(2),_post(2),chatstart(1),chatmessage(1),runworkflow(1),workflow_from_text(1)  # Call nlp2dsl REST endpoints used in conversation test scenar
  testql/adapters/nlp2dsl/live_llm.py:
    e: LiveLLMProvider
    LiveLLMProvider: from_env(1),reply_for(1),_build_prompt(1),_chat(1),_parse_json_object(1)  # Call an OpenAI-compatible chat API to fill missing dialog fi
  testql/adapters/nlp2dsl/llm_provider.py:
    e: live_llm_enabled,resolve_llm_provider,LLMProvider
    LLMProvider: reply_for(1)
    live_llm_enabled(explicit)
    resolve_llm_provider()
  testql/adapters/nlp2dsl/mock_llm.py:
    e: load_mock_replies,MockLLMProvider
    MockLLMProvider: reply_for(1)  # Return canned assistant payloads keyed by conversation turn 
    load_mock_replies(source)
  testql/adapters/nlp2dsl/nlp2dsl_adapter.py:
    e: Nlp2DslAdapter
    Nlp2DslAdapter: detect(1),parse(1),render(1),validate(1)  # Wraps TestTOON parsing and adds conversation/nlp2dsl validat
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
    AdapterRegistry: __init__(0),register(1),register_plugin(1),register_module(1),load_plugins(0),ensure_plugins_loaded(0),unregister(1),clear(0),get(1),all(0),by_extension(1),detect(1)  # In-process registry of `BaseDSLAdapter` instances.
    get_registry()
  testql/adapters/scenario_yaml.py:
    e: _as_dict,_as_list,_parse_wait_ms,_split_request,_normalise_capture_path,_captures_from,_assertion_from_field,_assertions_from_expect,_step_common,_api_step,_gui_step,_encoder_step,_shell_step,_unit_step,_typed_step,_detect_step_type,_is_gui_step,_is_encoder_step,_is_unit_step,_create_step_by_type,_create_sql_step,_create_graphql_step,_create_nl_step,_create_generic_step,_metadata_from,_config_from,_plan_from_yaml,_render_step,_render_api_step,_render_gui_step,_render_shell_step,_render_encoder_step,_render_unit_step,_render_sql_step,_render_graphql_step,_render_nl_step,_add_common_step_attributes,_reverse_operator,parse,render,ScenarioYamlAdapter
    ScenarioYamlAdapter: detect(1),parse(1),render(1)
    _as_dict(value)
    _as_list(value)
    _parse_wait_ms(value)
    _split_request(value)
    _normalise_capture_path(path)
    _captures_from(value)
    _assertion_from_field(field;value)
    _assertions_from_expect(expect)
    _step_common(step;data)
    _api_step(data)
    _gui_step(data)
    _encoder_step(data)
    _shell_step(data)
    _unit_step(data)
    _typed_step(item)
    _detect_step_type(data)
    _is_gui_step(data)
    _is_encoder_step(data)
    _is_unit_step(data)
    _create_step_by_type(step_type;data)
    _create_sql_step(data)
    _create_graphql_step(data)
    _create_nl_step(data)
    _create_generic_step(data)
    _metadata_from(data)
    _config_from(data)
    _plan_from_yaml(data)
    _render_step(step)
    _render_api_step(step)
    _render_gui_step(step)
    _render_shell_step(step)
    _render_encoder_step(step)
    _render_unit_step(step)
    _render_sql_step(step)
    _render_graphql_step(step)
    _render_nl_step(step)
    _add_common_step_attributes(data;step)
    _reverse_operator(op)
    parse(source)
    render(plan)
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
    e: _config_to_dict,_api_section_to_steps,_navigate_section_to_steps,_gui_section_to_steps,_encoder_section_to_steps,_assert_section_to_steps,_capture_section_apply,_resolve_capture_target,_coerce_assert_expected,_assert_json_field,_assert_json_section_apply,_generic_section_to_steps,_shell_section_to_steps,_unit_section_to_steps,_log_section_to_steps,_context_section_to_config,_conversation_section_to_steps,_nlp2dsl_section_to_steps,_validate_section_to_steps,_parse_artifact_criteria,_translate_section,_toon_to_plan,_render_meta,_render_config,_render_api_steps,_render_navigate_steps,_render_encoder_steps,_toon_safe_selector,_render_gui_action_steps,_render_shell_steps,_render_unit_steps,_render_log_steps,_render_assertions,_render_captures,_render_validate_steps,_format_extra_value,_group_generic_steps,_derive_columns,_render_group_section,_render_generic_section_steps,_render_plan,parse,render,TestToonAdapter
    TestToonAdapter: detect(1),parse(1),render(1)  # Adapter for the legacy `*.testql.toon.yaml` format (TestTOON
    _config_to_dict(section)
    _api_section_to_steps(section)
    _navigate_section_to_steps(section)
    _gui_section_to_steps(section)
    _encoder_section_to_steps(section)
    _assert_section_to_steps(section)
    _capture_section_apply(section;plan)
    _resolve_capture_target(target;by_name;steps)
    _coerce_assert_expected(raw)
    _assert_json_field(path)
    _assert_json_section_apply(section;plan)
    _generic_section_to_steps(section)
    _shell_section_to_steps(section)
    _unit_section_to_steps(section)
    _log_section_to_steps(section)
    _context_section_to_config(section)
    _conversation_section_to_steps(section)
    _nlp2dsl_section_to_steps(section)
    _validate_section_to_steps(section)
    _parse_artifact_criteria(criteria)
    _translate_section(section)
    _toon_to_plan(toon)
    _render_meta(md)
    _render_config(config)
    _render_api_steps(steps)
    _render_navigate_steps(steps)
    _render_encoder_steps(steps)
    _toon_safe_selector(selector)
    _render_gui_action_steps(steps)
    _render_shell_steps(steps)
    _render_unit_steps(steps)
    _render_log_steps(steps)
    _render_assertions(steps)
    _render_captures(steps)
    _render_validate_steps(steps)
    _format_extra_value(value)
    _group_generic_steps(steps)
    _derive_columns(rows)
    _render_group_section(name;rows;columns)
    _render_generic_section_steps(steps)
    _render_plan(plan)
    parse(source)
    render(plan)
  testql/artifacts/__init__.py:
  testql/artifacts/base.py:
    e: ArtifactCheckResult,BaseArtifactChecker
    ArtifactCheckResult:
    BaseArtifactChecker: check(1)
  testql/artifacts/email_checker.py:
    e: EmailArtifactChecker
    EmailArtifactChecker: check(1),_list_messages(1)
  testql/artifacts/file_checker.py:
    e: FileArtifactChecker
    FileArtifactChecker: check(1)
  testql/artifacts/registry.py:
    e: get_artifact_registry,ArtifactCheckerRegistry
    ArtifactCheckerRegistry: __init__(0),register(1),check(1)
    get_artifact_registry()
  testql/autoloop_runner.py:
  testql/base.py:
  testql/cli.py:
    e: mcp_serve,cli,_fetch_latest_version,check_and_upgrade,main
    mcp_serve()
    cli()
    _fetch_latest_version()
    check_and_upgrade()
    main()
  testql/commands/__init__.py:
  testql/commands/auto_cmd.py:
    e: auto,_status_color,_run_generation_phase,_run_analysis_phase,_build_report_data,_run_report_phase,_print_summary,_render_console_report,_render_markdown_report
    auto(ctx;source;url;api_url;output_dir;output_format;fail_fast;keep_generated)
    _status_color(status)
    _run_generation_phase(source;out_dir)
    _run_analysis_phase(topology)
    _build_report_data(source;url;api_url;topology;envelope;testable_nodes;written;out_dir)
    _run_report_phase(report_data;out_dir;output_format)
    _print_summary(envelope;report_data;out_dir)
    _render_console_report(data;out_dir)
    _render_markdown_report(data;out_dir)
  testql/commands/conversation_cmd.py:
    e: _validate_scenario,_resolve_base_url,_create_runner,_format_mode,_output_json,_output_text,conversation,conversation_run
    _validate_scenario(adapter;scenario)
    _resolve_base_url(api_url;plan)
    _create_runner(api_url;dry_run;live_llm;mock_replies)
    _format_mode(dry_run;live_llm)
    _output_json(result)
    _output_text(result;scenario;plan;dry_run;live_llm)
    conversation()
    conversation_run(scenario;api_url;dry_run;mock_replies;live_llm;output_fmt)
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
    e: _strip_path_segments,_migrate_legacy_extension,_remap_tests_prefix,_normalize_oql_path,_resolve_oql_path,_assert_bool_prop,_assert_count_prop,_assert_text_prop,_assert_classes_prop,_evaluate_assertion,_format_log_detail,_exec_encoder_cmd,_exec_browser_cmd,_exec_assert_cmd,_execute_oql_line,oql_list_files,oql_read_file,oql_list_tables,_extract_table_names,oql_run_line,oql_run_file,_run_oql_lines,_update_counters,_build_run_summary,_write_run_log,oql_list_logs,oql_read_log
    _strip_path_segments(candidate)
    _migrate_legacy_extension(candidate)
    _remap_tests_prefix(candidate)
    _normalize_oql_path(path)
    _resolve_oql_path(path)
    _assert_bool_prop(result;prop;expected)
    _assert_count_prop(result;expected)
    _assert_text_prop(result;expected)
    _assert_classes_prop(result;expected)
    _evaluate_assertion(result;prop;expected)
    _format_log_detail(cmd;result)
    _exec_encoder_cmd(cmd;arg)
    _exec_browser_cmd(cmd;arg;raw_arg)
    _exec_assert_cmd(raw_arg)
    _execute_oql_line(line)
    oql_list_files()
    oql_read_file(path)
    oql_list_tables(path)
    _extract_table_names(content)
    oql_run_line(req)
    oql_run_file(req)
    _run_oql_lines(lines;label)
    _update_counters(counters;result)
    _build_run_summary(normalized_path;requested_path;lines;results;counters)
    _write_run_log(normalized_path;lines;log_lines;summary)
    oql_list_logs()
    oql_read_log(name)
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
    generate(path;output_dir;analyze_only;fmt;to_ir;validate_url)
    _emit_ir_json(paths;fmt)
    analyze(path)
    _count_routes_by(routes;key)
    _print_routes_section(profile)
    _print_scenarios_section(profile)
  testql/commands/generate_from_page_cmd.py:
    e: _default_output,generate_from_page
    _default_output(url)
    generate_from_page(url;output;max_steps;headless;from_elements;print_only)
  testql/commands/generate_ir_cmd.py:
    e: _split_from_arg,generate_ir
    _split_from_arg(value)
    generate_ir(from_;to_;out;no_llm)
  testql/commands/generate_topology_cmd.py:
    e: generate_topology,_pick_trace
    generate_topology(source;trace_id;output;fmt;scan_network)
    _pick_trace(topology;trace_id)
  testql/commands/heal_scenario_cmd.py:
    e: _collect_selectors,_selector_resolves,_healed_path,_heal_text,heal_scenario,_heal_with_elements,_heal_with_browser,_print_summary,HealReport
    HealReport: __post_init__(0)
    _collect_selectors(text)
    _selector_resolves(page;selector)
    _healed_path(file)
    _heal_text(text;replacements)
    heal_scenario(file;url;write;from_elements;headless;report_path)
    _heal_with_elements(selectors;elements)
    _heal_with_browser(url;selectors)
    _print_summary(report;replacements)
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
    e: _resolve_input_paths,_run_single,_emit_single_json,_emit_multi_json,_maybe_planfile,run
    _resolve_input_paths(spec)
    _run_single(path;url;dry_run;quiet;timeout)
    _emit_single_json(result)
    _emit_multi_json(results)
    _maybe_planfile(result;filename;planfile)
    run(files;url;dry_run;output;quiet;planfile;timeout)
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
  testql/commands/watchdog_cmd.py:
    e: _discover_scenarios,_run_scenario,_post_failures,_extract_failures,_start_metrics_server,_update_metrics,_resolve_watchdog_config,_process_one_scenario,watchdog
    _discover_scenarios(specs)
    _run_scenario(scenario;url;timeout)
    _post_failures(webhook_url;scenario;failures)
    _extract_failures(payload)
    _start_metrics_server(port;scenarios)
    _update_metrics(metrics;scenario;exit_code;payload;elapsed)
    _resolve_watchdog_config(interval;webhook;port;url;timeout)
    _process_one_scenario(scenario;base_url;timeout_s;webhook_url;metrics)
    watchdog(scenarios;interval;webhook;port;url;timeout;once;verbose)
  testql/conversation/__init__.py:
  testql/conversation/runner.py:
    e: _step_status_name,_extract_path,TurnTrace,ConversationRunResult,ConversationRunner
    TurnTrace:
    ConversationRunResult: to_report_dict(0)
    ConversationRunner: __init__(3),variables(0),run(1),_apply_plan_config(1),_run_step(2),_run_via_ir(2),_dispatch_nlp2dsl_endpoint(2),_apply_nlp2dsl_mock(2),_determine_nlp2dsl_status(3),_extract_captures(2),_build_captures_dict(1),_run_nlp2dsl(2),_run_turn(2),_run_artifact(2),_interpolate_str(1),_interpolate(1)  # Execute conversation-layer steps and collect trace for resul
    _step_status_name(status)
    _extract_path(payload;path)
  testql/detectors/__init__.py:
  testql/detectors/base.py:
    e: BaseEndpointDetector
    BaseEndpointDetector: __init__(1),detect(0),_find_files(2)  # Base class for endpoint detectors.
  testql/detectors/config_detector.py:
    e: ConfigEndpointDetector
    ConfigEndpointDetector: detect(0),_detect_from_docker_compose(0),_detect_from_env_files(0),_detect_from_config_py(0),_analyze_docker_compose(1),_parse_port_mapping(1),_infer_protocol(1),_analyze_env_file(1),_analyze_config_py(1),_extract_port_from_url(1)  # Detect endpoints from configuration files.
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
    UnifiedEndpointDetector: __init__(2),detect_all(0),validate_endpoints(2),detect_and_validate(1),_deduplicate_endpoints(1),get_endpoints_by_type(1),get_endpoints_by_framework(1),generate_testql_scenario(2),_rest_block(1),_graphql_block(1),_ws_block(1)  # Unified detector that runs all specialized detectors.
    detect_endpoints(project_path;validate;base_url)
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
  testql/generators/api_generator.py:
    e: APIGeneratorMixin,_ValidationResult
    APIGeneratorMixin: _generate_api_tests(1),_validate_endpoints(2),_validate_single_endpoint(2),_try_endpoint_request(2),_sleep_with_backoff(2),_log_validation_summary(3),_build_api_test_header(1),_build_api_test_config(2),_build_api_test_preamble(1),_build_api_test_captures(0),_build_rest_section(1),_build_graphql_section(1),_build_websocket_section(1),_build_api_test_endpoints(1),_deduplicate_rest_routes(1),_build_api_test_assertions(0),_build_api_test_flow(0),_build_api_test_summary(1)  # Mixin for generating API-focused test scenarios.
    _ValidationResult: __init__(5)  # Result of endpoint validation.
  testql/generators/base.py:
    e: TestPattern,ProjectProfile,BaseAnalyzer
    TestPattern:  # Discovered test pattern from source code.
    ProjectProfile:  # Analyzed project profile.
    BaseAnalyzer: __init__(1),_get_exclude_dirs(0),_should_exclude_path(1)  # Base class for project analyzers.
  testql/generators/convenience.py:
    e: generate_for_project,generate_for_workspace
    generate_for_project(project_path)
    generate_for_workspace(workspace_path)
  testql/generators/conversation_generator.py:
    e: trace_from_export,ConversationGenerator
    ConversationGenerator: from_trace(1),render_toon(1)  # Build a declarative TestPlan from a runtime conversation tra
    trace_from_export(export)
  testql/generators/generators.py:
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
  testql/generators/page_analyzer.py:
    e: _is_unstable,_css_escape,pick_selector,_try_testid_selector,_try_id_selector,_try_name_selector,_try_role_aria_selector,_try_input_type_selector,_try_class_selector,default_input_value,is_typed_input,is_clickable,_name_or_selector,snapshot_to_plan,_create_base_plan,_add_navigate_step,_process_elements,_should_add_input_step,_add_input_step,_should_add_click_step,_add_click_step,_should_add_assert_visible,_add_assert_visible_step,_add_body_assertion,_normalise,find_replacement,_find_exact_match,_find_fuzzy_match,_build_element_haystack,_hint_from_selector,PageSnapshot
    PageSnapshot: __post_init__(0)  # Result of analysing one page — the input to plan constructio
    _is_unstable(value)
    _css_escape(value)
    pick_selector(elem)
    _try_testid_selector(elem)
    _try_id_selector(elem)
    _try_name_selector(elem)
    _try_role_aria_selector(elem)
    _try_input_type_selector(elem)
    _try_class_selector(elem)
    default_input_value(elem)
    is_typed_input(elem)
    is_clickable(elem)
    _name_or_selector(elem;selector)
    snapshot_to_plan(snap)
    _create_base_plan(snap;base_url)
    _add_navigate_step(plan;path)
    _process_elements(plan;elements;include_inputs;include_clicks;include_assert_visible;max_steps)
    _should_add_input_step(elem;include_inputs)
    _add_input_step(plan;elem;selector)
    _should_add_click_step(elem;include_clicks)
    _add_click_step(plan;elem;selector)
    _should_add_assert_visible(elem;include_assert_visible)
    _add_assert_visible_step(plan;elem;selector)
    _add_body_assertion(plan)
    _normalise(text)
    find_replacement(broken_selector;elements)
    _find_exact_match(candidates;normalised_hint)
    _find_fuzzy_match(candidates;normalised_hint)
    _build_element_haystack(elem)
    _hint_from_selector(selector)
  testql/generators/pipeline.py:
    e: _resolve_source,_resolve_target,sorted_sources,sorted_targets,run,write,PipelineResult
    PipelineResult:
    _resolve_source(spec)
    _resolve_target(spec)
    sorted_sources()
    sorted_targets()
    run()
    write(result;out)
  testql/generators/pytest_generator.py:
    e: PythonTestGeneratorMixin
    PythonTestGeneratorMixin: _generate_from_python_tests(1),_build_test_header(0),_extract_api_commands(1),_build_api_section(1),_extract_assertions(1),_parse_assertion_expression(1),_build_assertions_section(1),_build_no_conversions_note(0),_normalize_assertion_field(1)  # Mixin for generating tests from existing Python tests.
  testql/generators/scenario_generator.py:
    e: ScenarioGeneratorMixin
    ScenarioGeneratorMixin: _generate_from_scenarios(1),_convert_oql_command(1)  # Mixin for generating tests from OQL/CQL scenarios.
  testql/generators/sources/__init__.py:
    e: _get_config_source,get_source,available_sources
    _get_config_source()
    get_source(name)
    available_sources()
  testql/generators/sources/base.py:
    e: BaseSource
    BaseSource: load(1)  # Convert an external artifact (OpenAPI / SQL DDL / .proto / S
  testql/generators/sources/config_source.py:
    e: _load_file,_load_includes,_extract_phony_targets,_extract_target_commands,_parse_makefile,_parse_taskfile,_parse_docker_compose,_select_parser_for_file,_auto_detect_parser,_parse_targets,_parse_buf_yaml,_filter_commands,ConfigSource
    ConfigSource: load(1)  # Makefile, Taskfile.yml, docker-compose.yml, buf.yaml → TestP
    _load_file(source)
    _load_includes(content;file_path)
    _extract_phony_targets(content)
    _extract_target_commands(content;start_pos)
    _parse_makefile(content;file_path)
    _parse_taskfile(content)
    _parse_docker_compose(content)
    _select_parser_for_file(file_name)
    _auto_detect_parser(content)
    _parse_targets(content;source_path)
    _parse_buf_yaml(content)
    _filter_commands(commands;target_name)
  testql/generators/sources/conversation.py:
    e: ConversationTestSource
    ConversationTestSource: load(1)  # Load `.testql.toon.yaml` conversation scenarios into TestPla
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
  testql/generators/sources/oql_models.py:
    e: OqlCommand,ParsedScenario
    OqlCommand:  # Represents a single OQL/CQL command.
    ParsedScenario:  # Represents a parsed OQL/CQL scenario file.
  testql/generators/sources/oql_parser.py:
    e: OqlParser
    OqlParser: parse_file(1),_read_file_content(1),_should_skip_line(1),_extract_metadata_from_comment(2),_handle_sequence_block(3),_categorize_command(2),_parse_command(3),_create_command_from_match(4),_parse_set_command(3),_parse_read_command(3),_parse_write_command(3),_parse_check_command(3),_parse_wait_command(3),_parse_poll_command(3),_parse_exec_command(3),_parse_log_command(3),_parse_call_command(3),_parse_sequence_command(3),_parse_end_command(3),_parse_generic_command(3)  # Parse OQL/CQL scenario files.
  testql/generators/sources/oql_source.py:
    e: OqlSource
    OqlSource: load(1),ingest(1),_to_unified_ir(1),_detect_scenario_type(1),_convert_command(1),_convert_set(1),_convert_read(1),_convert_write(1),_convert_check(1),_convert_wait(1),_convert_poll(1),_convert_exec(1),_convert_log(1),_convert_call(1),to_oql(1),_build_oql_header(1),_build_oql_config(1),_build_oql_steps(1),_render_step_to_oql(2),_render_hardware_step(1),_build_oql_assertions(1),_render_assertion_to_oql(2)  # Source adapter for OQL/CQL scenario files.
  testql/generators/sources/page_source.py:
    e: extract_elements_from_page,_path_of,_origin,PageSource
    PageSource: load(1),_resolve_source(1),_fetch_via_playwright(2)  # Live-URL source: drive Playwright once, extract DOM, build T
    extract_elements_from_page(page)
    _path_of(url)
    _origin(url)
  testql/generators/sources/proto_source.py:
    e: _load_proto_text,_sample_value_for,_sample_fields_blob,_message_to_step,ProtoSource
    ProtoSource: load(1)  # `.proto` file or text → TestPlan with one round-trip step pe
    _load_proto_text(source)
    _sample_value_for(type_name)
    _sample_fields_blob(message)
    _message_to_step(message;schema_file)
  testql/generators/sources/pytest_source.py:
    e: ParsedTest,PytestParser,PytestSource
    ParsedTest:  # Represents a single parsed test function.
    PytestParser: parse_file(1),_parse_test_function(4),_extract_fixtures(1),_parse_body(2),_get_source_segment(2),_parse_assertion(2),_parse_call(2),_parse_assignment(2)  # Parse pytest test files into structured test definitions.
    PytestSource: load(1),ingest(1),_to_unified_ir(1),_detect_test_type(1),to_oql(1)  # Source adapter for pytest files - converts to Unified IR.
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
  testql/generators/specialized_generator.py:
    e: SpecializedGeneratorMixin
    SpecializedGeneratorMixin: _generate_api_integration_tests(1),_generate_cli_tests(1),_generate_lib_tests(1),_generate_frontend_tests(1),_generate_hardware_tests(1)  # Mixin for generating specialized test types.
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
  testql/integrations/planfile_hook.py:
    e: create_test_failure_ticket,create_individual_button_tickets
    create_test_failure_ticket(errors;file_path)
    create_individual_button_tickets(broken_buttons;project_path)
  testql/interpreter/__init__.py:
    e: main
    main()
  testql/interpreter/_api_runner.py:
    e: _resolve_length,_navigate_step,_navigate_json_path,_navigate_bracket_notation,_navigate_dot_notation,_navigate_dot_part,_handle_length_virtual,_handle_mixed_notation,ApiRunnerMixin
    ApiRunnerMixin: _do_http_request(3),_do_http_request_with_retry(3),_store_api_response(3),_record_api_success(4),_record_api_http_error(2),_record_api_error(2),_cmd_api(2),_cmd_capture(2)  # Mixin providing HTTP API execution commands: API, CAPTURE.
    _resolve_length(root;path)
    _navigate_step(obj;key)
    _navigate_json_path(root;path)
    _navigate_bracket_notation(root;path)
    _navigate_dot_notation(root;path)
    _navigate_dot_part(obj;part)
    _handle_length_virtual(obj)
    _handle_mixed_notation(obj;part)
  testql/interpreter/_assertions.py:
    e: AssertionsMixin
    AssertionsMixin: _cmd_assert_status(2),_cmd_assert_ok(2),_cmd_assert_contains(2),_cmd_assert_json(2),_cmd_assert_schema(2),_cmd_assert_headers(2),_cmd_assert_cookies(2)  # Mixin providing ASSERT_STATUS, ASSERT_OK, ASSERT_CONTAINS, A
  testql/interpreter/_converter.py:
  testql/interpreter/_dom_scan.py:
  testql/interpreter/_encoder.py:
    e: EncoderMixin
    EncoderMixin: _encoder_url(0),_encoder_prefix(0),_encoder_do_http(4),_encoder_call(5),_cmd_encoder_on(2),_cmd_encoder_off(2),_cmd_encoder_scroll(2),_cmd_encoder_click(2),_cmd_encoder_dblclick(2),_cmd_encoder_focus(2),_cmd_encoder_status(2),_cmd_encoder_page_next(2),_cmd_encoder_page_prev(2)  # Mixin providing all ENCODER_* hardware control commands.
  testql/interpreter/_flow.py:
    e: FlowMixin
    FlowMixin: _cmd_wait_for(2),_cmd_wait(2),_cmd_log(2),_cmd_print(2),_cmd_include(2),_emit_event(3)  # Mixin providing: WAIT, LOG, PRINT, INCLUDE and _emit_event.
  testql/interpreter/_gui.py:
    e: GuiMixin
    GuiMixin: _resolve_selector_with_fallback(1),_generate_fallback_selectors(1),_get_class_fallbacks(1),_get_id_fallbacks(1),_get_role_based_fallbacks(1),_get_button_text_fallbacks(1),_try_selectors(2),_try_single_selector(2),_find_element_with_logging(2),_init_gui_driver(0),_cmd_gui_start(2),_start_playwright(2),_start_selenium(2),_cmd_gui_navigate(2),_cmd_navigate(2),_cmd_gui_click(2),_cmd_gui_input(2),_cmd_gui_assert_visible(2),_cmd_gui_assert_text(2),_cmd_gui_capture(2),_cmd_gui_stop(2),_cmd_start(2),_cmd_stop(2),_cmd_close(2),_cmd_goto(2),_cmd_click(2),_cmd_input(2),_cmd_type(2),_cmd_assert_visible(2),_cmd_visible(2),_cmd_assert_text(2),_cmd_text(2),_cmd_capture(2),_cmd_screenshot(2)  # Mixin providing desktop GUI test commands using Playwright.
  testql/interpreter/_hardware.py:
    e: HardwareMixin
    HardwareMixin: _hardware_url(0),_hardware_do_http(4),_hardware_call(5),_cmd_hardware(2)  # Mixin providing HARDWARE command support for peripheral chec
  testql/interpreter/_modbus.py:
    e: ModbusMixin
    ModbusMixin: _modbus_probe_script(0),_modbus_store_response(2),_modbus_skip_enabled(0),_modbus_serial_exists(1),_modbus_parse_kv_args(1),_execute_probe_script(4),_parse_probe_response(1),_emit_probe_result(2),_modbus_run_probe_script(3),_cmd_modbus(2)  # MODBUS probe / API wizard helpers for TestQL automation.
  testql/interpreter/_parser.py:
    e: parse_oql,OqlLine,OqlScript
    OqlLine:
    OqlScript:
    parse_oql(source;filename)
  testql/interpreter/_shell.py:
    e: ShellMixin
    ShellMixin: _parse_shell_command(1),_execute_shell_dry_run(2),_execute_shell_live(3),_cmd_shell(2),_cmd_exec(2),_cmd_run(2),_cmd_assert_exit_code(2),_cmd_assert_stdout_contains(2),_cmd_assert_stderr_contains(2)  # Mixin providing shell command execution: SHELL, EXEC, RUN, A
  testql/interpreter/_testtoon_parser.py:
    e: validate_testtoon,_expand_config,_append_api_asserts,_expand_api,_expand_navigate,_expand_encoder,_expand_select,_expand_assert,_expand_steps,_expand_flow,_expand_oql,_expand_wait,_expand_include,_expand_record,_expand_validate,_expand_commands,_expand_dom_audit_buttons,_shell_expected_exit,_shell_timeout_ms,_quote_shell_command,_expand_shell,_expand_modbus,_expand_generic,testtoon_to_oql
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
    _expand_validate(section;lines;line_num)
    _expand_commands(section;lines;line_num)
    _expand_dom_audit_buttons(section;lines;line_num)
    _shell_expected_exit(row)
    _shell_timeout_ms(row;default_ms)
    _quote_shell_command(command)
    _expand_shell(section;lines;line_num)
    _expand_modbus(section;lines;line_num)
    _expand_generic(section;lines;line_num)
    testtoon_to_oql(text;filename)
  testql/interpreter/_unit.py:
    e: UnitMixin
    UnitMixin: _parse_pytest_args(1),_extract_pytest_summary(1),_run_pytest_subprocess(3),_handle_pytest_dry_run(2),_handle_pytest_success(2),_handle_pytest_error(3),_cmd_unit_pytest(2),_cmd_unit_pytest_discover(2),_cmd_unit_import(2),_cmd_unit_assert(2)  # Mixin providing unit test execution: UNIT_PYTEST, UNIT_IMPOR
  testql/interpreter/_validation.py:
    e: _resolve_target,ValidationMixin
    ValidationMixin: _cmd_validate(2),_record_validate(5)  # Mixin providing the VALIDATE command for textual / NL assert
    _resolve_target(interpreter;target)
  testql/interpreter/_websockets.py:
    e: WebSocketMixin
    WebSocketMixin: __init_subclass__(1),_get_ws_context(0),_cmd_ws_connect(2),_cmd_ws_send(2),_ws_do_receive(4),_cmd_ws_receive(2),_cmd_ws_assert_msg(2),_cmd_ws_close(2)  # Mixin for WebSocket testing support.
  testql/interpreter/converter/__init__.py:
  testql/interpreter/converter/core.py:
    e: convert_oql_to_testtoon,convert_file,convert_directory
    convert_oql_to_testtoon(source;filename)
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
  testql/interpreter/dom_scan_formatters.py:
    e: to_json,to_toon,to_text,to_text_audit
    to_json(result;indent)
    to_toon(result)
    to_text(result)
    to_text_audit(report)
  testql/interpreter/dom_scan_mixin.py:
    e: DomScanMixin
    DomScanMixin: _parse_dom_scan_args(2),_execute_dom_scan(4),_cmd_dom_scan(2),_cmd_dom_audit_buttons(2),_parse_audit_args(1),_ensure_gui_session(1),_handle_audit_report(2),_save_report_to_file(2),_cmd_assert_taborder(2),_cmd_assert_aria(2),_cmd_assert_focusable(2)  # Mixin for DOM Scan commands.
  testql/interpreter/dom_scan_models.py:
    e: FocusableElement,DomScanResult,ButtonAuditResult,ButtonAuditReport
    FocusableElement:
    DomScanResult:
    ButtonAuditResult:
    ButtonAuditReport:
  testql/interpreter/dom_scanner.py:
    e: _aom_node_to_element,_flatten_aom,DomScanner
    DomScanner: __init__(1),scan_focusable(1),scan_aria(1),scan_interactive(1),scan_taborder(1),audit_buttons(2),_should_skip_button(2),_audit_single_button(1),_setup_mutation_observer(0),_classify_button_result(5),_handle_button_click_error(2),_remove_event_listeners(3),_update_report_counts(2),_restore_page_if_needed(1),assert_taborder(2),assert_aria(2),assert_focusable(1),_get_focusable_elements(0),_simulate_tab_order(0),_implicit_role(1),_build_selector(2),_check_duplicate_labels(1),_check_aria_errors(1),_check_tabindex_warnings(1)
    _aom_node_to_element(node;index)
    _flatten_aom(node;result;depth)
  testql/interpreter/interpreter.py:
    e: OqlInterpreter
    OqlInterpreter: __init__(7),parse(2),_is_testtoon(2),execute(1),_dispatch(3),_cmd_set(2),_cmd_get(2)  # OQL interpreter — runs .testql.toon.yaml / .oql / .tql scrip
  testql/interpreter/testtoon_models.py:
    e: ToonSection,ToonScript
    ToonSection: validate(0)  # Represents a section in TestTOON format.
    ToonScript:  # Represents a parsed TestTOON script.
  testql/interpreter/testtoon_parser.py:
    e: _strip_quoted_regions,_detect_separator,_split_quoted,_parse_inline_array,_parse_inline_dict,_parse_value,_make_section,_make_mapping_section,_make_data_row,_make_mapping_row,parse_testtoon,_process_line,_is_meta_line,_process_meta_line,_is_comment,_try_parse_section_header,_should_end_section,_is_bare_command,_add_row_to_section,_add_bare_commands_section,_find_commands_insert_position
    _strip_quoted_regions(line)
    _detect_separator(line)
    _split_quoted(line;sep;maxsplit)
    _parse_inline_array(v)
    _parse_inline_dict(v)
    _parse_value(v)
    _make_section(m)
    _make_mapping_section(m)
    _make_data_row(raw;section)
    _make_mapping_row(raw)
    parse_testtoon(text;filename)
    _process_line(raw;current;script;bare_commands)
    _is_meta_line(line)
    _process_meta_line(line;script)
    _is_comment(line)
    _try_parse_section_header(line)
    _should_end_section(raw;current)
    _is_bare_command(raw;current)
    _add_row_to_section(raw;current)
    _add_bare_commands_section(script;bare_commands)
    _find_commands_insert_position(sections)
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
    e: Step,ApiStep,GuiStep,EncoderStep,ShellStep,UnitStep,NlStep,SqlStep,ProtoStep,GraphqlStep,ConversationTurnStep,Nlp2DslStep,ArtifactAssertStep,ValidateStep
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
    ConversationTurnStep: __post_init__(0),to_dict(0)  # Single turn in a multi-step dialog scenario.
    Nlp2DslStep: __post_init__(0),to_dict(0)  # Call into nlp2dsl (HTTP or SDK) as part of a conversation te
    ArtifactAssertStep: __post_init__(0),to_dict(0)  # Verify a service side-effect rather than an HTTP response bo
    ValidateStep: __post_init__(0),to_dict(0)  # NL/text validation step with type, target, and criteria.
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
    IRRunner: __init__(0),_apply_plan_config(1),run(2)  # Execute a `TestPlan` step-by-step against an `ExecutionConte
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
  testql/ir_runner/executors/assert_json.py:
    e: _last_payload,execute
    _last_payload(ctx)
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
  testql/mcp/__init__.py:
  testql/mcp/server.py:
    e: _require_fastmcp,_normalize_run_payload,create_server,run_server,TestQLMCPServer
    TestQLMCPServer: __post_init__(0),_register_tools(0),run(0)  # Thin wrapper exposing selected TestQL actions as FastMCP too
    _require_fastmcp()
    _normalize_run_payload(results)
    create_server(name)
    run_server()
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
    e: inspect_source,analyze_topology,_check_confidence,_check_nodes,_check_edges,_check_interfaces,_check_evidence,_crawl_checks,_check_link_statuses,_check_asset_statuses,_head_check_urls,_sitemap_checks,_browser_checks,_check_browser_render,_check_browser_console,_check_browser_network,_sitemap_node,_check_sitemap_crawl,_check_sitemap_broken,_check_sitemap_duplicates,_web_checks,_page_node,_check_web_status,_check_web_title,_check_web_links,_check_web_assets,_check_web_forms,_status_code,_looks_like_spa,_findings_from_checks,_actions_from_findings,_status_from_checks,_likely_cause,_action_type,_action_summary,_topology_id,_run_id,_safe
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
    _looks_like_spa(metadata)
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
    e: write_inspection_artifacts,_write_group,_render_summary_md,_metadata
    write_inspection_artifacts(topology;envelope;plan;out_dir)
    _write_group(target;prefix;contents)
    _render_summary_md(topology;envelope;plan;written)
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
  tests/conftest.py:
    e: project_root,testql_pkg_dir,project_root_manifest,testql_pkg_manifest,pytest_configure,pytest_collection_modifyitems
    project_root()
    testql_pkg_dir()
    project_root_manifest()
    testql_pkg_manifest()
    pytest_configure(config)
    pytest_collection_modifyitems(config;items)
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
  tests/test_cli_no_block.py:
    e: TestNoInputCall,TestCheckAndUpgradeNeverBlocks,TestMainNeverBlocks
    TestNoInputCall: test_no_input_in_source(0),test_no_subprocess_in_check_and_upgrade(0)  # Static guarantee: input() must not appear in cli.py.
    TestCheckAndUpgradeNeverBlocks: test_runs_when_up_to_date(0),test_runs_when_outdated(1),test_runs_when_pypi_unreachable(0),test_runs_when_version_unavailable(0),test_is_tty_agnostic(0)  # check_and_upgrade must return quickly regardless of TTY or v
    TestMainNeverBlocks: test_main_via_runner(0),test_main_does_not_call_input(0)  # main() entry point must not block in any environment.
  tests/test_conversation_live_llm.py:
    e: test_live_llm_reply_for_real_api,test_conversation_runner_with_live_llm_smoke,TestLLMProviderResolution,TestLiveLLMParsing
    TestLLMProviderResolution: test_defaults_to_mock(1),test_live_flag_selects_live_provider(1),test_live_without_key_raises(1)
    TestLiveLLMParsing: test_parse_json_object_strips_fence(0)
    test_live_llm_reply_for_real_api()
    test_conversation_runner_with_live_llm_smoke()
  tests/test_conversation_nlp2dsl.py:
    e: test_runner_with_fake_client,TestAssertJsonSection,TestConversationGenerator,TestConversationIRParse,TestConversationRunner,TestArtifactChecker,FakeClient
    TestAssertJsonSection: test_assert_json_attached_to_step(0),test_assert_json_executor_uses_last_response(0)
    TestConversationGenerator: test_from_trace_builds_plan(0)
    TestConversationIRParse: test_parse_conversation_sections(0),test_nlp2dsl_adapter_detects_conversation(0),test_conversation_source_loads(0)
    TestConversationRunner: test_dry_run_skips_http(0)
    TestArtifactChecker: test_file_hash(1)
    FakeClient: chatstart(1),chatmessage(1)
    test_runner_with_fake_client()
  tests/test_converter.py:
    e: TestRow,TestSection,TestConvertOqlToTesttoon,TestConvertFile,TestConvertDirectory
    TestRow: test_row_creation(0),test_row_empty(0),test_row_multiple_fields(0)
    TestSection: test_section_creation(0),test_section_with_rows(0),test_section_with_comment(0)
    TestConvertOqlToTesttoon: test_navigate_command(0),test_scenario_name_from_filename(0),test_header_present(0),test_click_converts_to_flow(0),test_assert_text_converts(0),test_empty_source(0),test_get_request(0),test_default_filename(0),test_returns_string(0),test_multiline_script(0)
    TestConvertFile: test_creates_output_file(1),test_output_filename_pattern(1),test_oql_extension(1),test_output_is_in_same_dir(1),test_output_content_has_scenario(1),test_returns_path(1)
    TestConvertDirectory: test_empty_directory(1),test_converts_tql_files(1),test_converts_oql_files(1),test_converts_multiple_files(1),test_returns_list_of_paths(1),test_recursive_subdirectory(1),test_ignores_non_tql_files(1)
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
    e: _write,TestEndpointInfoModel,TestFastAPIDetector,TestFlaskDetector,TestUnifiedDetector,TestOpenAPIDetector,TestConfigDetector,TestExpressDetector
    TestEndpointInfoModel: test_to_testql_api_call(1),test_defaults(1)
    TestFastAPIDetector: test_detects_route_decorator(1),test_empty_project(1),test_non_route_decorators_ignored(1)
    TestFlaskDetector: test_detects_route(1),test_empty_project(1)
    TestUnifiedDetector: test_returns_list(1),test_detects_fastapi(1),test_detectors_used_populated(1)
    TestOpenAPIDetector: test_empty_project(1),test_detects_yaml_spec(1),test_detects_json_spec(1),test_framework_is_openapi(1),test_base_path_from_servers(1),test_base_path_swagger2(1),test_x_extension_methods_skipped(1),test_invalid_yaml_skipped(1),test_spec_without_paths_skipped(1)
    TestConfigDetector: test_empty_project(1),test_detects_docker_compose_services(1),test_unified_does_not_dedup_docker_services(1)
    TestExpressDetector: test_empty_project(1),test_detects_app_get(1),test_detects_router_post(1),test_framework_is_express(1),test_typescript_file_detected(1)
    _write(tmp_path;name;content)
  tests/test_discovery.py:
    e: TestDiscoveryCore,TestDiscoveryCli
    TestDiscoveryCore: test_empty_directory_is_inferred(1),test_python_package_probe_detects_fastapi(0),test_node_package_probe_detects_node_and_frontend_markers(0),test_openapi_probe_detects_openapi3_interface(0),test_dockerfile_probe_detects_container_metadata(0),test_compose_probe_detects_services(0),test_registry_returns_raw_probe_results(0),test_self_discovery_detects_current_project_root(1),test_self_discovery_detects_testql_package_directory(1)
    TestDiscoveryCli: test_discover_summary_output(0),test_discover_json_output(0),test_discover_manifest_output(0),test_discover_missing_path_exits_nonzero(0)
  tests/test_dispatcher.py:
    e: TestCommandDispatcher,TestDispatcherIntegration
    TestCommandDispatcher: interpreter(0),dispatcher(1),test_auto_discovery(1),test_has_command(1),test_dispatch_known_command(2),test_dispatch_unknown_command(2),test_dispatch_with_suggestion(2),test_register_custom_command(2),test_case_insensitive_dispatch(1)  # Test CommandDispatcher functionality.
    TestDispatcherIntegration: interpreter(0),test_interpreter_uses_dispatcher(1),test_dispatch_through_interpreter(1),test_all_mixin_commands_discovered(1)  # Test CommandDispatcher integration with OqlInterpreter.
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
  tests/test_generate_from_page_cli.py:
    e: _write_elements,TestGenerateFromPageCli,TestHealScenarioCli
    TestGenerateFromPageCli: test_writes_scenario_with_expected_steps(1),test_print_only_does_not_write_file(1),test_max_steps_caps_output(1)
    TestHealScenarioCli: _scenario_with_broken_selectors(0),test_heals_class_selector_via_fuzzy_match(1),test_write_in_place(1),test_section_header_brackets_not_treated_as_selectors(1),test_data_testid_used_for_fuzzy_match(1),test_unhealable_selector_reported(1)
    _write_elements(tmp_path)
  tests/test_generate_ir_cli.py:
    e: TestGenerateIRCLI
    TestGenerateIRCLI: test_command_exists(0),test_round_trip_to_stdout(1),test_writes_to_file(1),test_bad_from_arg_errors(0),test_legacy_generate_still_works(0),test_generate_ir_makefile_alias(1),test_generate_ir_taskfile_alias(1),test_generate_ir_docker_compose_alias(1),test_generate_ir_buf_alias(1)
  tests/test_generators.py:
    e: TestBaseAnalyzer,TestProjectAnalyzerDetectType,TestTestPattern,TestOqlScenarioConversion,TestGeneratorConfig
    TestBaseAnalyzer: test_init(1),test_get_exclude_dirs(1),test_should_exclude_path_venv(1),test_should_exclude_path_src(1)
    TestProjectAnalyzerDetectType: test_detect_python_api_fastapi(1),test_detect_python_api_flask(1),test_detect_python_cli(1),test_detect_python_lib(1),test_detect_hardware(1),test_detect_mixed_default(1),test_detect_web_frontend(1),test_detect_web_frontend_missing_e2e_markers(1)
    TestTestPattern: test_defaults(0),test_metadata(0)
    TestOqlScenarioConversion: test_oql_scenario_conversion(1),test_convert_oql_command_wait(0),test_convert_oql_command_encoder(0),test_convert_oql_command_unknown(0)
    TestGeneratorConfig: test_build_api_test_config(0),test_build_api_test_header(0)
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
    e: TestParseOql,TestParseTestTOON,TestTestTOONExpansion,TestOqlInterpreter
    TestParseOql: test_empty(0),test_comments_ignored(0),test_basic_commands(0)
    TestParseTestTOON: test_empty(0),test_meta(0),test_api_section(0),test_encoder_section(0),test_validation_pass(0),test_validation_fail(0)
    TestTestTOONExpansion: test_api_expansion(0),test_encoder_expansion(0),test_config_expansion(0),test_config_mapping_expansion(0),test_config_mapping_applies_to_encoder_flow(0),test_navigate_expansion(0)
    TestOqlInterpreter: test_dry_run_api(0),test_set_get(0),test_testtoon_dry_run(0),test_assert_json_nested_virtual_encoder_status_path(0),test_assert_json_nested_virtual_encoder_status_bool(0)
  tests/test_ir.py:
    e: TestScenarioMetadata,TestAssertion,TestFixture,TestStepVariants,TestTestPlan
    TestScenarioMetadata: test_defaults(0),test_to_dict_minimal(0),test_to_dict_full(0)
    TestAssertion: test_defaults(0),test_to_dict_minimal(0),test_to_dict_full(0)
    TestFixture: test_defaults(0),test_to_dict(0)
    TestStepVariants: test_base_step_kind(0),test_api_step(0),test_gui_step(0),test_encoder_step(0),test_shell_step(0),test_unit_step(0),test_nl_step(0),test_sql_step(0),test_proto_step(0),test_graphql_step(0),test_conversation_turn_step(0),test_nlp2dsl_step(0),test_artifact_assert_step(0),test_step_with_asserts_and_wait(0)
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
  tests/test_mcp_autoloop.py:
    e: TestCLIAvailability,TestMCPModule,TestDiscoveryPipeline,TestTopologyPipeline,TestScenarioRoundTrip,TestAutoloopSchema,TestMCPConfig
    TestCLIAvailability: test_cli_help_exits_cleanly(0),test_mcp_subcommand_registered(0),test_discover_subcommand_exists(0),test_topology_subcommand_exists(0),test_run_subcommand_exists(0)  # CLI must work without hanging in non-TTY context.
    TestMCPModule: test_mcp_server_module_importable(0),test_mcp_init_importable(0),test_mcp_server_raises_on_missing_package(0)  # MCP server module must import without requiring mcp package 
    TestDiscoveryPipeline: test_self_discovery_returns_manifest(1),test_self_discovery_json_serializable(1),test_discover_cli_json_output(0)  # Discovery must work on this project itself (self-discovery).
    TestTopologyPipeline: test_topology_cli_json_output(0)  # Topology generation must produce valid structure.
    TestScenarioRoundTrip: test_scenario_parses(1),test_scenario_round_trips(1),test_api_smoke_has_api_steps(0)  # Scenarios in testql-scenarios/ must parse cleanly.
    TestAutoloopSchema: test_autoloop_state_valid_json(0),test_llm_decision_schema_exists(0),test_llm_decision_schema_valid_decision_values(0)  # Autoloop state and schema must be valid.
    TestMCPConfig: test_mcp_config_structure(0),test_mcp_server_module_path(0)  # MCP config structure must be correct for IDE integration.
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
  tests/test_modbus_commands.py:
    e: TestModbusToonExpansion,TestModbusDryRun,TestModbusApiExpansion
    TestModbusToonExpansion: test_modbus_probe_section(0)
    TestModbusDryRun: test_modbus_probe_dry_run(0),test_modbus_skip_if_no_port(1)
    TestModbusApiExpansion: test_modbus_api_plan_expansion(0)
  tests/test_navigate_json_path.py:
    e: TestNavigateJsonPath,TestAssertJsonAndCaptureWithIndexedPath,TestToonBareImperativeIndexedPath
    TestNavigateJsonPath: test_indexed_first_element_field(0),test_indexed_second_element_field(0),test_indexed_nested_field(0),test_top_level_scalar(0),test_missing_key_returns_none(0),test_out_of_range_index_returns_none(0),test_length_of_list(0)
    TestAssertJsonAndCaptureWithIndexedPath: _make_interp(0),test_assert_json_indexed_path_passes(0),test_assert_json_indexed_path_fails_on_mismatch(0),test_capture_indexed_path_stores_value(0),test_assert_json_total_count_ge(0),test_assert_json_results_length_ge(0)  # Behavioural regression: ASSERT_JSON / CAPTURE must support r
    TestToonBareImperativeIndexedPath: _make_interp(0),test_toon_parser_parses_bare_commands(0),test_toon_assert_json_indexed_passes(0),test_toon_capture_stores_value(0)  # End-to-end: TestTOON parser -> COMMANDS -> OqlScript -> ASSE
  tests/test_network_discovery.py:
    e: test_discover_url_requires_scan_network_for_match,test_topology_url_builds_page_schema_nodes,test_inspect_url_nlp_passes_with_mocked_network,test_inspect_cli_url_json_with_scan_network,test_inspect_url_reports_http_failure,test_inspect_url_builds_sitemap_with_mocked_network,test_inspect_spa_without_anchors_skips_web_links,FakeClient,FakeErrorClient,FakeSpaClient
    FakeClient: __init__(0),__enter__(0),__exit__(3),get(1),head(1)
    FakeErrorClient:
    FakeSpaClient:
    test_discover_url_requires_scan_network_for_match(monkeypatch)
    test_topology_url_builds_page_schema_nodes(monkeypatch)
    test_inspect_url_nlp_passes_with_mocked_network(monkeypatch)
    test_inspect_cli_url_json_with_scan_network(monkeypatch)
    test_inspect_url_reports_http_failure(monkeypatch)
    test_inspect_url_builds_sitemap_with_mocked_network(monkeypatch)
    test_inspect_spa_without_anchors_skips_web_links(monkeypatch)
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
  tests/test_page_analyzer.py:
    e: TestPickSelector,TestDefaultInputValue,TestClassification,TestSnapshotToPlan,TestFindReplacement
    TestPickSelector: test_data_testid_wins(0),test_data_test_fallback(0),test_id_when_stable(0),test_id_skipped_when_unstable(0),test_id_skipped_for_uuid_like(0),test_form_field_name_attr(0),test_role_with_aria_label(0),test_input_type_when_distinctive(0),test_input_type_text_not_distinctive(0),test_skips_generic_classes(0),test_returns_none_when_only_generic(0),test_returns_none_when_nothing_stable(0),test_quote_escaping(0)
    TestDefaultInputValue: test_input_type_takes_precedence(2),test_email_inferred_from_name(0),test_password_inferred_from_placeholder(0),test_search_inferred_from_aria_label(0),test_id_field_uses_id_default(0),test_fallback(0)
    TestClassification: test_textarea_is_typed(0),test_input_email_is_typed(0),test_input_submit_is_not_typed(0),test_button_is_clickable(0),test_link_is_clickable(0),test_role_button_clickable(0),test_disabled_not_clickable(0),test_input_submit_clickable(0)
    TestSnapshotToPlan: _snap(1),test_emits_navigate_first(0),test_emits_input_with_default_value(0),test_emits_click_for_button(0),test_skips_invisible_and_unstable(0),test_dedup_same_selector(0),test_max_steps_respected(0),test_metadata_records_source_url(0)
    TestFindReplacement: test_replaces_broken_class_with_id_match(0),test_exact_accessible_name_match_wins(0),test_returns_none_when_no_match(0),test_token_match_picks_best(0)
  tests/test_pipeline.py:
    e: TestRegistries,TestResolution,TestMatrix,TestLLMEnrichmentOptIn,TestWrite
    TestRegistries: test_sorted_sources(0),test_sorted_targets(0)
    TestResolution: test_unknown_source_raises(0),test_unknown_target_raises(0)
    TestMatrix: test_run_returns_result(2),test_output_non_empty(2),test_plan_has_metadata(2)
    TestLLMEnrichmentOptIn: test_default_runs_without_llm(0),test_no_op_enricher_is_pure(0),test_custom_enricher_invoked(0),test_custom_optimizer_attached_to_metadata(0)
    TestWrite: test_writes_to_file(1),test_writes_to_directory_with_derived_name(1)
  tests/test_plugin_registry.py:
    e: _install_module,_StubAdapter,TestRegisterPlugin,TestLoadPlugins
    _StubAdapter: detect(1),parse(1),render(1)
    TestRegisterPlugin: test_register_adapter_instance(0),test_register_iterable(0),test_register_module_with_register_hook(0),test_register_module_with_adapters_attribute(0),test_register_unsupported_raises(0)
    TestLoadPlugins: test_env_var_loading(1),test_ensure_plugins_loaded_runs_once(1)
    _install_module(name;body)
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
  tests/test_run_cmd.py:
    e: _install_fake_interpreter,_mk_scenario,_FakeResult,_FakeInterpreter,TestRunCommandInputs
    _FakeResult: __post_init__(0)
    _FakeInterpreter: __init__(0),run(2)
    TestRunCommandInputs: test_run_accepts_directory(2),test_run_accepts_glob_pattern(2),test_run_errors_for_missing_input(1),test_run_accepts_shell_expanded_multiple_files(2)
    _install_fake_interpreter(monkeypatch)
    _mk_scenario(path)
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
  tests/test_scenario_yaml_adapter.py:
    e: TestDetect,TestParseApi,TestParseGui,TestParseMixed,TestRender,TestRegistration,TestParseErrors
    TestDetect: test_detect_extension(1),test_detect_content(0),test_detect_negative(0)
    TestParseApi: test_metadata(0),test_targets_become_config(0),test_steps_typed(0),test_capture(0)
    TestParseGui: test_navigate_and_form(0)
    TestParseMixed: test_step_kinds(0),test_using_overrides_propagate(0),test_shell_expect_exit_code(0),test_encoder_target(0),test_unit_target(0)
    TestRender: test_round_trip_metadata_steps(0)
    TestRegistration: test_registered_in_default_registry(0),test_extension_lookup_picks_scenario_yaml(1),test_extension_lookup_keeps_testtoon(1)
    TestParseErrors: test_non_mapping_root(0)
  tests/test_shell_execution.py:
    e: TestShellExecution,TestShellDryRun
    TestShellExecution: interpreter(1),test_shell_echo_command(2),test_shell_with_exit_code(1),test_assert_exit_code_success(1),test_assert_exit_code_failure(1),test_assert_stdout_contains_success(1),test_assert_stdout_contains_failure(1),test_shell_timeout(1),test_shell_no_previous_command_warning(1)  # Test SHELL, EXEC, RUN commands and assertions.
    TestShellDryRun: interpreter(0),test_shell_dry_run(1)  # Test shell commands in dry-run mode.
  tests/test_smoke_decisions.py:
    e: _load,_schema,_check_required,_check_decision,_check_metrics,_check_numerics,_check_next_actions,_validate,TestKimiDecision,TestSWEDecision,TestModelComparison
    TestKimiDecision: test_file_exists(0),test_valid_json(0),test_schema_valid(0),test_decision_value(0),test_confidence_high(0),test_has_topology_focus(0)
    TestSWEDecision: test_file_exists(0),test_valid_json(0),test_schema_valid(0),test_decision_value(0),test_conservative_risk(0),test_has_multiple_next_actions(0)
    TestModelComparison: test_both_same_iteration(0),test_both_valid_decisions(0),test_kimi_higher_confidence_than_swe(0),test_swe_higher_risk_than_kimi(0),test_summary(0)
    _load(name)
    _schema()
    _check_required(data;schema)
    _check_decision(data;schema)
    _check_metrics(data;schema)
    _check_numerics(data)
    _check_next_actions(data)
    _validate(data;schema)
  tests/test_sources.py:
    e: TestRegistry,TestOpenAPISource,TestSqlSource,TestProtoSource,TestGraphQLSource,TestNLSource,TestUISource,TestConfigSourceHelpers,TestConfigSourceIntegration
    TestRegistry: test_builtin_sources(0),test_get_source(1),test_get_unknown(0),test_get_config_aliases(1)
    TestOpenAPISource: test_paths_become_api_steps(0),test_status_picks_lowest_2xx(0),test_default_status_when_unspecified(0),test_base_url_from_servers(0),test_metadata_from_info(0),test_load_from_path(1),test_load_from_dict(0)
    TestSqlSource: test_two_tables_yield_four_steps(0),test_count_step_has_assert(0),test_schema_fixture_emitted(0),test_dialect_propagates(0),test_load_from_path(1)
    TestProtoSource: test_one_step_per_message(0),test_sample_fields_blob(0),test_round_trip_assertion(0),test_schema_fixture(0)
    TestGraphQLSource: test_one_step_per_object_type(0),test_endpoint_set_in_config(0),test_query_body_uses_field_list(0)
    TestNLSource: test_delegates_to_adapter(0)
    TestUISource: test_navigate_first(0),test_inputs_extracted(0),test_buttons_extracted(0)
    TestConfigSourceHelpers: test_load_includes_single_file(1),test_load_includes_glob_pattern(1),test_load_includes_nonexistent_file(1),test_extract_phony_targets(0),test_extract_phony_targets_multiline(0),test_extract_phony_targets_none(0),test_extract_target_commands_simple(0),test_extract_target_commands_with_prefixes(0),test_extract_target_commands_stops_at_next_target(0),test_extract_target_commands_ignores_comments(0),test_extract_target_commands_max_lines(0)
    TestConfigSourceIntegration: test_parse_makefile_simple(1),test_parse_makefile_with_includes(1),test_parse_makefile_phony_flag(1),test_parse_makefile_comments(1),test_parse_makefile_excludes_special_targets(1)
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
    e: TestDetect,TestParse,TestRender,TestAdapterRegistration,TestFlowExpansion,TestShellExpansion,TestBackwardCompatibility
    TestDetect: test_detect_by_extension(1),test_detect_by_metadata_header(0),test_detect_negative(0),test_detect_section_header(0)
    TestParse: test_parse_string(0),test_parse_file(1),test_api_steps(0),test_api_step_has_status_assert(0),test_navigate_step(0),test_encoder_step(0),test_assert_section(0),test_unknown_section_falls_through_to_generic(0),test_indented_row_starting_with_hash_is_not_comment(0)
    TestRender: test_render_round_trip_basic(0),test_render_includes_metadata(0),test_render_includes_config(0),test_render_empty_plan(0),test_round_trip_preserves_flow_steps(0),test_round_trip_preserves_wait_steps(0),test_round_trip_preserves_include_steps(0)
    TestAdapterRegistration: test_adapter_registered_in_default_registry(0),test_extensions_match(0)
    TestFlowExpansion: _expand(1),test_flow_value_column_quoted_for_input(0),test_flow_text_column_alias(0),test_flow_meta_dash_emits_no_extra_arg(0),test_flow_value_dash_does_not_pollute_click(0),test_flow_value_null_treated_as_empty(0),test_flow_meta_dict_legacy_passthrough(0),test_flow_two_column_still_works(0)  # FLOW section third-column handling (regression for GUI_INPUT
    TestShellExpansion: _expand(1),test_shell_section_quotes_compound_command(0),test_shell_expected_exit_column_alias(0),test_shell_quoted_row_in_testtoon(0),test_shell_dry_run_executes_full_command_not_first_token(0)  # SHELL section must quote compound commands (&&, |) for OQL e
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
  tests/test_validation.py:
    e: interp,_seed_shell,TestValidateExpansion,TestValidateContains,TestValidateRegex,TestValidateTemplate,TestValidateSemantic
    TestValidateExpansion: test_validate_row_emits_validate_oql_line(0),test_validate_quotes_regex_metachars(0),test_validate_pipe_inside_quoted_criteria_is_literal(0),test_validate_comma_inside_quoted_criteria_is_literal(0),test_validate_skips_rows_without_type_or_target(0)
    TestValidateContains: test_contains_pass(1),test_contains_fail(1),test_not_contains_pass(1),test_not_contains_fail(1)
    TestValidateRegex: test_regex_pass(1),test_regex_fail(1)
    TestValidateTemplate: test_template_pass(2),test_template_missing_file(2)
    TestValidateSemantic: test_semantic_emits_event_and_passes(1)
    interp()
    _seed_shell(interp;stdout;stderr;rc)
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('testql', '1.2.54', 'python').

% ── Project Files ────────────────────────────────────────
project_file('TODO/testtoon_parser.py', 142, 'python').
project_file('app.doql.less', 237, 'less').
project_file('examples/api-testing/mock_server.py', 51, 'python').
project_file('examples/api-testing/run.sh', 28, 'shell').
project_file('examples/artifact-bundle/generate_bundle.py', 37, 'python').
project_file('examples/artifact-bundle/run.sh', 19, 'shell').
project_file('examples/browser-inspection/run.sh', 65, 'shell').
project_file('examples/discovery/discover-local.sh', 15, 'shell').
project_file('examples/discovery/inspect-web.sh', 21, 'shell').
project_file('examples/discovery/topology.sh', 19, 'shell').
project_file('examples/encoder-testing/run.sh', 22, 'shell').
project_file('examples/flow-control/run.sh', 18, 'shell').
project_file('examples/gui-testing/run.sh', 23, 'shell').
project_file('examples/project-echo/app.doql.less', 37, 'less').
project_file('examples/project-echo/run.sh', 38, 'shell').
project_file('examples/run-all.sh', 72, 'shell').
project_file('examples/shell-testing/run.sh', 17, 'shell').
project_file('examples/testtoon-basics/run.sh', 23, 'shell').
project_file('examples/topology/run.sh', 23, 'shell').
project_file('examples/unit-testing/run.sh', 24, 'shell').
project_file('examples/web-inspection/c2004-localhost/run-matrix.sh', 102, 'shell').
project_file('examples/web-inspection/c2004-localhost/run.sh', 73, 'shell').
project_file('examples/web-inspection/run.sh', 43, 'shell').
project_file('examples/web-inspection-dot-testql/run.sh', 14, 'shell').
project_file('project.sh', 50, 'shell').
project_file('scripts/install_testql_autoloop.sh', 157, 'shell').
project_file('scripts/setup_mcp_windsurf.sh', 92, 'shell').
project_file('scripts/smoke_manifest_flow.sh', 71, 'shell').
project_file('test_autoloop_api.py', 453, 'python').
project_file('test_autoloop_mcp.py', 519, 'python').
project_file('test_manifest_and_generators.py', 526, 'python').
project_file('testql/__init__.py', 10, 'python').
project_file('testql/__main__.py', 7, 'python').
project_file('testql/_base_fallback.py', 233, 'python').
project_file('testql/adapters/__init__.py', 54, 'python').
project_file('testql/adapters/base.py', 98, 'python').
project_file('testql/adapters/graphql/__init__.py', 26, 'python').
project_file('testql/adapters/graphql/graphql_adapter.py', 274, 'python').
project_file('testql/adapters/graphql/query_executor.py', 77, 'python').
project_file('testql/adapters/graphql/schema_introspection.py', 136, 'python').
project_file('testql/adapters/graphql/subscription_runner.py', 41, 'python').
project_file('testql/adapters/nl/__init__.py', 67, 'python').
project_file('testql/adapters/nl/entity_extractor.py', 116, 'python').
project_file('testql/adapters/nl/grammar.py', 108, 'python').
project_file('testql/adapters/nl/intent_recognizer.py', 100, 'python').
project_file('testql/adapters/nl/lexicon/__init__.py', 39, 'python').
project_file('testql/adapters/nl/llm_fallback.py', 50, 'python').
project_file('testql/adapters/nl/nl_adapter.py', 354, 'python').
project_file('testql/adapters/nlp2dsl/__init__.py', 22, 'python').
project_file('testql/adapters/nlp2dsl/client.py', 63, 'python').
project_file('testql/adapters/nlp2dsl/live_llm.py', 91, 'python').
project_file('testql/adapters/nlp2dsl/llm_provider.py', 43, 'python').
project_file('testql/adapters/nlp2dsl/mock_llm.py', 47, 'python').
project_file('testql/adapters/nlp2dsl/nlp2dsl_adapter.py', 82, 'python').
project_file('testql/adapters/proto/__init__.py', 54, 'python').
project_file('testql/adapters/proto/compatibility.py', 144, 'python').
project_file('testql/adapters/proto/descriptor_loader.py', 163, 'python').
project_file('testql/adapters/proto/message_validator.py', 188, 'python').
project_file('testql/adapters/proto/proto_adapter.py', 243, 'python').
project_file('testql/adapters/registry.py', 151, 'python').
project_file('testql/adapters/scenario_yaml.py', 507, 'python').
project_file('testql/adapters/sql/__init__.py', 51, 'python').
project_file('testql/adapters/sql/ddl_parser.py', 229, 'python').
project_file('testql/adapters/sql/dialect_resolver.py', 89, 'python').
project_file('testql/adapters/sql/fixtures.py', 106, 'python').
project_file('testql/adapters/sql/query_parser.py', 96, 'python').
project_file('testql/adapters/sql/sql_adapter.py', 334, 'python').
project_file('testql/adapters/testtoon_adapter.py', 743, 'python').
project_file('testql/artifacts/__init__.py', 18, 'python').
project_file('testql/artifacts/base.py', 25, 'python').
project_file('testql/artifacts/email_checker.py', 45, 'python').
project_file('testql/artifacts/file_checker.py', 43, 'python').
project_file('testql/artifacts/registry.py', 36, 'python').
project_file('testql/autoloop_runner.py', 1, 'python').
project_file('testql/base.py', 38, 'python').
project_file('testql/cli.py', 107, 'python').
project_file('testql/commands/__init__.py', 36, 'python').
project_file('testql/commands/auto_cmd.py', 203, 'python').
project_file('testql/commands/conversation_cmd.py', 109, 'python').
project_file('testql/commands/discover_cmd.py', 47, 'python').
project_file('testql/commands/echo/__init__.py', 23, 'python').
project_file('testql/commands/echo/cli.py', 40, 'python').
project_file('testql/commands/echo/context.py', 55, 'python').
project_file('testql/commands/echo/formatters/__init__.py', 10, 'python').
project_file('testql/commands/echo/formatters/text.py', 96, 'python').
project_file('testql/commands/echo/parsers/__init__.py', 11, 'python').
project_file('testql/commands/echo/parsers/doql.py', 116, 'python').
project_file('testql/commands/echo/parsers/toon.py', 77, 'python').
project_file('testql/commands/echo.py', 25, 'python').
project_file('testql/commands/echo_helpers.py', 69, 'python').
project_file('testql/commands/encoder_routes.py', 478, 'python').
project_file('testql/commands/endpoints_cmd.py', 137, 'python').
project_file('testql/commands/generate_cmd.py', 172, 'python').
project_file('testql/commands/generate_from_page_cmd.py', 100, 'python').
project_file('testql/commands/generate_ir_cmd.py', 50, 'python').
project_file('testql/commands/generate_topology_cmd.py', 59, 'python').
project_file('testql/commands/heal_scenario_cmd.py', 308, 'python').
project_file('testql/commands/inspect_cmd.py', 35, 'python').
project_file('testql/commands/misc_cmds.py', 293, 'python').
project_file('testql/commands/run_cmd.py', 161, 'python').
project_file('testql/commands/run_ir_cmd.py', 66, 'python').
project_file('testql/commands/self_test_cmd.py', 46, 'python').
project_file('testql/commands/suite/__init__.py', 9, 'python').
project_file('testql/commands/suite/cli.py', 101, 'python').
project_file('testql/commands/suite/collection.py', 123, 'python').
project_file('testql/commands/suite/execution.py', 74, 'python').
project_file('testql/commands/suite/listing.py', 115, 'python').
project_file('testql/commands/suite/reports.py', 90, 'python').
project_file('testql/commands/suite_cmd.py', 13, 'python').
project_file('testql/commands/templates/__init__.py', 19, 'python').
project_file('testql/commands/templates/content.py', 167, 'python').
project_file('testql/commands/templates/templates.py', 60, 'python').
project_file('testql/commands/topology_cmd.py', 24, 'python').
project_file('testql/commands/watchdog_cmd.py', 283, 'python').
project_file('testql/conversation/__init__.py', 6, 'python').
project_file('testql/conversation/runner.py', 287, 'python').
project_file('testql/detectors/__init__.py', 54, 'python').
project_file('testql/detectors/base.py', 35, 'python').
project_file('testql/detectors/config_detector.py', 219, 'python').
project_file('testql/detectors/django_detector.py', 52, 'python').
project_file('testql/detectors/express_detector.py', 60, 'python').
project_file('testql/detectors/fastapi_detector.py', 154, 'python').
project_file('testql/detectors/flask_detector.py', 122, 'python').
project_file('testql/detectors/graphql_detector.py', 88, 'python').
project_file('testql/detectors/models.py', 61, 'python').
project_file('testql/detectors/openapi_detector.py', 91, 'python').
project_file('testql/detectors/test_detector.py', 70, 'python').
project_file('testql/detectors/unified.py', 240, 'python').
project_file('testql/detectors/websocket_detector.py', 49, 'python').
project_file('testql/discovery/__init__.py', 15, 'python').
project_file('testql/discovery/manifest.py', 174, 'python').
project_file('testql/discovery/probes/__init__.py', 6, 'python').
project_file('testql/discovery/probes/base.py', 71, 'python').
project_file('testql/discovery/probes/browser/__init__.py', 8, 'python').
project_file('testql/discovery/probes/browser/playwright_page.py', 148, 'python').
project_file('testql/discovery/probes/filesystem/__init__.py', 16, 'python').
project_file('testql/discovery/probes/filesystem/api_openapi.py', 73, 'python').
project_file('testql/discovery/probes/filesystem/container_compose.py', 45, 'python').
project_file('testql/discovery/probes/filesystem/container_dockerfile.py', 42, 'python').
project_file('testql/discovery/probes/filesystem/package_node.py', 55, 'python').
project_file('testql/discovery/probes/filesystem/package_python.py', 201, 'python').
project_file('testql/discovery/probes/network/__init__.py', 6, 'python').
project_file('testql/discovery/probes/network/http_endpoint.py', 161, 'python').
project_file('testql/discovery/registry.py', 60, 'python').
project_file('testql/discovery/source.py', 34, 'python').
project_file('testql/doql_parser.py', 173, 'python').
project_file('testql/echo_schemas.py', 154, 'python').
project_file('testql/endpoint_detector.py', 63, 'python').
project_file('testql/generator.py', 62, 'python').
project_file('testql/generators/__init__.py', 53, 'python').
project_file('testql/generators/analyzers.py', 310, 'python').
project_file('testql/generators/api_generator.py', 299, 'python').
project_file('testql/generators/base.py', 60, 'python').
project_file('testql/generators/convenience.py', 52, 'python').
project_file('testql/generators/conversation_generator.py', 70, 'python').
project_file('testql/generators/generators.py', 31, 'python').
project_file('testql/generators/llm/__init__.py', 17, 'python').
project_file('testql/generators/llm/coverage_optimizer.py', 33, 'python').
project_file('testql/generators/llm/edge_case_generator.py', 27, 'python').
project_file('testql/generators/multi.py', 106, 'python').
project_file('testql/generators/page_analyzer.py', 527, 'python').
project_file('testql/generators/pipeline.py', 96, 'python').
project_file('testql/generators/pytest_generator.py', 148, 'python').
project_file('testql/generators/scenario_generator.py', 88, 'python').
project_file('testql/generators/sources/__init__.py', 86, 'python').
project_file('testql/generators/sources/base.py', 33, 'python').
project_file('testql/generators/sources/config_source.py', 306, 'python').
project_file('testql/generators/sources/conversation.py', 36, 'python').
project_file('testql/generators/sources/graphql_source.py', 67, 'python').
project_file('testql/generators/sources/nl_source.py', 28, 'python').
project_file('testql/generators/sources/openapi_source.py', 94, 'python').
project_file('testql/generators/sources/oql_models.py', 31, 'python').
project_file('testql/generators/sources/oql_parser.py', 268, 'python').
project_file('testql/generators/sources/oql_source.py', 307, 'python').
project_file('testql/generators/sources/page_source.py', 173, 'python').
project_file('testql/generators/sources/proto_source.py', 91, 'python').
project_file('testql/generators/sources/pytest_source.py', 390, 'python').
project_file('testql/generators/sources/sql_source.py', 80, 'python').
project_file('testql/generators/sources/ui_source.py', 82, 'python').
project_file('testql/generators/specialized_generator.py', 171, 'python').
project_file('testql/generators/targets/__init__.py', 37, 'python').
project_file('testql/generators/targets/base.py', 22, 'python').
project_file('testql/generators/targets/nl_target.py', 23, 'python').
project_file('testql/generators/targets/pytest_target.py', 65, 'python').
project_file('testql/generators/targets/testtoon_target.py', 24, 'python').
project_file('testql/generators/test_generator.py', 107, 'python').
project_file('testql/integrations/planfile_hook.py', 116, 'python').
project_file('testql/interpreter/__init__.py', 92, 'python').
project_file('testql/interpreter/_api_runner.py', 303, 'python').
project_file('testql/interpreter/_assertions.py', 305, 'python').
project_file('testql/interpreter/_converter.py', 63, 'python').
project_file('testql/interpreter/_dom_scan.py', 41, 'python').
project_file('testql/interpreter/_encoder.py', 101, 'python').
project_file('testql/interpreter/_flow.py', 166, 'python').
project_file('testql/interpreter/_gui.py', 709, 'python').
project_file('testql/interpreter/_hardware.py', 110, 'python').
project_file('testql/interpreter/_modbus.py', 233, 'python').
project_file('testql/interpreter/_parser.py', 34, 'python').
project_file('testql/interpreter/_shell.py', 261, 'python').
project_file('testql/interpreter/_testtoon_parser.py', 565, 'python').
project_file('testql/interpreter/_unit.py', 268, 'python').
project_file('testql/interpreter/_validation.py', 154, 'python').
project_file('testql/interpreter/_websockets.py', 173, 'python').
project_file('testql/interpreter/converter/__init__.py', 20, 'python').
project_file('testql/interpreter/converter/core.py', 59, 'python').
project_file('testql/interpreter/converter/dispatcher.py', 50, 'python').
project_file('testql/interpreter/converter/handlers/__init__.py', 31, 'python').
project_file('testql/interpreter/converter/handlers/api.py', 32, 'python').
project_file('testql/interpreter/converter/handlers/assertions.py', 35, 'python').
project_file('testql/interpreter/converter/handlers/encoder.py', 48, 'python').
project_file('testql/interpreter/converter/handlers/flow.py', 40, 'python').
project_file('testql/interpreter/converter/handlers/include.py', 15, 'python').
project_file('testql/interpreter/converter/handlers/navigate.py', 33, 'python').
project_file('testql/interpreter/converter/handlers/record.py', 25, 'python').
project_file('testql/interpreter/converter/handlers/select.py', 27, 'python').
project_file('testql/interpreter/converter/handlers/unknown.py', 19, 'python').
project_file('testql/interpreter/converter/handlers/wait.py', 23, 'python').
project_file('testql/interpreter/converter/models.py', 21, 'python').
project_file('testql/interpreter/converter/parsers.py', 94, 'python').
project_file('testql/interpreter/converter/renderer.py', 65, 'python').
project_file('testql/interpreter/dispatcher.py', 87, 'python').
project_file('testql/interpreter/dom_scan_formatters.py', 85, 'python').
project_file('testql/interpreter/dom_scan_mixin.py', 319, 'python').
project_file('testql/interpreter/dom_scan_models.py', 54, 'python').
project_file('testql/interpreter/dom_scanner.py', 419, 'python').
project_file('testql/interpreter/interpreter.py', 160, 'python').
project_file('testql/interpreter/testtoon_models.py', 34, 'python').
project_file('testql/interpreter/testtoon_parser.py', 297, 'python').
project_file('testql/interpreter.py', 28, 'python').
project_file('testql/ir/__init__.py', 55, 'python').
project_file('testql/ir/assertions.py', 34, 'python').
project_file('testql/ir/captures.py', 38, 'python').
project_file('testql/ir/fixtures.py', 34, 'python').
project_file('testql/ir/metadata.py', 32, 'python').
project_file('testql/ir/plan.py', 43, 'python').
project_file('testql/ir/steps.py', 319, 'python').
project_file('testql/ir_runner/__init__.py', 35, 'python').
project_file('testql/ir_runner/assertion_eval.py', 125, 'python').
project_file('testql/ir_runner/context.py', 43, 'python').
project_file('testql/ir_runner/engine.py', 137, 'python').
project_file('testql/ir_runner/executors/__init__.py', 54, 'python').
project_file('testql/ir_runner/executors/api.py', 68, 'python').
project_file('testql/ir_runner/executors/assert_json.py', 31, 'python').
project_file('testql/ir_runner/executors/base.py', 69, 'python').
project_file('testql/ir_runner/executors/encoder.py', 78, 'python').
project_file('testql/ir_runner/executors/graphql.py', 60, 'python').
project_file('testql/ir_runner/executors/gui.py', 31, 'python').
project_file('testql/ir_runner/executors/nl.py', 25, 'python').
project_file('testql/ir_runner/executors/proto.py', 88, 'python').
project_file('testql/ir_runner/executors/shell.py', 47, 'python').
project_file('testql/ir_runner/executors/sql.py', 66, 'python').
project_file('testql/ir_runner/executors/unit.py', 43, 'python').
project_file('testql/ir_runner/interpolation.py', 30, 'python').
project_file('testql/mcp/__init__.py', 34, 'python').
project_file('testql/mcp/server.py', 160, 'python').
project_file('testql/meta/__init__.py', 42, 'python').
project_file('testql/meta/confidence_scorer.py', 95, 'python').
project_file('testql/meta/coverage_analyzer.py', 174, 'python').
project_file('testql/meta/mutator.py', 220, 'python').
project_file('testql/meta/self_test.py', 59, 'python').
project_file('testql/openapi_generator.py', 445, 'python').
project_file('testql/pipeline.py', 146, 'python').
project_file('testql/report_generator.py', 251, 'python').
project_file('testql/reporters/__init__.py', 7, 'python').
project_file('testql/reporters/console.py', 39, 'python').
project_file('testql/reporters/json_reporter.py', 34, 'python').
project_file('testql/reporters/junit.py', 80, 'python').
project_file('testql/results/__init__.py', 21, 'python').
project_file('testql/results/analyzer.py', 505, 'python').
project_file('testql/results/artifacts.py', 145, 'python').
project_file('testql/results/models.py', 141, 'python').
project_file('testql/results/serializers.py', 113, 'python').
project_file('testql/runner.py', 372, 'python').
project_file('testql/runners/__init__.py', 1, 'python').
project_file('testql/scenarios/c2004/c2004.testql.less', 29, 'less').
project_file('testql/scenarios/config.testql.less', 44, 'less').
project_file('testql/sumd_generator.py', 209, 'python').
project_file('testql/sumd_parser.py', 278, 'python').
project_file('testql/toon_parser.py', 111, 'python').
project_file('testql/topology/__init__.py', 22, 'python').
project_file('testql/topology/builder.py', 143, 'python').
project_file('testql/topology/generator.py', 242, 'python').
project_file('testql/topology/models.py', 106, 'python').
project_file('testql/topology/serializers.py', 52, 'python').
project_file('testql/topology/sitemap.py', 120, 'python').
project_file('tests/conftest.py', 60, 'python').
project_file('tests/fixtures/discovery/python_pkg/sample_api/__init__.py', 2, 'python').
project_file('tests/fixtures/discovery/python_pkg/sample_api/main.py', 8, 'python').
project_file('tests/test_adapter_capture_syntax.py', 167, 'python').
project_file('tests/test_adapters_base.py', 159, 'python').
project_file('tests/test_api_handler.py', 90, 'python').
project_file('tests/test_browser_discovery.py', 111, 'python').
project_file('tests/test_cli.py', 98, 'python').
project_file('tests/test_cli_no_block.py', 104, 'python').
project_file('tests/test_conversation_live_llm.py', 83, 'python').
project_file('tests/test_conversation_nlp2dsl.py', 158, 'python').
project_file('tests/test_converter.py', 178, 'python').
project_file('tests/test_converter_handlers.py', 352, 'python').
project_file('tests/test_detectors.py', 389, 'python').
project_file('tests/test_discovery.py', 104, 'python').
project_file('tests/test_dispatcher.py', 140, 'python').
project_file('tests/test_doql_parser_sumd_gen.py', 323, 'python').
project_file('tests/test_echo.py', 227, 'python').
project_file('tests/test_echo_doql_parser.py', 220, 'python').
project_file('tests/test_echo_schemas_helpers.py', 214, 'python').
project_file('tests/test_encoder_routes.py', 42, 'python').
project_file('tests/test_generate_cmd.py', 95, 'python').
project_file('tests/test_generate_from_page_cli.py', 280, 'python').
project_file('tests/test_generate_ir_cli.py', 151, 'python').
project_file('tests/test_generators.py', 238, 'python').
project_file('tests/test_graphql_adapter.py', 197, 'python').
project_file('tests/test_gui_execution.py', 130, 'python').
project_file('tests/test_interpreter.py', 224, 'python').
project_file('tests/test_ir.py', 217, 'python').
project_file('tests/test_ir_captures.py', 51, 'python').
project_file('tests/test_ir_runner_assertion_eval.py', 108, 'python').
project_file('tests/test_ir_runner_captures.py', 153, 'python').
project_file('tests/test_ir_runner_engine.py', 143, 'python').
project_file('tests/test_ir_runner_executors.py', 174, 'python').
project_file('tests/test_ir_runner_interpolation.py', 41, 'python').
project_file('tests/test_mcp_autoloop.py', 202, 'python').
project_file('tests/test_meta_confidence.py', 97, 'python').
project_file('tests/test_meta_coverage.py', 137, 'python').
project_file('tests/test_meta_mutator.py', 190, 'python').
project_file('tests/test_meta_self_test.py', 99, 'python').
project_file('tests/test_misc_cmds.py', 111, 'python').
project_file('tests/test_modbus_commands.py', 46, 'python').
project_file('tests/test_navigate_json_path.py', 161, 'python').
project_file('tests/test_network_discovery.py', 163, 'python').
project_file('tests/test_nl_adapter.py', 278, 'python').
project_file('tests/test_nl_entity_extractor.py', 155, 'python').
project_file('tests/test_nl_grammar.py', 101, 'python').
project_file('tests/test_nl_intent_recognizer.py', 133, 'python').
project_file('tests/test_nl_scenarios_e2e.py', 92, 'python').
project_file('tests/test_openapi_generator.py', 344, 'python').
project_file('tests/test_page_analyzer.py', 246, 'python').
project_file('tests/test_pipeline.py', 153, 'python').
project_file('tests/test_plugin_registry.py', 120, 'python').
project_file('tests/test_proto_adapter.py', 128, 'python').
project_file('tests/test_proto_compatibility.py', 159, 'python').
project_file('tests/test_proto_descriptor_loader.py', 175, 'python').
project_file('tests/test_proto_graphql_scenarios_e2e.py', 82, 'python').
project_file('tests/test_proto_message_validator.py', 123, 'python').
project_file('tests/test_report_generator.py', 169, 'python').
project_file('tests/test_reporters.py', 317, 'python').
project_file('tests/test_results.py', 124, 'python').
project_file('tests/test_run_cmd.py', 114, 'python').
project_file('tests/test_run_ir_cli.py', 66, 'python').
project_file('tests/test_runner.py', 188, 'python').
project_file('tests/test_scenario_yaml_adapter.py', 208, 'python').
project_file('tests/test_shell_execution.py', 134, 'python').
project_file('tests/test_smoke_decisions.py', 160, 'python').
project_file('tests/test_sources.py', 497, 'python').
project_file('tests/test_sql_adapter.py', 191, 'python').
project_file('tests/test_sql_ddl_parser.py', 108, 'python').
project_file('tests/test_sql_dialect_resolver.py', 75, 'python').
project_file('tests/test_sql_fixtures.py', 73, 'python').
project_file('tests/test_sql_query_parser.py', 67, 'python').
project_file('tests/test_sql_scenarios_e2e.py', 71, 'python').
project_file('tests/test_suite_cmd_helpers.py', 141, 'python').
project_file('tests/test_suite_execution.py', 93, 'python').
project_file('tests/test_suite_listing.py', 167, 'python').
project_file('tests/test_sumd_parser.py', 206, 'python').
project_file('tests/test_targets.py', 87, 'python').
project_file('tests/test_test_generator.py', 121, 'python').
project_file('tests/test_testtoon_adapter.py', 412, 'python').
project_file('tests/test_toon_parser.py', 84, 'python').
project_file('tests/test_topology.py', 88, 'python').
project_file('tests/test_topology_generator.py', 162, 'python').
project_file('tests/test_unit_execution.py', 113, 'python').
project_file('tests/test_validation.py', 185, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('TODO/testtoon_parser.py', 'detect_separator', 1, 2, 0).
python_function('TODO/testtoon_parser.py', 'parse_value', 1, 11, 7).
python_function('TODO/testtoon_parser.py', 'parse_testtoon', 1, 14, 14).
python_function('TODO/testtoon_parser.py', 'validate', 1, 3, 2).
python_function('TODO/testtoon_parser.py', 'print_parsed', 1, 8, 4).
python_function('examples/api-testing/mock_server.py', 'health', 0, 1, 1).
python_function('examples/api-testing/mock_server.py', 'devices', 0, 1, 1).
python_function('examples/api-testing/mock_server.py', 'list_scenarios', 0, 1, 3).
python_function('examples/api-testing/mock_server.py', 'create_scenario', 1, 1, 2).
python_function('examples/api-testing/mock_server.py', 'get_scenario', 1, 1, 1).
python_function('examples/api-testing/mock_server.py', 'update_scenario', 2, 2, 3).
python_function('examples/api-testing/mock_server.py', 'delete_scenario', 1, 1, 3).
python_function('examples/api-testing/mock_server.py', 'users', 0, 1, 1).
python_function('examples/artifact-bundle/generate_bundle.py', 'main', 0, 2, 7).
python_function('test_autoloop_api.py', 'add_colors', 0, 1, 0).
python_function('test_autoloop_api.py', 'ok', 1, 1, 1).
python_function('test_autoloop_api.py', 'fail', 1, 1, 1).
python_function('test_autoloop_api.py', 'warn', 1, 1, 1).
python_function('test_autoloop_api.py', 'info', 1, 1, 1).
python_function('test_autoloop_api.py', 'header', 1, 1, 1).
python_function('test_autoloop_api.py', 'step_import_testql', 0, 3, 4).
python_function('test_autoloop_api.py', 'step_mcp_check', 0, 4, 3).
python_function('test_autoloop_api.py', 'step_discovery', 1, 2, 8).
python_function('test_autoloop_api.py', 'step_topology', 1, 4, 7).
python_function('test_autoloop_api.py', 'step_inspect', 1, 4, 7).
python_function('test_autoloop_api.py', 'step_generate_tests', 1, 4, 8).
python_function('test_autoloop_api.py', 'step_run_scenario', 1, 4, 6).
python_function('test_autoloop_api.py', 'step_run_tests', 1, 4, 6).
python_function('test_autoloop_api.py', 'step_generate_llm_decision', 5, 6, 3).
python_function('test_autoloop_api.py', 'step_save_artifacts', 6, 6, 5).
python_function('test_autoloop_api.py', 'run_iteration', 3, 2, 8).
python_function('test_autoloop_api.py', 'main', 0, 9, 18).
python_function('test_autoloop_mcp.py', 'ok', 1, 1, 1).
python_function('test_autoloop_mcp.py', 'fail', 1, 1, 1).
python_function('test_autoloop_mcp.py', 'warn', 1, 1, 1).
python_function('test_autoloop_mcp.py', 'info', 1, 1, 1).
python_function('test_autoloop_mcp.py', 'header', 1, 1, 1).
python_function('test_autoloop_mcp.py', 'step_generate_topology', 2, 5, 10).
python_function('test_autoloop_mcp.py', 'step_generate_tests', 2, 8, 12).
python_function('test_autoloop_mcp.py', 'step_run_tests', 2, 8, 13).
python_function('test_autoloop_mcp.py', 'step_generate_llm_prompt', 5, 11, 11).
python_function('test_autoloop_mcp.py', 'step_check_mcp_windsurf', 1, 6, 7).
python_function('test_autoloop_mcp.py', 'run_autoloop', 3, 6, 14).
python_function('test_autoloop_mcp.py', 'main', 0, 3, 10).
python_function('test_manifest_and_generators.py', 'log_ok', 1, 1, 1).
python_function('test_manifest_and_generators.py', 'log_fail', 1, 1, 1).
python_function('test_manifest_and_generators.py', 'log_warn', 1, 1, 1).
python_function('test_manifest_and_generators.py', 'log_info', 1, 1, 1).
python_function('test_manifest_and_generators.py', 'generate_report', 2, 6, 8).
python_function('test_manifest_and_generators.py', 'main', 0, 15, 14).
python_function('testql/adapters/base.py', 'read_source', 1, 5, 5).
python_function('testql/adapters/graphql/graphql_adapter.py', '_config_section', 1, 3, 3).
python_function('testql/adapters/graphql/graphql_adapter.py', '_query_section', 2, 5, 7).
python_function('testql/adapters/graphql/graphql_adapter.py', '_mutation_section', 2, 2, 1).
python_function('testql/adapters/graphql/graphql_adapter.py', '_subscription_section', 2, 2, 1).
python_function('testql/adapters/graphql/graphql_adapter.py', '_assert_section', 2, 4, 7).
python_function('testql/adapters/graphql/graphql_adapter.py', '_toon_to_plan', 1, 4, 5).
python_function('testql/adapters/graphql/graphql_adapter.py', '_apply_section', 3, 2, 6).
python_function('testql/adapters/graphql/graphql_adapter.py', '_h_config', 3, 1, 2).
python_function('testql/adapters/graphql/graphql_adapter.py', '_h_query', 3, 2, 4).
python_function('testql/adapters/graphql/graphql_adapter.py', '_h_mutation', 3, 2, 4).
python_function('testql/adapters/graphql/graphql_adapter.py', '_h_subscription', 3, 2, 4).
python_function('testql/adapters/graphql/graphql_adapter.py', '_h_assert', 3, 1, 2).
python_function('testql/adapters/graphql/graphql_adapter.py', '_render_meta', 1, 4, 1).
python_function('testql/adapters/graphql/graphql_adapter.py', '_render_config', 1, 3, 3).
python_function('testql/adapters/graphql/graphql_adapter.py', '_format_variables', 1, 3, 2).
python_function('testql/adapters/graphql/graphql_adapter.py', '_render_operation_section', 3, 6, 4).
python_function('testql/adapters/graphql/graphql_adapter.py', '_render_asserts', 1, 5, 3).
python_function('testql/adapters/graphql/graphql_adapter.py', '_render_plan', 1, 3, 7).
python_function('testql/adapters/graphql/graphql_adapter.py', 'parse', 1, 1, 2).
python_function('testql/adapters/graphql/graphql_adapter.py', 'render', 1, 1, 2).
python_function('testql/adapters/graphql/query_executor.py', 'classify_operation', 1, 3, 3).
python_function('testql/adapters/graphql/query_executor.py', 'parse_variables', 1, 6, 6).
python_function('testql/adapters/graphql/query_executor.py', '_try_number', 1, 3, 2).
python_function('testql/adapters/graphql/query_executor.py', '_is_quoted', 1, 3, 1).
python_function('testql/adapters/graphql/query_executor.py', '_coerce_literal', 1, 3, 2).
python_function('testql/adapters/graphql/schema_introspection.py', '_scan_balanced_braces', 2, 5, 1).
python_function('testql/adapters/graphql/schema_introspection.py', '_kind_to_canonical', 1, 1, 2).
python_function('testql/adapters/graphql/schema_introspection.py', '_extract_field_names', 1, 2, 3).
python_function('testql/adapters/graphql/schema_introspection.py', '_parse_type_block', 2, 4, 8).
python_function('testql/adapters/graphql/schema_introspection.py', 'parse_schema', 1, 4, 6).
python_function('testql/adapters/graphql/schema_introspection.py', 'has_graphql_core', 0, 2, 0).
python_function('testql/adapters/nl/entity_extractor.py', 'first_quoted', 1, 3, 2).
python_function('testql/adapters/nl/entity_extractor.py', 'all_quoted', 1, 3, 2).
python_function('testql/adapters/nl/entity_extractor.py', 'first_backtick', 1, 2, 2).
python_function('testql/adapters/nl/entity_extractor.py', 'all_backticked', 1, 2, 2).
python_function('testql/adapters/nl/entity_extractor.py', 'first_path', 1, 6, 5).
python_function('testql/adapters/nl/entity_extractor.py', 'first_selector', 1, 7, 4).
python_function('testql/adapters/nl/entity_extractor.py', 'first_http_method', 1, 2, 3).
python_function('testql/adapters/nl/entity_extractor.py', 'first_number', 1, 2, 3).
python_function('testql/adapters/nl/entity_extractor.py', 'strip_quotes_and_backticks', 1, 1, 3).
python_function('testql/adapters/nl/entity_extractor.py', 'split_on_preposition', 2, 4, 8).
python_function('testql/adapters/nl/entity_extractor.py', 'trim_field_nouns', 2, 5, 5).
python_function('testql/adapters/nl/grammar.py', 'is_step_line', 1, 1, 2).
python_function('testql/adapters/nl/grammar.py', 'strip_step_prefix', 1, 1, 2).
python_function('testql/adapters/nl/grammar.py', '_apply_meta', 3, 2, 0).
python_function('testql/adapters/nl/grammar.py', '_consume_line', 3, 5, 8).
python_function('testql/adapters/nl/grammar.py', 'split_header_and_body', 1, 2, 4).
python_function('testql/adapters/nl/grammar.py', 'normalize', 1, 1, 3).
python_function('testql/adapters/nl/intent_recognizer.py', '_intent_table', 1, 5, 6).
python_function('testql/adapters/nl/intent_recognizer.py', 'recognize_intent', 2, 4, 8).
python_function('testql/adapters/nl/intent_recognizer.py', 'recognize_operator', 2, 6, 7).
python_function('testql/adapters/nl/lexicon/__init__.py', 'load_lexicon', 1, 3, 5).
python_function('testql/adapters/nl/lexicon/__init__.py', 'available', 0, 2, 2).
python_function('testql/adapters/nl/llm_fallback.py', 'get_resolver', 0, 1, 0).
python_function('testql/adapters/nl/llm_fallback.py', 'set_resolver', 1, 1, 0).
python_function('testql/adapters/nl/nl_adapter.py', '_build_navigate', 2, 3, 2).
python_function('testql/adapters/nl/nl_adapter.py', '_build_click', 2, 5, 3).
python_function('testql/adapters/nl/nl_adapter.py', '_build_input', 2, 7, 7).
python_function('testql/adapters/nl/nl_adapter.py', '_build_assert', 3, 2, 5).
python_function('testql/adapters/nl/nl_adapter.py', '_assert_field', 2, 7, 6).
python_function('testql/adapters/nl/nl_adapter.py', '_assert_expected', 1, 4, 3).
python_function('testql/adapters/nl/nl_adapter.py', '_build_wait', 2, 3, 3).
python_function('testql/adapters/nl/nl_adapter.py', '_api_status_part', 1, 2, 2).
python_function('testql/adapters/nl/nl_adapter.py', '_build_api', 2, 6, 5).
python_function('testql/adapters/nl/nl_adapter.py', '_build_sql', 2, 3, 4).
python_function('testql/adapters/nl/nl_adapter.py', '_resolve_encoder_action', 1, 3, 1).
python_function('testql/adapters/nl/nl_adapter.py', '_build_encoder', 2, 2, 5).
python_function('testql/adapters/nl/nl_adapter.py', '_build_step', 4, 3, 4).
python_function('testql/adapters/nl/nl_adapter.py', '_build_unresolved', 2, 2, 3).
python_function('testql/adapters/nl/nl_adapter.py', '_render_api', 2, 3, 0).
python_function('testql/adapters/nl/nl_adapter.py', '_render_sql', 2, 2, 0).
python_function('testql/adapters/nl/nl_adapter.py', '_render_encoder', 2, 3, 1).
python_function('testql/adapters/nl/nl_adapter.py', '_render_assert', 2, 4, 0).
python_function('testql/adapters/nl/nl_adapter.py', '_render_wait', 2, 3, 0).
python_function('testql/adapters/nl/nl_adapter.py', '_render_nl', 2, 1, 0).
python_function('testql/adapters/nl/nl_adapter.py', '_render_gui', 2, 2, 2).
python_function('testql/adapters/nl/nl_adapter.py', '_render_by_kind', 2, 3, 2).
python_function('testql/adapters/nl/nl_adapter.py', '_render_step', 2, 4, 3).
python_function('testql/adapters/nl/nl_adapter.py', '_metadata_from_header', 2, 2, 2).
python_function('testql/adapters/nl/nl_adapter.py', 'parse', 1, 3, 2).
python_function('testql/adapters/nl/nl_adapter.py', 'render', 1, 5, 2).
python_function('testql/adapters/nlp2dsl/llm_provider.py', 'live_llm_enabled', 1, 2, 3).
python_function('testql/adapters/nlp2dsl/llm_provider.py', 'resolve_llm_provider', 0, 4, 5).
python_function('testql/adapters/nlp2dsl/mock_llm.py', 'load_mock_replies', 1, 5, 8).
python_function('testql/adapters/proto/__init__.py', 'has_protobuf', 0, 2, 0).
python_function('testql/adapters/proto/compatibility.py', '_wire_compatible', 2, 4, 1).
python_function('testql/adapters/proto/compatibility.py', '_compare_field', 3, 5, 3).
python_function('testql/adapters/proto/compatibility.py', '_find_candidate_field', 2, 6, 1).
python_function('testql/adapters/proto/compatibility.py', '_compare_message', 2, 2, 3).
python_function('testql/adapters/proto/compatibility.py', '_scan_old_messages', 3, 3, 5).
python_function('testql/adapters/proto/compatibility.py', '_scan_new_messages', 3, 4, 2).
python_function('testql/adapters/proto/compatibility.py', 'compare_schemas', 2, 2, 3).
python_function('testql/adapters/proto/descriptor_loader.py', '_strip_comments', 1, 1, 1).
python_function('testql/adapters/proto/descriptor_loader.py', '_scan_balanced_braces', 2, 5, 1).
python_function('testql/adapters/proto/descriptor_loader.py', '_parse_field', 1, 3, 4).
python_function('testql/adapters/proto/descriptor_loader.py', '_parse_message', 2, 2, 3).
python_function('testql/adapters/proto/descriptor_loader.py', '_iter_messages', 1, 3, 4).
python_function('testql/adapters/proto/descriptor_loader.py', 'parse_proto', 1, 4, 7).
python_function('testql/adapters/proto/descriptor_loader.py', 'load_proto_file', 1, 1, 3).
python_function('testql/adapters/proto/message_validator.py', 'parse_instance_fields', 1, 7, 6).
python_function('testql/adapters/proto/message_validator.py', 'coerce_scalar', 2, 5, 6).
python_function('testql/adapters/proto/message_validator.py', '_validate_field_known', 2, 2, 2).
python_function('testql/adapters/proto/message_validator.py', '_validate_field_type', 3, 3, 2).
python_function('testql/adapters/proto/message_validator.py', '_validate_field_value', 3, 3, 2).
python_function('testql/adapters/proto/message_validator.py', 'validate_message_instance', 2, 5, 6).
python_function('testql/adapters/proto/message_validator.py', '_row_issues', 4, 3, 4).
python_function('testql/adapters/proto/message_validator.py', '_missing_required', 2, 4, 1).
python_function('testql/adapters/proto/message_validator.py', 'round_trip_equal', 2, 6, 3).
python_function('testql/adapters/proto/message_validator.py', 'lookup_message', 2, 1, 1).
python_function('testql/adapters/proto/proto_adapter.py', '_proto_section', 1, 3, 4).
python_function('testql/adapters/proto/proto_adapter.py', '_message_section', 2, 5, 5).
python_function('testql/adapters/proto/proto_adapter.py', '_assert_section', 2, 5, 6).
python_function('testql/adapters/proto/proto_adapter.py', '_toon_to_plan', 1, 4, 5).
python_function('testql/adapters/proto/proto_adapter.py', '_apply_section', 4, 2, 6).
python_function('testql/adapters/proto/proto_adapter.py', '_h_proto', 4, 1, 4).
python_function('testql/adapters/proto/proto_adapter.py', '_h_message', 4, 1, 2).
python_function('testql/adapters/proto/proto_adapter.py', '_h_assert', 4, 3, 2).
python_function('testql/adapters/proto/proto_adapter.py', '_render_meta', 1, 4, 1).
python_function('testql/adapters/proto/proto_adapter.py', '_render_proto_files', 1, 6, 3).
python_function('testql/adapters/proto/proto_adapter.py', '_render_messages', 1, 6, 4).
python_function('testql/adapters/proto/proto_adapter.py', '_render_asserts', 1, 5, 4).
python_function('testql/adapters/proto/proto_adapter.py', '_render_plan', 1, 3, 7).
python_function('testql/adapters/proto/proto_adapter.py', 'parse', 1, 1, 2).
python_function('testql/adapters/proto/proto_adapter.py', 'render', 1, 1, 2).
python_function('testql/adapters/registry.py', 'get_registry', 0, 1, 0).
python_function('testql/adapters/scenario_yaml.py', '_as_dict', 1, 2, 1).
python_function('testql/adapters/scenario_yaml.py', '_as_list', 1, 3, 1).
python_function('testql/adapters/scenario_yaml.py', '_parse_wait_ms', 1, 5, 7).
python_function('testql/adapters/scenario_yaml.py', '_split_request', 1, 7, 8).
python_function('testql/adapters/scenario_yaml.py', '_normalise_capture_path', 1, 1, 3).
python_function('testql/adapters/scenario_yaml.py', '_captures_from', 1, 2, 5).
python_function('testql/adapters/scenario_yaml.py', '_assertion_from_field', 2, 3, 7).
python_function('testql/adapters/scenario_yaml.py', '_assertions_from_expect', 1, 9, 6).
python_function('testql/adapters/scenario_yaml.py', '_step_common', 2, 6, 6).
python_function('testql/adapters/scenario_yaml.py', '_api_step', 1, 9, 8).
python_function('testql/adapters/scenario_yaml.py', '_gui_step', 1, 9, 6).
python_function('testql/adapters/scenario_yaml.py', '_encoder_step', 1, 13, 5).
python_function('testql/adapters/scenario_yaml.py', '_shell_step', 1, 6, 8).
python_function('testql/adapters/scenario_yaml.py', '_unit_step', 1, 6, 4).
python_function('testql/adapters/scenario_yaml.py', '_typed_step', 1, 2, 5).
python_function('testql/adapters/scenario_yaml.py', '_detect_step_type', 1, 12, 3).
python_function('testql/adapters/scenario_yaml.py', '_is_gui_step', 1, 5, 2).
python_function('testql/adapters/scenario_yaml.py', '_is_encoder_step', 1, 4, 2).
python_function('testql/adapters/scenario_yaml.py', '_is_unit_step', 1, 2, 1).
python_function('testql/adapters/scenario_yaml.py', '_create_step_by_type', 2, 1, 2).
python_function('testql/adapters/scenario_yaml.py', '_create_sql_step', 1, 3, 4).
python_function('testql/adapters/scenario_yaml.py', '_create_graphql_step', 1, 2, 5).
python_function('testql/adapters/scenario_yaml.py', '_create_nl_step', 1, 1, 2).
python_function('testql/adapters/scenario_yaml.py', '_create_generic_step', 1, 1, 4).
python_function('testql/adapters/scenario_yaml.py', '_metadata_from', 1, 7, 6).
python_function('testql/adapters/scenario_yaml.py', '_config_from', 1, 7, 5).
python_function('testql/adapters/scenario_yaml.py', '_plan_from_yaml', 1, 4, 7).
python_function('testql/adapters/scenario_yaml.py', '_render_step', 1, 10, 11).
python_function('testql/adapters/scenario_yaml.py', '_render_api_step', 1, 4, 0).
python_function('testql/adapters/scenario_yaml.py', '_render_gui_step', 1, 4, 0).
python_function('testql/adapters/scenario_yaml.py', '_render_shell_step', 1, 3, 0).
python_function('testql/adapters/scenario_yaml.py', '_render_encoder_step', 1, 3, 0).
python_function('testql/adapters/scenario_yaml.py', '_render_unit_step', 1, 1, 0).
python_function('testql/adapters/scenario_yaml.py', '_render_sql_step', 1, 1, 0).
python_function('testql/adapters/scenario_yaml.py', '_render_graphql_step', 1, 1, 0).
python_function('testql/adapters/scenario_yaml.py', '_render_nl_step', 1, 1, 0).
python_function('testql/adapters/scenario_yaml.py', '_add_common_step_attributes', 2, 7, 1).
python_function('testql/adapters/scenario_yaml.py', '_reverse_operator', 1, 1, 1).
python_function('testql/adapters/scenario_yaml.py', 'parse', 1, 3, 2).
python_function('testql/adapters/scenario_yaml.py', 'render', 1, 9, 2).
python_function('testql/adapters/sql/ddl_parser.py', '_scan_balanced_parens', 2, 5, 1).
python_function('testql/adapters/sql/ddl_parser.py', '_iter_create_tables', 1, 3, 4).
python_function('testql/adapters/sql/ddl_parser.py', '_depth_delta', 1, 3, 0).
python_function('testql/adapters/sql/ddl_parser.py', '_split_top_level', 1, 7, 4).
python_function('testql/adapters/sql/ddl_parser.py', '_parse_column_line', 1, 3, 8).
python_function('testql/adapters/sql/ddl_parser.py', '_extract_default', 1, 2, 2).
python_function('testql/adapters/sql/ddl_parser.py', '_parse_table_regex', 2, 4, 3).
python_function('testql/adapters/sql/ddl_parser.py', '_parse_ddl_regex', 1, 2, 3).
python_function('testql/adapters/sql/ddl_parser.py', '_parse_ddl_sqlglot', 2, 5, 7).
python_function('testql/adapters/sql/ddl_parser.py', '_table_from_sqlglot', 1, 5, 5).
python_function('testql/adapters/sql/ddl_parser.py', '_column_from_sqlglot', 1, 4, 8).
python_function('testql/adapters/sql/ddl_parser.py', 'parse_ddl', 3, 4, 3).
python_function('testql/adapters/sql/dialect_resolver.py', 'normalize_dialect', 1, 2, 3).
python_function('testql/adapters/sql/dialect_resolver.py', 'is_supported', 1, 2, 1).
python_function('testql/adapters/sql/dialect_resolver.py', 'has_sqlglot', 0, 2, 0).
python_function('testql/adapters/sql/dialect_resolver.py', 'transpile', 3, 4, 4).
python_function('testql/adapters/sql/fixtures.py', 'schema_fixture_from_rows', 1, 4, 8).
python_function('testql/adapters/sql/fixtures.py', '_truthy', 2, 5, 4).
python_function('testql/adapters/sql/fixtures.py', '_optional_str', 1, 4, 2).
python_function('testql/adapters/sql/query_parser.py', 'classify', 1, 2, 4).
python_function('testql/adapters/sql/query_parser.py', '_analyze_with_sqlglot', 2, 5, 8).
python_function('testql/adapters/sql/query_parser.py', '_projection_columns', 1, 5, 4).
python_function('testql/adapters/sql/query_parser.py', 'analyze_query', 2, 3, 4).
python_function('testql/adapters/sql/sql_adapter.py', '_config_section', 2, 5, 6).
python_function('testql/adapters/sql/sql_adapter.py', '_schema_section', 1, 1, 2).
python_function('testql/adapters/sql/sql_adapter.py', '_query_section', 2, 4, 6).
python_function('testql/adapters/sql/sql_adapter.py', '_row_query', 1, 3, 3).
python_function('testql/adapters/sql/sql_adapter.py', '_assert_section', 2, 4, 7).
python_function('testql/adapters/sql/sql_adapter.py', '_resolve_owner', 2, 1, 3).
python_function('testql/adapters/sql/sql_adapter.py', '_toon_to_plan', 1, 5, 6).
python_function('testql/adapters/sql/sql_adapter.py', '_apply_section', 4, 2, 6).
python_function('testql/adapters/sql/sql_adapter.py', '_h_config', 4, 1, 3).
python_function('testql/adapters/sql/sql_adapter.py', '_h_schema', 4, 1, 2).
python_function('testql/adapters/sql/sql_adapter.py', '_h_query', 4, 1, 2).
python_function('testql/adapters/sql/sql_adapter.py', '_h_assert', 4, 3, 2).
python_function('testql/adapters/sql/sql_adapter.py', '_h_capture', 4, 8, 5).
python_function('testql/adapters/sql/sql_adapter.py', '_render_meta', 1, 5, 2).
python_function('testql/adapters/sql/sql_adapter.py', '_render_config', 1, 3, 3).
python_function('testql/adapters/sql/sql_adapter.py', '_collect_schema_rows', 1, 6, 2).
python_function('testql/adapters/sql/sql_adapter.py', '_render_schema', 1, 3, 3).
python_function('testql/adapters/sql/sql_adapter.py', '_render_queries', 1, 6, 3).
python_function('testql/adapters/sql/sql_adapter.py', '_render_asserts', 1, 5, 2).
python_function('testql/adapters/sql/sql_adapter.py', '_render_captures', 1, 7, 3).
python_function('testql/adapters/sql/sql_adapter.py', '_render_plan', 1, 3, 9).
python_function('testql/adapters/sql/sql_adapter.py', 'parse', 1, 1, 2).
python_function('testql/adapters/sql/sql_adapter.py', 'render', 1, 1, 2).
python_function('testql/adapters/testtoon_adapter.py', '_config_to_dict', 1, 3, 1).
python_function('testql/adapters/testtoon_adapter.py', '_api_section_to_steps', 1, 10, 10).
python_function('testql/adapters/testtoon_adapter.py', '_navigate_section_to_steps', 1, 3, 5).
python_function('testql/adapters/testtoon_adapter.py', '_gui_section_to_steps', 1, 7, 8).
python_function('testql/adapters/testtoon_adapter.py', '_encoder_section_to_steps', 1, 3, 6).
python_function('testql/adapters/testtoon_adapter.py', '_assert_section_to_steps', 1, 3, 4).
python_function('testql/adapters/testtoon_adapter.py', '_capture_section_apply', 2, 8, 6).
python_function('testql/adapters/testtoon_adapter.py', '_resolve_capture_target', 3, 4, 3).
python_function('testql/adapters/testtoon_adapter.py', '_coerce_assert_expected', 1, 7, 5).
python_function('testql/adapters/testtoon_adapter.py', '_assert_json_field', 1, 3, 3).
python_function('testql/adapters/testtoon_adapter.py', '_assert_json_section_apply', 2, 12, 9).
python_function('testql/adapters/testtoon_adapter.py', '_generic_section_to_steps', 1, 2, 4).
python_function('testql/adapters/testtoon_adapter.py', '_shell_section_to_steps', 1, 10, 9).
python_function('testql/adapters/testtoon_adapter.py', '_unit_section_to_steps', 1, 5, 5).
python_function('testql/adapters/testtoon_adapter.py', '_log_section_to_steps', 1, 4, 4).
python_function('testql/adapters/testtoon_adapter.py', '_context_section_to_config', 1, 1, 1).
python_function('testql/adapters/testtoon_adapter.py', '_conversation_section_to_steps', 1, 7, 6).
python_function('testql/adapters/testtoon_adapter.py', '_nlp2dsl_section_to_steps', 1, 11, 8).
python_function('testql/adapters/testtoon_adapter.py', '_validate_section_to_steps', 1, 9, 8).
python_function('testql/adapters/testtoon_adapter.py', '_parse_artifact_criteria', 1, 5, 2).
python_function('testql/adapters/testtoon_adapter.py', '_translate_section', 1, 3, 4).
python_function('testql/adapters/testtoon_adapter.py', '_toon_to_plan', 1, 8, 10).
python_function('testql/adapters/testtoon_adapter.py', '_render_meta', 1, 5, 1).
python_function('testql/adapters/testtoon_adapter.py', '_render_config', 1, 3, 3).
python_function('testql/adapters/testtoon_adapter.py', '_render_api_steps', 1, 4, 2).
python_function('testql/adapters/testtoon_adapter.py', '_render_navigate_steps', 1, 6, 2).
python_function('testql/adapters/testtoon_adapter.py', '_render_encoder_steps', 1, 6, 2).
python_function('testql/adapters/testtoon_adapter.py', '_toon_safe_selector', 1, 3, 2).
python_function('testql/adapters/testtoon_adapter.py', '_render_gui_action_steps', 1, 9, 7).
python_function('testql/adapters/testtoon_adapter.py', '_render_shell_steps', 1, 6, 3).
python_function('testql/adapters/testtoon_adapter.py', '_render_unit_steps', 1, 5, 3).
python_function('testql/adapters/testtoon_adapter.py', '_render_log_steps', 1, 5, 5).
python_function('testql/adapters/testtoon_adapter.py', '_render_assertions', 1, 6, 2).
python_function('testql/adapters/testtoon_adapter.py', '_render_captures', 1, 5, 4).
python_function('testql/adapters/testtoon_adapter.py', '_render_validate_steps', 1, 5, 3).
python_function('testql/adapters/testtoon_adapter.py', '_format_extra_value', 1, 6, 2).
python_function('testql/adapters/testtoon_adapter.py', '_group_generic_steps', 1, 9, 3).
python_function('testql/adapters/testtoon_adapter.py', '_derive_columns', 1, 4, 4).
python_function('testql/adapters/testtoon_adapter.py', '_render_group_section', 3, 3, 5).
python_function('testql/adapters/testtoon_adapter.py', '_render_generic_section_steps', 1, 4, 4).
python_function('testql/adapters/testtoon_adapter.py', '_render_plan', 1, 9, 17).
python_function('testql/adapters/testtoon_adapter.py', 'parse', 1, 1, 2).
python_function('testql/adapters/testtoon_adapter.py', 'render', 1, 1, 2).
python_function('testql/artifacts/registry.py', 'get_artifact_registry', 0, 2, 4).
python_function('testql/cli.py', 'mcp_serve', 0, 2, 4).
python_function('testql/cli.py', 'cli', 0, 1, 3).
python_function('testql/cli.py', '_fetch_latest_version', 0, 2, 3).
python_function('testql/cli.py', 'check_and_upgrade', 0, 4, 3).
python_function('testql/cli.py', 'main', 0, 1, 2).
python_function('testql/commands/auto_cmd.py', 'auto', 8, 5, 12).
python_function('testql/commands/auto_cmd.py', '_status_color', 1, 1, 1).
python_function('testql/commands/auto_cmd.py', '_run_generation_phase', 2, 2, 6).
python_function('testql/commands/auto_cmd.py', '_run_analysis_phase', 1, 4, 3).
python_function('testql/commands/auto_cmd.py', '_build_report_data', 8, 9, 3).
python_function('testql/commands/auto_cmd.py', '_run_report_phase', 3, 3, 6).
python_function('testql/commands/auto_cmd.py', '_print_summary', 3, 1, 6).
python_function('testql/commands/auto_cmd.py', '_render_console_report', 2, 4, 3).
python_function('testql/commands/auto_cmd.py', '_render_markdown_report', 2, 4, 4).
python_function('testql/commands/conversation_cmd.py', '_validate_scenario', 2, 3, 2).
python_function('testql/commands/conversation_cmd.py', '_resolve_base_url', 2, 4, 1).
python_function('testql/commands/conversation_cmd.py', '_create_runner', 4, 2, 2).
python_function('testql/commands/conversation_cmd.py', '_format_mode', 2, 4, 1).
python_function('testql/commands/conversation_cmd.py', '_output_json', 1, 1, 3).
python_function('testql/commands/conversation_cmd.py', '_output_text', 5, 6, 2).
python_function('testql/commands/conversation_cmd.py', 'conversation', 0, 1, 1).
python_function('testql/commands/conversation_cmd.py', 'conversation_run', 6, 6, 16).
python_function('testql/commands/discover_cmd.py', 'discover', 3, 5, 14).
python_function('testql/commands/discover_cmd.py', '_print_summary', 1, 9, 6).
python_function('testql/commands/echo/cli.py', 'echo', 5, 3, 10).
python_function('testql/commands/echo/context.py', '_find_doql_file', 1, 4, 3).
python_function('testql/commands/echo/context.py', '_find_toon_path', 1, 2, 1).
python_function('testql/commands/echo/context.py', 'generate_context', 3, 4, 5).
python_function('testql/commands/echo/formatters/text.py', '_fmt_interfaces', 1, 3, 2).
python_function('testql/commands/echo/formatters/text.py', '_fmt_workflows', 1, 3, 3).
python_function('testql/commands/echo/formatters/text.py', '_fmt_contracts', 1, 5, 3).
python_function('testql/commands/echo/formatters/text.py', '_fmt_entities', 1, 4, 3).
python_function('testql/commands/echo/formatters/text.py', '_fmt_suggestions', 1, 6, 3).
python_function('testql/commands/echo/formatters/text.py', '_build_header', 1, 1, 1).
python_function('testql/commands/echo/formatters/text.py', 'format_text_output', 1, 1, 7).
python_function('testql/commands/echo/parsers/doql.py', '_parse_kv_block', 1, 3, 3).
python_function('testql/commands/echo/parsers/doql.py', '_parse_app_block', 1, 2, 3).
python_function('testql/commands/echo/parsers/doql.py', '_parse_entities', 1, 7, 8).
python_function('testql/commands/echo/parsers/doql.py', '_parse_interfaces', 1, 2, 4).
python_function('testql/commands/echo/parsers/doql.py', '_parse_workflows', 1, 7, 8).
python_function('testql/commands/echo/parsers/doql.py', '_parse_deploy', 1, 2, 3).
python_function('testql/commands/echo/parsers/doql.py', '_parse_environment', 1, 2, 3).
python_function('testql/commands/echo/parsers/doql.py', '_parse_integrations', 1, 4, 9).
python_function('testql/commands/echo/parsers/doql.py', 'parse_doql_less', 1, 1, 8).
python_function('testql/commands/echo/parsers/toon.py', '_extract_endpoint', 2, 2, 4).
python_function('testql/commands/echo/parsers/toon.py', '_extract_assert', 2, 1, 0).
python_function('testql/commands/echo/parsers/toon.py', '_parse_scenario', 3, 5, 9).
python_function('testql/commands/echo/parsers/toon.py', 'parse_toon_scenarios', 1, 3, 5).
python_function('testql/commands/echo_helpers.py', '_collect_toon_directory', 2, 8, 7).
python_function('testql/commands/echo_helpers.py', 'collect_toon_data', 2, 3, 6).
python_function('testql/commands/echo_helpers.py', 'collect_doql_data', 2, 2, 4).
python_function('testql/commands/echo_helpers.py', 'render_echo', 3, 3, 4).
python_function('testql/commands/encoder_routes.py', '_strip_path_segments', 1, 3, 3).
python_function('testql/commands/encoder_routes.py', '_migrate_legacy_extension', 1, 4, 3).
python_function('testql/commands/encoder_routes.py', '_remap_tests_prefix', 1, 3, 2).
python_function('testql/commands/encoder_routes.py', '_normalize_oql_path', 1, 3, 5).
python_function('testql/commands/encoder_routes.py', '_resolve_oql_path', 1, 1, 2).
python_function('testql/commands/encoder_routes.py', '_assert_bool_prop', 3, 2, 4).
python_function('testql/commands/encoder_routes.py', '_assert_count_prop', 2, 2, 2).
python_function('testql/commands/encoder_routes.py', '_assert_text_prop', 2, 2, 2).
python_function('testql/commands/encoder_routes.py', '_assert_classes_prop', 2, 2, 1).
python_function('testql/commands/encoder_routes.py', '_evaluate_assertion', 3, 6, 6).
python_function('testql/commands/encoder_routes.py', '_format_log_detail', 2, 7, 2).
python_function('testql/commands/encoder_routes.py', '_exec_encoder_cmd', 2, 6, 2).
python_function('testql/commands/encoder_routes.py', '_exec_browser_cmd', 3, 9, 5).
python_function('testql/commands/encoder_routes.py', '_exec_assert_cmd', 1, 7, 8).
python_function('testql/commands/encoder_routes.py', '_execute_oql_line', 1, 10, 10).
python_function('testql/commands/encoder_routes.py', 'oql_list_files', 0, 7, 10).
python_function('testql/commands/encoder_routes.py', 'oql_read_file', 1, 3, 9).
python_function('testql/commands/encoder_routes.py', 'oql_list_tables', 1, 3, 9).
python_function('testql/commands/encoder_routes.py', '_extract_table_names', 1, 2, 4).
python_function('testql/commands/encoder_routes.py', 'oql_run_line', 1, 1, 2).
python_function('testql/commands/encoder_routes.py', 'oql_run_file', 1, 3, 12).
python_function('testql/commands/encoder_routes.py', '_run_oql_lines', 2, 6, 15).
python_function('testql/commands/encoder_routes.py', '_update_counters', 2, 4, 1).
python_function('testql/commands/encoder_routes.py', '_build_run_summary', 5, 2, 1).
python_function('testql/commands/encoder_routes.py', '_write_run_log', 4, 1, 7).
python_function('testql/commands/encoder_routes.py', 'oql_list_logs', 0, 3, 9).
python_function('testql/commands/encoder_routes.py', 'oql_read_log', 1, 3, 9).
python_function('testql/commands/endpoints_cmd.py', 'endpoints', 5, 9, 12).
python_function('testql/commands/endpoints_cmd.py', '_format_endpoints_json', 2, 3, 3).
python_function('testql/commands/endpoints_cmd.py', '_format_endpoints_csv', 2, 5, 6).
python_function('testql/commands/endpoints_cmd.py', '_format_endpoints_table', 2, 5, 3).
python_function('testql/commands/endpoints_cmd.py', '_format_endpoints', 4, 3, 3).
python_function('testql/commands/endpoints_cmd.py', 'openapi', 6, 3, 12).
python_function('testql/commands/generate_cmd.py', '_is_workspace', 1, 1, 1).
python_function('testql/commands/generate_cmd.py', '_echo_analysis', 2, 4, 5).
python_function('testql/commands/generate_cmd.py', '_echo_generation', 2, 3, 2).
python_function('testql/commands/generate_cmd.py', 'generate', 6, 5, 12).
python_function('testql/commands/generate_cmd.py', '_emit_ir_json', 2, 4, 9).
python_function('testql/commands/generate_cmd.py', 'analyze', 1, 4, 11).
python_function('testql/commands/generate_cmd.py', '_count_routes_by', 2, 2, 1).
python_function('testql/commands/generate_cmd.py', '_print_routes_section', 1, 10, 7).
python_function('testql/commands/generate_cmd.py', '_print_scenarios_section', 1, 3, 3).
python_function('testql/commands/generate_from_page_cmd.py', '_default_output', 1, 3, 4).
python_function('testql/commands/generate_from_page_cmd.py', 'generate_from_page', 6, 8, 19).
python_function('testql/commands/generate_ir_cmd.py', '_split_from_arg', 1, 2, 5).
python_function('testql/commands/generate_ir_cmd.py', 'generate_ir', 4, 2, 8).
python_function('testql/commands/generate_topology_cmd.py', 'generate_topology', 5, 5, 16).
python_function('testql/commands/generate_topology_cmd.py', '_pick_trace', 2, 5, 1).
python_function('testql/commands/heal_scenario_cmd.py', '_collect_selectors', 1, 3, 6).
python_function('testql/commands/heal_scenario_cmd.py', '_selector_resolves', 2, 2, 2).
python_function('testql/commands/heal_scenario_cmd.py', '_healed_path', 1, 3, 4).
python_function('testql/commands/heal_scenario_cmd.py', '_heal_text', 2, 3, 4).
python_function('testql/commands/heal_scenario_cmd.py', 'heal_scenario', 6, 8, 19).
python_function('testql/commands/heal_scenario_cmd.py', '_heal_with_elements', 2, 6, 5).
python_function('testql/commands/heal_scenario_cmd.py', '_heal_with_browser', 2, 7, 11).
python_function('testql/commands/heal_scenario_cmd.py', '_print_summary', 2, 5, 3).
python_function('testql/commands/inspect_cmd.py', 'inspect', 6, 6, 15).
python_function('testql/commands/misc_cmds.py', '_create_templates', 2, 4, 4).
python_function('testql/commands/misc_cmds.py', 'init', 3, 4, 10).
python_function('testql/commands/misc_cmds.py', 'create', 5, 6, 11).
python_function('testql/commands/misc_cmds.py', 'watch', 4, 4, 19).
python_function('testql/commands/misc_cmds.py', 'from_sumd', 3, 3, 10).
python_function('testql/commands/misc_cmds.py', 'report', 3, 4, 10).
python_function('testql/commands/misc_cmds.py', 'echo', 5, 4, 10).
python_function('testql/commands/run_cmd.py', '_resolve_input_paths', 1, 10, 8).
python_function('testql/commands/run_cmd.py', '_run_single', 5, 1, 4).
python_function('testql/commands/run_cmd.py', '_emit_single_json', 1, 1, 4).
python_function('testql/commands/run_cmd.py', '_emit_multi_json', 1, 3, 7).
python_function('testql/commands/run_cmd.py', '_maybe_planfile', 3, 9, 4).
python_function('testql/commands/run_cmd.py', 'run', 7, 10, 16).
python_function('testql/commands/run_ir_cmd.py', '_emit_json', 1, 2, 3).
python_function('testql/commands/run_ir_cmd.py', '_emit_console', 1, 3, 3).
python_function('testql/commands/run_ir_cmd.py', 'run_ir', 6, 3, 9).
python_function('testql/commands/self_test_cmd.py', '_print_human', 1, 4, 1).
python_function('testql/commands/self_test_cmd.py', 'self_test', 2, 2, 7).
python_function('testql/commands/suite/cli.py', 'suite', 10, 13, 19).
python_function('testql/commands/suite/cli.py', 'list_tests', 4, 2, 8).
python_function('testql/commands/suite/collection.py', '_resolve_search_dir_and_pattern', 2, 4, 2).
python_function('testql/commands/suite/collection.py', '_find_files', 2, 6, 6).
python_function('testql/commands/suite/collection.py', '_collect_from_suite', 3, 4, 6).
python_function('testql/commands/suite/collection.py', '_collect_by_pattern', 2, 2, 3).
python_function('testql/commands/suite/collection.py', '_collect_recursive', 1, 4, 3).
python_function('testql/commands/suite/collection.py', '_deduplicate_files', 1, 5, 5).
python_function('testql/commands/suite/collection.py', 'collect_test_files', 4, 5, 6).
python_function('testql/commands/suite/collection.py', 'collect_list_files', 1, 4, 5).
python_function('testql/commands/suite/execution.py', 'run_single_file', 2, 3, 3).
python_function('testql/commands/suite/execution.py', 'run_suite_files', 5, 5, 8).
python_function('testql/commands/suite/listing.py', '_parse_testtoon_header', 1, 6, 4).
python_function('testql/commands/suite/listing.py', '_collect_meta_lines', 1, 7, 4).
python_function('testql/commands/suite/listing.py', '_parse_yaml_meta_block', 2, 5, 4).
python_function('testql/commands/suite/listing.py', 'parse_meta', 2, 6, 5).
python_function('testql/commands/suite/listing.py', 'filter_tests', 5, 6, 5).
python_function('testql/commands/suite/listing.py', 'render_test_list', 2, 6, 5).
python_function('testql/commands/suite/reports.py', 'build_report_data', 5, 6, 2).
python_function('testql/commands/suite/reports.py', '_save_json_report', 2, 1, 3).
python_function('testql/commands/suite/reports.py', '_build_junit_xml', 1, 5, 2).
python_function('testql/commands/suite/reports.py', 'save_report', 3, 3, 5).
python_function('testql/commands/suite/reports.py', 'print_summary', 4, 3, 3).
python_function('testql/commands/topology_cmd.py', 'topology', 4, 3, 11).
python_function('testql/commands/watchdog_cmd.py', '_discover_scenarios', 1, 8, 8).
python_function('testql/commands/watchdog_cmd.py', '_run_scenario', 3, 3, 5).
python_function('testql/commands/watchdog_cmd.py', '_post_failures', 3, 4, 5).
python_function('testql/commands/watchdog_cmd.py', '_extract_failures', 1, 10, 3).
python_function('testql/commands/watchdog_cmd.py', '_start_metrics_server', 2, 2, 7).
python_function('testql/commands/watchdog_cmd.py', '_update_metrics', 5, 11, 6).
python_function('testql/commands/watchdog_cmd.py', '_resolve_watchdog_config', 5, 6, 4).
python_function('testql/commands/watchdog_cmd.py', '_process_one_scenario', 5, 3, 7).
python_function('testql/commands/watchdog_cmd.py', 'watchdog', 8, 14, 19).
python_function('testql/conversation/runner.py', '_step_status_name', 1, 4, 0).
python_function('testql/conversation/runner.py', '_extract_path', 2, 4, 3).
python_function('testql/detectors/unified.py', 'detect_endpoints', 3, 2, 3).
python_function('testql/discovery/manifest.py', '_score_confidence', 1, 5, 1).
python_function('testql/discovery/manifest.py', '_merge_metadata', 1, 10, 5).
python_function('testql/discovery/manifest.py', '_dependencies_from_metadata', 1, 4, 4).
python_function('testql/discovery/manifest.py', '_interfaces_from_metadata', 1, 5, 4).
python_function('testql/discovery/manifest.py', '_unique', 1, 3, 3).
python_function('testql/discovery/manifest.py', '_dedupe_dicts', 1, 4, 7).
python_function('testql/discovery/probes/browser/playwright_page.py', '_link_kind', 2, 4, 3).
python_function('testql/discovery/probes/browser/playwright_page.py', '_asset_kind', 1, 8, 3).
python_function('testql/discovery/probes/filesystem/api_openapi.py', '_excluded', 2, 4, 2).
python_function('testql/discovery/probes/filesystem/package_python.py', '_parse_pyproject', 1, 7, 4).
python_function('testql/discovery/probes/filesystem/package_python.py', '_parse_setup_cfg', 1, 3, 3).
python_function('testql/discovery/probes/filesystem/package_python.py', '_parse_setup_py', 1, 3, 2).
python_function('testql/discovery/probes/filesystem/package_python.py', '_parse_pyproject_dependencies', 1, 6, 11).
python_function('testql/discovery/probes/filesystem/package_python.py', '_parse_requirements', 1, 4, 5).
python_function('testql/discovery/probes/filesystem/package_python.py', '_dep', 1, 3, 3).
python_function('testql/discovery/probes/filesystem/package_python.py', '_section', 2, 2, 3).
python_function('testql/discovery/probes/filesystem/package_python.py', '_quoted_value', 2, 2, 3).
python_function('testql/discovery/probes/filesystem/package_python.py', '_plain_value', 2, 2, 4).
python_function('testql/discovery/probes/filesystem/package_python.py', '_call_kw', 2, 2, 3).
python_function('testql/discovery/probes/filesystem/package_python.py', '_dedupe_deps', 1, 4, 5).
python_function('testql/discovery/probes/filesystem/package_python.py', '_excluded', 1, 2, 1).
python_function('testql/discovery/probes/network/http_endpoint.py', '_fetch', 2, 1, 2).
python_function('testql/discovery/probes/network/http_endpoint.py', '_looks_textual', 1, 2, 2).
python_function('testql/discovery/probes/network/http_endpoint.py', '_metadata', 4, 1, 2).
python_function('testql/discovery/probes/network/http_endpoint.py', '_parse_html', 2, 2, 3).
python_function('testql/discovery/probes/network/http_endpoint.py', '_limit', 2, 1, 0).
python_function('testql/discovery/probes/network/http_endpoint.py', '_asset_kind', 2, 8, 2).
python_function('testql/discovery/probes/network/http_endpoint.py', '_link_kind', 2, 4, 3).
python_function('testql/discovery/registry.py', 'default_probes', 2, 3, 8).
python_function('testql/discovery/registry.py', 'discover_path', 3, 1, 2).
python_function('testql/discovery/registry.py', '_cost_key', 1, 1, 1).
python_function('testql/doql_parser.py', 'parse_doql_file', 1, 1, 2).
python_function('testql/generators/convenience.py', 'generate_for_project', 1, 1, 2).
python_function('testql/generators/convenience.py', 'generate_for_workspace', 1, 1, 3).
python_function('testql/generators/conversation_generator.py', 'trace_from_export', 1, 4, 2).
python_function('testql/generators/page_analyzer.py', '_is_unstable', 1, 2, 2).
python_function('testql/generators/page_analyzer.py', '_css_escape', 1, 1, 1).
python_function('testql/generators/page_analyzer.py', 'pick_selector', 1, 3, 1).
python_function('testql/generators/page_analyzer.py', '_try_testid_selector', 1, 4, 3).
python_function('testql/generators/page_analyzer.py', '_try_id_selector', 1, 3, 3).
python_function('testql/generators/page_analyzer.py', '_try_name_selector', 1, 4, 4).
python_function('testql/generators/page_analyzer.py', '_try_role_aria_selector', 1, 3, 3).
python_function('testql/generators/page_analyzer.py', '_try_input_type_selector', 1, 5, 4).
python_function('testql/generators/page_analyzer.py', '_try_class_selector', 1, 10, 3).
python_function('testql/generators/page_analyzer.py', 'default_input_value', 1, 8, 6).
python_function('testql/generators/page_analyzer.py', 'is_typed_input', 1, 5, 2).
python_function('testql/generators/page_analyzer.py', 'is_clickable', 1, 9, 2).
python_function('testql/generators/page_analyzer.py', '_name_or_selector', 2, 4, 2).
python_function('testql/generators/page_analyzer.py', 'snapshot_to_plan', 1, 2, 4).
python_function('testql/generators/page_analyzer.py', '_create_base_plan', 2, 3, 2).
python_function('testql/generators/page_analyzer.py', '_add_navigate_step', 2, 2, 2).
python_function('testql/generators/page_analyzer.py', '_process_elements', 6, 10, 11).
python_function('testql/generators/page_analyzer.py', '_should_add_input_step', 2, 2, 1).
python_function('testql/generators/page_analyzer.py', '_add_input_step', 3, 1, 4).
python_function('testql/generators/page_analyzer.py', '_should_add_click_step', 2, 2, 1).
python_function('testql/generators/page_analyzer.py', '_add_click_step', 3, 1, 3).
python_function('testql/generators/page_analyzer.py', '_should_add_assert_visible', 2, 3, 2).
python_function('testql/generators/page_analyzer.py', '_add_assert_visible_step', 3, 1, 4).
python_function('testql/generators/page_analyzer.py', '_add_body_assertion', 1, 1, 2).
python_function('testql/generators/page_analyzer.py', '_normalise', 1, 2, 3).
python_function('testql/generators/page_analyzer.py', 'find_replacement', 2, 3, 5).
python_function('testql/generators/page_analyzer.py', '_find_exact_match', 2, 6, 4).
python_function('testql/generators/page_analyzer.py', '_find_fuzzy_match', 2, 9, 4).
python_function('testql/generators/page_analyzer.py', '_build_element_haystack', 1, 4, 5).
python_function('testql/generators/page_analyzer.py', '_hint_from_selector', 1, 7, 2).
python_function('testql/generators/pipeline.py', '_resolve_source', 1, 3, 4).
python_function('testql/generators/pipeline.py', '_resolve_target', 1, 3, 4).
python_function('testql/generators/pipeline.py', 'sorted_sources', 0, 1, 1).
python_function('testql/generators/pipeline.py', 'sorted_targets', 0, 1, 1).
python_function('testql/generators/pipeline.py', 'run', 0, 5, 12).
python_function('testql/generators/pipeline.py', 'write', 2, 5, 9).
python_function('testql/generators/sources/__init__.py', '_get_config_source', 0, 1, 0).
python_function('testql/generators/sources/__init__.py', 'get_source', 1, 5, 4).
python_function('testql/generators/sources/__init__.py', 'available_sources', 0, 1, 3).
python_function('testql/generators/sources/config_source.py', '_load_file', 1, 4, 5).
python_function('testql/generators/sources/config_source.py', '_load_includes', 2, 6, 7).
python_function('testql/generators/sources/config_source.py', '_extract_phony_targets', 1, 3, 3).
python_function('testql/generators/sources/config_source.py', '_extract_target_commands', 2, 13, 6).
python_function('testql/generators/sources/config_source.py', '_parse_makefile', 2, 4, 7).
python_function('testql/generators/sources/config_source.py', '_parse_taskfile', 1, 5, 6).
python_function('testql/generators/sources/config_source.py', '_parse_docker_compose', 1, 4, 3).
python_function('testql/generators/sources/config_source.py', '_select_parser_for_file', 1, 5, 1).
python_function('testql/generators/sources/config_source.py', '_auto_detect_parser', 1, 4, 0).
python_function('testql/generators/sources/config_source.py', '_parse_targets', 2, 5, 6).
python_function('testql/generators/sources/config_source.py', '_parse_buf_yaml', 1, 1, 0).
python_function('testql/generators/sources/config_source.py', '_filter_commands', 2, 14, 12).
python_function('testql/generators/sources/graphql_source.py', '_load_sdl', 1, 5, 6).
python_function('testql/generators/sources/graphql_source.py', '_type_to_query', 2, 3, 4).
python_function('testql/generators/sources/graphql_source.py', '_is_smoke_target', 1, 3, 2).
python_function('testql/generators/sources/openapi_source.py', '_load_spec', 1, 6, 5).
python_function('testql/generators/sources/openapi_source.py', '_pick_success_status', 1, 7, 6).
python_function('testql/generators/sources/openapi_source.py', '_operation_to_step', 3, 3, 5).
python_function('testql/generators/sources/openapi_source.py', '_iter_operations', 1, 6, 3).
python_function('testql/generators/sources/page_source.py', 'extract_elements_from_page', 1, 1, 1).
python_function('testql/generators/sources/page_source.py', '_path_of', 1, 2, 1).
python_function('testql/generators/sources/page_source.py', '_origin', 1, 3, 1).
python_function('testql/generators/sources/proto_source.py', '_load_proto_text', 1, 5, 6).
python_function('testql/generators/sources/proto_source.py', '_sample_value_for', 1, 1, 1).
python_function('testql/generators/sources/proto_source.py', '_sample_fields_blob', 1, 3, 3).
python_function('testql/generators/sources/proto_source.py', '_message_to_step', 2, 2, 3).
python_function('testql/generators/sources/sql_source.py', '_load_sql_text', 1, 5, 6).
python_function('testql/generators/sources/sql_source.py', '_crud_steps', 2, 1, 2).
python_function('testql/generators/sources/sql_source.py', '_schema_fixture_from_ddl', 1, 2, 2).
python_function('testql/generators/sources/ui_source.py', '_load_html', 1, 5, 6).
python_function('testql/generators/sources/ui_source.py', '_navigate_step', 1, 2, 1).
python_function('testql/generators/sources/ui_source.py', '_input_steps', 1, 2, 2).
python_function('testql/generators/sources/ui_source.py', '_button_steps', 1, 2, 3).
python_function('testql/generators/targets/__init__.py', 'get_target', 1, 2, 3).
python_function('testql/generators/targets/__init__.py', 'available_targets', 0, 1, 2).
python_function('testql/generators/targets/pytest_target.py', '_safe_ident', 2, 5, 4).
python_function('testql/generators/targets/pytest_target.py', '_step_summary', 1, 3, 2).
python_function('testql/generators/targets/pytest_target.py', '_emit_test', 2, 2, 3).
python_function('testql/integrations/planfile_hook.py', 'create_test_failure_ticket', 2, 6, 5).
python_function('testql/integrations/planfile_hook.py', 'create_individual_button_tickets', 2, 9, 8).
python_function('testql/interpreter/__init__.py', 'main', 0, 8, 18).
python_function('testql/interpreter/_api_runner.py', '_resolve_length', 2, 4, 5).
python_function('testql/interpreter/_api_runner.py', '_navigate_step', 2, 4, 3).
python_function('testql/interpreter/_api_runner.py', '_navigate_json_path', 2, 4, 4).
python_function('testql/interpreter/_api_runner.py', '_navigate_bracket_notation', 2, 3, 3).
python_function('testql/interpreter/_api_runner.py', '_navigate_dot_notation', 2, 3, 2).
python_function('testql/interpreter/_api_runner.py', '_navigate_dot_part', 2, 4, 4).
python_function('testql/interpreter/_api_runner.py', '_handle_length_virtual', 1, 2, 2).
python_function('testql/interpreter/_api_runner.py', '_handle_mixed_notation', 2, 3, 4).
python_function('testql/interpreter/_parser.py', 'parse_oql', 2, 5, 9).
python_function('testql/interpreter/_testtoon_parser.py', 'validate_testtoon', 1, 2, 2).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_config', 3, 4, 7).
python_function('testql/interpreter/_testtoon_parser.py', '_append_api_asserts', 3, 9, 4).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_api', 3, 4, 7).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_navigate', 3, 3, 4).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_encoder', 3, 7, 7).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_select', 3, 5, 8).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_assert', 3, 9, 4).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_steps', 3, 3, 5).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_flow', 3, 14, 9).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_oql', 3, 2, 3).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_wait', 3, 2, 4).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_include', 3, 2, 3).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_record', 3, 3, 3).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_validate', 3, 6, 8).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_commands', 3, 6, 6).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_dom_audit_buttons', 3, 6, 5).
python_function('testql/interpreter/_testtoon_parser.py', '_shell_expected_exit', 1, 7, 6).
python_function('testql/interpreter/_testtoon_parser.py', '_shell_timeout_ms', 2, 5, 6).
python_function('testql/interpreter/_testtoon_parser.py', '_quote_shell_command', 1, 1, 1).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_shell', 3, 6, 8).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_modbus', 3, 7, 8).
python_function('testql/interpreter/_testtoon_parser.py', '_expand_generic', 3, 4, 5).
python_function('testql/interpreter/_testtoon_parser.py', 'testtoon_to_oql', 2, 2, 4).
python_function('testql/interpreter/_validation.py', '_resolve_target', 2, 11, 8).
python_function('testql/interpreter/converter/core.py', 'convert_oql_to_testtoon', 2, 5, 9).
python_function('testql/interpreter/converter/core.py', 'convert_file', 1, 1, 3).
python_function('testql/interpreter/converter/core.py', 'convert_directory', 1, 4, 7).
python_function('testql/interpreter/converter/dispatcher.py', 'dispatch', 2, 3, 3).
python_function('testql/interpreter/converter/handlers/api.py', 'handle_api', 2, 6, 7).
python_function('testql/interpreter/converter/handlers/assertions.py', 'collect_assert', 2, 9, 5).
python_function('testql/interpreter/converter/handlers/encoder.py', '_encoder_action_fields', 2, 5, 4).
python_function('testql/interpreter/converter/handlers/encoder.py', '_advance_past_wait', 2, 4, 2).
python_function('testql/interpreter/converter/handlers/encoder.py', 'handle_encoder', 2, 3, 8).
python_function('testql/interpreter/converter/handlers/flow.py', 'handle_flow', 2, 3, 6).
python_function('testql/interpreter/converter/handlers/include.py', 'handle_include', 2, 1, 2).
python_function('testql/interpreter/converter/handlers/navigate.py', 'handle_navigate', 2, 6, 7).
python_function('testql/interpreter/converter/handlers/record.py', 'handle_record_start', 2, 1, 2).
python_function('testql/interpreter/converter/handlers/record.py', 'handle_record_stop', 2, 1, 1).
python_function('testql/interpreter/converter/handlers/select.py', 'handle_select', 2, 3, 8).
python_function('testql/interpreter/converter/handlers/unknown.py', 'handle_unknown', 2, 3, 4).
python_function('testql/interpreter/converter/handlers/wait.py', 'handle_wait', 2, 4, 6).
python_function('testql/interpreter/converter/parsers.py', 'parse_api_args', 1, 5, 6).
python_function('testql/interpreter/converter/parsers.py', 'parse_meta_from_args', 1, 4, 6).
python_function('testql/interpreter/converter/parsers.py', 'parse_target_from_args', 1, 4, 4).
python_function('testql/interpreter/converter/parsers.py', 'parse_commands', 1, 5, 7).
python_function('testql/interpreter/converter/parsers.py', 'detect_scenario_type', 1, 11, 3).
python_function('testql/interpreter/converter/parsers.py', 'extract_scenario_name', 2, 6, 6).
python_function('testql/interpreter/converter/renderer.py', 'build_config_section', 1, 6, 5).
python_function('testql/interpreter/converter/renderer.py', '_render_section_header', 1, 3, 2).
python_function('testql/interpreter/converter/renderer.py', 'render_sections', 1, 7, 7).
python_function('testql/interpreter/converter/renderer.py', 'build_header', 2, 1, 0).
python_function('testql/interpreter/dom_scan_formatters.py', 'to_json', 2, 1, 2).
python_function('testql/interpreter/dom_scan_formatters.py', 'to_toon', 1, 7, 4).
python_function('testql/interpreter/dom_scan_formatters.py', 'to_text', 1, 13, 3).
python_function('testql/interpreter/dom_scan_formatters.py', 'to_text_audit', 1, 4, 2).
python_function('testql/interpreter/dom_scanner.py', '_aom_node_to_element', 2, 2, 3).
python_function('testql/interpreter/dom_scanner.py', '_flatten_aom', 3, 2, 3).
python_function('testql/interpreter/testtoon_parser.py', '_strip_quoted_regions', 1, 6, 2).
python_function('testql/interpreter/testtoon_parser.py', '_detect_separator', 1, 2, 1).
python_function('testql/interpreter/testtoon_parser.py', '_split_quoted', 3, 9, 2).
python_function('testql/interpreter/testtoon_parser.py', '_parse_inline_array', 1, 2, 2).
python_function('testql/interpreter/testtoon_parser.py', '_parse_inline_dict', 1, 3, 3).
python_function('testql/interpreter/testtoon_parser.py', '_parse_value', 1, 8, 7).
python_function('testql/interpreter/testtoon_parser.py', '_make_section', 1, 4, 5).
python_function('testql/interpreter/testtoon_parser.py', '_make_mapping_section', 1, 1, 2).
python_function('testql/interpreter/testtoon_parser.py', '_make_data_row', 2, 2, 6).
python_function('testql/interpreter/testtoon_parser.py', '_make_mapping_row', 1, 4, 4).
python_function('testql/interpreter/testtoon_parser.py', 'parse_testtoon', 2, 2, 4).
python_function('testql/interpreter/testtoon_parser.py', '_process_line', 4, 11, 10).
python_function('testql/interpreter/testtoon_parser.py', '_is_meta_line', 1, 1, 1).
python_function('testql/interpreter/testtoon_parser.py', '_process_meta_line', 2, 2, 4).
python_function('testql/interpreter/testtoon_parser.py', '_is_comment', 1, 1, 1).
python_function('testql/interpreter/testtoon_parser.py', '_try_parse_section_header', 1, 4, 3).
python_function('testql/interpreter/testtoon_parser.py', '_should_end_section', 2, 2, 1).
python_function('testql/interpreter/testtoon_parser.py', '_is_bare_command', 2, 2, 1).
python_function('testql/interpreter/testtoon_parser.py', '_add_row_to_section', 2, 5, 4).
python_function('testql/interpreter/testtoon_parser.py', '_add_bare_commands_section', 2, 3, 4).
python_function('testql/interpreter/testtoon_parser.py', '_find_commands_insert_position', 1, 3, 1).
python_function('testql/ir_runner/assertion_eval.py', '_next_segment', 2, 6, 6).
python_function('testql/ir_runner/assertion_eval.py', 'navigate', 2, 3, 2).
python_function('testql/ir_runner/assertion_eval.py', '_op_contains', 2, 2, 0).
python_function('testql/ir_runner/assertion_eval.py', '_op_matches', 2, 3, 2).
python_function('testql/ir_runner/assertion_eval.py', 'evaluate', 2, 3, 5).
python_function('testql/ir_runner/assertion_eval.py', 'evaluate_all', 2, 2, 1).
python_function('testql/ir_runner/engine.py', 'load_plan', 1, 4, 6).
python_function('testql/ir_runner/engine.py', '_apply_captures', 3, 6, 5).
python_function('testql/ir_runner/engine.py', '_run_step', 2, 4, 8).
python_function('testql/ir_runner/engine.py', 'run_plan', 1, 1, 2).
python_function('testql/ir_runner/executors/__init__.py', 'get_executor', 1, 1, 1).
python_function('testql/ir_runner/executors/__init__.py', 'register', 2, 1, 0).
python_function('testql/ir_runner/executors/__init__.py', 'supported_kinds', 0, 1, 2).
python_function('testql/ir_runner/executors/api.py', '_resolve_url', 2, 2, 1).
python_function('testql/ir_runner/executors/api.py', '_parse_response', 1, 3, 1).
python_function('testql/ir_runner/executors/api.py', '_do_request', 4, 4, 7).
python_function('testql/ir_runner/executors/api.py', '_payload', 3, 1, 0).
python_function('testql/ir_runner/executors/api.py', 'execute', 2, 4, 8).
python_function('testql/ir_runner/executors/assert_json.py', '_last_payload', 1, 1, 0).
python_function('testql/ir_runner/executors/assert_json.py', 'execute', 2, 5, 5).
python_function('testql/ir_runner/executors/base.py', 'step_label', 2, 2, 0).
python_function('testql/ir_runner/executors/base.py', '_aggregate_assertion_status', 2, 3, 0).
python_function('testql/ir_runner/executors/base.py', '_compose_message', 2, 3, 1).
python_function('testql/ir_runner/executors/base.py', 'assemble_result', 5, 5, 6).
python_function('testql/ir_runner/executors/base.py', 'error_result', 2, 1, 2).
python_function('testql/ir_runner/executors/base.py', 'skipped_result', 2, 1, 1).
python_function('testql/ir_runner/executors/encoder.py', '_request_body', 3, 5, 2).
python_function('testql/ir_runner/executors/encoder.py', '_do_call', 3, 5, 7).
python_function('testql/ir_runner/executors/encoder.py', 'execute', 2, 5, 9).
python_function('testql/ir_runner/executors/graphql.py', '_post_graphql', 3, 4, 7).
python_function('testql/ir_runner/executors/graphql.py', '_resolve_endpoint', 2, 2, 1).
python_function('testql/ir_runner/executors/graphql.py', 'execute', 2, 5, 9).
python_function('testql/ir_runner/executors/gui.py', 'execute', 2, 2, 2).
python_function('testql/ir_runner/executors/nl.py', 'execute', 2, 1, 2).
python_function('testql/ir_runner/executors/proto.py', '_resolve_source', 2, 3, 5).
python_function('testql/ir_runner/executors/proto.py', '_instance_tuples', 1, 2, 3).
python_function('testql/ir_runner/executors/proto.py', '_run_check', 3, 6, 3).
python_function('testql/ir_runner/executors/proto.py', 'execute', 2, 5, 10).
python_function('testql/ir_runner/executors/shell.py', '_aggregate_status', 2, 4, 0).
python_function('testql/ir_runner/executors/shell.py', '_payload', 3, 1, 0).
python_function('testql/ir_runner/executors/shell.py', 'execute', 2, 5, 8).
python_function('testql/ir_runner/executors/sql.py', '_get_connection', 1, 2, 3).
python_function('testql/ir_runner/executors/sql.py', '_classify', 1, 2, 3).
python_function('testql/ir_runner/executors/sql.py', '_execute_query', 2, 5, 6).
python_function('testql/ir_runner/executors/sql.py', 'execute', 2, 3, 7).
python_function('testql/ir_runner/executors/unit.py', '_payload', 3, 1, 0).
python_function('testql/ir_runner/executors/unit.py', 'execute', 2, 6, 9).
python_function('testql/ir_runner/interpolation.py', 'interp_value', 2, 6, 4).
python_function('testql/mcp/server.py', '_require_fastmcp', 0, 2, 1).
python_function('testql/mcp/server.py', '_normalize_run_payload', 1, 4, 6).
python_function('testql/mcp/server.py', 'create_server', 1, 1, 1).
python_function('testql/mcp/server.py', 'run_server', 0, 1, 2).
python_function('testql/meta/confidence_scorer.py', '_is_llm_resolved', 1, 3, 1).
python_function('testql/meta/confidence_scorer.py', '_score_assertions', 1, 3, 1).
python_function('testql/meta/confidence_scorer.py', '_score_typed', 1, 2, 1).
python_function('testql/meta/confidence_scorer.py', '_score_step', 1, 3, 8).
python_function('testql/meta/confidence_scorer.py', 'score_plan', 1, 4, 4).
python_function('testql/meta/coverage_analyzer.py', '_load_text', 1, 4, 4).
python_function('testql/meta/coverage_analyzer.py', '_load_yaml', 1, 3, 3).
python_function('testql/meta/coverage_analyzer.py', '_build_report', 3, 1, 4).
python_function('testql/meta/coverage_analyzer.py', '_openapi_endpoints', 1, 6, 7).
python_function('testql/meta/coverage_analyzer.py', '_plan_endpoints', 1, 3, 1).
python_function('testql/meta/coverage_analyzer.py', 'coverage_vs_openapi', 2, 1, 4).
python_function('testql/meta/coverage_analyzer.py', '_sql_tables', 1, 2, 1).
python_function('testql/meta/coverage_analyzer.py', '_plan_sql_tables', 1, 3, 4).
python_function('testql/meta/coverage_analyzer.py', '_extract_table_names', 1, 3, 4).
python_function('testql/meta/coverage_analyzer.py', 'coverage_vs_sql', 2, 1, 5).
python_function('testql/meta/coverage_analyzer.py', '_proto_messages', 1, 2, 0).
python_function('testql/meta/coverage_analyzer.py', '_plan_proto_messages', 1, 4, 1).
python_function('testql/meta/coverage_analyzer.py', 'coverage_vs_proto', 2, 1, 5).
python_function('testql/meta/coverage_analyzer.py', 'analyze', 3, 2, 4).
python_function('testql/meta/mutator.py', '_flipped_op', 1, 1, 1).
python_function('testql/meta/mutator.py', 'mutations_flip_assertion_op', 1, 5, 5).
python_function('testql/meta/mutator.py', '_next_status', 1, 2, 0).
python_function('testql/meta/mutator.py', '_tweak_status_mutation', 3, 4, 3).
python_function('testql/meta/mutator.py', 'mutations_tweak_status', 1, 4, 4).
python_function('testql/meta/mutator.py', 'mutations_remove_step', 1, 2, 4).
python_function('testql/meta/mutator.py', '_scrambled', 1, 5, 1).
python_function('testql/meta/mutator.py', 'mutations_scramble_assertion_value', 1, 6, 5).
python_function('testql/meta/mutator.py', 'mutate', 1, 2, 2).
python_function('testql/meta/mutator.py', 'run_mutation_test', 2, 4, 4).
python_function('testql/meta/self_test.py', 'generate_self_test_plan', 1, 1, 2).
python_function('testql/meta/self_test.py', 'run_self_test', 1, 1, 6).
python_function('testql/openapi_generator.py', '_extract_path_params', 1, 4, 3).
python_function('testql/openapi_generator.py', '_extract_ep_params', 2, 7, 4).
python_function('testql/openapi_generator.py', 'generate_openapi_spec', 3, 1, 3).
python_function('testql/openapi_generator.py', 'generate_contract_tests_from_spec', 2, 1, 2).
python_function('testql/report_generator.py', '_adapt_test_entry', 1, 5, 5).
python_function('testql/report_generator.py', 'generate_report', 2, 3, 8).
python_function('testql/reporters/console.py', 'report_console', 1, 6, 4).
python_function('testql/reporters/json_reporter.py', 'report_json', 1, 2, 3).
python_function('testql/reporters/junit.py', 'report_junit', 2, 1, 2).
python_function('testql/results/analyzer.py', 'inspect_source', 3, 1, 3).
python_function('testql/results/analyzer.py', 'analyze_topology', 3, 2, 17).
python_function('testql/results/analyzer.py', '_check_confidence', 1, 2, 1).
python_function('testql/results/analyzer.py', '_check_nodes', 1, 2, 2).
python_function('testql/results/analyzer.py', '_check_edges', 1, 2, 2).
python_function('testql/results/analyzer.py', '_check_interfaces', 1, 4, 2).
python_function('testql/results/analyzer.py', '_check_evidence', 1, 4, 2).
python_function('testql/results/analyzer.py', '_crawl_checks', 2, 3, 3).
python_function('testql/results/analyzer.py', '_check_link_statuses', 2, 14, 6).
python_function('testql/results/analyzer.py', '_check_asset_statuses', 2, 12, 6).
python_function('testql/results/analyzer.py', '_head_check_urls', 1, 3, 3).
python_function('testql/results/analyzer.py', '_sitemap_checks', 1, 5, 5).
python_function('testql/results/analyzer.py', '_browser_checks', 2, 3, 4).
python_function('testql/results/analyzer.py', '_check_browser_render', 2, 3, 2).
python_function('testql/results/analyzer.py', '_check_browser_console', 2, 3, 3).
python_function('testql/results/analyzer.py', '_check_browser_network', 2, 3, 3).
python_function('testql/results/analyzer.py', '_sitemap_node', 1, 3, 1).
python_function('testql/results/analyzer.py', '_check_sitemap_crawl', 2, 1, 2).
python_function('testql/results/analyzer.py', '_check_sitemap_broken', 2, 10, 3).
python_function('testql/results/analyzer.py', '_check_sitemap_duplicates', 2, 7, 9).
python_function('testql/results/analyzer.py', '_web_checks', 1, 2, 6).
python_function('testql/results/analyzer.py', '_page_node', 1, 3, 1).
python_function('testql/results/analyzer.py', '_check_web_status', 2, 3, 2).
python_function('testql/results/analyzer.py', '_check_web_title', 2, 3, 4).
python_function('testql/results/analyzer.py', '_check_web_links', 2, 8, 5).
python_function('testql/results/analyzer.py', '_check_web_assets', 2, 3, 3).
python_function('testql/results/analyzer.py', '_check_web_forms', 2, 3, 3).
python_function('testql/results/analyzer.py', '_status_code', 1, 3, 2).
python_function('testql/results/analyzer.py', '_looks_like_spa', 1, 4, 4).
python_function('testql/results/analyzer.py', '_findings_from_checks', 1, 4, 5).
python_function('testql/results/analyzer.py', '_actions_from_findings', 2, 4, 6).
python_function('testql/results/analyzer.py', '_status_from_checks', 1, 5, 1).
python_function('testql/results/analyzer.py', '_likely_cause', 1, 1, 1).
python_function('testql/results/analyzer.py', '_action_type', 1, 14, 0).
python_function('testql/results/analyzer.py', '_action_summary', 1, 1, 0).
python_function('testql/results/analyzer.py', '_topology_id', 1, 1, 1).
python_function('testql/results/analyzer.py', '_run_id', 1, 1, 1).
python_function('testql/results/analyzer.py', '_safe', 1, 4, 4).
python_function('testql/results/artifacts.py', 'write_inspection_artifacts', 4, 1, 13).
python_function('testql/results/artifacts.py', '_write_group', 3, 2, 3).
python_function('testql/results/artifacts.py', '_render_summary_md', 4, 10, 7).
python_function('testql/results/artifacts.py', '_metadata', 4, 2, 4).
python_function('testql/results/serializers.py', 'render_result_envelope', 2, 1, 2).
python_function('testql/results/serializers.py', 'render_refactor_plan', 2, 1, 2).
python_function('testql/results/serializers.py', 'render_inspection', 4, 2, 3).
python_function('testql/results/serializers.py', '_render_data', 2, 7, 6).
python_function('testql/results/serializers.py', '_render_toon', 1, 6, 5).
python_function('testql/results/serializers.py', '_render_nlp', 2, 1, 2).
python_function('testql/results/serializers.py', '_render_nlp_dict', 2, 5, 4).
python_function('testql/results/serializers.py', '_clean', 1, 1, 3).
python_function('testql/runner.py', 'parse_line', 1, 9, 8).
python_function('testql/runner.py', 'parse_script', 1, 3, 2).
python_function('testql/runner.py', 'main', 0, 10, 14).
python_function('testql/sumd_generator.py', 'generate_sumd', 2, 4, 10).
python_function('testql/sumd_generator.py', '_header_section', 2, 1, 1).
python_function('testql/sumd_generator.py', '_metadata_section', 2, 1, 0).
python_function('testql/sumd_generator.py', '_architecture_section', 0, 1, 0).
python_function('testql/sumd_generator.py', '_doql_declaration_section', 3, 7, 1).
python_function('testql/sumd_generator.py', '_api_contract_section', 1, 6, 4).
python_function('testql/sumd_generator.py', '_workflows_table_section', 1, 5, 2).
python_function('testql/sumd_generator.py', '_configuration_section', 3, 2, 1).
python_function('testql/sumd_generator.py', '_llm_suggestions_section', 1, 4, 3).
python_function('testql/sumd_generator.py', '_workflow_snippet', 4, 4, 1).
python_function('testql/sumd_generator.py', 'save_sumd', 3, 2, 2).
python_function('testql/sumd_parser.py', '_parse_block_interfaces', 1, 3, 5).
python_function('testql/sumd_parser.py', '_parse_api_interfaces', 1, 8, 7).
python_function('testql/sumd_parser.py', 'parse_sumd_file', 1, 1, 2).
python_function('testql/toon_parser.py', 'parse_toon_file', 1, 1, 2).
python_function('testql/topology/builder.py', 'build_topology', 3, 1, 2).
python_function('testql/topology/builder.py', '_source_location', 1, 2, 1).
python_function('testql/topology/builder.py', '_root_metadata', 1, 3, 2).
python_function('testql/topology/builder.py', '_default_trace', 1, 3, 1).
python_function('testql/topology/builder.py', '_safe_id', 1, 4, 5).
python_function('testql/topology/builder.py', '_protocol_for_interface', 1, 1, 1).
python_function('testql/topology/builder.py', '_protocol_for_evidence', 1, 2, 1).
python_function('testql/topology/serializers.py', 'render_topology', 3, 4, 5).
python_function('testql/topology/serializers.py', '_render_toon', 1, 5, 5).
python_function('testql/topology/serializers.py', '_source_location', 1, 2, 3).
python_function('testql/topology/sitemap.py', 'build_sitemap', 3, 5, 6).
python_function('testql/topology/sitemap.py', '_extract_internal_links', 2, 4, 1).
python_function('testql/topology/sitemap.py', '_resolve_urls', 2, 4, 3).
python_function('testql/topology/sitemap.py', '_crawl_subpage', 3, 4, 7).
python_function('testql/topology/sitemap.py', '_is_html', 2, 2, 1).
python_function('testql/topology/sitemap.py', '_add_sitemap_nodes', 4, 2, 5).
python_function('testql/topology/sitemap.py', '_looks_textual', 1, 2, 2).
python_function('testql/topology/sitemap.py', '_parse_subpage', 1, 2, 2).
python_function('tests/conftest.py', 'project_root', 0, 1, 1).
python_function('tests/conftest.py', 'testql_pkg_dir', 0, 1, 1).
python_function('tests/conftest.py', 'project_root_manifest', 0, 1, 2).
python_function('tests/conftest.py', 'testql_pkg_manifest', 0, 1, 2).
python_function('tests/conftest.py', 'pytest_configure', 1, 1, 1).
python_function('tests/conftest.py', 'pytest_collection_modifyitems', 2, 4, 6).
python_function('tests/fixtures/discovery/python_pkg/sample_api/main.py', 'health', 0, 1, 1).
python_function('tests/test_browser_discovery.py', 'mock_playwright', 0, 1, 2).
python_function('tests/test_browser_discovery.py', 'test_playwright_probe_collects_console_and_network', 1, 9, 4).
python_function('tests/test_conversation_live_llm.py', 'test_live_llm_reply_for_real_api', 0, 5, 5).
python_function('tests/test_conversation_live_llm.py', 'test_conversation_runner_with_live_llm_smoke', 0, 4, 10).
python_function('tests/test_conversation_nlp2dsl.py', 'test_runner_with_fake_client', 0, 3, 7).
python_function('tests/test_detectors.py', '_write', 3, 1, 2).
python_function('tests/test_echo.py', 'write_toon', 3, 1, 2).
python_function('tests/test_encoder_routes.py', 'test_normalize_legacy_test_path', 0, 2, 2).
python_function('tests/test_encoder_routes.py', 'test_normalize_legacy_view_path', 0, 2, 2).
python_function('tests/test_encoder_routes.py', 'test_normalize_testql_prefixed_path', 0, 2, 2).
python_function('tests/test_encoder_routes.py', 'test_normalize_passthrough_diagnostics_path', 0, 2, 2).
python_function('tests/test_encoder_routes.py', 'test_normalize_testtoon_path', 0, 2, 1).
python_function('tests/test_encoder_routes.py', 'test_resolve_new_format', 0, 4, 3).
python_function('tests/test_generate_from_page_cli.py', '_write_elements', 1, 1, 2).
python_function('tests/test_ir_runner_captures.py', '_plan', 0, 1, 3).
python_function('tests/test_ir_runner_engine.py', '_plan', 0, 1, 3).
python_function('tests/test_ir_runner_interpolation.py', '_store', 0, 1, 1).
python_function('tests/test_meta_mutator.py', '_sample_plan', 0, 1, 4).
python_function('tests/test_network_discovery.py', 'test_discover_url_requires_scan_network_for_match', 1, 6, 3).
python_function('tests/test_network_discovery.py', 'test_topology_url_builds_page_schema_nodes', 1, 8, 3).
python_function('tests/test_network_discovery.py', 'test_inspect_url_nlp_passes_with_mocked_network', 1, 11, 3).
python_function('tests/test_network_discovery.py', 'test_inspect_cli_url_json_with_scan_network', 1, 4, 5).
python_function('tests/test_network_discovery.py', 'test_inspect_url_reports_http_failure', 1, 5, 3).
python_function('tests/test_network_discovery.py', 'test_inspect_url_builds_sitemap_with_mocked_network', 1, 9, 4).
python_function('tests/test_network_discovery.py', 'test_inspect_spa_without_anchors_skips_web_links', 1, 7, 4).
python_function('tests/test_nl_intent_recognizer.py', 'pl', 0, 1, 1).
python_function('tests/test_nl_intent_recognizer.py', 'en', 0, 1, 1).
python_function('tests/test_nl_scenarios_e2e.py', '_scenario_files', 0, 1, 2).
python_function('tests/test_nl_scenarios_e2e.py', 'scenario', 1, 1, 2).
python_function('tests/test_openapi_generator.py', '_make_ep', 11, 4, 2).
python_function('tests/test_plugin_registry.py', '_install_module', 2, 2, 3).
python_function('tests/test_proto_graphql_scenarios_e2e.py', '_proto_scenarios', 0, 1, 2).
python_function('tests/test_proto_graphql_scenarios_e2e.py', '_graphql_scenarios', 0, 1, 2).
python_function('tests/test_proto_graphql_scenarios_e2e.py', 'proto_scenario', 1, 1, 2).
python_function('tests/test_proto_graphql_scenarios_e2e.py', 'graphql_scenario', 1, 1, 2).
python_function('tests/test_report_generator.py', '_make_report', 0, 1, 4).
python_function('tests/test_reporters.py', 'make_result', 6, 4, 1).
python_function('tests/test_reporters.py', 'make_step', 4, 1, 1).
python_function('tests/test_run_cmd.py', '_install_fake_interpreter', 1, 1, 2).
python_function('tests/test_run_cmd.py', '_mk_scenario', 1, 1, 1).
python_function('tests/test_run_ir_cli.py', '_write', 3, 1, 1).
python_function('tests/test_smoke_decisions.py', '_load', 1, 1, 2).
python_function('tests/test_smoke_decisions.py', '_schema', 0, 1, 2).
python_function('tests/test_smoke_decisions.py', '_check_required', 2, 3, 1).
python_function('tests/test_smoke_decisions.py', '_check_decision', 2, 2, 1).
python_function('tests/test_smoke_decisions.py', '_check_metrics', 2, 3, 1).
python_function('tests/test_smoke_decisions.py', '_check_numerics', 1, 4, 3).
python_function('tests/test_smoke_decisions.py', '_check_next_actions', 1, 6, 3).
python_function('tests/test_smoke_decisions.py', '_validate', 2, 1, 5).
python_function('tests/test_sql_scenarios_e2e.py', '_scenarios', 0, 1, 2).
python_function('tests/test_sql_scenarios_e2e.py', 'scenario', 1, 1, 2).
python_function('tests/test_suite_cmd_helpers.py', '_collect_test_files', 4, 5, 5).
python_function('tests/test_targets.py', '_sample_plan', 0, 1, 4).
python_function('tests/test_topology_generator.py', '_manifest', 0, 2, 6).
python_function('tests/test_validation.py', 'interp', 0, 1, 2).
python_function('tests/test_validation.py', '_seed_shell', 4, 1, 0).

% ── Python Classes ───────────────────────────────────────
python_class('TODO/testtoon_parser.py', 'Section').
python_method('Section', 'to_dicts', 0, 1, 0).
python_method('Section', 'validate', 0, 3, 2).
python_class('test_autoloop_mcp.py', 'C').
python_class('test_manifest_and_generators.py', 'Colors').
python_class('test_manifest_and_generators.py', 'ManifestProbeTester').
python_method('ManifestProbeTester', 'run_all', 0, 1, 3).
python_method('ManifestProbeTester', '_test_probe', 2, 4, 9).
python_class('test_manifest_and_generators.py', 'GeneratorTester').
python_method('GeneratorTester', 'run_all', 0, 1, 5).
python_method('GeneratorTester', '_test_api_generator', 0, 5, 10).
python_method('GeneratorTester', '_test_python_test_generator', 0, 3, 9).
python_method('GeneratorTester', '_test_scenario_generator', 0, 3, 10).
python_method('GeneratorTester', '_test_round_trip', 0, 6, 6).
python_class('test_manifest_and_generators.py', 'MCPWindsurfChecker').
python_method('MCPWindsurfChecker', 'run_all', 0, 1, 5).
python_method('MCPWindsurfChecker', '_check_cli', 0, 3, 3).
python_method('MCPWindsurfChecker', '_check_json_output', 0, 6, 8).
python_method('MCPWindsurfChecker', '_check_discover_command', 0, 4, 5).
python_method('MCPWindsurfChecker', '_check_generate_command', 0, 5, 9).
python_class('testql/_base_fallback.py', 'StepStatus').
python_class('testql/_base_fallback.py', 'StepResult').
python_class('testql/_base_fallback.py', 'ScriptResult').
python_method('ScriptResult', 'passed', 0, 3, 1).
python_method('ScriptResult', 'failed', 0, 3, 1).
python_method('ScriptResult', 'summary', 0, 2, 1).
python_class('testql/_base_fallback.py', 'VariableStore').
python_method('VariableStore', '__init__', 1, 1, 1).
python_method('VariableStore', 'set', 2, 1, 0).
python_method('VariableStore', 'get', 2, 1, 1).
python_method('VariableStore', 'has', 1, 1, 0).
python_method('VariableStore', 'all', 0, 1, 1).
python_method('VariableStore', 'clear', 0, 1, 1).
python_method('VariableStore', 'interpolate', 1, 1, 4).
python_class('testql/_base_fallback.py', 'InterpreterOutput').
python_method('InterpreterOutput', '__init__', 1, 1, 0).
python_method('InterpreterOutput', 'emit', 1, 2, 2).
python_method('InterpreterOutput', 'info', 1, 1, 1).
python_method('InterpreterOutput', 'ok', 1, 1, 1).
python_method('InterpreterOutput', 'fail', 1, 1, 1).
python_method('InterpreterOutput', 'warn', 1, 1, 1).
python_method('InterpreterOutput', 'error', 1, 1, 1).
python_method('InterpreterOutput', 'step', 2, 1, 1).
python_class('testql/_base_fallback.py', 'BaseInterpreter').
python_method('BaseInterpreter', '__init__', 3, 1, 2).
python_method('BaseInterpreter', 'parse', 2, 1, 0).
python_method('BaseInterpreter', 'execute', 1, 1, 0).
python_method('BaseInterpreter', 'run', 2, 1, 3).
python_method('BaseInterpreter', 'run_file', 1, 1, 3).
python_method('BaseInterpreter', 'strip_comments', 1, 3, 3).
python_class('testql/_base_fallback.py', 'EventBridge').
python_method('EventBridge', '__init__', 1, 1, 0).
python_method('EventBridge', 'connect', 0, 2, 1).
python_method('EventBridge', 'disconnect', 0, 3, 1).
python_method('EventBridge', 'send_event', 2, 4, 7).
python_method('EventBridge', 'connected', 0, 1, 0).
python_class('testql/adapters/base.py', 'DSLDetectionResult').
python_class('testql/adapters/base.py', 'ValidationIssue').
python_class('testql/adapters/base.py', 'BaseDSLAdapter').
python_method('BaseDSLAdapter', 'detect', 1, 1, 0).
python_method('BaseDSLAdapter', 'parse', 1, 1, 0).
python_method('BaseDSLAdapter', 'render', 1, 1, 0).
python_method('BaseDSLAdapter', 'validate', 1, 1, 0).
python_class('testql/adapters/graphql/graphql_adapter.py', 'GraphQLDSLAdapter').
python_method('GraphQLDSLAdapter', 'detect', 1, 4, 4).
python_method('GraphQLDSLAdapter', 'parse', 1, 1, 3).
python_method('GraphQLDSLAdapter', 'render', 1, 1, 1).
python_class('testql/adapters/graphql/schema_introspection.py', 'TypeDef').
python_method('TypeDef', 'to_dict', 0, 1, 1).
python_class('testql/adapters/graphql/subscription_runner.py', 'SubscriptionPlan').
python_method('SubscriptionPlan', 'to_dict', 0, 1, 1).
python_class('testql/adapters/nl/grammar.py', 'Header').
python_method('Header', 'merged_extra', 0, 2, 1).
python_class('testql/adapters/nl/intent_recognizer.py', 'IntentMatch').
python_class('testql/adapters/nl/llm_fallback.py', 'LLMSuggestion').
python_class('testql/adapters/nl/llm_fallback.py', 'LLMResolver').
python_method('LLMResolver', 'resolve', 2, 1, 0).
python_class('testql/adapters/nl/llm_fallback.py', 'NoOpLLMResolver').
python_method('NoOpLLMResolver', 'resolve', 2, 1, 0).
python_class('testql/adapters/nl/nl_adapter.py', 'NLDSLAdapter').
python_method('NLDSLAdapter', 'detect', 1, 6, 4).
python_method('NLDSLAdapter', 'parse', 1, 3, 8).
python_method('NLDSLAdapter', 'render', 1, 5, 4).
python_method('NLDSLAdapter', '_load_lexicon_safe', 1, 4, 2).
python_class('testql/adapters/nlp2dsl/client.py', 'Nlp2DslResponse').
python_method('Nlp2DslResponse', 'ok', 0, 1, 0).
python_class('testql/adapters/nlp2dsl/client.py', 'Nlp2DslClient').
python_method('Nlp2DslClient', '__init__', 2, 3, 2).
python_method('Nlp2DslClient', '_post', 2, 5, 9).
python_method('Nlp2DslClient', 'chatstart', 1, 2, 1).
python_method('Nlp2DslClient', 'chatmessage', 1, 1, 1).
python_method('Nlp2DslClient', 'runworkflow', 1, 1, 1).
python_method('Nlp2DslClient', 'workflow_from_text', 1, 1, 1).
python_class('testql/adapters/nlp2dsl/live_llm.py', 'LiveLLMProvider').
python_method('LiveLLMProvider', 'from_env', 1, 4, 4).
python_method('LiveLLMProvider', 'reply_for', 1, 3, 3).
python_method('LiveLLMProvider', '_build_prompt', 1, 1, 1).
python_method('LiveLLMProvider', '_chat', 1, 6, 8).
python_method('LiveLLMProvider', '_parse_json_object', 1, 4, 6).
python_class('testql/adapters/nlp2dsl/llm_provider.py', 'LLMProvider').
python_method('LLMProvider', 'reply_for', 1, 1, 0).
python_class('testql/adapters/nlp2dsl/mock_llm.py', 'MockLLMProvider').
python_method('MockLLMProvider', 'reply_for', 1, 6, 1).
python_class('testql/adapters/nlp2dsl/nlp2dsl_adapter.py', 'Nlp2DslAdapter').
python_method('Nlp2DslAdapter', 'detect', 1, 7, 7).
python_method('Nlp2DslAdapter', 'parse', 1, 4, 5).
python_method('Nlp2DslAdapter', 'render', 1, 1, 1).
python_method('Nlp2DslAdapter', 'validate', 1, 6, 4).
python_class('testql/adapters/proto/compatibility.py', 'CompatibilityIssue').
python_class('testql/adapters/proto/compatibility.py', 'CompatibilityReport').
python_method('CompatibilityReport', 'is_compatible', 0, 2, 1).
python_method('CompatibilityReport', 'to_dict', 0, 2, 1).
python_class('testql/adapters/proto/descriptor_loader.py', 'FieldDef').
python_method('FieldDef', 'to_dict', 0, 2, 0).
python_class('testql/adapters/proto/descriptor_loader.py', 'MessageDef').
python_method('MessageDef', 'field_by_name', 1, 3, 0).
python_method('MessageDef', 'field_by_number', 1, 3, 0).
python_method('MessageDef', 'to_dict', 0, 2, 1).
python_class('testql/adapters/proto/descriptor_loader.py', 'ProtoFile').
python_method('ProtoFile', 'message', 1, 3, 0).
python_method('ProtoFile', 'to_dict', 0, 2, 1).
python_class('testql/adapters/proto/message_validator.py', 'ValidationIssue').
python_class('testql/adapters/proto/message_validator.py', 'ValidationResult').
python_method('ValidationResult', 'ok', 0, 2, 1).
python_method('ValidationResult', 'to_dict', 0, 2, 0).
python_class('testql/adapters/proto/proto_adapter.py', 'ProtoDSLAdapter').
python_method('ProtoDSLAdapter', 'detect', 1, 5, 4).
python_method('ProtoDSLAdapter', 'parse', 1, 1, 3).
python_method('ProtoDSLAdapter', 'render', 1, 1, 1).
python_class('testql/adapters/registry.py', 'AdapterRegistry').
python_method('AdapterRegistry', '__init__', 0, 1, 0).
python_method('AdapterRegistry', 'register', 1, 2, 1).
python_method('AdapterRegistry', 'register_plugin', 1, 9, 7).
python_method('AdapterRegistry', 'register_module', 1, 1, 2).
python_method('AdapterRegistry', 'load_plugins', 0, 6, 10).
python_method('AdapterRegistry', 'ensure_plugins_loaded', 0, 2, 1).
python_method('AdapterRegistry', 'unregister', 1, 1, 1).
python_method('AdapterRegistry', 'clear', 0, 1, 1).
python_method('AdapterRegistry', 'get', 1, 1, 1).
python_method('AdapterRegistry', 'all', 0, 1, 2).
python_method('AdapterRegistry', 'by_extension', 1, 5, 7).
python_method('AdapterRegistry', 'detect', 1, 9, 7).
python_class('testql/adapters/scenario_yaml.py', 'ScenarioYamlAdapter').
python_method('ScenarioYamlAdapter', 'detect', 1, 5, 6).
python_method('ScenarioYamlAdapter', 'parse', 1, 3, 5).
python_method('ScenarioYamlAdapter', 'render', 1, 9, 6).
python_class('testql/adapters/sql/ddl_parser.py', 'Column').
python_method('Column', 'to_dict', 0, 2, 0).
python_class('testql/adapters/sql/ddl_parser.py', 'Table').
python_method('Table', 'column', 1, 3, 1).
python_method('Table', 'to_dict', 0, 2, 1).
python_class('testql/adapters/sql/ddl_parser.py', 'ParsedDDL').
python_method('ParsedDDL', 'table', 1, 3, 1).
python_method('ParsedDDL', 'to_dict', 0, 2, 1).
python_class('testql/adapters/sql/dialect_resolver.py', 'SqlglotMissing').
python_class('testql/adapters/sql/fixtures.py', 'ConnectionFixture').
python_method('ConnectionFixture', 'to_fixture', 0, 2, 1).
python_class('testql/adapters/sql/fixtures.py', 'SchemaFixture').
python_method('SchemaFixture', 'add_column', 2, 1, 2).
python_method('SchemaFixture', '_ensure_table', 1, 3, 3).
python_method('SchemaFixture', 'to_fixture', 0, 2, 2).
python_class('testql/adapters/sql/query_parser.py', 'QueryInfo').
python_method('QueryInfo', 'to_dict', 0, 1, 1).
python_class('testql/adapters/sql/sql_adapter.py', 'SqlDSLAdapter').
python_method('SqlDSLAdapter', 'detect', 1, 5, 4).
python_method('SqlDSLAdapter', 'parse', 1, 1, 3).
python_method('SqlDSLAdapter', 'render', 1, 1, 1).
python_class('testql/adapters/testtoon_adapter.py', 'TestToonAdapter').
python_method('TestToonAdapter', 'detect', 1, 9, 7).
python_method('TestToonAdapter', 'parse', 1, 1, 3).
python_method('TestToonAdapter', 'render', 1, 1, 1).
python_class('testql/artifacts/base.py', 'ArtifactCheckResult').
python_class('testql/artifacts/base.py', 'BaseArtifactChecker').
python_method('BaseArtifactChecker', 'check', 1, 1, 0).
python_class('testql/artifacts/email_checker.py', 'EmailArtifactChecker').
python_method('EmailArtifactChecker', 'check', 1, 10, 10).
python_method('EmailArtifactChecker', '_list_messages', 1, 2, 3).
python_class('testql/artifacts/file_checker.py', 'FileArtifactChecker').
python_method('FileArtifactChecker', 'check', 1, 9, 9).
python_class('testql/artifacts/registry.py', 'ArtifactCheckerRegistry').
python_method('ArtifactCheckerRegistry', '__init__', 0, 1, 0).
python_method('ArtifactCheckerRegistry', 'register', 1, 1, 0).
python_method('ArtifactCheckerRegistry', 'check', 1, 2, 3).
python_class('testql/commands/heal_scenario_cmd.py', 'HealReport').
python_method('HealReport', '__post_init__', 0, 2, 0).
python_class('testql/commands/templates/content.py', 'TestContentBuilder').
python_method('TestContentBuilder', 'build', 5, 1, 2).
python_method('TestContentBuilder', '_build_meta_header', 4, 1, 1).
python_method('TestContentBuilder', '_build_standard_vars', 0, 1, 0).
python_method('TestContentBuilder', '_build_gui', 4, 2, 2).
python_method('TestContentBuilder', '_build_api', 4, 1, 1).
python_method('TestContentBuilder', '_build_mixed', 4, 1, 1).
python_method('TestContentBuilder', '_build_performance', 4, 1, 1).
python_method('TestContentBuilder', '_build_workflow', 4, 1, 1).
python_method('TestContentBuilder', '_build_encoder', 4, 1, 1).
python_class('testql/conversation/runner.py', 'TurnTrace').
python_class('testql/conversation/runner.py', 'ConversationRunResult').
python_method('ConversationRunResult', 'to_report_dict', 0, 2, 2).
python_class('testql/conversation/runner.py', 'ConversationRunner').
python_method('ConversationRunner', '__init__', 3, 4, 6).
python_method('ConversationRunner', 'variables', 0, 1, 1).
python_method('ConversationRunner', 'run', 1, 3, 6).
python_method('ConversationRunner', '_apply_plan_config', 1, 9, 7).
python_method('ConversationRunner', '_run_step', 2, 7, 6).
python_method('ConversationRunner', '_run_via_ir', 2, 7, 5).
python_method('ConversationRunner', '_dispatch_nlp2dsl_endpoint', 2, 5, 9).
python_method('ConversationRunner', '_apply_nlp2dsl_mock', 2, 4, 5).
python_method('ConversationRunner', '_determine_nlp2dsl_status', 3, 4, 2).
python_method('ConversationRunner', '_extract_captures', 2, 3, 2).
python_method('ConversationRunner', '_build_captures_dict', 1, 2, 1).
python_method('ConversationRunner', '_run_nlp2dsl', 2, 3, 8).
python_method('ConversationRunner', '_run_turn', 2, 4, 5).
python_method('ConversationRunner', '_run_artifact', 2, 4, 6).
python_method('ConversationRunner', '_interpolate_str', 1, 2, 3).
python_method('ConversationRunner', '_interpolate', 1, 6, 4).
python_class('testql/detectors/base.py', 'BaseEndpointDetector').
python_method('BaseEndpointDetector', '__init__', 1, 1, 0).
python_method('BaseEndpointDetector', 'detect', 0, 1, 0).
python_method('BaseEndpointDetector', '_find_files', 2, 6, 4).
python_class('testql/detectors/config_detector.py', 'ConfigEndpointDetector').
python_method('ConfigEndpointDetector', 'detect', 0, 1, 3).
python_method('ConfigEndpointDetector', '_detect_from_docker_compose', 0, 3, 2).
python_method('ConfigEndpointDetector', '_detect_from_env_files', 0, 4, 2).
python_method('ConfigEndpointDetector', '_detect_from_config_py', 0, 4, 2).
python_method('ConfigEndpointDetector', '_analyze_docker_compose', 1, 8, 7).
python_method('ConfigEndpointDetector', '_parse_port_mapping', 1, 5, 4).
python_method('ConfigEndpointDetector', '_infer_protocol', 1, 3, 0).
python_method('ConfigEndpointDetector', '_analyze_env_file', 1, 14, 11).
python_method('ConfigEndpointDetector', '_analyze_config_py', 1, 6, 7).
python_method('ConfigEndpointDetector', '_extract_port_from_url', 1, 4, 4).
python_class('testql/detectors/django_detector.py', 'DjangoDetector').
python_method('DjangoDetector', 'detect', 0, 3, 2).
python_method('DjangoDetector', '_analyze_urls_py', 1, 4, 10).
python_class('testql/detectors/express_detector.py', 'ExpressDetector').
python_method('ExpressDetector', 'detect', 0, 3, 2).
python_method('ExpressDetector', '_analyze_express_file', 1, 5, 8).
python_method('ExpressDetector', '_extract_method_path', 1, 3, 2).
python_class('testql/detectors/fastapi_detector.py', 'FastAPIDetector').
python_method('FastAPIDetector', 'detect', 0, 3, 2).
python_method('FastAPIDetector', '_analyze_file', 1, 6, 9).
python_method('FastAPIDetector', '_detect_router_assignment', 2, 6, 2).
python_method('FastAPIDetector', '_extract_router_prefix', 1, 4, 1).
python_method('FastAPIDetector', '_detect_app_assignment', 1, 1, 0).
python_method('FastAPIDetector', '_extract_include_router', 1, 6, 1).
python_method('FastAPIDetector', '_analyze_route_handler', 4, 4, 7).
python_method('FastAPIDetector', '_extract_route_info', 1, 6, 2).
python_method('FastAPIDetector', '_get_router_prefix', 2, 6, 1).
python_method('FastAPIDetector', '_extract_parameters', 1, 4, 2).
python_method('FastAPIDetector', '_get_annotation_name', 1, 4, 1).
python_method('FastAPIDetector', '_extract_docstring', 1, 5, 3).
python_class('testql/detectors/flask_detector.py', 'FlaskDetector').
python_method('FlaskDetector', 'detect', 0, 3, 2).
python_method('FlaskDetector', '_analyze_flask_file', 1, 4, 6).
python_method('FlaskDetector', '_detect_blueprint', 2, 6, 2).
python_method('FlaskDetector', '_extract_blueprint_prefix', 1, 4, 1).
python_method('FlaskDetector', '_analyze_flask_route', 4, 5, 4).
python_method('FlaskDetector', '_extract_flask_route_info', 2, 3, 4).
python_method('FlaskDetector', '_extract_route_path', 1, 3, 1).
python_method('FlaskDetector', '_extract_route_methods', 1, 6, 3).
python_method('FlaskDetector', '_apply_blueprint_prefix', 3, 4, 1).
python_class('testql/detectors/graphql_detector.py', 'GraphQLDetector').
python_method('GraphQLDetector', 'detect', 0, 5, 3).
python_method('GraphQLDetector', '_analyze_schema', 1, 4, 5).
python_method('GraphQLDetector', '_analyze_python_graphql', 1, 4, 7).
python_class('testql/detectors/models.py', 'EndpointInfo').
python_method('EndpointInfo', 'to_testql_api_call', 1, 2, 1).
python_method('EndpointInfo', '_infer_expected_status', 0, 1, 2).
python_class('testql/detectors/models.py', 'ServiceInfo').
python_class('testql/detectors/openapi_detector.py', 'OpenAPIDetector').
python_method('OpenAPIDetector', 'detect', 0, 4, 3).
python_method('OpenAPIDetector', '_parse_spec', 1, 9, 11).
python_method('OpenAPIDetector', '_extract_base_path', 1, 4, 2).
python_class('testql/detectors/test_detector.py', 'TestEndpointDetector').
python_method('TestEndpointDetector', 'detect', 0, 3, 2).
python_method('TestEndpointDetector', '_analyze_test_file', 1, 5, 9).
python_method('TestEndpointDetector', '_extract_method_path', 2, 3, 6).
python_class('testql/detectors/unified.py', 'UnifiedEndpointDetector').
python_method('UnifiedEndpointDetector', '__init__', 2, 1, 1).
python_method('UnifiedEndpointDetector', 'detect_all', 0, 4, 6).
python_method('UnifiedEndpointDetector', 'validate_endpoints', 2, 9, 4).
python_method('UnifiedEndpointDetector', 'detect_and_validate', 1, 2, 4).
python_method('UnifiedEndpointDetector', '_deduplicate_endpoints', 1, 3, 4).
python_method('UnifiedEndpointDetector', 'get_endpoints_by_type', 1, 3, 0).
python_method('UnifiedEndpointDetector', 'get_endpoints_by_framework', 1, 3, 0).
python_method('UnifiedEndpointDetector', 'generate_testql_scenario', 2, 13, 8).
python_method('UnifiedEndpointDetector', '_rest_block', 1, 3, 3).
python_method('UnifiedEndpointDetector', '_graphql_block', 1, 4, 2).
python_method('UnifiedEndpointDetector', '_ws_block', 1, 3, 2).
python_class('testql/detectors/websocket_detector.py', 'WebSocketDetector').
python_method('WebSocketDetector', 'detect', 0, 3, 3).
python_method('WebSocketDetector', '_analyze_content', 2, 3, 6).
python_class('testql/discovery/manifest.py', 'ManifestConfidence').
python_class('testql/discovery/manifest.py', 'Evidence').
python_method('Evidence', 'to_dict', 0, 9, 0).
python_class('testql/discovery/manifest.py', 'Dependency').
python_method('Dependency', 'to_dict', 0, 9, 0).
python_class('testql/discovery/manifest.py', 'Interface').
python_method('Interface', 'to_dict', 0, 9, 1).
python_class('testql/discovery/manifest.py', 'BuildArtifact').
python_method('BuildArtifact', 'to_dict', 0, 9, 1).
python_class('testql/discovery/manifest.py', 'ArtifactManifest').
python_method('ArtifactManifest', 'from_probe_results', 3, 8, 6).
python_method('ArtifactManifest', 'to_dict', 1, 9, 5).
python_class('testql/discovery/probes/base.py', 'ProbeResult').
python_method('ProbeResult', 'to_dict', 0, 3, 3).
python_class('testql/discovery/probes/base.py', 'Probe').
python_method('Probe', 'applicable', 1, 1, 0).
python_method('Probe', 'probe', 1, 1, 0).
python_class('testql/discovery/probes/base.py', 'BaseProbe').
python_method('BaseProbe', 'applicable', 1, 1, 0).
python_method('BaseProbe', 'no_match', 0, 1, 1).
python_method('BaseProbe', 'result', 5, 3, 1).
python_method('BaseProbe', 'evidence', 3, 1, 2).
python_method('BaseProbe', 'source_roots', 1, 4, 3).
python_class('testql/discovery/probes/browser/playwright_page.py', 'PlaywrightPageProbe').
python_method('PlaywrightPageProbe', '__init__', 2, 1, 0).
python_method('PlaywrightPageProbe', 'applicable', 1, 1, 0).
python_method('PlaywrightPageProbe', 'probe', 1, 10, 15).
python_method('PlaywrightPageProbe', 'evidence', 3, 1, 2).
python_class('testql/discovery/probes/filesystem/api_openapi.py', 'OpenAPIProbe').
python_method('OpenAPIProbe', 'probe', 1, 9, 11).
python_method('OpenAPIProbe', '_find_specs', 1, 9, 11).
python_method('OpenAPIProbe', '_load', 1, 2, 3).
python_method('OpenAPIProbe', '_metadata', 3, 3, 3).
python_class('testql/discovery/probes/filesystem/container_compose.py', 'DockerComposeProbe').
python_method('DockerComposeProbe', 'probe', 1, 4, 6).
python_method('DockerComposeProbe', '_find_files', 1, 6, 3).
python_method('DockerComposeProbe', '_metadata', 1, 9, 6).
python_class('testql/discovery/probes/filesystem/container_dockerfile.py', 'DockerfileProbe').
python_method('DockerfileProbe', 'probe', 1, 5, 5).
python_method('DockerfileProbe', '_find_files', 1, 6, 3).
python_method('DockerfileProbe', '_metadata', 1, 4, 8).
python_class('testql/discovery/probes/filesystem/package_node.py', 'NodePackageProbe').
python_method('NodePackageProbe', 'probe', 1, 14, 8).
python_method('NodePackageProbe', '_metadata', 1, 7, 7).
python_class('testql/discovery/probes/filesystem/package_python.py', 'PythonPackageProbe').
python_method('PythonPackageProbe', 'probe', 1, 9, 14).
python_method('PythonPackageProbe', '_find_manifests', 1, 5, 3).
python_method('PythonPackageProbe', '_find_requirements', 1, 3, 4).
python_method('PythonPackageProbe', '_find_python_files', 1, 7, 6).
python_method('PythonPackageProbe', '_read_metadata', 2, 8, 10).
python_method('PythonPackageProbe', '_looks_like_fastapi', 2, 6, 3).
python_method('PythonPackageProbe', '_confidence', 4, 10, 2).
python_class('testql/discovery/probes/network/http_endpoint.py', 'HTTPPageProbe').
python_method('HTTPPageProbe', '__init__', 1, 1, 0).
python_method('HTTPPageProbe', 'applicable', 1, 1, 0).
python_method('HTTPPageProbe', 'probe', 1, 6, 9).
python_method('HTTPPageProbe', 'evidence', 3, 1, 2).
python_class('testql/discovery/probes/network/http_endpoint.py', '_PageParser').
python_method('_PageParser', '__init__', 1, 1, 2).
python_method('_PageParser', 'handle_starttag', 2, 10, 6).
python_method('_PageParser', 'handle_data', 1, 6, 4).
python_method('_PageParser', 'handle_endtag', 1, 5, 2).
python_class('testql/discovery/registry.py', 'ProbeRegistry').
python_method('ProbeRegistry', '__init__', 3, 2, 1).
python_method('ProbeRegistry', 'run', 1, 5, 7).
python_method('ProbeRegistry', 'discover', 1, 2, 4).
python_class('testql/discovery/source.py', 'SourceKind').
python_class('testql/discovery/source.py', 'ArtifactSource').
python_method('ArtifactSource', 'from_value', 2, 4, 5).
python_method('ArtifactSource', 'path', 0, 1, 1).
python_method('ArtifactSource', 'to_dict', 0, 1, 0).
python_class('testql/doql_parser.py', 'DoqlParser').
python_method('DoqlParser', '__init__', 0, 1, 1).
python_method('DoqlParser', 'parse_file', 1, 1, 2).
python_method('DoqlParser', 'parse', 1, 6, 9).
python_method('DoqlParser', '_parse_app_block', 1, 3, 3).
python_method('DoqlParser', '_parse_entity_block', 2, 6, 6).
python_method('DoqlParser', '_parse_workflow_block', 2, 6, 5).
python_method('DoqlParser', '_parse_interface_block', 2, 2, 5).
python_method('DoqlParser', '_parse_deploy_block', 1, 3, 3).
python_class('testql/echo_schemas.py', 'APIContract').
python_class('testql/echo_schemas.py', 'Entity').
python_class('testql/echo_schemas.py', 'Workflow').
python_class('testql/echo_schemas.py', 'Interface').
python_class('testql/echo_schemas.py', 'SystemModel').
python_class('testql/echo_schemas.py', 'ProjectEcho').
python_method('ProjectEcho', 'to_dict', 0, 4, 0).
python_method('ProjectEcho', 'to_text', 0, 8, 4).
python_class('testql/generators/analyzers.py', 'ProjectAnalyzer').
python_method('ProjectAnalyzer', '_detect_web_frontend', 1, 3, 0).
python_method('ProjectAnalyzer', '_detect_python_type', 1, 7, 4).
python_method('ProjectAnalyzer', '_has_argparse_usage', 0, 7, 2).
python_method('ProjectAnalyzer', '_detect_hardware', 0, 3, 2).
python_method('ProjectAnalyzer', 'detect_project_type', 0, 5, 5).
python_method('ProjectAnalyzer', 'run_full_analysis', 0, 1, 6).
python_method('ProjectAnalyzer', '_scan_directory_structure', 0, 8, 4).
python_method('ProjectAnalyzer', '_collect_patterns_from_tree', 3, 10, 5).
python_method('ProjectAnalyzer', '_analyze_python_tests', 0, 3, 5).
python_method('ProjectAnalyzer', '_extract_test_pattern', 4, 4, 6).
python_method('ProjectAnalyzer', '_detect_pattern_type', 2, 9, 1).
python_method('ProjectAnalyzer', '_extract_commands_and_assertions', 1, 4, 6).
python_method('ProjectAnalyzer', '_analyze_config_files', 0, 6, 4).
python_method('ProjectAnalyzer', '_analyze_api_routes', 0, 3, 6).
python_method('ProjectAnalyzer', '_analyze_api_routes_fallback', 0, 4, 6).
python_method('ProjectAnalyzer', '_analyze_scenarios', 0, 5, 5).
python_class('testql/generators/api_generator.py', 'APIGeneratorMixin').
python_method('APIGeneratorMixin', '_generate_api_tests', 1, 8, 14).
python_method('APIGeneratorMixin', '_validate_endpoints', 2, 4, 5).
python_method('APIGeneratorMixin', '_validate_single_endpoint', 2, 9, 7).
python_method('APIGeneratorMixin', '_try_endpoint_request', 2, 6, 2).
python_method('APIGeneratorMixin', '_sleep_with_backoff', 2, 1, 1).
python_method('APIGeneratorMixin', '_log_validation_summary', 3, 4, 2).
python_method('APIGeneratorMixin', '_build_api_test_header', 1, 1, 1).
python_method('APIGeneratorMixin', '_build_api_test_config', 2, 5, 3).
python_method('APIGeneratorMixin', '_build_api_test_preamble', 1, 1, 0).
python_method('APIGeneratorMixin', '_build_api_test_captures', 0, 1, 0).
python_method('APIGeneratorMixin', '_build_rest_section', 1, 4, 3).
python_method('APIGeneratorMixin', '_build_graphql_section', 1, 2, 3).
python_method('APIGeneratorMixin', '_build_websocket_section', 1, 2, 2).
python_method('APIGeneratorMixin', '_build_api_test_endpoints', 1, 10, 5).
python_method('APIGeneratorMixin', '_deduplicate_rest_routes', 1, 4, 3).
python_method('APIGeneratorMixin', '_build_api_test_assertions', 0, 1, 0).
python_method('APIGeneratorMixin', '_build_api_test_flow', 0, 1, 0).
python_method('APIGeneratorMixin', '_build_api_test_summary', 1, 5, 4).
python_class('testql/generators/api_generator.py', '_ValidationResult').
python_method('_ValidationResult', '__init__', 5, 1, 0).
python_class('testql/generators/base.py', 'TestPattern').
python_class('testql/generators/base.py', 'ProjectProfile').
python_class('testql/generators/base.py', 'BaseAnalyzer').
python_method('BaseAnalyzer', '__init__', 1, 1, 2).
python_method('BaseAnalyzer', '_get_exclude_dirs', 0, 1, 0).
python_method('BaseAnalyzer', '_should_exclude_path', 1, 1, 3).
python_class('testql/generators/conversation_generator.py', 'ConversationGenerator').
python_method('ConversationGenerator', 'from_trace', 1, 8, 9).
python_method('ConversationGenerator', 'render_toon', 1, 1, 2).
python_class('testql/generators/llm/coverage_optimizer.py', 'CoverageReport').
python_class('testql/generators/llm/coverage_optimizer.py', 'CoverageOptimizer').
python_method('CoverageOptimizer', 'analyse', 1, 1, 0).
python_class('testql/generators/llm/coverage_optimizer.py', 'NoOpCoverageOptimizer').
python_method('NoOpCoverageOptimizer', 'analyse', 1, 1, 1).
python_class('testql/generators/llm/edge_case_generator.py', 'EdgeCaseGenerator').
python_method('EdgeCaseGenerator', 'enrich', 1, 1, 0).
python_class('testql/generators/llm/edge_case_generator.py', 'NoOpEdgeCaseGenerator').
python_method('NoOpEdgeCaseGenerator', 'enrich', 1, 1, 0).
python_class('testql/generators/multi.py', 'MultiProjectTestGenerator').
python_method('MultiProjectTestGenerator', '__init__', 1, 1, 1).
python_method('MultiProjectTestGenerator', 'discover_projects', 0, 6, 6).
python_method('MultiProjectTestGenerator', 'analyze_all', 0, 2, 3).
python_method('MultiProjectTestGenerator', 'generate_all', 0, 2, 2).
python_method('MultiProjectTestGenerator', 'generate_cross_project_tests', 1, 3, 8).
python_class('testql/generators/page_analyzer.py', 'PageSnapshot').
python_method('PageSnapshot', '__post_init__', 0, 3, 0).
python_class('testql/generators/pipeline.py', 'PipelineResult').
python_class('testql/generators/pytest_generator.py', 'PythonTestGeneratorMixin').
python_method('PythonTestGeneratorMixin', '_generate_from_python_tests', 1, 6, 9).
python_method('PythonTestGeneratorMixin', '_build_test_header', 0, 1, 0).
python_method('PythonTestGeneratorMixin', '_extract_api_commands', 1, 4, 2).
python_method('PythonTestGeneratorMixin', '_build_api_section', 1, 3, 2).
python_method('PythonTestGeneratorMixin', '_extract_assertions', 1, 4, 3).
python_method('PythonTestGeneratorMixin', '_parse_assertion_expression', 1, 3, 3).
python_method('PythonTestGeneratorMixin', '_build_assertions_section', 1, 3, 3).
python_method('PythonTestGeneratorMixin', '_build_no_conversions_note', 0, 1, 0).
python_method('PythonTestGeneratorMixin', '_normalize_assertion_field', 1, 7, 6).
python_class('testql/generators/scenario_generator.py', 'ScenarioGeneratorMixin').
python_method('ScenarioGeneratorMixin', '_generate_from_scenarios', 1, 13, 10).
python_method('ScenarioGeneratorMixin', '_convert_oql_command', 1, 7, 1).
python_class('testql/generators/sources/base.py', 'BaseSource').
python_method('BaseSource', 'load', 1, 1, 0).
python_class('testql/generators/sources/config_source.py', 'ConfigSource').
python_method('ConfigSource', 'load', 1, 6, 12).
python_class('testql/generators/sources/conversation.py', 'ConversationTestSource').
python_method('ConversationTestSource', 'load', 1, 6, 7).
python_class('testql/generators/sources/graphql_source.py', 'GraphQLSource').
python_method('GraphQLSource', 'load', 1, 3, 7).
python_class('testql/generators/sources/nl_source.py', 'NLSource').
python_method('NLSource', 'load', 1, 2, 5).
python_class('testql/generators/sources/openapi_source.py', 'OpenAPISource').
python_method('OpenAPISource', 'load', 1, 7, 8).
python_class('testql/generators/sources/oql_models.py', 'OqlCommand').
python_class('testql/generators/sources/oql_models.py', 'ParsedScenario').
python_class('testql/generators/sources/oql_parser.py', 'OqlParser').
python_method('OqlParser', 'parse_file', 1, 7, 12).
python_method('OqlParser', '_read_file_content', 1, 2, 1).
python_method('OqlParser', '_should_skip_line', 1, 3, 1).
python_method('OqlParser', '_extract_metadata_from_comment', 2, 3, 4).
python_method('OqlParser', '_handle_sequence_block', 3, 3, 0).
python_method('OqlParser', '_categorize_command', 2, 5, 2).
python_method('OqlParser', '_parse_command', 3, 3, 5).
python_method('OqlParser', '_create_command_from_match', 4, 2, 2).
python_method('OqlParser', '_parse_set_command', 3, 1, 2).
python_method('OqlParser', '_parse_read_command', 3, 2, 3).
python_method('OqlParser', '_parse_write_command', 3, 2, 3).
python_method('OqlParser', '_parse_check_command', 3, 3, 3).
python_method('OqlParser', '_parse_wait_command', 3, 1, 2).
python_method('OqlParser', '_parse_poll_command', 3, 1, 2).
python_method('OqlParser', '_parse_exec_command', 3, 1, 2).
python_method('OqlParser', '_parse_log_command', 3, 1, 2).
python_method('OqlParser', '_parse_call_command', 3, 2, 3).
python_method('OqlParser', '_parse_sequence_command', 3, 1, 2).
python_method('OqlParser', '_parse_end_command', 3, 1, 2).
python_method('OqlParser', '_parse_generic_command', 3, 3, 5).
python_class('testql/generators/sources/oql_source.py', 'OqlSource').
python_method('OqlSource', 'load', 1, 2, 4).
python_method('OqlSource', 'ingest', 1, 10, 9).
python_method('OqlSource', '_to_unified_ir', 1, 7, 4).
python_method('OqlSource', '_detect_scenario_type', 1, 6, 2).
python_method('OqlSource', '_convert_command', 1, 2, 2).
python_method('OqlSource', '_convert_set', 1, 1, 1).
python_method('OqlSource', '_convert_read', 1, 3, 1).
python_method('OqlSource', '_convert_write', 1, 7, 2).
python_method('OqlSource', '_convert_check', 1, 2, 2).
python_method('OqlSource', '_convert_wait', 1, 1, 1).
python_method('OqlSource', '_convert_poll', 1, 1, 2).
python_method('OqlSource', '_convert_exec', 1, 1, 0).
python_method('OqlSource', '_convert_log', 1, 1, 0).
python_method('OqlSource', '_convert_call', 1, 1, 1).
python_method('OqlSource', 'to_oql', 1, 1, 5).
python_method('OqlSource', '_build_oql_header', 1, 1, 1).
python_method('OqlSource', '_build_oql_config', 1, 3, 4).
python_method('OqlSource', '_build_oql_steps', 1, 3, 3).
python_method('OqlSource', '_render_step_to_oql', 2, 2, 2).
python_method('OqlSource', '_render_hardware_step', 1, 1, 1).
python_method('OqlSource', '_build_oql_assertions', 1, 4, 3).
python_method('OqlSource', '_render_assertion_to_oql', 2, 3, 1).
python_class('testql/generators/sources/page_source.py', 'PageSource').
python_method('PageSource', 'load', 1, 1, 5).
python_method('PageSource', '_resolve_source', 1, 4, 6).
python_method('PageSource', '_fetch_via_playwright', 2, 4, 8).
python_class('testql/generators/sources/proto_source.py', 'ProtoSource').
python_method('ProtoSource', 'load', 1, 3, 7).
python_class('testql/generators/sources/pytest_source.py', 'ParsedTest').
python_class('testql/generators/sources/pytest_source.py', 'PytestParser').
python_method('PytestParser', 'parse_file', 1, 10, 9).
python_method('PytestParser', '_parse_test_function', 4, 1, 5).
python_method('PytestParser', '_extract_fixtures', 1, 7, 2).
python_method('PytestParser', '_parse_body', 2, 12, 7).
python_method('PytestParser', '_get_source_segment', 2, 4, 2).
python_method('PytestParser', '_parse_assertion', 2, 3, 4).
python_method('PytestParser', '_parse_call', 2, 7, 6).
python_method('PytestParser', '_parse_assignment', 2, 1, 1).
python_class('testql/generators/sources/pytest_source.py', 'PytestSource').
python_method('PytestSource', 'load', 1, 2, 4).
python_method('PytestSource', 'ingest', 1, 8, 10).
python_method('PytestSource', '_to_unified_ir', 1, 11, 4).
python_method('PytestSource', '_detect_test_type', 1, 9, 2).
python_method('PytestSource', 'to_oql', 1, 13, 4).
python_class('testql/generators/sources/sql_source.py', 'SqlSource').
python_method('SqlSource', 'load', 1, 3, 10).
python_class('testql/generators/sources/ui_source.py', 'UISource').
python_method('UISource', 'load', 1, 1, 10).
python_class('testql/generators/specialized_generator.py', 'SpecializedGeneratorMixin').
python_method('SpecializedGeneratorMixin', '_generate_api_integration_tests', 1, 1, 2).
python_method('SpecializedGeneratorMixin', '_generate_cli_tests', 1, 1, 2).
python_method('SpecializedGeneratorMixin', '_generate_lib_tests', 1, 1, 2).
python_method('SpecializedGeneratorMixin', '_generate_frontend_tests', 1, 1, 2).
python_method('SpecializedGeneratorMixin', '_generate_hardware_tests', 1, 1, 2).
python_class('testql/generators/targets/base.py', 'BaseTarget').
python_method('BaseTarget', 'render', 1, 1, 0).
python_class('testql/generators/targets/nl_target.py', 'NLTarget').
python_method('NLTarget', 'render', 1, 1, 2).
python_class('testql/generators/targets/pytest_target.py', 'PytestTarget').
python_method('PytestTarget', 'render', 1, 3, 3).
python_class('testql/generators/targets/testtoon_target.py', 'TestToonTarget').
python_method('TestToonTarget', 'render', 1, 1, 2).
python_class('testql/generators/test_generator.py', 'TestGenerator').
python_method('TestGenerator', 'analyze', 0, 1, 1).
python_method('TestGenerator', 'generate_tests', 1, 12, 9).
python_class('testql/interpreter/_api_runner.py', 'ApiRunnerMixin').
python_method('ApiRunnerMixin', '_do_http_request', 3, 3, 8).
python_method('ApiRunnerMixin', '_do_http_request_with_retry', 3, 10, 6).
python_method('ApiRunnerMixin', '_store_api_response', 3, 4, 4).
python_method('ApiRunnerMixin', '_record_api_success', 4, 2, 4).
python_method('ApiRunnerMixin', '_record_api_http_error', 2, 1, 3).
python_method('ApiRunnerMixin', '_record_api_error', 2, 1, 4).
python_method('ApiRunnerMixin', '_cmd_api', 2, 13, 18).
python_method('ApiRunnerMixin', '_cmd_capture', 2, 3, 9).
python_class('testql/interpreter/_assertions.py', 'AssertionsMixin').
python_method('AssertionsMixin', '_cmd_assert_status', 2, 2, 5).
python_method('AssertionsMixin', '_cmd_assert_ok', 2, 2, 3).
python_method('AssertionsMixin', '_cmd_assert_contains', 2, 3, 5).
python_method('AssertionsMixin', '_cmd_assert_json', 2, 13, 16).
python_method('AssertionsMixin', '_cmd_assert_schema', 2, 8, 13).
python_method('AssertionsMixin', '_cmd_assert_headers', 2, 8, 10).
python_method('AssertionsMixin', '_cmd_assert_cookies', 2, 13, 11).
python_class('testql/interpreter/_encoder.py', 'EncoderMixin').
python_method('EncoderMixin', '_encoder_url', 0, 1, 1).
python_method('EncoderMixin', '_encoder_prefix', 0, 1, 1).
python_method('EncoderMixin', '_encoder_do_http', 4, 4, 11).
python_method('EncoderMixin', '_encoder_call', 5, 9, 10).
python_method('EncoderMixin', '_cmd_encoder_on', 2, 1, 2).
python_method('EncoderMixin', '_cmd_encoder_off', 2, 1, 2).
python_method('EncoderMixin', '_cmd_encoder_scroll', 2, 2, 4).
python_method('EncoderMixin', '_cmd_encoder_click', 2, 1, 2).
python_method('EncoderMixin', '_cmd_encoder_dblclick', 2, 1, 2).
python_method('EncoderMixin', '_cmd_encoder_focus', 2, 2, 3).
python_method('EncoderMixin', '_cmd_encoder_status', 2, 1, 2).
python_method('EncoderMixin', '_cmd_encoder_page_next', 2, 1, 2).
python_method('EncoderMixin', '_cmd_encoder_page_prev', 2, 1, 2).
python_class('testql/interpreter/_flow.py', 'FlowMixin').
python_method('FlowMixin', '_cmd_wait_for', 2, 9, 10).
python_method('FlowMixin', '_cmd_wait', 2, 8, 10).
python_method('FlowMixin', '_cmd_log', 2, 3, 4).
python_method('FlowMixin', '_cmd_print', 2, 1, 1).
python_method('FlowMixin', '_cmd_include', 2, 7, 14).
python_method('FlowMixin', '_emit_event', 3, 1, 5).
python_class('testql/interpreter/_gui.py', 'GuiMixin').
python_method('GuiMixin', '_resolve_selector_with_fallback', 1, 3, 2).
python_method('GuiMixin', '_generate_fallback_selectors', 1, 1, 5).
python_method('GuiMixin', '_get_class_fallbacks', 1, 2, 2).
python_method('GuiMixin', '_get_id_fallbacks', 1, 2, 1).
python_method('GuiMixin', '_get_role_based_fallbacks', 1, 5, 2).
python_method('GuiMixin', '_get_button_text_fallbacks', 1, 5, 2).
python_method('GuiMixin', '_try_selectors', 2, 3, 1).
python_method('GuiMixin', '_try_single_selector', 2, 5, 3).
python_method('GuiMixin', '_find_element_with_logging', 2, 6, 5).
python_method('GuiMixin', '_init_gui_driver', 0, 6, 2).
python_method('GuiMixin', '_cmd_gui_start', 2, 8, 11).
python_method('GuiMixin', '_start_playwright', 2, 3, 14).
python_method('GuiMixin', '_start_selenium', 2, 4, 12).
python_method('GuiMixin', '_cmd_gui_navigate', 2, 12, 11).
python_method('GuiMixin', '_cmd_navigate', 2, 1, 1).
python_method('GuiMixin', '_cmd_gui_click', 2, 9, 8).
python_method('GuiMixin', '_cmd_gui_input', 2, 7, 12).
python_method('GuiMixin', '_cmd_gui_assert_visible', 2, 9, 9).
python_method('GuiMixin', '_cmd_gui_assert_text', 2, 8, 10).
python_method('GuiMixin', '_cmd_gui_capture', 2, 9, 11).
python_method('GuiMixin', '_cmd_gui_stop', 2, 6, 8).
python_method('GuiMixin', '_cmd_start', 2, 1, 1).
python_method('GuiMixin', '_cmd_stop', 2, 1, 1).
python_method('GuiMixin', '_cmd_close', 2, 1, 1).
python_method('GuiMixin', '_cmd_goto', 2, 1, 1).
python_method('GuiMixin', '_cmd_click', 2, 1, 1).
python_method('GuiMixin', '_cmd_input', 2, 1, 1).
python_method('GuiMixin', '_cmd_type', 2, 1, 1).
python_method('GuiMixin', '_cmd_assert_visible', 2, 1, 1).
python_method('GuiMixin', '_cmd_visible', 2, 1, 1).
python_method('GuiMixin', '_cmd_assert_text', 2, 1, 1).
python_method('GuiMixin', '_cmd_text', 2, 1, 1).
python_method('GuiMixin', '_cmd_capture', 2, 1, 1).
python_method('GuiMixin', '_cmd_screenshot', 2, 1, 1).
python_class('testql/interpreter/_hardware.py', 'HardwareMixin').
python_method('HardwareMixin', '_hardware_url', 0, 1, 1).
python_method('HardwareMixin', '_hardware_do_http', 4, 4, 7).
python_method('HardwareMixin', '_hardware_call', 5, 5, 6).
python_method('HardwareMixin', '_cmd_hardware', 2, 8, 11).
python_class('testql/interpreter/_modbus.py', 'ModbusMixin').
python_method('ModbusMixin', '_modbus_probe_script', 0, 1, 4).
python_method('ModbusMixin', '_modbus_store_response', 2, 1, 1).
python_method('ModbusMixin', '_modbus_skip_enabled', 0, 1, 3).
python_method('ModbusMixin', '_modbus_serial_exists', 1, 4, 3).
python_method('ModbusMixin', '_modbus_parse_kv_args', 1, 3, 3).
python_method('ModbusMixin', '_execute_probe_script', 4, 3, 7).
python_method('ModbusMixin', '_parse_probe_response', 1, 5, 2).
python_method('ModbusMixin', '_emit_probe_result', 2, 6, 7).
python_method('ModbusMixin', '_modbus_run_probe_script', 3, 6, 14).
python_method('ModbusMixin', '_cmd_modbus', 2, 14, 18).
python_class('testql/interpreter/_parser.py', 'OqlLine').
python_class('testql/interpreter/_parser.py', 'OqlScript').
python_class('testql/interpreter/_shell.py', 'ShellMixin').
python_method('ShellMixin', '_parse_shell_command', 1, 8, 7).
python_method('ShellMixin', '_execute_shell_dry_run', 2, 1, 3).
python_method('ShellMixin', '_execute_shell_live', 3, 5, 7).
python_method('ShellMixin', '_cmd_shell', 2, 4, 5).
python_method('ShellMixin', '_cmd_exec', 2, 8, 13).
python_method('ShellMixin', '_cmd_run', 2, 7, 8).
python_method('ShellMixin', '_cmd_assert_exit_code', 2, 3, 7).
python_method('ShellMixin', '_cmd_assert_stdout_contains', 2, 3, 6).
python_method('ShellMixin', '_cmd_assert_stderr_contains', 2, 3, 6).
python_class('testql/interpreter/_unit.py', 'UnitMixin').
python_method('UnitMixin', '_parse_pytest_args', 1, 6, 6).
python_method('UnitMixin', '_extract_pytest_summary', 1, 4, 1).
python_method('UnitMixin', '_run_pytest_subprocess', 3, 2, 5).
python_method('UnitMixin', '_handle_pytest_dry_run', 2, 1, 3).
python_method('UnitMixin', '_handle_pytest_success', 2, 3, 4).
python_method('UnitMixin', '_handle_pytest_error', 3, 3, 5).
python_method('UnitMixin', '_cmd_unit_pytest', 2, 4, 6).
python_method('UnitMixin', '_cmd_unit_pytest_discover', 2, 5, 10).
python_method('UnitMixin', '_cmd_unit_import', 2, 5, 7).
python_method('UnitMixin', '_cmd_unit_assert', 2, 10, 13).
python_class('testql/interpreter/_validation.py', 'ValidationMixin').
python_method('ValidationMixin', '_cmd_validate', 2, 10, 18).
python_method('ValidationMixin', '_record_validate', 5, 2, 4).
python_class('testql/interpreter/_websockets.py', 'WebSocketMixin').
python_method('WebSocketMixin', '__init_subclass__', 1, 3, 3).
python_method('WebSocketMixin', '_get_ws_context', 0, 3, 1).
python_method('WebSocketMixin', '_cmd_ws_connect', 2, 5, 11).
python_method('WebSocketMixin', '_cmd_ws_send', 2, 7, 11).
python_method('WebSocketMixin', '_ws_do_receive', 4, 1, 7).
python_method('WebSocketMixin', '_cmd_ws_receive', 2, 8, 11).
python_method('WebSocketMixin', '_cmd_ws_assert_msg', 2, 6, 10).
python_method('WebSocketMixin', '_cmd_ws_close', 2, 6, 7).
python_class('testql/interpreter/converter/models.py', 'Row').
python_class('testql/interpreter/converter/models.py', 'Section').
python_class('testql/interpreter/dispatcher.py', 'CommandDispatcher').
python_method('CommandDispatcher', '__init__', 1, 1, 1).
python_method('CommandDispatcher', '_discover_handlers', 0, 3, 3).
python_method('CommandDispatcher', 'register', 2, 1, 1).
python_method('CommandDispatcher', 'dispatch', 3, 5, 11).
python_method('CommandDispatcher', 'list_commands', 0, 1, 2).
python_method('CommandDispatcher', 'has_command', 1, 1, 1).
python_class('testql/interpreter/dom_scan_mixin.py', 'DomScanMixin').
python_method('DomScanMixin', '_parse_dom_scan_args', 2, 7, 6).
python_method('DomScanMixin', '_execute_dom_scan', 4, 5, 12).
python_method('DomScanMixin', '_cmd_dom_scan', 2, 5, 9).
python_method('DomScanMixin', '_cmd_dom_audit_buttons', 2, 4, 10).
python_method('DomScanMixin', '_parse_audit_args', 1, 9, 3).
python_method('DomScanMixin', '_ensure_gui_session', 1, 2, 5).
python_method('DomScanMixin', '_handle_audit_report', 2, 4, 8).
python_method('DomScanMixin', '_save_report_to_file', 2, 1, 4).
python_method('DomScanMixin', '_cmd_assert_taborder', 2, 6, 10).
python_method('DomScanMixin', '_cmd_assert_aria', 2, 5, 9).
python_method('DomScanMixin', '_cmd_assert_focusable', 2, 5, 8).
python_class('testql/interpreter/dom_scan_models.py', 'FocusableElement').
python_class('testql/interpreter/dom_scan_models.py', 'DomScanResult').
python_class('testql/interpreter/dom_scan_models.py', 'ButtonAuditResult').
python_class('testql/interpreter/dom_scan_models.py', 'ButtonAuditReport').
python_class('testql/interpreter/dom_scanner.py', 'DomScanner').
python_method('DomScanner', '__init__', 1, 1, 0).
python_method('DomScanner', 'scan_focusable', 1, 1, 4).
python_method('DomScanner', 'scan_aria', 1, 4, 9).
python_method('DomScanner', 'scan_interactive', 1, 3, 4).
python_method('DomScanner', 'scan_taborder', 1, 1, 4).
python_method('DomScanner', 'audit_buttons', 2, 6, 8).
python_method('DomScanner', '_should_skip_button', 2, 4, 0).
python_method('DomScanner', '_audit_single_button', 1, 2, 10).
python_method('DomScanner', '_setup_mutation_observer', 0, 1, 1).
python_method('DomScanner', '_classify_button_result', 5, 6, 2).
python_method('DomScanner', '_handle_button_click_error', 2, 4, 3).
python_method('DomScanner', '_remove_event_listeners', 3, 1, 1).
python_method('DomScanner', '_update_report_counts', 2, 4, 0).
python_method('DomScanner', '_restore_page_if_needed', 1, 3, 1).
python_method('DomScanner', 'assert_taborder', 2, 5, 2).
python_method('DomScanner', 'assert_aria', 2, 5, 4).
python_method('DomScanner', 'assert_focusable', 1, 5, 3).
python_method('DomScanner', '_get_focusable_elements', 0, 13, 14).
python_method('DomScanner', '_simulate_tab_order', 0, 9, 10).
python_method('DomScanner', '_implicit_role', 1, 1, 1).
python_method('DomScanner', '_build_selector', 2, 5, 2).
python_method('DomScanner', '_check_duplicate_labels', 1, 5, 3).
python_method('DomScanner', '_check_aria_errors', 1, 4, 1).
python_method('DomScanner', '_check_tabindex_warnings', 1, 6, 3).
python_class('testql/interpreter/interpreter.py', 'OqlInterpreter').
python_method('OqlInterpreter', '__init__', 7, 3, 4).
python_method('OqlInterpreter', 'parse', 2, 2, 3).
python_method('OqlInterpreter', '_is_testtoon', 2, 4, 3).
python_method('OqlInterpreter', 'execute', 1, 4, 12).
python_method('OqlInterpreter', '_dispatch', 3, 2, 3).
python_method('OqlInterpreter', '_cmd_set', 2, 8, 8).
python_method('OqlInterpreter', '_cmd_get', 2, 1, 3).
python_class('testql/interpreter/testtoon_models.py', 'ToonSection').
python_method('ToonSection', 'validate', 0, 3, 2).
python_class('testql/interpreter/testtoon_models.py', 'ToonScript').
python_class('testql/ir/assertions.py', 'Assertion').
python_method('Assertion', 'to_dict', 0, 3, 0).
python_class('testql/ir/captures.py', 'Capture').
python_method('Capture', 'to_dict', 0, 1, 0).
python_class('testql/ir/fixtures.py', 'Fixture').
python_method('Fixture', 'to_dict', 0, 1, 1).
python_class('testql/ir/metadata.py', 'ScenarioMetadata').
python_method('ScenarioMetadata', 'to_dict', 0, 3, 2).
python_class('testql/ir/plan.py', 'TestPlan').
python_method('TestPlan', 'to_dict', 0, 3, 2).
python_method('TestPlan', 'name', 0, 1, 0).
python_method('TestPlan', 'type', 0, 1, 0).
python_class('testql/ir/steps.py', 'Step').
python_method('Step', 'to_dict', 0, 1, 2).
python_class('testql/ir/steps.py', 'ApiStep').
python_method('ApiStep', '__post_init__', 0, 1, 0).
python_method('ApiStep', 'to_dict', 0, 1, 4).
python_class('testql/ir/steps.py', 'GuiStep').
python_method('GuiStep', '__post_init__', 0, 1, 0).
python_method('GuiStep', 'to_dict', 0, 1, 2).
python_class('testql/ir/steps.py', 'EncoderStep').
python_method('EncoderStep', '__post_init__', 0, 1, 0).
python_method('EncoderStep', 'to_dict', 0, 1, 2).
python_class('testql/ir/steps.py', 'ShellStep').
python_method('ShellStep', '__post_init__', 0, 1, 0).
python_method('ShellStep', 'to_dict', 0, 1, 2).
python_class('testql/ir/steps.py', 'UnitStep').
python_method('UnitStep', '__post_init__', 0, 1, 0).
python_method('UnitStep', 'to_dict', 0, 1, 4).
python_class('testql/ir/steps.py', 'NlStep').
python_method('NlStep', '__post_init__', 0, 1, 0).
python_method('NlStep', 'to_dict', 0, 1, 2).
python_class('testql/ir/steps.py', 'SqlStep').
python_method('SqlStep', '__post_init__', 0, 1, 0).
python_method('SqlStep', 'to_dict', 0, 1, 3).
python_class('testql/ir/steps.py', 'ProtoStep').
python_method('ProtoStep', '__post_init__', 0, 1, 0).
python_method('ProtoStep', 'to_dict', 0, 1, 4).
python_class('testql/ir/steps.py', 'GraphqlStep').
python_method('GraphqlStep', '__post_init__', 0, 1, 0).
python_method('GraphqlStep', 'to_dict', 0, 1, 4).
python_class('testql/ir/steps.py', 'ConversationTurnStep').
python_method('ConversationTurnStep', '__post_init__', 0, 1, 0).
python_method('ConversationTurnStep', 'to_dict', 0, 1, 4).
python_class('testql/ir/steps.py', 'Nlp2DslStep').
python_method('Nlp2DslStep', '__post_init__', 0, 1, 0).
python_method('Nlp2DslStep', 'to_dict', 0, 1, 3).
python_class('testql/ir/steps.py', 'ArtifactAssertStep').
python_method('ArtifactAssertStep', '__post_init__', 0, 1, 0).
python_method('ArtifactAssertStep', 'to_dict', 0, 1, 4).
python_class('testql/ir/steps.py', 'ValidateStep').
python_method('ValidateStep', '__post_init__', 0, 1, 0).
python_method('ValidateStep', 'to_dict', 0, 1, 3).
python_class('testql/ir_runner/assertion_eval.py', 'AssertionResult').
python_method('AssertionResult', 'to_dict', 0, 1, 0).
python_class('testql/ir_runner/context.py', 'ExecutionContext').
python_method('ExecutionContext', 'record', 1, 1, 1).
python_class('testql/ir_runner/engine.py', 'IRRunner').
python_method('IRRunner', '__init__', 0, 2, 2).
python_method('IRRunner', '_apply_plan_config', 1, 9, 6).
python_method('IRRunner', 'run', 2, 5, 7).
python_class('testql/ir_runner/executors/base.py', 'StepExecutor').
python_method('StepExecutor', '__call__', 2, 1, 0).
python_class('testql/mcp/server.py', 'TestQLMCPServer').
python_method('TestQLMCPServer', '__post_init__', 0, 1, 3).
python_method('TestQLMCPServer', '_register_tools', 0, 1, 12).
python_method('TestQLMCPServer', 'run', 0, 1, 1).
python_class('testql/meta/confidence_scorer.py', 'StepConfidence').
python_method('StepConfidence', 'to_dict', 0, 2, 2).
python_class('testql/meta/confidence_scorer.py', 'PlanConfidence').
python_method('PlanConfidence', 'to_dict', 0, 2, 2).
python_class('testql/meta/coverage_analyzer.py', 'CoverageReport').
python_method('CoverageReport', 'percent', 0, 2, 0).
python_method('CoverageReport', 'to_dict', 0, 1, 2).
python_class('testql/meta/mutator.py', 'Mutation').
python_method('Mutation', 'to_dict', 0, 3, 0).
python_class('testql/meta/mutator.py', 'MutationReport').
python_method('MutationReport', 'killed_ratio', 0, 2, 0).
python_method('MutationReport', 'to_dict', 0, 3, 1).
python_class('testql/meta/self_test.py', 'SelfTestReport').
python_method('SelfTestReport', 'is_release_ready', 0, 2, 0).
python_method('SelfTestReport', 'to_dict', 0, 1, 1).
python_class('testql/openapi_generator.py', 'OpenAPISpec').
python_method('OpenAPISpec', 'to_dict', 0, 1, 0).
python_method('OpenAPISpec', 'to_json', 1, 1, 2).
python_method('OpenAPISpec', 'to_yaml', 0, 1, 2).
python_class('testql/openapi_generator.py', 'OpenAPIGenerator').
python_method('OpenAPIGenerator', '__init__', 1, 3, 2).
python_method('OpenAPIGenerator', 'generate', 2, 5, 5).
python_method('OpenAPIGenerator', '_normalize_path', 1, 2, 1).
python_method('OpenAPIGenerator', '_build_operation', 1, 7, 7).
python_method('OpenAPIGenerator', '_infer_tags', 1, 7, 6).
python_method('OpenAPIGenerator', '_extract_parameters', 1, 1, 3).
python_method('OpenAPIGenerator', '_build_request_body', 1, 6, 1).
python_method('OpenAPIGenerator', '_build_responses', 1, 3, 0).
python_method('OpenAPIGenerator', 'save', 2, 3, 3).
python_class('testql/openapi_generator.py', 'ContractTestGenerator').
python_method('ContractTestGenerator', '__init__', 1, 3, 4).
python_method('ContractTestGenerator', '_load_spec', 1, 2, 3).
python_method('ContractTestGenerator', 'generate_contract_tests', 1, 6, 8).
python_method('ContractTestGenerator', '_get_expected_status', 2, 4, 2).
python_method('ContractTestGenerator', 'validate_response', 3, 11, 6).
python_class('testql/pipeline.py', 'GenerationContext').
python_class('testql/pipeline.py', 'GenerationPipeline').
python_method('GenerationPipeline', '__init__', 1, 1, 2).
python_method('GenerationPipeline', '_collect', 0, 2, 6).
python_method('GenerationPipeline', '_emit', 2, 2, 2).
python_method('GenerationPipeline', '_emit_workspace', 2, 4, 6).
python_method('GenerationPipeline', '_emit_single', 2, 1, 2).
python_method('GenerationPipeline', 'run', 0, 7, 4).
python_method('GenerationPipeline', '_is_workspace', 1, 5, 2).
python_class('testql/report_generator.py', 'TestResult').
python_class('testql/report_generator.py', 'TestSuiteReport').
python_class('testql/report_generator.py', 'ReportDataParser').
python_method('ReportDataParser', 'parse_testql_results', 1, 1, 1).
python_method('ReportDataParser', 'to_json', 1, 1, 2).
python_class('testql/report_generator.py', 'HTMLReportGenerator').
python_method('HTMLReportGenerator', '__init__', 1, 2, 1).
python_method('HTMLReportGenerator', 'generate', 2, 1, 2).
python_method('HTMLReportGenerator', '_render_html', 1, 3, 2).
python_method('HTMLReportGenerator', '_render_test_row', 1, 2, 3).
python_class('testql/reporters/junit.py', 'JUnitReporter').
python_method('JUnitReporter', 'generate', 2, 7, 11).
python_method('JUnitReporter', '_add_testcase', 3, 8, 1).
python_class('testql/results/models.py', 'CheckResult').
python_method('CheckResult', 'to_dict', 0, 3, 2).
python_class('testql/results/models.py', 'FailureFinding').
python_method('FailureFinding', 'to_dict', 0, 3, 2).
python_class('testql/results/models.py', 'SuggestedAction').
python_method('SuggestedAction', 'to_dict', 0, 3, 2).
python_class('testql/results/models.py', 'TestResultEnvelope').
python_method('TestResultEnvelope', 'to_dict', 0, 3, 2).
python_class('testql/results/models.py', 'RefactorPlan').
python_method('RefactorPlan', 'from_envelope', 2, 3, 2).
python_method('RefactorPlan', 'to_dict', 0, 3, 2).
python_class('testql/runner.py', 'DslCommand').
python_class('testql/runner.py', 'ExecutionResult').
python_class('testql/runner.py', 'DslCliExecutor').
python_method('DslCliExecutor', '__init__', 2, 1, 3).
python_method('DslCliExecutor', 'execute', 1, 2, 5).
python_method('DslCliExecutor', '_dispatch', 1, 6, 5).
python_method('DslCliExecutor', 'cmd_api', 1, 7, 6).
python_method('DslCliExecutor', 'cmd_wait', 1, 1, 2).
python_method('DslCliExecutor', 'cmd_log', 1, 2, 3).
python_method('DslCliExecutor', 'cmd_print', 1, 2, 4).
python_method('DslCliExecutor', 'cmd_store', 1, 2, 1).
python_method('DslCliExecutor', 'cmd_env', 1, 2, 2).
python_method('DslCliExecutor', 'cmd_assert_status', 1, 2, 3).
python_method('DslCliExecutor', 'cmd_assert_json', 1, 12, 10).
python_method('DslCliExecutor', 'cmd_set_header', 1, 2, 1).
python_method('DslCliExecutor', 'cmd_set_base_url', 1, 1, 1).
python_method('DslCliExecutor', 'run_script', 2, 11, 9).
python_method('DslCliExecutor', '_format_cmd', 1, 2, 1).
python_class('testql/sumd_parser.py', 'SumdMetadata').
python_class('testql/sumd_parser.py', 'SumdInterface').
python_class('testql/sumd_parser.py', 'SumdWorkflow').
python_class('testql/sumd_parser.py', 'SumdDocument').
python_class('testql/sumd_parser.py', 'SumdParser').
python_method('SumdParser', 'parse_file', 1, 1, 2).
python_method('SumdParser', 'parse', 1, 1, 6).
python_method('SumdParser', '_parse_metadata', 1, 8, 5).
python_method('SumdParser', '_parse_interfaces', 1, 1, 2).
python_method('SumdParser', '_parse_workflows', 1, 4, 6).
python_method('SumdParser', '_parse_testql_scenarios', 1, 11, 7).
python_method('SumdParser', '_parse_architecture', 1, 3, 4).
python_method('SumdParser', '_extract_section', 2, 2, 4).
python_method('SumdParser', 'generate_testql_scenarios', 1, 5, 5).
python_class('testql/toon_parser.py', 'ToonParser').
python_method('ToonParser', '__init__', 0, 1, 1).
python_method('ToonParser', 'parse_file', 1, 1, 2).
python_method('ToonParser', 'parse', 1, 4, 7).
python_method('ToonParser', '_parse_api_block', 1, 3, 3).
python_method('ToonParser', '_parse_assert_block', 1, 2, 4).
python_method('ToonParser', '_parse_log_block', 1, 2, 2).
python_class('testql/topology/builder.py', 'TopologyBuilder').
python_method('TopologyBuilder', '__init__', 2, 1, 0).
python_method('TopologyBuilder', 'build', 1, 4, 17).
python_method('TopologyBuilder', '_add_type_nodes', 3, 2, 4).
python_method('TopologyBuilder', '_add_interface_nodes', 3, 2, 7).
python_method('TopologyBuilder', '_add_dependency_nodes', 3, 2, 6).
python_method('TopologyBuilder', '_add_evidence_nodes', 3, 2, 6).
python_method('TopologyBuilder', '_add_page_schema_nodes', 3, 5, 8).
python_class('testql/topology/generator.py', 'NodeMappingConfig').
python_class('testql/topology/generator.py', 'TopologyScenarioGenerator').
python_method('TopologyScenarioGenerator', '__init__', 2, 3, 1).
python_method('TopologyScenarioGenerator', 'from_trace', 1, 4, 6).
python_method('TopologyScenarioGenerator', 'from_path', 1, 1, 2).
python_method('TopologyScenarioGenerator', 'to_testtoon', 1, 1, 1).
python_method('TopologyScenarioGenerator', '_node_to_step', 1, 8, 8).
python_method('TopologyScenarioGenerator', '_interface_to_step', 2, 6, 6).
python_method('TopologyScenarioGenerator', '_page_to_step', 1, 2, 2).
python_method('TopologyScenarioGenerator', '_link_to_step', 1, 2, 2).
python_method('TopologyScenarioGenerator', '_form_to_step', 1, 4, 3).
python_method('TopologyScenarioGenerator', '_asset_to_step', 1, 2, 2).
python_method('TopologyScenarioGenerator', '_dependency_to_step', 1, 1, 2).
python_method('TopologyScenarioGenerator', '_evidence_to_step', 1, 2, 2).
python_method('TopologyScenarioGenerator', '_attach_assertions', 2, 8, 5).
python_method('TopologyScenarioGenerator', '_outgoing_edges', 1, 3, 0).
python_method('TopologyScenarioGenerator', '_condition_to_assertion', 1, 2, 1).
python_method('TopologyScenarioGenerator', '_location', 1, 2, 2).
python_method('TopologyScenarioGenerator', '_protocol_for_node', 1, 2, 1).
python_class('testql/topology/models.py', 'Condition').
python_method('Condition', 'to_dict', 0, 4, 1).
python_class('testql/topology/models.py', 'TopologyNode').
python_method('TopologyNode', 'to_dict', 1, 4, 4).
python_class('testql/topology/models.py', 'TopologyEdge').
python_method('TopologyEdge', 'to_dict', 0, 4, 1).
python_class('testql/topology/models.py', 'TraversalTrace').
python_method('TraversalTrace', 'to_dict', 0, 4, 2).
python_class('testql/topology/models.py', 'TopologyManifest').
python_method('TopologyManifest', 'to_dict', 1, 4, 2).
python_method('TopologyManifest', 'node', 1, 3, 1).
python_class('testql/topology/sitemap.py', '_SubpageParser').
python_method('_SubpageParser', '__init__', 0, 1, 2).
python_method('_SubpageParser', 'handle_starttag', 2, 9, 2).
python_method('_SubpageParser', 'handle_data', 1, 2, 2).
python_method('_SubpageParser', 'handle_endtag', 1, 4, 2).
python_class('tests/test_adapter_capture_syntax.py', 'TestTestToonCaptureByIndex').
python_method('TestTestToonCaptureByIndex', 'test_parse_attaches_capture_to_first_step', 0, 7, 4).
python_method('TestTestToonCaptureByIndex', 'test_round_trip', 0, 4, 3).
python_class('tests/test_adapter_capture_syntax.py', 'TestTestToonCaptureByName').
python_method('TestTestToonCaptureByName', 'test_parse_attaches_via_step_name', 0, 3, 2).
python_class('tests/test_adapter_capture_syntax.py', 'TestUnresolvedCaptureSilentlyDropped').
python_method('TestUnresolvedCaptureSilentlyDropped', 'test_unknown_target_is_ignored', 0, 2, 3).
python_class('tests/test_adapter_capture_syntax.py', 'TestSqlAdapterCapture').
python_method('TestSqlAdapterCapture', 'test_parse_attaches_to_named_step', 0, 7, 5).
python_method('TestSqlAdapterCapture', 'test_round_trip_emits_capture_section', 0, 3, 3).
python_method('TestSqlAdapterCapture', 'test_unknown_query_is_ignored', 0, 2, 5).
python_class('tests/test_adapter_capture_syntax.py', 'TestSqlCaptureExecutesEndToEnd').
python_method('TestSqlCaptureExecutesEndToEnd', 'test_parsed_capture_chains_through_runner', 0, 2, 6).
python_class('tests/test_adapters_base.py', '_DummyAdapter').
python_method('_DummyAdapter', 'detect', 1, 1, 3).
python_method('_DummyAdapter', 'parse', 1, 1, 4).
python_method('_DummyAdapter', 'render', 1, 1, 0).
python_class('tests/test_adapters_base.py', 'TestDSLDetectionResult').
python_method('TestDSLDetectionResult', 'test_defaults', 0, 4, 1).
python_class('tests/test_adapters_base.py', 'TestValidationIssue').
python_method('TestValidationIssue', 'test_minimal', 0, 3, 1).
python_class('tests/test_adapters_base.py', 'TestReadSource').
python_method('TestReadSource', 'test_string_passthrough', 0, 3, 1).
python_method('TestReadSource', 'test_path_reads_file', 1, 3, 3).
python_method('TestReadSource', 'test_string_pointing_to_file', 1, 3, 3).
python_class('tests/test_adapters_base.py', 'TestAdapterRegistry').
python_method('TestAdapterRegistry', 'test_register_and_get', 0, 3, 5).
python_method('TestAdapterRegistry', 'test_register_requires_name', 0, 1, 4).
python_method('TestAdapterRegistry', 'test_unregister_and_clear', 0, 3, 7).
python_method('TestAdapterRegistry', 'test_by_extension', 1, 3, 5).
python_method('TestAdapterRegistry', 'test_by_extension_prefers_longest_match', 0, 3, 9).
python_method('TestAdapterRegistry', 'test_detect_falls_back_to_content', 0, 3, 4).
python_method('TestAdapterRegistry', 'test_detect_returns_none_when_no_match', 0, 2, 4).
python_class('tests/test_adapters_base.py', 'TestDefaultRegistry').
python_method('TestDefaultRegistry', 'test_singleton', 0, 2, 1).
python_method('TestDefaultRegistry', 'test_testtoon_preregistered', 0, 3, 1).
python_class('tests/test_adapters_base.py', 'TestBaseAdapterDefaultValidate').
python_method('TestBaseAdapterDefaultValidate', 'test_validate_default_empty', 0, 2, 3).
python_class('tests/test_api_handler.py', 'TestCollectAssert').
python_method('TestCollectAssert', 'test_no_assert', 0, 2, 1).
python_method('TestCollectAssert', 'test_assert_status', 0, 2, 1).
python_method('TestCollectAssert', 'test_assert_status_invalid_defaults_200', 0, 2, 1).
python_method('TestCollectAssert', 'test_assert_ok', 0, 2, 1).
python_method('TestCollectAssert', 'test_assert_json_three_parts', 0, 2, 1).
python_method('TestCollectAssert', 'test_assert_contains_one_part', 0, 2, 1).
python_method('TestCollectAssert', 'test_multiple_asserts', 0, 2, 1).
python_method('TestCollectAssert', 'test_stops_at_non_assert', 0, 2, 1).
python_method('TestCollectAssert', 'test_empty', 0, 2, 1).
python_class('tests/test_api_handler.py', 'TestHandleApi').
python_method('TestHandleApi', 'test_simple_get', 0, 6, 1).
python_method('TestHandleApi', 'test_post_with_assert_status', 0, 3, 1).
python_method('TestHandleApi', 'test_with_assert_json', 0, 3, 1).
python_method('TestHandleApi', 'test_multiple_api_calls', 0, 2, 2).
python_method('TestHandleApi', 'test_stops_at_non_api', 0, 2, 2).
python_method('TestHandleApi', 'test_columns_without_assert', 0, 2, 1).
python_class('tests/test_browser_discovery.py', 'FakePlaywright').
python_method('FakePlaywright', '__enter__', 0, 1, 0).
python_method('FakePlaywright', '__exit__', 0, 1, 0).
python_method('FakePlaywright', 'chromium', 0, 1, 1).
python_class('tests/test_browser_discovery.py', 'FakeBrowserLauncher').
python_method('FakeBrowserLauncher', 'launch', 0, 1, 1).
python_class('tests/test_browser_discovery.py', 'FakeBrowser').
python_method('FakeBrowser', 'new_page', 0, 1, 1).
python_method('FakeBrowser', 'close', 0, 1, 0).
python_class('tests/test_browser_discovery.py', 'FakePage').
python_method('FakePage', '__init__', 0, 1, 0).
python_method('FakePage', 'on', 2, 1, 2).
python_method('FakePage', 'goto', 3, 3, 3).
python_method('FakePage', 'title', 0, 1, 0).
python_method('FakePage', 'evaluate', 1, 5, 0).
python_class('tests/test_browser_discovery.py', 'FakePlaywrightImport').
python_method('FakePlaywrightImport', 'sync_playwright', 0, 1, 1).
python_class('tests/test_cli.py', 'TestCliHelp').
python_method('TestCliHelp', 'test_help', 0, 3, 3).
python_method('TestCliHelp', 'test_version', 0, 3, 2).
python_method('TestCliHelp', 'test_subcommands_listed', 0, 4, 2).
python_method('TestCliHelp', 'test_run_help', 0, 2, 2).
python_method('TestCliHelp', 'test_suite_help', 0, 2, 2).
python_method('TestCliHelp', 'test_list_help', 0, 2, 2).
python_method('TestCliHelp', 'test_generate_help', 0, 2, 2).
python_method('TestCliHelp', 'test_endpoints_help', 0, 2, 2).
python_method('TestCliHelp', 'test_init_help', 0, 2, 2).
python_method('TestCliHelp', 'test_echo_help', 0, 2, 2).
python_class('tests/test_cli.py', 'TestSuiteCommand').
python_method('TestSuiteCommand', 'test_suite_no_files_exits_1', 1, 2, 3).
python_method('TestSuiteCommand', 'test_list_no_files', 1, 3, 3).
python_method('TestSuiteCommand', 'test_list_with_toon_file', 1, 2, 4).
python_method('TestSuiteCommand', 'test_list_format_simple', 1, 2, 4).
python_method('TestSuiteCommand', 'test_list_format_json', 1, 2, 4).
python_class('tests/test_cli_no_block.py', 'TestNoInputCall').
python_method('TestNoInputCall', 'test_no_input_in_source', 0, 6, 4).
python_method('TestNoInputCall', 'test_no_subprocess_in_check_and_upgrade', 0, 4, 1).
python_class('tests/test_cli_no_block.py', 'TestCheckAndUpgradeNeverBlocks').
python_method('TestCheckAndUpgradeNeverBlocks', 'test_runs_when_up_to_date', 0, 1, 2).
python_method('TestCheckAndUpgradeNeverBlocks', 'test_runs_when_outdated', 1, 4, 3).
python_method('TestCheckAndUpgradeNeverBlocks', 'test_runs_when_pypi_unreachable', 0, 1, 2).
python_method('TestCheckAndUpgradeNeverBlocks', 'test_runs_when_version_unavailable', 0, 1, 3).
python_method('TestCheckAndUpgradeNeverBlocks', 'test_is_tty_agnostic', 0, 1, 2).
python_class('tests/test_cli_no_block.py', 'TestMainNeverBlocks').
python_method('TestMainNeverBlocks', 'test_main_via_runner', 0, 3, 3).
python_method('TestMainNeverBlocks', 'test_main_does_not_call_input', 0, 2, 5).
python_class('tests/test_conversation_live_llm.py', 'TestLLMProviderResolution').
python_method('TestLLMProviderResolution', 'test_defaults_to_mock', 1, 2, 3).
python_method('TestLLMProviderResolution', 'test_live_flag_selects_live_provider', 1, 2, 3).
python_method('TestLLMProviderResolution', 'test_live_without_key_raises', 1, 1, 3).
python_class('tests/test_conversation_live_llm.py', 'TestLiveLLMParsing').
python_method('TestLiveLLMParsing', 'test_parse_json_object_strips_fence', 0, 2, 1).
python_class('tests/test_conversation_nlp2dsl.py', 'TestAssertJsonSection').
python_method('TestAssertJsonSection', 'test_assert_json_attached_to_step', 0, 6, 4).
python_method('TestAssertJsonSection', 'test_assert_json_executor_uses_last_response', 0, 2, 6).
python_class('tests/test_conversation_nlp2dsl.py', 'TestConversationGenerator').
python_method('TestConversationGenerator', 'test_from_trace_builds_plan', 0, 4, 5).
python_class('tests/test_conversation_nlp2dsl.py', 'TestConversationIRParse').
python_method('TestConversationIRParse', 'test_parse_conversation_sections', 0, 13, 4).
python_method('TestConversationIRParse', 'test_nlp2dsl_adapter_detects_conversation', 0, 2, 2).
python_method('TestConversationIRParse', 'test_conversation_source_loads', 0, 2, 2).
python_class('tests/test_conversation_nlp2dsl.py', 'TestConversationRunner').
python_method('TestConversationRunner', 'test_dry_run_skips_http', 0, 3, 5).
python_class('tests/test_conversation_nlp2dsl.py', 'TestArtifactChecker').
python_method('TestArtifactChecker', 'test_file_hash', 1, 2, 7).
python_class('tests/test_conversation_nlp2dsl.py', 'FakeClient').
python_method('FakeClient', 'chatstart', 1, 1, 1).
python_method('FakeClient', 'chatmessage', 1, 2, 2).
python_class('tests/test_converter.py', 'TestRow').
python_method('TestRow', 'test_row_creation', 0, 2, 1).
python_method('TestRow', 'test_row_empty', 0, 2, 1).
python_method('TestRow', 'test_row_multiple_fields', 0, 3, 1).
python_class('tests/test_converter.py', 'TestSection').
python_method('TestSection', 'test_section_creation', 0, 5, 1).
python_method('TestSection', 'test_section_with_rows', 0, 2, 2).
python_method('TestSection', 'test_section_with_comment', 0, 2, 1).
python_class('tests/test_converter.py', 'TestConvertOqlToTesttoon').
python_method('TestConvertOqlToTesttoon', 'test_navigate_command', 0, 3, 1).
python_method('TestConvertOqlToTesttoon', 'test_scenario_name_from_filename', 0, 2, 2).
python_method('TestConvertOqlToTesttoon', 'test_header_present', 0, 4, 1).
python_method('TestConvertOqlToTesttoon', 'test_click_converts_to_flow', 0, 2, 1).
python_method('TestConvertOqlToTesttoon', 'test_assert_text_converts', 0, 2, 1).
python_method('TestConvertOqlToTesttoon', 'test_empty_source', 0, 2, 1).
python_method('TestConvertOqlToTesttoon', 'test_get_request', 0, 2, 1).
python_method('TestConvertOqlToTesttoon', 'test_default_filename', 0, 2, 1).
python_method('TestConvertOqlToTesttoon', 'test_returns_string', 0, 2, 2).
python_method('TestConvertOqlToTesttoon', 'test_multiline_script', 0, 3, 2).
python_class('tests/test_converter.py', 'TestConvertFile').
python_method('TestConvertFile', 'test_creates_output_file', 1, 2, 3).
python_method('TestConvertFile', 'test_output_filename_pattern', 1, 2, 2).
python_method('TestConvertFile', 'test_oql_extension', 1, 2, 2).
python_method('TestConvertFile', 'test_output_is_in_same_dir', 1, 2, 2).
python_method('TestConvertFile', 'test_output_content_has_scenario', 1, 2, 3).
python_method('TestConvertFile', 'test_returns_path', 1, 2, 3).
python_class('tests/test_converter.py', 'TestConvertDirectory').
python_method('TestConvertDirectory', 'test_empty_directory', 1, 2, 1).
python_method('TestConvertDirectory', 'test_converts_tql_files', 1, 2, 3).
python_method('TestConvertDirectory', 'test_converts_oql_files', 1, 2, 3).
python_method('TestConvertDirectory', 'test_converts_multiple_files', 1, 2, 3).
python_method('TestConvertDirectory', 'test_returns_list_of_paths', 1, 2, 4).
python_method('TestConvertDirectory', 'test_recursive_subdirectory', 1, 3, 4).
python_method('TestConvertDirectory', 'test_ignores_non_tql_files', 1, 2, 2).
python_class('tests/test_converter_handlers.py', 'TestParseApiArgs').
python_method('TestParseApiArgs', 'test_method_and_path', 0, 2, 1).
python_method('TestParseApiArgs', 'test_quoted_path', 0, 2, 1).
python_method('TestParseApiArgs', 'test_no_args_defaults', 0, 2, 1).
python_method('TestParseApiArgs', 'test_strips_json_body', 0, 2, 1).
python_method('TestParseApiArgs', 'test_uppercases_method', 0, 2, 1).
python_class('tests/test_converter_handlers.py', 'TestParseTargetFromArgs').
python_method('TestParseTargetFromArgs', 'test_double_quoted', 0, 2, 1).
python_method('TestParseTargetFromArgs', 'test_single_quoted', 0, 2, 1).
python_method('TestParseTargetFromArgs', 'test_unquoted_first_token', 0, 2, 1).
python_method('TestParseTargetFromArgs', 'test_empty', 0, 2, 1).
python_class('tests/test_converter_handlers.py', 'TestParseMetaFromArgs').
python_method('TestParseMetaFromArgs', 'test_json_dict', 0, 2, 1).
python_method('TestParseMetaFromArgs', 'test_no_meta', 0, 2, 1).
python_method('TestParseMetaFromArgs', 'test_raw_dict_fallback', 0, 2, 1).
python_class('tests/test_converter_handlers.py', 'TestParseCommands').
python_method('TestParseCommands', 'test_navigate', 0, 2, 1).
python_method('TestParseCommands', 'test_comment_collected', 0, 3, 3).
python_method('TestParseCommands', 'test_blank_line', 0, 2, 1).
python_method('TestParseCommands', 'test_empty_source', 0, 2, 1).
python_method('TestParseCommands', 'test_uppercase_cmd', 0, 2, 1).
python_class('tests/test_converter_handlers.py', 'TestDetectScenarioType').
python_method('TestDetectScenarioType', 'test_api_only', 0, 2, 1).
python_method('TestDetectScenarioType', 'test_gui_navigate', 0, 2, 1).
python_method('TestDetectScenarioType', 'test_encoder', 0, 2, 1).
python_method('TestDetectScenarioType', 'test_e2e', 0, 2, 1).
python_method('TestDetectScenarioType', 'test_interaction_record', 0, 2, 1).
python_class('tests/test_converter_handlers.py', 'TestExtractScenarioName').
python_method('TestExtractScenarioName', 'test_from_comment', 0, 2, 1).
python_method('TestExtractScenarioName', 'test_fallback_filename', 0, 2, 2).
python_method('TestExtractScenarioName', 'test_skip_usage_comments', 0, 2, 2).
python_class('tests/test_converter_handlers.py', 'TestHandleWait').
python_method('TestHandleWait', 'test_single_wait', 0, 5, 2).
python_method('TestHandleWait', 'test_multiple_waits', 0, 2, 2).
python_method('TestHandleWait', 'test_invalid_ms_defaults_100', 0, 2, 1).
python_method('TestHandleWait', 'test_stops_at_non_wait', 0, 2, 2).
python_class('tests/test_converter_handlers.py', 'TestHandleNavigate').
python_method('TestHandleNavigate', 'test_single_navigate', 0, 5, 1).
python_method('TestHandleNavigate', 'test_navigate_with_wait', 0, 3, 1).
python_method('TestHandleNavigate', 'test_multiple_navigates', 0, 2, 2).
python_method('TestHandleNavigate', 'test_stops_at_non_navigate', 0, 2, 2).
python_class('tests/test_converter_handlers.py', 'TestHandleSelect').
python_method('TestHandleSelect', 'test_select_option', 0, 5, 1).
python_method('TestHandleSelect', 'test_plain_select', 0, 2, 1).
python_method('TestHandleSelect', 'test_multiple_selects', 0, 2, 2).
python_method('TestHandleSelect', 'test_stops_at_non_select', 0, 2, 1).
python_class('tests/test_converter_handlers.py', 'TestHandleEncoder').
python_method('TestHandleEncoder', 'test_encoder_focus', 0, 5, 1).
python_method('TestHandleEncoder', 'test_encoder_scroll', 0, 3, 1).
python_method('TestHandleEncoder', 'test_encoder_scroll_invalid_value', 0, 2, 1).
python_method('TestHandleEncoder', 'test_encoder_with_wait', 0, 3, 1).
python_method('TestHandleEncoder', 'test_multiple_encoder_commands', 0, 2, 2).
python_class('tests/test_converter_handlers.py', 'TestHandleFlow').
python_method('TestHandleFlow', 'test_app_start', 0, 3, 1).
python_method('TestHandleFlow', 'test_session_start', 0, 2, 1).
python_method('TestHandleFlow', 'test_multiple_flow_commands', 0, 2, 2).
python_method('TestHandleFlow', 'test_stops_at_non_flow', 0, 2, 1).
python_method('TestHandleFlow', 'test_flow_commands_frozenset', 0, 3, 0).
python_class('tests/test_converter_handlers.py', 'TestHandleRecord').
python_method('TestHandleRecord', 'test_record_start', 0, 4, 1).
python_method('TestHandleRecord', 'test_record_stop', 0, 3, 1).
python_class('tests/test_converter_handlers.py', 'TestHandleInclude').
python_method('TestHandleInclude', 'test_include', 0, 4, 1).
python_class('tests/test_converter_handlers.py', 'TestHandleUnknown').
python_method('TestHandleUnknown', 'test_unknown_command', 0, 3, 1).
python_class('tests/test_converter_handlers.py', 'TestDispatch').
python_method('TestDispatch', 'test_dispatches_navigate', 0, 2, 1).
python_method('TestDispatch', 'test_dispatches_wait', 0, 2, 1).
python_method('TestDispatch', 'test_dispatches_select', 0, 2, 1).
python_method('TestDispatch', 'test_dispatches_encoder', 0, 2, 1).
python_method('TestDispatch', 'test_dispatches_flow', 0, 2, 1).
python_method('TestDispatch', 'test_dispatches_record_start', 0, 2, 1).
python_method('TestDispatch', 'test_dispatches_record_stop', 0, 2, 1).
python_method('TestDispatch', 'test_dispatches_include', 0, 2, 1).
python_method('TestDispatch', 'test_dispatches_unknown', 0, 2, 1).
python_class('tests/test_detectors.py', 'TestEndpointInfoModel').
python_method('TestEndpointInfoModel', 'test_to_testql_api_call', 1, 3, 2).
python_method('TestEndpointInfoModel', 'test_defaults', 1, 5, 1).
python_class('tests/test_detectors.py', 'TestFastAPIDetector').
python_method('TestFastAPIDetector', 'test_detects_route_decorator', 1, 7, 3).
python_method('TestFastAPIDetector', 'test_empty_project', 1, 2, 2).
python_method('TestFastAPIDetector', 'test_non_route_decorators_ignored', 1, 2, 4).
python_class('tests/test_detectors.py', 'TestFlaskDetector').
python_method('TestFlaskDetector', 'test_detects_route', 1, 2, 4).
python_method('TestFlaskDetector', 'test_empty_project', 1, 2, 2).
python_class('tests/test_detectors.py', 'TestUnifiedDetector').
python_method('TestUnifiedDetector', 'test_returns_list', 1, 2, 3).
python_method('TestUnifiedDetector', 'test_detects_fastapi', 1, 2, 4).
python_method('TestUnifiedDetector', 'test_detectors_used_populated', 1, 2, 3).
python_class('tests/test_detectors.py', 'TestOpenAPIDetector').
python_method('TestOpenAPIDetector', 'test_empty_project', 1, 2, 2).
python_method('TestOpenAPIDetector', 'test_detects_yaml_spec', 1, 6, 3).
python_method('TestOpenAPIDetector', 'test_detects_json_spec', 1, 2, 5).
python_method('TestOpenAPIDetector', 'test_framework_is_openapi', 1, 2, 3).
python_method('TestOpenAPIDetector', 'test_base_path_from_servers', 1, 2, 3).
python_method('TestOpenAPIDetector', 'test_base_path_swagger2', 1, 2, 3).
python_method('TestOpenAPIDetector', 'test_x_extension_methods_skipped', 1, 2, 4).
python_method('TestOpenAPIDetector', 'test_invalid_yaml_skipped', 1, 2, 4).
python_method('TestOpenAPIDetector', 'test_spec_without_paths_skipped', 1, 2, 3).
python_class('tests/test_detectors.py', 'TestConfigDetector').
python_method('TestConfigDetector', 'test_empty_project', 1, 2, 2).
python_method('TestConfigDetector', 'test_detects_docker_compose_services', 1, 6, 4).
python_method('TestConfigDetector', 'test_unified_does_not_dedup_docker_services', 1, 5, 4).
python_class('tests/test_detectors.py', 'TestExpressDetector').
python_method('TestExpressDetector', 'test_empty_project', 1, 2, 2).
python_method('TestExpressDetector', 'test_detects_app_get', 1, 3, 4).
python_method('TestExpressDetector', 'test_detects_router_post', 1, 2, 4).
python_method('TestExpressDetector', 'test_framework_is_express', 1, 2, 4).
python_method('TestExpressDetector', 'test_typescript_file_detected', 1, 2, 4).
python_class('tests/test_discovery.py', 'TestDiscoveryCore').
python_method('TestDiscoveryCore', 'test_empty_directory_is_inferred', 1, 3, 1).
python_method('TestDiscoveryCore', 'test_python_package_probe_detects_fastapi', 0, 6, 2).
python_method('TestDiscoveryCore', 'test_node_package_probe_detects_node_and_frontend_markers', 0, 6, 1).
python_method('TestDiscoveryCore', 'test_openapi_probe_detects_openapi3_interface', 0, 5, 1).
python_method('TestDiscoveryCore', 'test_dockerfile_probe_detects_container_metadata', 0, 4, 1).
python_method('TestDiscoveryCore', 'test_compose_probe_detects_services', 0, 3, 2).
python_method('TestDiscoveryCore', 'test_registry_returns_raw_probe_results', 0, 3, 3).
python_method('TestDiscoveryCore', 'test_self_discovery_detects_current_project_root', 1, 5, 0).
python_method('TestDiscoveryCore', 'test_self_discovery_detects_testql_package_directory', 1, 5, 0).
python_class('tests/test_discovery.py', 'TestDiscoveryCli').
python_method('TestDiscoveryCli', 'test_discover_summary_output', 0, 4, 3).
python_method('TestDiscoveryCli', 'test_discover_json_output', 0, 4, 4).
python_method('TestDiscoveryCli', 'test_discover_manifest_output', 0, 4, 3).
python_method('TestDiscoveryCli', 'test_discover_missing_path_exits_nonzero', 0, 3, 3).
python_class('tests/test_dispatcher.py', 'TestCommandDispatcher').
python_method('TestCommandDispatcher', 'interpreter', 0, 1, 1).
python_method('TestCommandDispatcher', 'dispatcher', 1, 1, 1).
python_method('TestCommandDispatcher', 'test_auto_discovery', 1, 7, 2).
python_method('TestCommandDispatcher', 'test_has_command', 1, 5, 1).
python_method('TestCommandDispatcher', 'test_dispatch_known_command', 2, 3, 3).
python_method('TestCommandDispatcher', 'test_dispatch_unknown_command', 2, 3, 3).
python_method('TestCommandDispatcher', 'test_dispatch_with_suggestion', 2, 3, 3).
python_method('TestCommandDispatcher', 'test_register_custom_command', 2, 4, 6).
python_method('TestCommandDispatcher', 'test_case_insensitive_dispatch', 1, 4, 1).
python_class('tests/test_dispatcher.py', 'TestDispatcherIntegration').
python_method('TestDispatcherIntegration', 'interpreter', 0, 1, 1).
python_method('TestDispatcherIntegration', 'test_interpreter_uses_dispatcher', 1, 3, 2).
python_method('TestDispatcherIntegration', 'test_dispatch_through_interpreter', 1, 2, 3).
python_method('TestDispatcherIntegration', 'test_all_mixin_commands_discovered', 1, 11, 1).
python_class('tests/test_doql_parser_sumd_gen.py', 'TestDoqlParser').
python_method('TestDoqlParser', 'test_init', 0, 2, 2).
python_method('TestDoqlParser', 'test_parse_empty', 0, 4, 2).
python_method('TestDoqlParser', 'test_parse_app_block', 0, 3, 2).
python_method('TestDoqlParser', 'test_parse_entities', 0, 4, 2).
python_method('TestDoqlParser', 'test_entity_fields', 0, 4, 4).
python_method('TestDoqlParser', 'test_entity_fields_contain_domain', 0, 4, 4).
python_method('TestDoqlParser', 'test_parse_workflow', 0, 4, 3).
python_method('TestDoqlParser', 'test_parse_interface', 0, 4, 3).
python_method('TestDoqlParser', 'test_parse_resets_between_calls', 0, 4, 2).
python_method('TestDoqlParser', 'test_parse_file', 1, 2, 2).
python_method('TestDoqlParser', 'test_no_app_block', 0, 3, 3).
python_class('tests/test_doql_parser_sumd_gen.py', 'TestHeaderSection').
python_method('TestHeaderSection', 'test_contains_project_name', 0, 2, 2).
python_method('TestHeaderSection', 'test_returns_list', 0, 2, 2).
python_class('tests/test_doql_parser_sumd_gen.py', 'TestMetadataSection').
python_method('TestMetadataSection', 'test_contains_name', 0, 2, 2).
python_method('TestMetadataSection', 'test_contains_version', 0, 2, 2).
python_class('tests/test_doql_parser_sumd_gen.py', 'TestArchitectureSection').
python_method('TestArchitectureSection', 'test_contains_code_block', 0, 2, 1).
python_method('TestArchitectureSection', 'test_mentions_doql', 0, 2, 2).
python_class('tests/test_doql_parser_sumd_gen.py', 'TestGenerateSumd').
python_method('TestGenerateSumd', '_make_echo', 0, 1, 4).
python_method('TestGenerateSumd', 'test_returns_string', 1, 2, 3).
python_method('TestGenerateSumd', 'test_contains_project_name', 1, 2, 3).
python_method('TestGenerateSumd', 'test_contains_version', 1, 2, 2).
python_method('TestGenerateSumd', 'test_contains_metadata_section', 1, 2, 2).
python_method('TestGenerateSumd', 'test_contains_architecture_section', 1, 2, 2).
python_method('TestGenerateSumd', 'test_uses_path_name_as_fallback', 1, 2, 3).
python_method('TestGenerateSumd', 'test_interfaces_included', 1, 2, 2).
python_method('TestGenerateSumd', 'test_entities_not_in_base_output', 1, 2, 4).
python_method('TestGenerateSumd', 'test_workflows_included', 1, 2, 2).
python_class('tests/test_doql_parser_sumd_gen.py', 'TestApiContractSection').
python_method('TestApiContractSection', 'test_no_endpoints_returns_empty', 0, 2, 2).
python_method('TestApiContractSection', 'test_with_endpoints', 0, 3, 3).
python_method('TestApiContractSection', 'test_endpoint_with_description', 0, 2, 3).
python_class('tests/test_doql_parser_sumd_gen.py', 'TestWorkflowsTableSection').
python_method('TestWorkflowsTableSection', 'test_no_workflows_returns_empty', 0, 2, 2).
python_method('TestWorkflowsTableSection', 'test_with_workflows', 0, 3, 4).
python_method('TestWorkflowsTableSection', 'test_long_command_truncated', 0, 2, 4).
python_class('tests/test_doql_parser_sumd_gen.py', 'TestConfigurationSection').
python_method('TestConfigurationSection', 'test_basic', 0, 3, 3).
python_method('TestConfigurationSection', 'test_with_base_url', 0, 2, 3).
python_class('tests/test_doql_parser_sumd_gen.py', 'TestLlmSuggestionsSection').
python_method('TestLlmSuggestionsSection', 'test_has_testql_commands', 0, 2, 4).
python_method('TestLlmSuggestionsSection', 'test_with_test_workflow', 0, 2, 4).
python_method('TestLlmSuggestionsSection', 'test_with_install_workflow', 0, 2, 4).
python_class('tests/test_doql_parser_sumd_gen.py', 'TestSaveSumd').
python_method('TestSaveSumd', 'test_saves_to_default_path', 1, 3, 3).
python_method('TestSaveSumd', 'test_saves_to_custom_path', 1, 3, 4).
python_class('tests/test_echo.py', 'TestFindDoqlFile').
python_method('TestFindDoqlFile', 'test_finds_less_file', 1, 2, 2).
python_method('TestFindDoqlFile', 'test_prefers_less_over_css', 1, 2, 2).
python_method('TestFindDoqlFile', 'test_returns_none_when_missing', 1, 2, 1).
python_class('tests/test_echo.py', 'TestFindToonPath').
python_method('TestFindToonPath', 'test_returns_testql_scenarios_if_exists', 1, 2, 2).
python_method('TestFindToonPath', 'test_falls_back_to_path', 1, 2, 1).
python_class('tests/test_echo.py', 'TestGenerateContext').
python_method('TestGenerateContext', 'test_returns_dict_with_project', 1, 3, 1).
python_method('TestGenerateContext', 'test_no_doql_when_excluded', 1, 2, 1).
python_method('TestGenerateContext', 'test_no_toon_when_excluded', 1, 2, 1).
python_method('TestGenerateContext', 'test_empty_contracts_when_no_toon_files', 1, 2, 2).
python_class('tests/test_echo.py', 'TestExtractEndpoint').
python_method('TestExtractEndpoint', 'test_dict_value', 0, 4, 1).
python_method('TestExtractEndpoint', 'test_string_value', 0, 4, 1).
python_class('tests/test_echo.py', 'TestExtractAssert').
python_method('TestExtractAssert', 'test_basic', 0, 3, 1).
python_class('tests/test_echo.py', 'TestParseToonScenarios').
python_method('TestParseToonScenarios', 'test_empty_dir', 1, 2, 1).
python_method('TestParseToonScenarios', 'test_parses_single_file', 1, 4, 3).
python_method('TestParseToonScenarios', 'test_multiple_http_methods', 1, 2, 3).
python_method('TestParseToonScenarios', 'test_skips_empty_files', 1, 2, 2).
python_method('TestParseToonScenarios', 'test_assert_blocks_parsed', 1, 2, 3).
python_class('tests/test_echo.py', 'TestFmtInterfaces').
python_method('TestFmtInterfaces', 'test_empty_when_no_system_model', 0, 2, 1).
python_method('TestFmtInterfaces', 'test_shows_interfaces', 0, 2, 2).
python_method('TestFmtInterfaces', 'test_empty_interfaces_returns_empty', 0, 2, 1).
python_class('tests/test_echo.py', 'TestFmtWorkflows').
python_method('TestFmtWorkflows', 'test_empty_when_no_workflows', 0, 2, 1).
python_method('TestFmtWorkflows', 'test_shows_workflow_name', 0, 2, 2).
python_class('tests/test_echo.py', 'TestFmtContracts').
python_method('TestFmtContracts', 'test_empty_when_no_contracts', 0, 2, 1).
python_method('TestFmtContracts', 'test_shows_contract_name', 0, 2, 2).
python_method('TestFmtContracts', 'test_truncates_long_endpoint_list', 0, 3, 3).
python_class('tests/test_echo.py', 'TestFmtEntities').
python_method('TestFmtEntities', 'test_empty_when_no_entities', 0, 2, 1).
python_method('TestFmtEntities', 'test_shows_entity_count', 0, 2, 2).
python_class('tests/test_echo.py', 'TestFormatTextOutput').
python_method('TestFormatTextOutput', 'test_returns_string', 1, 2, 3).
python_method('TestFormatTextOutput', 'test_contains_project_name', 1, 2, 2).
python_class('tests/test_echo_doql_parser.py', 'TestParseKvBlock').
python_method('TestParseKvBlock', 'test_simple', 0, 3, 1).
python_method('TestParseKvBlock', 'test_empty', 0, 2, 1).
python_method('TestParseKvBlock', 'test_no_colon_line_ignored', 0, 2, 1).
python_method('TestParseKvBlock', 'test_strips_trailing_semicolon', 0, 2, 1).
python_class('tests/test_echo_doql_parser.py', 'TestParseAppBlock').
python_method('TestParseAppBlock', 'test_parses_name_and_version', 0, 3, 1).
python_method('TestParseAppBlock', 'test_no_app_block_returns_empty', 0, 2, 1).
python_class('tests/test_echo_doql_parser.py', 'TestParseEntities').
python_method('TestParseEntities', 'test_count', 0, 2, 2).
python_method('TestParseEntities', 'test_entity_name', 0, 4, 1).
python_method('TestParseEntities', 'test_annotations_extracted', 0, 5, 2).
python_method('TestParseEntities', 'test_fields_extracted', 0, 4, 3).
python_method('TestParseEntities', 'test_no_entities_returns_empty', 0, 2, 1).
python_method('TestParseEntities', 'test_entity_without_annotations', 0, 4, 2).
python_class('tests/test_echo_doql_parser.py', 'TestParseInterfaces').
python_method('TestParseInterfaces', 'test_count', 0, 2, 2).
python_method('TestParseInterfaces', 'test_type', 0, 2, 1).
python_method('TestParseInterfaces', 'test_framework', 0, 2, 1).
python_method('TestParseInterfaces', 'test_no_interfaces', 0, 2, 1).
python_class('tests/test_echo_doql_parser.py', 'TestParseWorkflows').
python_method('TestParseWorkflows', 'test_count', 0, 2, 2).
python_method('TestParseWorkflows', 'test_name', 0, 2, 1).
python_method('TestParseWorkflows', 'test_trigger', 0, 2, 1).
python_method('TestParseWorkflows', 'test_steps', 0, 2, 2).
python_method('TestParseWorkflows', 'test_annotations', 0, 2, 1).
python_method('TestParseWorkflows', 'test_no_workflows', 0, 2, 1).
python_class('tests/test_echo_doql_parser.py', 'TestParseDeploy').
python_method('TestParseDeploy', 'test_platform', 0, 2, 1).
python_method('TestParseDeploy', 'test_no_deploy', 0, 2, 1).
python_class('tests/test_echo_doql_parser.py', 'TestParseEnvironment').
python_method('TestParseEnvironment', 'test_name', 0, 2, 1).
python_method('TestParseEnvironment', 'test_host', 0, 2, 1).
python_method('TestParseEnvironment', 'test_no_environment', 0, 2, 1).
python_class('tests/test_echo_doql_parser.py', 'TestParseIntegrations').
python_method('TestParseIntegrations', 'test_count', 0, 2, 2).
python_method('TestParseIntegrations', 'test_name', 0, 2, 1).
python_method('TestParseIntegrations', 'test_types_deduped', 0, 2, 2).
python_method('TestParseIntegrations', 'test_no_integrations', 0, 2, 1).
python_class('tests/test_echo_doql_parser.py', 'TestParseDoqlLess').
python_method('TestParseDoqlLess', 'test_returns_all_keys', 1, 2, 4).
python_method('TestParseDoqlLess', 'test_app_name_in_result', 1, 2, 2).
python_method('TestParseDoqlLess', 'test_entities_count', 1, 2, 3).
python_class('tests/test_echo_schemas_helpers.py', 'TestAPIContract').
python_method('TestAPIContract', 'test_defaults', 0, 4, 1).
python_class('tests/test_echo_schemas_helpers.py', 'TestEntity').
python_method('TestEntity', 'test_create', 0, 3, 1).
python_method('TestEntity', 'test_with_all_fields', 0, 3, 1).
python_class('tests/test_echo_schemas_helpers.py', 'TestWorkflow').
python_method('TestWorkflow', 'test_defaults', 0, 4, 1).
python_method('TestWorkflow', 'test_with_values', 0, 3, 1).
python_class('tests/test_echo_schemas_helpers.py', 'TestInterface').
python_method('TestInterface', 'test_create', 0, 3, 1).
python_method('TestInterface', 'test_no_framework', 0, 2, 1).
python_class('tests/test_echo_schemas_helpers.py', 'TestSystemModel').
python_method('TestSystemModel', 'test_defaults', 0, 4, 1).
python_class('tests/test_echo_schemas_helpers.py', 'TestProjectEcho').
python_method('TestProjectEcho', '_make_echo', 0, 1, 4).
python_method('TestProjectEcho', 'test_to_dict_has_keys', 0, 3, 2).
python_method('TestProjectEcho', 'test_to_dict_api_contract', 0, 3, 3).
python_method('TestProjectEcho', 'test_to_dict_interfaces', 0, 3, 3).
python_method('TestProjectEcho', 'test_to_dict_entities', 0, 3, 2).
python_method('TestProjectEcho', 'test_to_dict_workflows', 0, 3, 2).
python_method('TestProjectEcho', 'test_to_dict_is_json_serializable', 0, 2, 3).
python_method('TestProjectEcho', 'test_to_text_contains_project_name', 0, 2, 2).
python_method('TestProjectEcho', 'test_to_text_contains_interface', 0, 2, 3).
python_method('TestProjectEcho', 'test_to_text_contains_workflow', 0, 2, 2).
python_method('TestProjectEcho', 'test_to_text_contains_endpoints', 0, 2, 2).
python_method('TestProjectEcho', 'test_to_text_docker_deploy', 0, 2, 3).
python_method('TestProjectEcho', 'test_to_text_no_endpoints', 0, 2, 2).
python_method('TestProjectEcho', 'test_to_text_empty_interfaces', 0, 2, 3).
python_method('TestProjectEcho', 'test_to_dict_deploy_info', 0, 3, 2).
python_class('tests/test_echo_schemas_helpers.py', 'TestEchoHelpers').
python_method('TestEchoHelpers', 'test_collect_toon_data_missing_path', 2, 2, 6).
python_method('TestEchoHelpers', 'test_collect_toon_data_single_file', 2, 2, 5).
python_method('TestEchoHelpers', 'test_collect_toon_data_directory', 2, 2, 6).
python_method('TestEchoHelpers', 'test_collect_doql_data_missing', 2, 2, 6).
python_method('TestEchoHelpers', 'test_render_echo_json', 0, 2, 4).
python_method('TestEchoHelpers', 'test_render_echo_text', 0, 2, 3).
python_class('tests/test_generate_cmd.py', 'TestIsWorkspace').
python_method('TestIsWorkspace', 'test_has_pyproject_returns_false', 1, 2, 2).
python_method('TestIsWorkspace', 'test_has_setup_py_returns_false', 1, 2, 2).
python_method('TestIsWorkspace', 'test_workspace_dir_without_init', 1, 2, 2).
python_method('TestIsWorkspace', 'test_workspace_dir_with_init_returns_false', 1, 2, 3).
python_method('TestIsWorkspace', 'test_no_workspace_dirs_returns_false', 1, 2, 1).
python_method('TestIsWorkspace', 'test_multiple_workspace_dirs', 1, 2, 2).
python_class('tests/test_generate_cmd.py', 'TestGenerateCommand').
python_method('TestGenerateCommand', '_make_pipeline_ctx', 1, 2, 1).
python_method('TestGenerateCommand', 'test_analyze_only_single_project', 1, 2, 5).
python_method('TestGenerateCommand', 'test_analyze_only_workspace', 1, 2, 7).
python_method('TestGenerateCommand', 'test_generate_single_project', 1, 2, 5).
python_method('TestGenerateCommand', 'test_analyze_command', 1, 2, 5).
python_class('tests/test_generate_from_page_cli.py', 'TestGenerateFromPageCli').
python_method('TestGenerateFromPageCli', 'test_writes_scenario_with_expected_steps', 1, 8, 5).
python_method('TestGenerateFromPageCli', 'test_print_only_does_not_write_file', 1, 4, 5).
python_method('TestGenerateFromPageCli', 'test_max_steps_caps_output', 1, 4, 8).
python_class('tests/test_generate_from_page_cli.py', 'TestHealScenarioCli').
python_method('TestHealScenarioCli', '_scenario_with_broken_selectors', 0, 1, 0).
python_method('TestHealScenarioCli', 'test_heals_class_selector_via_fuzzy_match', 1, 7, 9).
python_method('TestHealScenarioCli', 'test_write_in_place', 1, 4, 9).
python_method('TestHealScenarioCli', 'test_section_header_brackets_not_treated_as_selectors', 1, 5, 9).
python_method('TestHealScenarioCli', 'test_data_testid_used_for_fuzzy_match', 1, 4, 7).
python_method('TestHealScenarioCli', 'test_unhealable_selector_reported', 1, 5, 8).
python_class('tests/test_generate_ir_cli.py', 'TestGenerateIRCLI').
python_method('TestGenerateIRCLI', 'test_command_exists', 0, 4, 2).
python_method('TestGenerateIRCLI', 'test_round_trip_to_stdout', 1, 3, 3).
python_method('TestGenerateIRCLI', 'test_writes_to_file', 1, 4, 6).
python_method('TestGenerateIRCLI', 'test_bad_from_arg_errors', 0, 3, 2).
python_method('TestGenerateIRCLI', 'test_legacy_generate_still_works', 0, 2, 2).
python_method('TestGenerateIRCLI', 'test_generate_ir_makefile_alias', 1, 4, 3).
python_method('TestGenerateIRCLI', 'test_generate_ir_taskfile_alias', 1, 4, 3).
python_method('TestGenerateIRCLI', 'test_generate_ir_docker_compose_alias', 1, 4, 3).
python_method('TestGenerateIRCLI', 'test_generate_ir_buf_alias', 1, 4, 3).
python_class('tests/test_generators.py', 'TestBaseAnalyzer').
python_method('TestBaseAnalyzer', 'test_init', 1, 4, 2).
python_method('TestBaseAnalyzer', 'test_get_exclude_dirs', 1, 4, 2).
python_method('TestBaseAnalyzer', 'test_should_exclude_path_venv', 1, 2, 2).
python_method('TestBaseAnalyzer', 'test_should_exclude_path_src', 1, 2, 2).
python_class('tests/test_generators.py', 'TestProjectAnalyzerDetectType').
python_method('TestProjectAnalyzerDetectType', 'test_detect_python_api_fastapi', 1, 2, 3).
python_method('TestProjectAnalyzerDetectType', 'test_detect_python_api_flask', 1, 2, 3).
python_method('TestProjectAnalyzerDetectType', 'test_detect_python_cli', 1, 2, 3).
python_method('TestProjectAnalyzerDetectType', 'test_detect_python_lib', 1, 2, 3).
python_method('TestProjectAnalyzerDetectType', 'test_detect_hardware', 1, 2, 3).
python_method('TestProjectAnalyzerDetectType', 'test_detect_mixed_default', 1, 2, 2).
python_method('TestProjectAnalyzerDetectType', 'test_detect_web_frontend', 1, 2, 3).
python_method('TestProjectAnalyzerDetectType', 'test_detect_web_frontend_missing_e2e_markers', 1, 2, 4).
python_class('tests/test_generators.py', 'TestTestPattern').
python_method('TestTestPattern', 'test_defaults', 0, 3, 1).
python_method('TestTestPattern', 'test_metadata', 0, 2, 1).
python_class('tests/test_generators.py', 'TestOqlScenarioConversion').
python_method('TestOqlScenarioConversion', 'test_oql_scenario_conversion', 1, 6, 7).
python_method('TestOqlScenarioConversion', 'test_convert_oql_command_wait', 0, 2, 3).
python_method('TestOqlScenarioConversion', 'test_convert_oql_command_encoder', 0, 4, 3).
python_method('TestOqlScenarioConversion', 'test_convert_oql_command_unknown', 0, 2, 3).
python_class('tests/test_generators.py', 'TestGeneratorConfig').
python_method('TestGeneratorConfig', 'test_build_api_test_config', 0, 6, 4).
python_method('TestGeneratorConfig', 'test_build_api_test_header', 0, 4, 4).
python_class('tests/test_graphql_adapter.py', 'TestClassifyOperation').
python_method('TestClassifyOperation', 'test_query', 0, 2, 1).
python_method('TestClassifyOperation', 'test_mutation', 0, 2, 1).
python_method('TestClassifyOperation', 'test_subscription', 0, 2, 1).
python_method('TestClassifyOperation', 'test_default_query', 0, 2, 1).
python_method('TestClassifyOperation', 'test_empty', 0, 2, 1).
python_class('tests/test_graphql_adapter.py', 'TestParseVariables').
python_method('TestParseVariables', 'test_basic', 0, 2, 1).
python_method('TestParseVariables', 'test_no_braces', 0, 2, 1).
python_method('TestParseVariables', 'test_bool_null', 0, 2, 1).
python_method('TestParseVariables', 'test_float', 0, 2, 1).
python_method('TestParseVariables', 'test_empty', 0, 2, 1).
python_class('tests/test_graphql_adapter.py', 'TestParseSchema').
python_method('TestParseSchema', 'test_object_type', 0, 7, 2).
python_method('TestParseSchema', 'test_scalar', 0, 2, 2).
python_method('TestParseSchema', 'test_input_renamed_to_input_object', 0, 4, 2).
python_method('TestParseSchema', 'test_enum', 0, 4, 2).
python_method('TestParseSchema', 'test_empty', 0, 2, 1).
python_class('tests/test_graphql_adapter.py', 'TestSubscriptionPlan').
python_method('TestSubscriptionPlan', 'test_to_dict', 0, 4, 2).
python_class('tests/test_graphql_adapter.py', 'TestAdapterDetect').
python_method('TestAdapterDetect', 'test_by_extension', 1, 2, 3).
python_method('TestAdapterDetect', 'test_by_header', 0, 2, 2).
python_method('TestAdapterDetect', 'test_negative', 0, 2, 2).
python_class('tests/test_graphql_adapter.py', 'TestAdapterParse').
python_method('TestAdapterParse', 'test_metadata', 0, 3, 2).
python_method('TestAdapterParse', 'test_endpoint_in_config', 0, 2, 2).
python_method('TestAdapterParse', 'test_query_step', 0, 8, 4).
python_method('TestAdapterParse', 'test_mutation_step', 0, 6, 4).
python_method('TestAdapterParse', 'test_subscription_step', 0, 6, 4).
python_method('TestAdapterParse', 'test_asserts_attached', 0, 5, 3).
python_class('tests/test_graphql_adapter.py', 'TestAdapterRender').
python_method('TestAdapterRender', 'test_round_trip_step_count', 0, 6, 5).
python_class('tests/test_graphql_adapter.py', 'TestRegistration').
python_method('TestRegistration', 'test_registered', 0, 3, 2).
python_class('tests/test_graphql_adapter.py', 'TestHasGraphQLCore').
python_method('TestHasGraphQLCore', 'test_returns_bool', 0, 2, 2).
python_class('tests/test_gui_execution.py', 'TestGuiExecution').
python_method('TestGuiExecution', 'interpreter', 0, 1, 1).
python_method('TestGuiExecution', 'test_gui_start_dry_run', 1, 2, 2).
python_method('TestGuiExecution', 'test_gui_click_dry_run', 1, 2, 2).
python_method('TestGuiExecution', 'test_gui_input_dry_run', 1, 2, 2).
python_method('TestGuiExecution', 'test_gui_assert_visible_dry_run', 1, 2, 2).
python_method('TestGuiExecution', 'test_gui_assert_text_dry_run', 1, 2, 2).
python_method('TestGuiExecution', 'test_gui_capture_dry_run', 1, 2, 2).
python_method('TestGuiExecution', 'test_gui_stop_dry_run', 1, 2, 2).
python_method('TestGuiExecution', 'test_gui_click_no_session_error', 1, 3, 2).
python_method('TestGuiExecution', 'test_gui_start_no_args_error', 1, 2, 3).
python_class('tests/test_gui_execution.py', 'TestGuiDriverSelection').
python_method('TestGuiDriverSelection', 'interpreter', 0, 1, 1).
python_method('TestGuiDriverSelection', 'test_gui_driver_default_playwright', 2, 3, 3).
python_method('TestGuiDriverSelection', 'test_gui_driver_selenium_fallback', 2, 2, 3).
python_class('tests/test_interpreter.py', 'TestParseOql').
python_method('TestParseOql', 'test_empty', 0, 2, 1).
python_method('TestParseOql', 'test_comments_ignored', 0, 2, 1).
python_method('TestParseOql', 'test_basic_commands', 0, 5, 2).
python_class('tests/test_interpreter.py', 'TestParseTestTOON').
python_method('TestParseTestTOON', 'test_empty', 0, 2, 1).
python_method('TestParseTestTOON', 'test_meta', 0, 4, 1).
python_method('TestParseTestTOON', 'test_api_section', 0, 7, 2).
python_method('TestParseTestTOON', 'test_encoder_section', 0, 8, 2).
python_method('TestParseTestTOON', 'test_validation_pass', 0, 2, 2).
python_method('TestParseTestTOON', 'test_validation_fail', 0, 3, 3).
python_class('tests/test_interpreter.py', 'TestTestTOONExpansion').
python_method('TestTestTOONExpansion', 'test_api_expansion', 0, 8, 2).
python_method('TestTestTOONExpansion', 'test_encoder_expansion', 0, 8, 1).
python_method('TestTestTOONExpansion', 'test_config_expansion', 0, 3, 2).
python_method('TestTestTOONExpansion', 'test_config_mapping_expansion', 0, 2, 1).
python_method('TestTestTOONExpansion', 'test_config_mapping_applies_to_encoder_flow', 0, 6, 1).
python_method('TestTestTOONExpansion', 'test_navigate_expansion', 0, 5, 2).
python_class('tests/test_interpreter.py', 'TestOqlInterpreter').
python_method('TestOqlInterpreter', 'test_dry_run_api', 0, 3, 2).
python_method('TestOqlInterpreter', 'test_set_get', 0, 3, 3).
python_method('TestOqlInterpreter', 'test_testtoon_dry_run', 0, 3, 2).
python_method('TestOqlInterpreter', 'test_assert_json_nested_virtual_encoder_status_path', 0, 3, 3).
python_method('TestOqlInterpreter', 'test_assert_json_nested_virtual_encoder_status_bool', 0, 3, 3).
python_class('tests/test_ir.py', 'TestScenarioMetadata').
python_method('TestScenarioMetadata', 'test_defaults', 0, 4, 1).
python_method('TestScenarioMetadata', 'test_to_dict_minimal', 0, 2, 2).
python_method('TestScenarioMetadata', 'test_to_dict_full', 0, 3, 2).
python_class('tests/test_ir.py', 'TestAssertion').
python_method('TestAssertion', 'test_defaults', 0, 4, 1).
python_method('TestAssertion', 'test_to_dict_minimal', 0, 2, 2).
python_method('TestAssertion', 'test_to_dict_full', 0, 3, 2).
python_class('tests/test_ir.py', 'TestFixture').
python_method('TestFixture', 'test_defaults', 0, 4, 1).
python_method('TestFixture', 'test_to_dict', 0, 5, 2).
python_class('tests/test_ir.py', 'TestStepVariants').
python_method('TestStepVariants', 'test_base_step_kind', 0, 2, 1).
python_method('TestStepVariants', 'test_api_step', 0, 5, 2).
python_method('TestStepVariants', 'test_gui_step', 0, 4, 2).
python_method('TestStepVariants', 'test_encoder_step', 0, 4, 2).
python_method('TestStepVariants', 'test_shell_step', 0, 4, 2).
python_method('TestStepVariants', 'test_unit_step', 0, 5, 2).
python_method('TestStepVariants', 'test_nl_step', 0, 4, 2).
python_method('TestStepVariants', 'test_sql_step', 0, 5, 2).
python_method('TestStepVariants', 'test_proto_step', 0, 6, 2).
python_method('TestStepVariants', 'test_graphql_step', 0, 4, 2).
python_method('TestStepVariants', 'test_conversation_turn_step', 0, 4, 2).
python_method('TestStepVariants', 'test_nlp2dsl_step', 0, 4, 2).
python_method('TestStepVariants', 'test_artifact_assert_step', 0, 3, 2).
python_method('TestStepVariants', 'test_step_with_asserts_and_wait', 0, 3, 3).
python_class('tests/test_ir.py', 'TestTestPlan').
python_method('TestTestPlan', 'test_empty', 0, 5, 1).
python_method('TestTestPlan', 'test_name_and_type_shortcuts', 0, 3, 2).
python_method('TestTestPlan', 'test_to_dict_round_trip_shape', 0, 5, 5).
python_class('tests/test_ir_captures.py', 'TestCaptureDataclass').
python_method('TestCaptureDataclass', 'test_minimal', 0, 3, 1).
python_method('TestCaptureDataclass', 'test_to_dict', 0, 2, 2).
python_class('tests/test_ir_captures.py', 'TestStepCapturesField').
python_method('TestStepCapturesField', 'test_default_empty', 0, 3, 2).
python_method('TestStepCapturesField', 'test_attaches_to_api_step', 0, 3, 3).
python_method('TestStepCapturesField', 'test_to_dict_omits_empty_captures', 0, 2, 2).
python_method('TestStepCapturesField', 'test_to_dict_includes_populated_captures', 0, 2, 3).
python_method('TestStepCapturesField', 'test_works_on_sql_step', 0, 2, 3).
python_class('tests/test_ir_runner_assertion_eval.py', 'TestNavigate').
python_method('TestNavigate', 'test_empty_path_returns_payload', 0, 2, 1).
python_method('TestNavigate', 'test_dotted_dict_path', 0, 2, 1).
python_method('TestNavigate', 'test_list_index', 0, 2, 1).
python_method('TestNavigate', 'test_missing_key', 0, 2, 1).
python_method('TestNavigate', 'test_none_short_circuits', 0, 2, 1).
python_method('TestNavigate', 'test_attribute_fallback', 0, 2, 2).
python_class('tests/test_ir_runner_assertion_eval.py', 'TestOperators').
python_method('TestOperators', 'test_op', 4, 2, 3).
python_method('TestOperators', 'test_unknown_op', 0, 3, 2).
python_method('TestOperators', 'test_lt_with_none_actual', 0, 2, 2).
python_class('tests/test_ir_runner_assertion_eval.py', 'TestResultShape').
python_method('TestResultShape', 'test_message_on_fail', 0, 3, 2).
python_method('TestResultShape', 'test_passing_has_no_message', 0, 2, 2).
python_method('TestResultShape', 'test_to_dict', 0, 4, 3).
python_method('TestResultShape', 'test_evaluate_all', 0, 3, 4).
python_class('tests/test_ir_runner_captures.py', 'TestSqlCaptures').
python_method('TestSqlCaptures', 'test_capture_from_first_row', 0, 4, 6).
python_method('TestSqlCaptures', 'test_capture_chains_into_next_step', 0, 3, 4).
python_class('tests/test_ir_runner_captures.py', 'TestShellCaptures').
python_method('TestShellCaptures', 'test_capture_returncode', 0, 3, 6).
python_class('tests/test_ir_runner_captures.py', 'TestMissingPath').
python_method('TestMissingPath', 'test_unknown_path_warns_but_passes', 0, 4, 7).
python_class('tests/test_ir_runner_captures.py', 'TestErrorAndSkippedSteps').
python_method('TestErrorAndSkippedSteps', 'test_error_step_does_not_capture', 0, 4, 7).
python_class('tests/test_ir_runner_captures.py', 'TestChainedInterpolation').
python_method('TestChainedInterpolation', 'test_captured_value_interpolated_in_subsequent_step', 0, 3, 10).
python_class('tests/test_ir_runner_engine.py', 'TestLoadPlan').
python_method('TestLoadPlan', 'test_passthrough_testplan', 0, 2, 2).
python_method('TestLoadPlan', 'test_unknown_source', 0, 1, 2).
python_class('tests/test_ir_runner_engine.py', 'TestSupportedKinds').
python_method('TestSupportedKinds', 'test_all_step_kinds_have_executor', 0, 2, 2).
python_class('tests/test_ir_runner_engine.py', 'TestEngineDryRun').
python_method('TestEngineDryRun', 'test_api_dry_run_does_not_call_network', 0, 4, 4).
python_method('TestEngineDryRun', 'test_summary_format', 0, 3, 3).
python_class('tests/test_ir_runner_engine.py', 'TestEngineSqlEndToEnd').
python_method('TestEngineSqlEndToEnd', 'test_sqlite_in_memory_round_trip', 0, 2, 4).
python_method('TestEngineSqlEndToEnd', 'test_failing_assertion_makes_plan_not_ok', 0, 4, 5).
python_class('tests/test_ir_runner_engine.py', 'TestEngineShell').
python_method('TestEngineShell', 'test_echo_succeeds', 0, 3, 3).
python_method('TestEngineShell', 'test_expect_exit_code', 0, 2, 3).
python_class('tests/test_ir_runner_engine.py', 'TestEngineUnknownKind').
python_method('TestEngineUnknownKind', 'test_unknown_kind_records_error', 0, 4, 3).
python_class('tests/test_ir_runner_engine.py', 'TestRegisterCustomExecutor').
python_method('TestRegisterCustomExecutor', 'test_register_custom_kind', 0, 3, 6).
python_class('tests/test_ir_runner_engine.py', 'TestRunnerVariables').
python_method('TestRunnerVariables', 'test_variables_persist_across_steps', 0, 2, 5).
python_class('tests/test_ir_runner_executors.py', 'TestSqlExecutor').
python_method('TestSqlExecutor', 'test_dry_run', 0, 3, 3).
python_method('TestSqlExecutor', 'test_select_returns_columns', 0, 3, 3).
python_method('TestSqlExecutor', 'test_invalid_sql_returns_error', 0, 2, 3).
python_class('tests/test_ir_runner_executors.py', 'TestShellExecutor').
python_method('TestShellExecutor', 'test_zero_exit', 0, 2, 3).
python_method('TestShellExecutor', 'test_nonzero_warning', 0, 2, 3).
python_method('TestShellExecutor', 'test_assertion_drives_status', 0, 2, 4).
python_class('tests/test_ir_runner_executors.py', 'TestProtoExecutor').
python_method('TestProtoExecutor', 'test_round_trip', 1, 3, 5).
python_method('TestProtoExecutor', 'test_unknown_message', 1, 3, 5).
python_method('TestProtoExecutor', 'test_no_source', 0, 2, 3).
python_class('tests/test_ir_runner_executors.py', 'TestSkippedExecutors').
python_method('TestSkippedExecutors', 'test_nl_skipped', 0, 2, 3).
python_method('TestSkippedExecutors', 'test_gui_skipped', 0, 2, 3).
python_method('TestSkippedExecutors', 'test_gui_dry_run_passes', 0, 2, 3).
python_class('tests/test_ir_runner_executors.py', 'TestDryRunExecutors').
python_method('TestDryRunExecutors', 'test_unit_dry_run', 0, 2, 3).
python_method('TestDryRunExecutors', 'test_unit_empty_target_errors', 0, 2, 3).
python_method('TestDryRunExecutors', 'test_encoder_dry_run', 0, 2, 3).
python_method('TestDryRunExecutors', 'test_encoder_unknown_action', 0, 2, 3).
python_method('TestDryRunExecutors', 'test_graphql_dry_run', 0, 2, 3).
python_method('TestDryRunExecutors', 'test_graphql_subscription_skipped', 0, 2, 3).
python_method('TestDryRunExecutors', 'test_api_dry_run_url_resolution', 0, 2, 3).
python_class('tests/test_ir_runner_interpolation.py', 'TestInterpValue').
python_method('TestInterpValue', 'test_string_brace_form', 0, 2, 2).
python_method('TestInterpValue', 'test_string_dollar_form', 0, 2, 2).
python_method('TestInterpValue', 'test_unset_passthrough', 0, 2, 2).
python_method('TestInterpValue', 'test_dict_recursion', 0, 2, 2).
python_method('TestInterpValue', 'test_list_recursion', 0, 2, 2).
python_method('TestInterpValue', 'test_nested', 0, 2, 2).
python_method('TestInterpValue', 'test_non_string_passthrough', 0, 4, 2).
python_class('tests/test_mcp_autoloop.py', 'TestCLIAvailability').
python_method('TestCLIAvailability', 'test_cli_help_exits_cleanly', 0, 3, 3).
python_method('TestCLIAvailability', 'test_mcp_subcommand_registered', 0, 3, 2).
python_method('TestCLIAvailability', 'test_discover_subcommand_exists', 0, 2, 2).
python_method('TestCLIAvailability', 'test_topology_subcommand_exists', 0, 2, 2).
python_method('TestCLIAvailability', 'test_run_subcommand_exists', 0, 2, 2).
python_class('tests/test_mcp_autoloop.py', 'TestMCPModule').
python_method('TestMCPModule', 'test_mcp_server_module_importable', 0, 4, 1).
python_method('TestMCPModule', 'test_mcp_init_importable', 0, 2, 1).
python_method('TestMCPModule', 'test_mcp_server_raises_on_missing_package', 0, 2, 3).
python_class('tests/test_mcp_autoloop.py', 'TestDiscoveryPipeline').
python_method('TestDiscoveryPipeline', 'test_self_discovery_returns_manifest', 1, 3, 0).
python_method('TestDiscoveryPipeline', 'test_self_discovery_json_serializable', 1, 3, 3).
python_method('TestDiscoveryPipeline', 'test_discover_cli_json_output', 0, 4, 4).
python_class('tests/test_mcp_autoloop.py', 'TestTopologyPipeline').
python_method('TestTopologyPipeline', 'test_topology_cli_json_output', 0, 3, 5).
python_class('tests/test_mcp_autoloop.py', 'TestScenarioRoundTrip').
python_method('TestScenarioRoundTrip', 'test_scenario_parses', 1, 2, 5).
python_method('TestScenarioRoundTrip', 'test_scenario_round_trips', 1, 3, 6).
python_method('TestScenarioRoundTrip', 'test_api_smoke_has_api_steps', 0, 4, 3).
python_class('tests/test_mcp_autoloop.py', 'TestAutoloopSchema').
python_method('TestAutoloopSchema', 'test_autoloop_state_valid_json', 0, 3, 3).
python_method('TestAutoloopSchema', 'test_llm_decision_schema_exists', 0, 6, 4).
python_method('TestAutoloopSchema', 'test_llm_decision_schema_valid_decision_values', 0, 4, 6).
python_class('tests/test_mcp_autoloop.py', 'TestMCPConfig').
python_method('TestMCPConfig', 'test_mcp_config_structure', 0, 5, 0).
python_method('TestMCPConfig', 'test_mcp_server_module_path', 0, 3, 2).
python_class('tests/test_meta_confidence.py', 'TestPlanConfidence').
python_method('TestPlanConfidence', 'test_empty_plan_zero', 0, 4, 3).
python_method('TestPlanConfidence', 'test_strong_step_high_score', 0, 2, 4).
python_method('TestPlanConfidence', 'test_step_without_asserts_lower', 0, 2, 3).
python_method('TestPlanConfidence', 'test_nl_unresolved_lower', 0, 2, 3).
python_method('TestPlanConfidence', 'test_nl_llm_resolved_lowest', 0, 2, 3).
python_method('TestPlanConfidence', 'test_multi_assert_bonus', 0, 2, 4).
python_method('TestPlanConfidence', 'test_per_step_scores_recorded', 0, 4, 5).
python_method('TestPlanConfidence', 'test_clamping', 0, 2, 2).
python_method('TestPlanConfidence', 'test_to_dict', 0, 4, 5).
python_class('tests/test_meta_confidence.py', 'TestStepReasons').
python_method('TestStepReasons', 'test_reasons_explain_score', 0, 3, 5).
python_method('TestStepReasons', 'test_llm_reason', 0, 2, 4).
python_class('tests/test_meta_coverage.py', 'TestOpenAPICoverage').
python_method('TestOpenAPICoverage', 'test_full', 0, 2, 3).
python_method('TestOpenAPICoverage', 'test_partial', 0, 3, 3).
python_method('TestOpenAPICoverage', 'test_empty_plan', 0, 3, 2).
python_method('TestOpenAPICoverage', 'test_empty_spec', 0, 3, 2).
python_method('TestOpenAPICoverage', 'test_load_dict', 0, 2, 4).
python_class('tests/test_meta_coverage.py', 'TestSqlCoverage').
python_method('TestSqlCoverage', 'test_table_in_select', 0, 2, 3).
python_method('TestSqlCoverage', 'test_partial', 0, 3, 3).
python_class('tests/test_meta_coverage.py', 'TestProtoCoverage').
python_method('TestProtoCoverage', 'test_full', 0, 2, 3).
python_method('TestProtoCoverage', 'test_partial', 0, 3, 3).
python_class('tests/test_meta_coverage.py', 'TestAnalyze').
python_method('TestAnalyze', 'test_openapi_dispatch', 0, 2, 3).
python_method('TestAnalyze', 'test_unknown_contract', 0, 1, 3).
python_class('tests/test_meta_coverage.py', 'TestReportShape').
python_method('TestReportShape', 'test_to_dict', 0, 4, 4).
python_class('tests/test_meta_mutator.py', 'TestFlipOp').
python_method('TestFlipOp', 'test_flips_eq_to_ne', 0, 3, 4).
python_method('TestFlipOp', 'test_flip_does_not_mutate_original', 0, 2, 2).
python_method('TestFlipOp', 'test_unknown_op_skipped', 0, 2, 4).
python_class('tests/test_meta_mutator.py', 'TestTweakStatus').
python_method('TestTweakStatus', 'test_one_per_api_step', 0, 2, 3).
python_method('TestTweakStatus', 'test_status_assertion_also_updated', 0, 3, 2).
python_method('TestTweakStatus', 'test_skips_non_api', 0, 2, 3).
python_class('tests/test_meta_mutator.py', 'TestRemoveStep').
python_method('TestRemoveStep', 'test_one_mutation_per_step', 0, 2, 3).
python_method('TestRemoveStep', 'test_each_mutation_has_one_fewer_step', 0, 3, 3).
python_class('tests/test_meta_mutator.py', 'TestScrambleValue').
python_method('TestScrambleValue', 'test_skips_status_assertions', 0, 2, 3).
python_method('TestScrambleValue', 'test_int_increments', 0, 2, 4).
python_method('TestScrambleValue', 'test_bool_negated', 0, 2, 4).
python_method('TestScrambleValue', 'test_string_suffixed', 0, 2, 4).
python_method('TestScrambleValue', 'test_unscrambleable_skipped', 0, 2, 4).
python_class('tests/test_meta_mutator.py', 'TestMutate').
python_method('TestMutate', 'test_combines_all_mutators', 0, 3, 2).
python_class('tests/test_meta_mutator.py', 'TestMutationHarness').
python_method('TestMutationHarness', 'test_perfect_executor_kills_all', 0, 4, 3).
python_method('TestMutationHarness', 'test_weak_executor_lets_mutations_survive', 0, 4, 2).
python_method('TestMutationHarness', 'test_failing_baseline_returns_empty', 0, 3, 2).
python_class('tests/test_meta_mutator.py', 'TestReportShape').
python_method('TestReportShape', 'test_to_dict', 0, 3, 4).
python_class('tests/test_meta_self_test.py', 'TestGenerateSelfTestPlan').
python_method('TestGenerateSelfTestPlan', 'test_loads_from_path', 1, 3, 3).
python_class('tests/test_meta_self_test.py', 'TestRunSelfTest').
python_method('TestRunSelfTest', 'test_returns_report', 1, 4, 2).
python_method('TestRunSelfTest', 'test_release_ready_when_full_coverage', 1, 2, 2).
python_method('TestRunSelfTest', 'test_to_dict_shape', 1, 5, 3).
python_class('tests/test_meta_self_test.py', 'TestSelfTestCLI').
python_method('TestSelfTestCLI', 'test_help', 0, 3, 2).
python_method('TestSelfTestCLI', 'test_human_output', 1, 5, 4).
python_method('TestSelfTestCLI', 'test_json_output', 1, 3, 5).
python_class('tests/test_meta_self_test.py', 'TestAgainstFrameworkOwnSpec').
python_method('TestAgainstFrameworkOwnSpec', 'test_real_openapi_yaml', 0, 4, 5).
python_class('tests/test_misc_cmds.py', 'TestInitCommand').
python_method('TestInitCommand', 'test_creates_dirs_and_config', 1, 6, 5).
python_method('TestInitCommand', 'test_config_contains_project_name', 1, 2, 4).
python_method('TestInitCommand', 'test_api_type_creates_api_template', 1, 3, 4).
python_method('TestInitCommand', 'test_gui_type_creates_gui_template', 1, 2, 4).
python_method('TestInitCommand', 'test_encoder_type_creates_encoder_template', 1, 2, 4).
python_method('TestInitCommand', 'test_all_type_creates_all_templates', 1, 4, 4).
python_method('TestInitCommand', 'test_existing_config_not_overwritten', 1, 2, 5).
python_method('TestInitCommand', 'test_default_path_is_current_dir', 1, 2, 3).
python_class('tests/test_misc_cmds.py', 'TestCreateCommand').
python_method('TestCreateCommand', 'test_creates_test_file', 1, 3, 4).
python_method('TestCreateCommand', 'test_file_contains_name', 1, 2, 5).
python_method('TestCreateCommand', 'test_fails_if_exists_without_force', 1, 3, 5).
python_method('TestCreateCommand', 'test_force_overwrites_existing', 1, 3, 5).
python_method('TestCreateCommand', 'test_api_type', 1, 3, 4).
python_method('TestCreateCommand', 'test_with_module', 1, 2, 3).
python_method('TestCreateCommand', 'test_creates_output_dir_if_missing', 1, 3, 4).
python_class('tests/test_modbus_commands.py', 'TestModbusToonExpansion').
python_method('TestModbusToonExpansion', 'test_modbus_probe_section', 0, 7, 3).
python_class('tests/test_modbus_commands.py', 'TestModbusDryRun').
python_method('TestModbusDryRun', 'test_modbus_probe_dry_run', 0, 4, 4).
python_method('TestModbusDryRun', 'test_modbus_skip_if_no_port', 1, 2, 3).
python_class('tests/test_modbus_commands.py', 'TestModbusApiExpansion').
python_method('TestModbusApiExpansion', 'test_modbus_api_plan_expansion', 0, 3, 1).
python_class('tests/test_navigate_json_path.py', 'TestNavigateJsonPath').
python_method('TestNavigateJsonPath', 'test_indexed_first_element_field', 0, 2, 1).
python_method('TestNavigateJsonPath', 'test_indexed_second_element_field', 0, 2, 1).
python_method('TestNavigateJsonPath', 'test_indexed_nested_field', 0, 2, 1).
python_method('TestNavigateJsonPath', 'test_top_level_scalar', 0, 2, 1).
python_method('TestNavigateJsonPath', 'test_missing_key_returns_none', 0, 2, 1).
python_method('TestNavigateJsonPath', 'test_out_of_range_index_returns_none', 0, 2, 1).
python_method('TestNavigateJsonPath', 'test_length_of_list', 0, 2, 1).
python_class('tests/test_navigate_json_path.py', 'TestAssertJsonAndCaptureWithIndexedPath').
python_method('TestAssertJsonAndCaptureWithIndexedPath', '_make_interp', 0, 1, 1).
python_method('TestAssertJsonAndCaptureWithIndexedPath', 'test_assert_json_indexed_path_passes', 0, 4, 2).
python_method('TestAssertJsonAndCaptureWithIndexedPath', 'test_assert_json_indexed_path_fails_on_mismatch', 0, 3, 2).
python_method('TestAssertJsonAndCaptureWithIndexedPath', 'test_capture_indexed_path_stores_value', 0, 3, 3).
python_method('TestAssertJsonAndCaptureWithIndexedPath', 'test_assert_json_total_count_ge', 0, 3, 2).
python_method('TestAssertJsonAndCaptureWithIndexedPath', 'test_assert_json_results_length_ge', 0, 3, 2).
python_class('tests/test_navigate_json_path.py', 'TestToonBareImperativeIndexedPath').
python_method('TestToonBareImperativeIndexedPath', '_make_interp', 0, 1, 1).
python_method('TestToonBareImperativeIndexedPath', 'test_toon_parser_parses_bare_commands', 0, 5, 2).
python_method('TestToonBareImperativeIndexedPath', 'test_toon_assert_json_indexed_passes', 0, 3, 3).
python_method('TestToonBareImperativeIndexedPath', 'test_toon_capture_stores_value', 0, 3, 4).
python_class('tests/test_network_discovery.py', 'FakeClient').
python_method('FakeClient', '__init__', 0, 1, 0).
python_method('FakeClient', '__enter__', 0, 1, 0).
python_method('FakeClient', '__exit__', 3, 1, 0).
python_method('FakeClient', 'get', 1, 1, 2).
python_method('FakeClient', 'head', 1, 1, 2).
python_class('tests/test_network_discovery.py', 'FakeErrorClient').
python_class('tests/test_network_discovery.py', 'FakeSpaClient').
python_class('tests/test_nl_adapter.py', 'TestDetect').
python_method('TestDetect', 'test_detect_by_extension', 1, 3, 3).
python_method('TestDetect', 'test_detect_by_header', 0, 2, 2).
python_method('TestDetect', 'test_negative', 0, 2, 2).
python_class('tests/test_nl_adapter.py', 'TestParseHeader').
python_method('TestParseHeader', 'test_metadata', 0, 4, 1).
python_method('TestParseHeader', 'test_default_lang_when_missing', 0, 2, 1).
python_method('TestParseHeader', 'test_default_type_when_missing', 0, 2, 1).
python_class('tests/test_nl_adapter.py', 'TestParsePolishLoginScenario').
python_method('TestParsePolishLoginScenario', 'plan', 0, 1, 1).
python_method('TestParsePolishLoginScenario', 'test_step_count', 1, 2, 1).
python_method('TestParsePolishLoginScenario', 'test_navigate', 1, 4, 1).
python_method('TestParsePolishLoginScenario', 'test_input_email', 1, 5, 1).
python_method('TestParsePolishLoginScenario', 'test_input_password', 1, 5, 1).
python_method('TestParsePolishLoginScenario', 'test_click', 1, 4, 1).
python_method('TestParsePolishLoginScenario', 'test_assert_visible', 1, 3, 0).
python_method('TestParsePolishLoginScenario', 'test_assert_url_contains', 1, 5, 0).
python_class('tests/test_nl_adapter.py', 'TestParseEnglishApiScenario').
python_method('TestParseEnglishApiScenario', 'plan', 0, 1, 1).
python_method('TestParseEnglishApiScenario', 'test_count', 1, 2, 1).
python_method('TestParseEnglishApiScenario', 'test_get', 1, 4, 1).
python_method('TestParseEnglishApiScenario', 'test_status_assert', 1, 5, 0).
python_method('TestParseEnglishApiScenario', 'test_post', 1, 3, 1).
python_method('TestParseEnglishApiScenario', 'test_wait', 1, 3, 0).
python_class('tests/test_nl_adapter.py', 'TestParseUnresolved').
python_method('TestParseUnresolved', 'test_unknown_line_becomes_nl_step', 0, 3, 2).
python_method('TestParseUnresolved', 'test_llm_fallback_when_resolver_set', 0, 5, 6).
python_class('tests/test_nl_adapter.py', 'TestSqlAndEncoder').
python_method('TestSqlAndEncoder', 'test_sql_intent', 0, 3, 2).
python_method('TestSqlAndEncoder', 'test_encoder_on', 0, 3, 2).
python_method('TestSqlAndEncoder', 'test_encoder_click', 0, 3, 2).
python_class('tests/test_nl_adapter.py', 'TestRender').
python_method('TestRender', 'test_round_trip_preserves_intents', 0, 5, 4).
python_method('TestRender', 'test_render_includes_header', 0, 4, 2).
python_class('tests/test_nl_adapter.py', 'TestAdapterRegistration').
python_method('TestAdapterRegistration', 'test_registered', 0, 3, 2).
python_method('TestAdapterRegistration', 'test_extension_lookup', 1, 3, 2).
python_class('tests/test_nl_adapter.py', 'TestDeterministicCoverage').
python_method('TestDeterministicCoverage', 'test_polish_coverage', 0, 4, 3).
python_class('tests/test_nl_entity_extractor.py', 'TestQuoted').
python_method('TestQuoted', 'test_double_quoted', 0, 2, 1).
python_method('TestQuoted', 'test_single_quoted', 0, 2, 1).
python_method('TestQuoted', 'test_no_match', 0, 2, 1).
python_method('TestQuoted', 'test_all_quoted', 0, 2, 1).
python_class('tests/test_nl_entity_extractor.py', 'TestBacktick').
python_method('TestBacktick', 'test_first', 0, 2, 1).
python_method('TestBacktick', 'test_all', 0, 2, 1).
python_method('TestBacktick', 'test_none', 0, 2, 1).
python_class('tests/test_nl_entity_extractor.py', 'TestPath').
python_method('TestPath', 'test_backticked_path', 0, 2, 1).
python_method('TestPath', 'test_quoted_path', 0, 2, 1).
python_method('TestPath', 'test_raw_path', 0, 2, 1).
python_method('TestPath', 'test_path_with_query', 0, 2, 1).
python_method('TestPath', 'test_no_path', 0, 2, 1).
python_method('TestPath', 'test_does_not_match_word_with_slash', 0, 2, 1).
python_class('tests/test_nl_entity_extractor.py', 'TestSelector').
python_method('TestSelector', 'test_attribute_selector', 0, 2, 1).
python_method('TestSelector', 'test_id_selector', 0, 2, 1).
python_method('TestSelector', 'test_class_selector', 0, 2, 1).
python_method('TestSelector', 'test_raw_selector', 0, 2, 1).
python_method('TestSelector', 'test_skips_path', 0, 2, 1).
python_method('TestSelector', 'test_none', 0, 2, 1).
python_class('tests/test_nl_entity_extractor.py', 'TestHttpMethod').
python_method('TestHttpMethod', 'test_get', 0, 2, 1).
python_method('TestHttpMethod', 'test_lowercase', 0, 2, 1).
python_method('TestHttpMethod', 'test_no_method', 0, 2, 1).
python_class('tests/test_nl_entity_extractor.py', 'TestNumber').
python_method('TestNumber', 'test_simple', 0, 2, 1).
python_method('TestNumber', 'test_negative_not_supported', 0, 2, 1).
python_method('TestNumber', 'test_no_number', 0, 2, 1).
python_class('tests/test_nl_entity_extractor.py', 'TestStripQuotesAndBackticks').
python_method('TestStripQuotesAndBackticks', 'test_removes_all', 0, 2, 1).
python_class('tests/test_nl_entity_extractor.py', 'TestSplitOnPreposition').
python_method('TestSplitOnPreposition', 'test_polish_do', 0, 3, 1).
python_method('TestSplitOnPreposition', 'test_english_into', 0, 3, 1).
python_method('TestSplitOnPreposition', 'test_no_preposition', 0, 3, 1).
python_method('TestSplitOnPreposition', 'test_picks_earliest', 0, 3, 1).
python_method('TestSplitOnPreposition', 'test_empty_prepositions', 0, 3, 1).
python_class('tests/test_nl_entity_extractor.py', 'TestTrimFieldNouns').
python_method('TestTrimFieldNouns', 'test_trims_pole', 0, 2, 1).
python_method('TestTrimFieldNouns', 'test_trims_pola', 0, 2, 1).
python_method('TestTrimFieldNouns', 'test_does_not_trim_other_words', 0, 2, 1).
python_method('TestTrimFieldNouns', 'test_empty', 0, 3, 1).
python_class('tests/test_nl_grammar.py', 'TestStepDetection').
python_method('TestStepDetection', 'test_numbered_dot', 0, 2, 1).
python_method('TestStepDetection', 'test_numbered_paren', 0, 2, 1).
python_method('TestStepDetection', 'test_dash_bullet', 0, 2, 1).
python_method('TestStepDetection', 'test_star_bullet', 0, 2, 1).
python_method('TestStepDetection', 'test_indented_bullet', 0, 2, 1).
python_method('TestStepDetection', 'test_not_a_step', 0, 4, 1).
python_class('tests/test_nl_grammar.py', 'TestStripPrefix').
python_method('TestStripPrefix', 'test_dot', 0, 2, 1).
python_method('TestStripPrefix', 'test_paren', 0, 2, 1).
python_method('TestStripPrefix', 'test_dash', 0, 2, 1).
python_method('TestStripPrefix', 'test_idempotent_for_non_steps', 0, 2, 1).
python_class('tests/test_nl_grammar.py', 'TestSplitHeaderAndBody').
python_method('TestSplitHeaderAndBody', 'test_basic', 0, 9, 3).
python_method('TestSplitHeaderAndBody', 'test_handles_hash_prefix_meta', 0, 4, 2).
python_method('TestSplitHeaderAndBody', 'test_empty', 0, 3, 2).
python_method('TestSplitHeaderAndBody', 'test_only_steps_no_header', 0, 4, 2).
python_method('TestSplitHeaderAndBody', 'test_skips_blank_and_unknown_lines', 0, 2, 1).
python_class('tests/test_nl_grammar.py', 'TestNormalize').
python_method('TestNormalize', 'test_lowers_and_collapses_whitespace', 0, 2, 1).
python_method('TestNormalize', 'test_idempotent', 0, 2, 1).
python_class('tests/test_nl_intent_recognizer.py', 'TestRecognizeIntentPolish').
python_method('TestRecognizeIntentPolish', 'test_navigate', 1, 2, 1).
python_method('TestRecognizeIntentPolish', 'test_navigate_multi_word', 1, 3, 1).
python_method('TestRecognizeIntentPolish', 'test_click', 1, 2, 1).
python_method('TestRecognizeIntentPolish', 'test_input', 1, 2, 1).
python_method('TestRecognizeIntentPolish', 'test_assert', 1, 2, 1).
python_method('TestRecognizeIntentPolish', 'test_wait', 1, 2, 1).
python_method('TestRecognizeIntentPolish', 'test_api', 1, 2, 1).
python_method('TestRecognizeIntentPolish', 'test_sql', 1, 2, 1).
python_method('TestRecognizeIntentPolish', 'test_encoder', 1, 2, 1).
python_method('TestRecognizeIntentPolish', 'test_unknown', 1, 3, 1).
python_class('tests/test_nl_intent_recognizer.py', 'TestRecognizeIntentEnglish').
python_method('TestRecognizeIntentEnglish', 'test_navigate', 1, 2, 1).
python_method('TestRecognizeIntentEnglish', 'test_navigate_multi_word', 1, 3, 1).
python_method('TestRecognizeIntentEnglish', 'test_click', 1, 2, 1).
python_method('TestRecognizeIntentEnglish', 'test_input', 1, 2, 1).
python_method('TestRecognizeIntentEnglish', 'test_api', 1, 2, 1).
python_method('TestRecognizeIntentEnglish', 'test_assert', 1, 2, 1).
python_class('tests/test_nl_intent_recognizer.py', 'TestLongestMatchWins').
python_method('TestLongestMatchWins', 'test_wykonaj_zapytanie_sql_beats_wykonaj', 1, 2, 1).
python_class('tests/test_nl_intent_recognizer.py', 'TestRecognizeOperator').
python_method('TestRecognizeOperator', 'test_equal_pl', 1, 3, 1).
python_method('TestRecognizeOperator', 'test_contains', 1, 3, 1).
python_method('TestRecognizeOperator', 'test_greater', 1, 3, 1).
python_method('TestRecognizeOperator', 'test_no_operator', 1, 2, 1).
python_method('TestRecognizeOperator', 'test_not_equal_takes_precedence_over_equal_when_same_position', 1, 3, 1).
python_method('TestRecognizeOperator', 'test_english_equal', 1, 3, 1).
python_class('tests/test_nl_scenarios_e2e.py', 'TestScenarioFilesParse').
python_method('TestScenarioFilesParse', 'test_scenario_dir_not_empty', 0, 2, 1).
python_method('TestScenarioFilesParse', 'test_parse_succeeds', 1, 4, 3).
python_method('TestScenarioFilesParse', 'test_no_unresolved_nl_steps', 1, 4, 3).
python_method('TestScenarioFilesParse', 'test_round_trip_preserves_step_count', 1, 2, 4).
python_class('tests/test_nl_scenarios_e2e.py', 'TestSpecificScenarios').
python_method('TestSpecificScenarios', 'test_login_pl', 0, 5, 3).
python_method('TestSpecificScenarios', 'test_api_smoke_pl', 0, 6, 4).
python_method('TestSpecificScenarios', 'test_encoder_flow_pl', 0, 5, 3).
python_method('TestSpecificScenarios', 'test_login_en', 0, 4, 3).
python_class('tests/test_openapi_generator.py', 'TestOpenAPISpec').
python_method('TestOpenAPISpec', 'test_defaults', 0, 3, 1).
python_method('TestOpenAPISpec', 'test_to_dict_has_keys', 0, 2, 4).
python_method('TestOpenAPISpec', 'test_to_json', 0, 2, 3).
python_method('TestOpenAPISpec', 'test_to_yaml', 0, 2, 3).
python_class('tests/test_openapi_generator.py', 'TestOpenAPIGenerator').
python_method('TestOpenAPIGenerator', 'test_init', 1, 2, 1).
python_method('TestOpenAPIGenerator', 'test_generate_empty_project', 1, 3, 3).
python_method('TestOpenAPIGenerator', 'test_generate_title', 1, 2, 2).
python_method('TestOpenAPIGenerator', 'test_generate_default_title_from_path', 1, 2, 2).
python_method('TestOpenAPIGenerator', 'test_generate_version', 1, 2, 2).
python_method('TestOpenAPIGenerator', 'test_generate_servers_present', 1, 2, 3).
python_method('TestOpenAPIGenerator', 'test_generate_components_schemas', 1, 2, 3).
python_method('TestOpenAPIGenerator', 'test_normalize_path_prepends_slash', 1, 2, 2).
python_method('TestOpenAPIGenerator', 'test_normalize_path_preserves_existing_slash', 1, 2, 2).
python_method('TestOpenAPIGenerator', 'test_build_operation_get', 1, 3, 3).
python_method('TestOpenAPIGenerator', 'test_build_operation_post', 1, 3, 3).
python_method('TestOpenAPIGenerator', 'test_build_operation_delete', 1, 2, 3).
python_method('TestOpenAPIGenerator', 'test_build_operation_with_summary', 1, 2, 3).
python_method('TestOpenAPIGenerator', 'test_build_operation_with_description', 1, 2, 3).
python_method('TestOpenAPIGenerator', 'test_build_operation_with_handler_name', 1, 2, 3).
python_method('TestOpenAPIGenerator', 'test_extract_parameters_path_param', 1, 4, 4).
python_method('TestOpenAPIGenerator', 'test_extract_parameters_id_is_string', 1, 4, 4).
python_method('TestOpenAPIGenerator', 'test_extract_parameters_with_query_param', 1, 4, 4).
python_method('TestOpenAPIGenerator', 'test_infer_tags_from_api_path', 1, 2, 3).
python_method('TestOpenAPIGenerator', 'test_infer_tags_from_direct_resource', 1, 2, 4).
python_method('TestOpenAPIGenerator', 'test_build_request_body_create_handler', 1, 3, 3).
python_method('TestOpenAPIGenerator', 'test_build_request_body_update_handler', 1, 2, 3).
python_method('TestOpenAPIGenerator', 'test_save_yaml', 1, 3, 6).
python_method('TestOpenAPIGenerator', 'test_save_json', 1, 3, 6).
python_method('TestOpenAPIGenerator', 'test_save_default_path', 1, 2, 3).
python_method('TestOpenAPIGenerator', 'test_generate_with_fastapi_project', 1, 2, 4).
python_class('tests/test_openapi_generator.py', 'TestContractTestGenerator').
python_method('TestContractTestGenerator', '_make_spec', 0, 1, 0).
python_method('TestContractTestGenerator', 'test_init_with_dict', 0, 2, 2).
python_method('TestContractTestGenerator', 'test_init_with_openapi_spec', 0, 2, 3).
python_method('TestContractTestGenerator', 'test_init_with_yaml_file', 1, 2, 4).
python_method('TestContractTestGenerator', 'test_init_with_json_file', 1, 2, 4).
python_method('TestContractTestGenerator', 'test_generate_contract_tests', 1, 3, 4).
python_method('TestContractTestGenerator', 'test_contract_tests_content', 1, 3, 4).
python_method('TestContractTestGenerator', 'test_get_expected_status_get', 1, 2, 3).
python_method('TestContractTestGenerator', 'test_get_expected_status_post', 1, 2, 3).
python_method('TestContractTestGenerator', 'test_get_expected_status_fallback', 1, 2, 3).
python_method('TestContractTestGenerator', 'test_validate_response_missing_endpoint', 0, 3, 5).
python_method('TestContractTestGenerator', 'test_validate_response_missing_method', 0, 2, 4).
python_method('TestContractTestGenerator', 'test_validate_response_valid', 0, 2, 3).
python_method('TestContractTestGenerator', 'test_validate_response_wrong_status', 0, 2, 4).
python_method('TestContractTestGenerator', 'test_validate_response_bad_content_type', 0, 2, 4).
python_class('tests/test_openapi_generator.py', 'TestConvenienceFunctions').
python_method('TestConvenienceFunctions', 'test_generate_openapi_spec', 1, 3, 2).
python_method('TestConvenienceFunctions', 'test_generate_openapi_spec_json', 1, 2, 1).
python_method('TestConvenienceFunctions', 'test_generate_contract_tests_from_spec', 1, 2, 4).
python_class('tests/test_page_analyzer.py', 'TestPickSelector').
python_method('TestPickSelector', 'test_data_testid_wins', 0, 2, 1).
python_method('TestPickSelector', 'test_data_test_fallback', 0, 2, 1).
python_method('TestPickSelector', 'test_id_when_stable', 0, 2, 1).
python_method('TestPickSelector', 'test_id_skipped_when_unstable', 0, 2, 1).
python_method('TestPickSelector', 'test_id_skipped_for_uuid_like', 0, 2, 1).
python_method('TestPickSelector', 'test_form_field_name_attr', 0, 2, 1).
python_method('TestPickSelector', 'test_role_with_aria_label', 0, 2, 1).
python_method('TestPickSelector', 'test_input_type_when_distinctive', 0, 2, 1).
python_method('TestPickSelector', 'test_input_type_text_not_distinctive', 0, 2, 1).
python_method('TestPickSelector', 'test_skips_generic_classes', 0, 2, 1).
python_method('TestPickSelector', 'test_returns_none_when_only_generic', 0, 2, 1).
python_method('TestPickSelector', 'test_returns_none_when_nothing_stable', 0, 2, 1).
python_method('TestPickSelector', 'test_quote_escaping', 0, 2, 1).
python_class('tests/test_page_analyzer.py', 'TestDefaultInputValue').
python_method('TestDefaultInputValue', 'test_input_type_takes_precedence', 2, 2, 2).
python_method('TestDefaultInputValue', 'test_email_inferred_from_name', 0, 2, 1).
python_method('TestDefaultInputValue', 'test_password_inferred_from_placeholder', 0, 2, 1).
python_method('TestDefaultInputValue', 'test_search_inferred_from_aria_label', 0, 2, 1).
python_method('TestDefaultInputValue', 'test_id_field_uses_id_default', 0, 2, 1).
python_method('TestDefaultInputValue', 'test_fallback', 0, 2, 1).
python_class('tests/test_page_analyzer.py', 'TestClassification').
python_method('TestClassification', 'test_textarea_is_typed', 0, 2, 1).
python_method('TestClassification', 'test_input_email_is_typed', 0, 2, 1).
python_method('TestClassification', 'test_input_submit_is_not_typed', 0, 2, 1).
python_method('TestClassification', 'test_button_is_clickable', 0, 2, 1).
python_method('TestClassification', 'test_link_is_clickable', 0, 2, 1).
python_method('TestClassification', 'test_role_button_clickable', 0, 2, 1).
python_method('TestClassification', 'test_disabled_not_clickable', 0, 2, 1).
python_method('TestClassification', 'test_input_submit_clickable', 0, 2, 1).
python_class('tests/test_page_analyzer.py', 'TestSnapshotToPlan').
python_method('TestSnapshotToPlan', '_snap', 1, 1, 1).
python_method('TestSnapshotToPlan', 'test_emits_navigate_first', 0, 6, 3).
python_method('TestSnapshotToPlan', 'test_emits_input_with_default_value', 0, 7, 4).
python_method('TestSnapshotToPlan', 'test_emits_click_for_button', 0, 6, 4).
python_method('TestSnapshotToPlan', 'test_skips_invisible_and_unstable', 0, 5, 3).
python_method('TestSnapshotToPlan', 'test_dedup_same_selector', 0, 5, 4).
python_method('TestSnapshotToPlan', 'test_max_steps_respected', 0, 3, 5).
python_method('TestSnapshotToPlan', 'test_metadata_records_source_url', 0, 4, 3).
python_class('tests/test_page_analyzer.py', 'TestFindReplacement').
python_method('TestFindReplacement', 'test_replaces_broken_class_with_id_match', 0, 2, 1).
python_method('TestFindReplacement', 'test_exact_accessible_name_match_wins', 0, 2, 1).
python_method('TestFindReplacement', 'test_returns_none_when_no_match', 0, 2, 1).
python_method('TestFindReplacement', 'test_token_match_picks_best', 0, 2, 1).
python_class('tests/test_pipeline.py', 'TestRegistries').
python_method('TestRegistries', 'test_sorted_sources', 0, 2, 1).
python_method('TestRegistries', 'test_sorted_targets', 0, 2, 1).
python_class('tests/test_pipeline.py', 'TestResolution').
python_method('TestResolution', 'test_unknown_source_raises', 0, 1, 2).
python_method('TestResolution', 'test_unknown_target_raises', 0, 1, 2).
python_class('tests/test_pipeline.py', 'TestMatrix').
python_method('TestMatrix', 'test_run_returns_result', 2, 4, 2).
python_method('TestMatrix', 'test_output_non_empty', 2, 2, 2).
python_method('TestMatrix', 'test_plan_has_metadata', 2, 2, 1).
python_class('tests/test_pipeline.py', 'TestLLMEnrichmentOptIn').
python_method('TestLLMEnrichmentOptIn', 'test_default_runs_without_llm', 0, 2, 1).
python_method('TestLLMEnrichmentOptIn', 'test_no_op_enricher_is_pure', 0, 2, 3).
python_method('TestLLMEnrichmentOptIn', 'test_custom_enricher_invoked', 0, 3, 5).
python_method('TestLLMEnrichmentOptIn', 'test_custom_optimizer_attached_to_metadata', 0, 3, 3).
python_class('tests/test_pipeline.py', 'TestWrite').
python_method('TestWrite', 'test_writes_to_file', 1, 2, 3).
python_method('TestWrite', 'test_writes_to_directory_with_derived_name', 1, 3, 3).
python_class('tests/test_plugin_registry.py', '_StubAdapter').
python_method('_StubAdapter', 'detect', 1, 1, 3).
python_method('_StubAdapter', 'parse', 1, 1, 4).
python_method('_StubAdapter', 'render', 1, 1, 0).
python_class('tests/test_plugin_registry.py', 'TestRegisterPlugin').
python_method('TestRegisterPlugin', 'test_register_adapter_instance', 0, 2, 4).
python_method('TestRegisterPlugin', 'test_register_iterable', 0, 2, 4).
python_method('TestRegisterPlugin', 'test_register_module_with_register_hook', 0, 3, 6).
python_method('TestRegisterPlugin', 'test_register_module_with_adapters_attribute', 0, 2, 6).
python_method('TestRegisterPlugin', 'test_register_unsupported_raises', 0, 1, 4).
python_class('tests/test_plugin_registry.py', 'TestLoadPlugins').
python_method('TestLoadPlugins', 'test_env_var_loading', 1, 3, 7).
python_method('TestLoadPlugins', 'test_ensure_plugins_loaded_runs_once', 1, 4, 3).
python_class('tests/test_proto_adapter.py', 'TestDetect').
python_method('TestDetect', 'test_by_extension', 1, 3, 3).
python_method('TestDetect', 'test_by_header', 0, 2, 2).
python_method('TestDetect', 'test_negative', 0, 2, 2).
python_class('tests/test_proto_adapter.py', 'TestParseMetadata').
python_method('TestParseMetadata', 'test_name_type_version', 0, 4, 1).
python_class('tests/test_proto_adapter.py', 'TestParseSchemas').
python_method('TestParseSchemas', 'test_proto_files_become_fixture', 0, 5, 2).
python_class('tests/test_proto_adapter.py', 'TestParseMessages').
python_method('TestParseMessages', 'test_step_count', 0, 4, 3).
python_method('TestParseMessages', 'test_message_names', 0, 4, 2).
python_method('TestParseMessages', 'test_schema_file_propagated', 0, 4, 2).
python_method('TestParseMessages', 'test_fields_blob_preserved', 0, 5, 3).
python_class('tests/test_proto_adapter.py', 'TestParseAsserts').
python_method('TestParseAsserts', 'test_assertions_attach_to_message', 0, 7, 3).
python_method('TestParseAsserts', 'test_orphan_assert', 0, 5, 1).
python_class('tests/test_proto_adapter.py', 'TestRender').
python_method('TestRender', 'test_round_trip_step_count', 0, 6, 4).
python_method('TestRender', 'test_render_includes_meta', 0, 3, 2).
python_class('tests/test_proto_adapter.py', 'TestRegistration').
python_method('TestRegistration', 'test_registered', 0, 3, 2).
python_class('tests/test_proto_compatibility.py', 'TestIdentitySchemas').
python_method('TestIdentitySchemas', 'test_no_issues', 0, 3, 3).
python_class('tests/test_proto_compatibility.py', 'TestRemovedField').
python_method('TestRemovedField', 'test_breaking', 0, 3, 2).
python_class('tests/test_proto_compatibility.py', 'TestAddedField').
python_method('TestAddedField', 'test_safe', 0, 2, 2).
python_class('tests/test_proto_compatibility.py', 'TestTypeChange').
python_method('TestTypeChange', 'test_incompatible_breaking', 0, 2, 2).
python_method('TestTypeChange', 'test_string_to_int_breaking', 0, 3, 3).
python_method('TestTypeChange', 'test_int32_to_uint32_safe', 0, 2, 3).
python_class('tests/test_proto_compatibility.py', 'TestTagChange').
python_method('TestTagChange', 'test_breaking', 0, 3, 3).
python_class('tests/test_proto_compatibility.py', 'TestRename').
python_method('TestRename', 'test_rename_is_warning', 0, 3, 3).
python_class('tests/test_proto_compatibility.py', 'TestRemovedMessage').
python_method('TestRemovedMessage', 'test_breaking', 0, 3, 3).
python_class('tests/test_proto_compatibility.py', 'TestAddedMessage').
python_method('TestAddedMessage', 'test_info_only', 0, 3, 3).
python_class('tests/test_proto_compatibility.py', 'TestReportShape').
python_method('TestReportShape', 'test_to_dict', 0, 3, 3).
python_class('tests/test_proto_descriptor_loader.py', 'TestParseHeader').
python_method('TestParseHeader', 'test_syntax', 0, 2, 1).
python_method('TestParseHeader', 'test_package', 0, 2, 1).
python_method('TestParseHeader', 'test_default_syntax', 0, 2, 1).
python_class('tests/test_proto_descriptor_loader.py', 'TestParseMessages').
python_method('TestParseMessages', 'test_two_messages', 0, 2, 1).
python_method('TestParseMessages', 'test_field_count', 0, 3, 3).
python_method('TestParseMessages', 'test_field_types', 0, 3, 2).
python_method('TestParseMessages', 'test_field_numbers_unique', 0, 3, 2).
python_class('tests/test_proto_descriptor_loader.py', 'TestLabelsAndDefaults').
python_method('TestLabelsAndDefaults', 'test_required', 0, 2, 3).
python_method('TestLabelsAndDefaults', 'test_optional_with_default', 0, 4, 3).
python_method('TestLabelsAndDefaults', 'test_repeated', 0, 2, 3).
python_class('tests/test_proto_descriptor_loader.py', 'TestComments').
python_method('TestComments', 'test_line_comments_stripped', 0, 2, 2).
python_method('TestComments', 'test_block_comments_stripped', 0, 2, 2).
python_class('tests/test_proto_descriptor_loader.py', 'TestLookups').
python_method('TestLookups', 'test_field_by_name', 0, 3, 3).
python_method('TestLookups', 'test_field_by_number', 0, 2, 3).
python_method('TestLookups', 'test_field_by_name_missing', 0, 2, 3).
python_method('TestLookups', 'test_message_missing', 0, 2, 2).
python_class('tests/test_proto_descriptor_loader.py', 'TestLoadProtoFile').
python_method('TestLoadProtoFile', 'test_round_trip', 1, 2, 3).
python_class('tests/test_proto_descriptor_loader.py', 'TestScalarTypes').
python_method('TestScalarTypes', 'test_includes_canonical_proto_scalars', 0, 3, 0).
python_class('tests/test_proto_descriptor_loader.py', 'TestToDict').
python_method('TestToDict', 'test_round_trip_shape', 0, 4, 2).
python_class('tests/test_proto_graphql_scenarios_e2e.py', 'TestProtoScenarios').
python_method('TestProtoScenarios', 'test_dir_not_empty', 0, 2, 1).
python_method('TestProtoScenarios', 'test_parse', 1, 5, 3).
python_method('TestProtoScenarios', 'test_round_trip_step_count', 1, 6, 5).
python_class('tests/test_proto_graphql_scenarios_e2e.py', 'TestGraphQLScenarios').
python_method('TestGraphQLScenarios', 'test_dir_not_empty', 0, 2, 1).
python_method('TestGraphQLScenarios', 'test_parse', 1, 5, 3).
python_method('TestGraphQLScenarios', 'test_endpoint_propagated', 1, 5, 4).
python_method('TestGraphQLScenarios', 'test_round_trip_step_count', 1, 6, 5).
python_class('tests/test_proto_message_validator.py', 'TestParseInstanceFields').
python_method('TestParseInstanceFields', 'test_basic', 0, 2, 1).
python_method('TestParseInstanceFields', 'test_quoted_value', 0, 2, 1).
python_method('TestParseInstanceFields', 'test_empty', 0, 3, 1).
python_class('tests/test_proto_message_validator.py', 'TestCoerceScalar').
python_method('TestCoerceScalar', 'test_int', 0, 3, 1).
python_method('TestCoerceScalar', 'test_float', 0, 2, 1).
python_method('TestCoerceScalar', 'test_bool', 0, 3, 1).
python_method('TestCoerceScalar', 'test_string_passthrough', 0, 2, 1).
python_method('TestCoerceScalar', 'test_bytes', 0, 2, 1).
python_method('TestCoerceScalar', 'test_unknown_type_returns_string', 0, 2, 1).
python_class('tests/test_proto_message_validator.py', 'TestValidateMessageInstance').
python_method('TestValidateMessageInstance', 'test_ok', 0, 3, 4).
python_method('TestValidateMessageInstance', 'test_unknown_field', 0, 3, 5).
python_method('TestValidateMessageInstance', 'test_type_mismatch', 0, 2, 3).
python_method('TestValidateMessageInstance', 'test_value_coercion_failure', 0, 3, 4).
python_method('TestValidateMessageInstance', 'test_required_missing', 0, 3, 5).
python_method('TestValidateMessageInstance', 'test_to_dict', 0, 3, 5).
python_class('tests/test_proto_message_validator.py', 'TestRoundTrip').
python_method('TestRoundTrip', 'test_clean_round_trip', 0, 2, 4).
python_method('TestRoundTrip', 'test_round_trip_failure_on_invalid_value', 0, 2, 3).
python_class('tests/test_report_generator.py', 'TestTestResult').
python_method('TestTestResult', 'test_create', 0, 5, 1).
python_method('TestTestResult', 'test_create_with_failures', 0, 2, 1).
python_class('tests/test_report_generator.py', 'TestTestSuiteReport').
python_method('TestTestSuiteReport', 'test_create', 0, 5, 1).
python_method('TestTestSuiteReport', 'test_zero_report', 0, 2, 1).
python_class('tests/test_report_generator.py', 'TestReportDataParser').
python_method('TestReportDataParser', 'test_parse_testql_results_returns_report', 1, 4, 4).
python_method('TestReportDataParser', 'test_to_json_is_valid_json', 0, 3, 4).
python_method('TestReportDataParser', 'test_to_json_includes_tests', 0, 3, 5).
python_method('TestReportDataParser', 'test_to_json_empty_suite', 0, 3, 4).
python_class('tests/test_report_generator.py', 'TestHTMLReportGenerator').
python_method('TestHTMLReportGenerator', 'test_generate_creates_file', 1, 3, 4).
python_method('TestHTMLReportGenerator', 'test_html_contains_suite_name', 1, 2, 4).
python_method('TestHTMLReportGenerator', 'test_html_contains_stats', 1, 4, 4).
python_method('TestHTMLReportGenerator', 'test_html_contains_test_names', 1, 3, 4).
python_method('TestHTMLReportGenerator', 'test_success_rate_zero_total', 1, 2, 5).
python_method('TestHTMLReportGenerator', 'test_html_is_valid_start', 1, 2, 6).
python_method('TestHTMLReportGenerator', 'test_custom_template_dir', 1, 2, 1).
python_method('TestHTMLReportGenerator', 'test_render_html_returns_string', 0, 3, 5).
python_method('TestHTMLReportGenerator', 'test_render_html_failed_test_name', 0, 2, 3).
python_method('TestHTMLReportGenerator', 'test_render_html_failure_message', 0, 2, 3).
python_class('tests/test_reporters.py', 'TestConsoleReporter').
python_method('TestConsoleReporter', 'test_returns_string', 0, 2, 3).
python_method('TestConsoleReporter', 'test_contains_source', 0, 2, 2).
python_method('TestConsoleReporter', 'test_passed_step_shows_checkmark', 0, 3, 3).
python_method('TestConsoleReporter', 'test_failed_step_shows_cross', 0, 2, 3).
python_method('TestConsoleReporter', 'test_error_step_shows_explosion', 0, 2, 3).
python_method('TestConsoleReporter', 'test_skipped_step_shows_icon', 0, 2, 3).
python_method('TestConsoleReporter', 'test_step_message_shown', 0, 2, 3).
python_method('TestConsoleReporter', 'test_errors_section_shown', 0, 2, 2).
python_method('TestConsoleReporter', 'test_summary_line_counts', 0, 2, 3).
python_method('TestConsoleReporter', 'test_duration_in_output', 0, 2, 2).
python_class('tests/test_reporters.py', 'TestJsonReporter').
python_method('TestJsonReporter', 'test_returns_valid_json', 0, 2, 4).
python_method('TestJsonReporter', 'test_has_required_fields', 0, 8, 3).
python_method('TestJsonReporter', 'test_source_matches', 0, 2, 3).
python_method('TestJsonReporter', 'test_step_fields', 0, 5, 5).
python_method('TestJsonReporter', 'test_counts', 0, 4, 4).
python_method('TestJsonReporter', 'test_errors_included', 0, 2, 3).
python_method('TestJsonReporter', 'test_warnings_included', 0, 2, 3).
python_class('tests/test_reporters.py', 'TestJunitReporter').
python_method('TestJunitReporter', 'test_returns_string', 0, 2, 3).
python_method('TestJunitReporter', 'test_valid_xml', 0, 1, 4).
python_method('TestJunitReporter', 'test_testsuite_element', 0, 2, 5).
python_method('TestJunitReporter', 'test_testcase_per_step', 0, 4, 6).
python_method('TestJunitReporter', 'test_failure_element_for_failed_step', 0, 2, 4).
python_class('tests/test_reporters.py', 'TestVariableStore').
python_method('TestVariableStore', 'test_set_get', 0, 2, 3).
python_method('TestVariableStore', 'test_default_if_missing', 0, 2, 2).
python_method('TestVariableStore', 'test_has', 0, 3, 2).
python_method('TestVariableStore', 'test_all', 0, 2, 2).
python_method('TestVariableStore', 'test_clear', 0, 2, 3).
python_method('TestVariableStore', 'test_interpolate_curly', 0, 2, 2).
python_method('TestVariableStore', 'test_interpolate_dollar', 0, 2, 2).
python_method('TestVariableStore', 'test_interpolate_missing_left_unchanged', 0, 2, 2).
python_method('TestVariableStore', 'test_interpolate_no_vars', 0, 2, 2).
python_method('TestVariableStore', 'test_initial_values', 0, 2, 2).
python_class('tests/test_reporters.py', 'TestInterpreterOutput').
python_method('TestInterpreterOutput', 'test_emit_stores_line', 0, 2, 2).
python_method('TestInterpreterOutput', 'test_ok_prefix', 0, 2, 3).
python_method('TestInterpreterOutput', 'test_fail_prefix', 0, 2, 3).
python_method('TestInterpreterOutput', 'test_warn_prefix', 0, 2, 3).
python_method('TestInterpreterOutput', 'test_info_prefix', 0, 2, 3).
python_method('TestInterpreterOutput', 'test_error_prefix', 0, 2, 3).
python_method('TestInterpreterOutput', 'test_step_with_icon', 0, 2, 3).
python_method('TestInterpreterOutput', 'test_not_quiet_prints', 1, 2, 3).
python_class('tests/test_reporters.py', 'TestScriptResultHelpers').
python_method('TestScriptResultHelpers', 'test_passed_count', 0, 2, 2).
python_method('TestScriptResultHelpers', 'test_failed_count', 0, 2, 2).
python_method('TestScriptResultHelpers', 'test_summary_ok', 0, 3, 3).
python_method('TestScriptResultHelpers', 'test_summary_fail', 0, 2, 3).
python_class('tests/test_results.py', 'TestResultEnvelope').
python_method('TestResultEnvelope', 'test_analyze_topology_passes_for_openapi_fixture', 0, 4, 2).
python_method('TestResultEnvelope', 'test_analyze_topology_warns_for_empty_directory', 1, 5, 3).
python_method('TestResultEnvelope', 'test_inspect_source_returns_refactor_plan', 1, 5, 1).
python_class('tests/test_results.py', 'TestResultSerializers').
python_method('TestResultSerializers', 'test_render_result_json', 0, 3, 3).
python_method('TestResultSerializers', 'test_render_refactor_yaml', 1, 3, 3).
python_method('TestResultSerializers', 'test_render_inspection_toon', 1, 4, 2).
python_method('TestResultSerializers', 'test_render_inspection_nlp', 1, 3, 2).
python_class('tests/test_results.py', 'TestInspectCli').
python_method('TestInspectCli', 'test_inspect_default_toon_output', 0, 4, 3).
python_method('TestInspectCli', 'test_inspect_json_result_artifact', 0, 3, 4).
python_method('TestInspectCli', 'test_inspect_refactor_plan_nlp_for_empty_dir', 1, 3, 3).
python_method('TestInspectCli', 'test_inspect_missing_path_exits_nonzero', 0, 3, 3).
python_class('tests/test_results.py', 'TestDotTestqlArtifacts').
python_method('TestDotTestqlArtifacts', 'test_write_inspection_artifacts_creates_dot_testql_bundle', 1, 14, 5).
python_method('TestDotTestqlArtifacts', 'test_inspect_cli_out_dir_writes_bundle', 1, 5, 4).
python_class('tests/test_run_cmd.py', '_FakeResult').
python_method('_FakeResult', '__post_init__', 0, 4, 1).
python_class('tests/test_run_cmd.py', '_FakeInterpreter').
python_method('_FakeInterpreter', '__init__', 0, 1, 0).
python_method('_FakeInterpreter', 'run', 2, 1, 1).
python_class('tests/test_run_cmd.py', 'TestRunCommandInputs').
python_method('TestRunCommandInputs', 'test_run_accepts_directory', 2, 5, 7).
python_method('TestRunCommandInputs', 'test_run_accepts_glob_pattern', 2, 4, 6).
python_method('TestRunCommandInputs', 'test_run_errors_for_missing_input', 1, 3, 3).
python_method('TestRunCommandInputs', 'test_run_accepts_shell_expanded_multiple_files', 2, 4, 7).
python_class('tests/test_run_ir_cli.py', 'TestRunIrCLI').
python_method('TestRunIrCLI', 'test_help', 0, 3, 2).
python_method('TestRunIrCLI', 'test_dry_run_console', 1, 4, 4).
python_method('TestRunIrCLI', 'test_json_output', 1, 5, 6).
python_method('TestRunIrCLI', 'test_actual_sqlite_run', 1, 3, 4).
python_class('tests/test_runner.py', 'TestDslCommand').
python_method('TestDslCommand', 'test_create_minimal', 0, 6, 1).
python_method('TestDslCommand', 'test_create_full', 0, 3, 1).
python_class('tests/test_runner.py', 'TestExecutionResult').
python_method('TestExecutionResult', 'test_success', 0, 3, 2).
python_method('TestExecutionResult', 'test_failure', 0, 3, 2).
python_class('tests/test_runner.py', 'TestParseLine').
python_method('TestParseLine', 'test_empty_returns_none', 0, 2, 1).
python_method('TestParseLine', 'test_comment_returns_none', 0, 2, 1).
python_method('TestParseLine', 'test_blank_line_returns_none', 0, 2, 1).
python_method('TestParseLine', 'test_api_get', 0, 5, 1).
python_method('TestParseLine', 'test_api_post_with_body', 0, 4, 1).
python_method('TestParseLine', 'test_api_with_expected', 0, 3, 1).
python_method('TestParseLine', 'test_api_with_comment', 0, 3, 1).
python_method('TestParseLine', 'test_wait_command', 0, 4, 1).
python_method('TestParseLine', 'test_wait_with_comment', 0, 3, 1).
python_method('TestParseLine', 'test_general_command_with_quotes', 0, 4, 1).
python_method('TestParseLine', 'test_simple_command', 0, 4, 1).
python_method('TestParseLine', 'test_api_patch', 0, 3, 1).
python_method('TestParseLine', 'test_api_delete', 0, 3, 1).
python_class('tests/test_runner.py', 'TestParseScript').
python_method('TestParseScript', 'test_empty_script', 0, 2, 1).
python_method('TestParseScript', 'test_comments_and_blanks_skipped', 0, 2, 1).
python_method('TestParseScript', 'test_multiline_script', 0, 5, 2).
python_method('TestParseScript', 'test_mixed_content', 0, 3, 2).
python_class('tests/test_runner.py', 'TestDslCliExecutor').
python_method('TestDslCliExecutor', 'test_init_defaults', 0, 3, 1).
python_method('TestDslCliExecutor', 'test_init_custom_url', 0, 2, 1).
python_method('TestDslCliExecutor', 'test_browser_command_skipped', 0, 3, 4).
python_method('TestDslCliExecutor', 'test_semantic_command_logged', 0, 3, 4).
python_method('TestDslCliExecutor', 'test_browser_command_verbose', 1, 2, 5).
python_method('TestDslCliExecutor', 'test_semantic_command_verbose', 1, 2, 4).
python_method('TestDslCliExecutor', 'test_execute_unknown_command_returns_result', 0, 2, 4).
python_method('TestDslCliExecutor', 'test_execute_returns_duration', 0, 2, 3).
python_method('TestDslCliExecutor', 'test_wait_command_via_execute', 0, 2, 4).
python_class('tests/test_scenario_yaml_adapter.py', 'TestDetect').
python_method('TestDetect', 'test_detect_extension', 1, 3, 3).
python_method('TestDetect', 'test_detect_content', 0, 2, 2).
python_method('TestDetect', 'test_detect_negative', 0, 2, 2).
python_class('tests/test_scenario_yaml_adapter.py', 'TestParseApi').
python_method('TestParseApi', 'test_metadata', 0, 4, 1).
python_method('TestParseApi', 'test_targets_become_config', 0, 3, 2).
python_method('TestParseApi', 'test_steps_typed', 0, 10, 3).
python_method('TestParseApi', 'test_capture', 0, 6, 2).
python_class('tests/test_scenario_yaml_adapter.py', 'TestParseGui').
python_method('TestParseGui', 'test_navigate_and_form', 0, 8, 2).
python_class('tests/test_scenario_yaml_adapter.py', 'TestParseMixed').
python_method('TestParseMixed', 'test_step_kinds', 0, 3, 1).
python_method('TestParseMixed', 'test_using_overrides_propagate', 0, 4, 4).
python_method('TestParseMixed', 'test_shell_expect_exit_code', 0, 4, 3).
python_method('TestParseMixed', 'test_encoder_target', 0, 5, 3).
python_method('TestParseMixed', 'test_unit_target', 0, 4, 3).
python_class('tests/test_scenario_yaml_adapter.py', 'TestRender').
python_method('TestRender', 'test_round_trip_metadata_steps', 0, 6, 2).
python_class('tests/test_scenario_yaml_adapter.py', 'TestRegistration').
python_method('TestRegistration', 'test_registered_in_default_registry', 0, 2, 2).
python_method('TestRegistration', 'test_extension_lookup_picks_scenario_yaml', 1, 3, 2).
python_method('TestRegistration', 'test_extension_lookup_keeps_testtoon', 1, 3, 2).
python_class('tests/test_scenario_yaml_adapter.py', 'TestParseErrors').
python_method('TestParseErrors', 'test_non_mapping_root', 0, 1, 2).
python_class('tests/test_shell_execution.py', 'TestShellExecution').
python_method('TestShellExecution', 'interpreter', 1, 1, 1).
python_method('TestShellExecution', 'test_shell_echo_command', 2, 5, 2).
python_method('TestShellExecution', 'test_shell_with_exit_code', 1, 3, 2).
python_method('TestShellExecution', 'test_assert_exit_code_success', 1, 2, 3).
python_method('TestShellExecution', 'test_assert_exit_code_failure', 1, 3, 4).
python_method('TestShellExecution', 'test_assert_stdout_contains_success', 1, 2, 3).
python_method('TestShellExecution', 'test_assert_stdout_contains_failure', 1, 2, 3).
python_method('TestShellExecution', 'test_shell_timeout', 1, 3, 3).
python_method('TestShellExecution', 'test_shell_no_previous_command_warning', 1, 2, 3).
python_class('tests/test_shell_execution.py', 'TestShellDryRun').
python_method('TestShellDryRun', 'interpreter', 0, 1, 1).
python_method('TestShellDryRun', 'test_shell_dry_run', 1, 4, 2).
python_class('tests/test_smoke_decisions.py', 'TestKimiDecision').
python_method('TestKimiDecision', 'test_file_exists', 0, 2, 1).
python_method('TestKimiDecision', 'test_valid_json', 0, 2, 2).
python_method('TestKimiDecision', 'test_schema_valid', 0, 2, 3).
python_method('TestKimiDecision', 'test_decision_value', 0, 2, 2).
python_method('TestKimiDecision', 'test_confidence_high', 0, 2, 1).
python_method('TestKimiDecision', 'test_has_topology_focus', 0, 2, 3).
python_class('tests/test_smoke_decisions.py', 'TestSWEDecision').
python_method('TestSWEDecision', 'test_file_exists', 0, 2, 1).
python_method('TestSWEDecision', 'test_valid_json', 0, 2, 2).
python_method('TestSWEDecision', 'test_schema_valid', 0, 2, 3).
python_method('TestSWEDecision', 'test_decision_value', 0, 2, 2).
python_method('TestSWEDecision', 'test_conservative_risk', 0, 2, 1).
python_method('TestSWEDecision', 'test_has_multiple_next_actions', 0, 2, 3).
python_class('tests/test_smoke_decisions.py', 'TestModelComparison').
python_method('TestModelComparison', 'test_both_same_iteration', 0, 2, 1).
python_method('TestModelComparison', 'test_both_valid_decisions', 0, 3, 2).
python_method('TestModelComparison', 'test_kimi_higher_confidence_than_swe', 0, 2, 1).
python_method('TestModelComparison', 'test_swe_higher_risk_than_kimi', 0, 2, 1).
python_method('TestModelComparison', 'test_summary', 0, 2, 4).
python_class('tests/test_sources.py', 'TestRegistry').
python_method('TestRegistry', 'test_builtin_sources', 0, 2, 2).
python_method('TestRegistry', 'test_get_source', 1, 4, 4).
python_method('TestRegistry', 'test_get_unknown', 0, 2, 1).
python_method('TestRegistry', 'test_get_config_aliases', 1, 4, 4).
python_class('tests/test_sources.py', 'TestOpenAPISource').
python_method('TestOpenAPISource', 'test_paths_become_api_steps', 0, 6, 4).
python_method('TestOpenAPISource', 'test_status_picks_lowest_2xx', 0, 5, 4).
python_method('TestOpenAPISource', 'test_default_status_when_unspecified', 0, 2, 4).
python_method('TestOpenAPISource', 'test_base_url_from_servers', 0, 2, 2).
python_method('TestOpenAPISource', 'test_metadata_from_info', 0, 4, 2).
python_method('TestOpenAPISource', 'test_load_from_path', 1, 2, 4).
python_method('TestOpenAPISource', 'test_load_from_dict', 0, 2, 4).
python_class('tests/test_sources.py', 'TestSqlSource').
python_method('TestSqlSource', 'test_two_tables_yield_four_steps', 0, 4, 4).
python_method('TestSqlSource', 'test_count_step_has_assert', 0, 5, 5).
python_method('TestSqlSource', 'test_schema_fixture_emitted', 0, 2, 3).
python_method('TestSqlSource', 'test_dialect_propagates', 0, 4, 3).
python_method('TestSqlSource', 'test_load_from_path', 1, 2, 3).
python_class('tests/test_sources.py', 'TestProtoSource').
python_method('TestProtoSource', 'test_one_step_per_message', 0, 6, 4).
python_method('TestProtoSource', 'test_sample_fields_blob', 0, 6, 4).
python_method('TestProtoSource', 'test_round_trip_assertion', 0, 5, 5).
python_method('TestProtoSource', 'test_schema_fixture', 0, 2, 3).
python_class('tests/test_sources.py', 'TestGraphQLSource').
python_method('TestGraphQLSource', 'test_one_step_per_object_type', 0, 5, 5).
python_method('TestGraphQLSource', 'test_endpoint_set_in_config', 0, 2, 2).
python_method('TestGraphQLSource', 'test_query_body_uses_field_list', 0, 5, 4).
python_class('tests/test_sources.py', 'TestNLSource').
python_method('TestNLSource', 'test_delegates_to_adapter', 0, 5, 4).
python_class('tests/test_sources.py', 'TestUISource').
python_method('TestUISource', 'test_navigate_first', 0, 3, 3).
python_method('TestUISource', 'test_inputs_extracted', 0, 7, 3).
python_method('TestUISource', 'test_buttons_extracted', 0, 5, 3).
python_class('tests/test_sources.py', 'TestConfigSourceHelpers').
python_method('TestConfigSourceHelpers', 'test_load_includes_single_file', 1, 3, 2).
python_method('TestConfigSourceHelpers', 'test_load_includes_glob_pattern', 1, 3, 2).
python_method('TestConfigSourceHelpers', 'test_load_includes_nonexistent_file', 1, 2, 1).
python_method('TestConfigSourceHelpers', 'test_extract_phony_targets', 0, 2, 2).
python_method('TestConfigSourceHelpers', 'test_extract_phony_targets_multiline', 0, 2, 2).
python_method('TestConfigSourceHelpers', 'test_extract_phony_targets_none', 0, 2, 1).
python_method('TestConfigSourceHelpers', 'test_extract_target_commands_simple', 0, 2, 3).
python_method('TestConfigSourceHelpers', 'test_extract_target_commands_with_prefixes', 0, 2, 3).
python_method('TestConfigSourceHelpers', 'test_extract_target_commands_stops_at_next_target', 0, 3, 3).
python_method('TestConfigSourceHelpers', 'test_extract_target_commands_ignores_comments', 0, 2, 3).
python_method('TestConfigSourceHelpers', 'test_extract_target_commands_max_lines', 0, 3, 4).
python_class('tests/test_sources.py', 'TestConfigSourceIntegration').
python_method('TestConfigSourceIntegration', 'test_parse_makefile_simple', 1, 4, 5).
python_method('TestConfigSourceIntegration', 'test_parse_makefile_with_includes', 1, 4, 5).
python_method('TestConfigSourceIntegration', 'test_parse_makefile_phony_flag', 1, 7, 4).
python_method('TestConfigSourceIntegration', 'test_parse_makefile_comments', 1, 7, 4).
python_method('TestConfigSourceIntegration', 'test_parse_makefile_excludes_special_targets', 1, 4, 4).
python_class('tests/test_sql_adapter.py', 'TestDetect').
python_method('TestDetect', 'test_by_extension', 1, 3, 3).
python_method('TestDetect', 'test_by_header', 0, 2, 2).
python_method('TestDetect', 'test_negative', 0, 2, 2).
python_class('tests/test_sql_adapter.py', 'TestParseMetadata').
python_method('TestParseMetadata', 'test_name', 0, 2, 1).
python_method('TestParseMetadata', 'test_type', 0, 2, 1).
python_method('TestParseMetadata', 'test_dialect_in_extra', 0, 2, 2).
python_method('TestParseMetadata', 'test_default_dialect', 0, 2, 2).
python_class('tests/test_sql_adapter.py', 'TestParseConfig').
python_method('TestParseConfig', 'test_config_dict', 0, 2, 1).
python_method('TestParseConfig', 'test_connection_fixture_added', 0, 3, 1).
python_class('tests/test_sql_adapter.py', 'TestParseSchema').
python_method('TestParseSchema', 'test_schema_fixture', 0, 6, 2).
python_class('tests/test_sql_adapter.py', 'TestParseQueries').
python_method('TestParseQueries', 'test_count_and_steps', 0, 4, 3).
python_method('TestParseQueries', 'test_query_text', 0, 6, 2).
python_method('TestParseQueries', 'test_dialect_propagated', 0, 5, 2).
python_class('tests/test_sql_adapter.py', 'TestParseAsserts').
python_method('TestParseAsserts', 'test_assert_attached_to_query', 0, 4, 3).
python_method('TestParseAsserts', 'test_dotted_assert_attaches_to_base_query', 0, 6, 2).
python_method('TestParseAsserts', 'test_orphan_asserts_become_assert_step', 0, 5, 1).
python_class('tests/test_sql_adapter.py', 'TestRender').
python_method('TestRender', 'test_round_trip_step_count', 0, 6, 4).
python_method('TestRender', 'test_render_includes_meta', 0, 3, 2).
python_method('TestRender', 'test_render_includes_schema', 0, 3, 2).
python_method('TestRender', 'test_render_empty_plan', 0, 2, 2).
python_class('tests/test_sql_adapter.py', 'TestRegistration').
python_method('TestRegistration', 'test_auto_registered', 0, 3, 2).
python_method('TestRegistration', 'test_extension_lookup', 1, 3, 2).
python_method('TestRegistration', 'test_extension_does_not_collide_with_testtoon', 1, 3, 2).
python_class('tests/test_sql_ddl_parser.py', 'TestRegexFallback').
python_method('TestRegexFallback', 'test_single_table', 0, 4, 2).
python_method('TestRegexFallback', 'test_column_types', 0, 5, 3).
python_method('TestRegexFallback', 'test_primary_key_flag', 0, 3, 3).
python_method('TestRegexFallback', 'test_not_null_flag', 0, 3, 3).
python_method('TestRegexFallback', 'test_unique_flag', 0, 2, 3).
python_method('TestRegexFallback', 'test_default_extracted', 0, 2, 3).
python_method('TestRegexFallback', 'test_multi_table', 0, 3, 1).
python_method('TestRegexFallback', 'test_empty_input', 0, 2, 1).
python_method('TestRegexFallback', 'test_to_dict', 0, 2, 2).
python_class('tests/test_sql_ddl_parser.py', 'TestSqlglotPath').
python_method('TestSqlglotPath', 'test_picks_sqlglot_by_default', 0, 4, 3).
python_method('TestSqlglotPath', 'test_falls_back_on_unparseable', 0, 2, 2).
python_class('tests/test_sql_ddl_parser.py', 'TestTableHelpers').
python_method('TestTableHelpers', 'test_column_lookup_case_insensitive', 0, 3, 3).
python_method('TestTableHelpers', 'test_to_dict_round_trip', 0, 3, 2).
python_class('tests/test_sql_dialect_resolver.py', 'TestNormalize').
python_method('TestNormalize', 'test_default_when_empty', 0, 3, 1).
python_method('TestNormalize', 'test_lowercases', 0, 2, 1).
python_method('TestNormalize', 'test_aliases', 0, 5, 1).
python_method('TestNormalize', 'test_unknown_passthrough', 0, 2, 1).
python_class('tests/test_sql_dialect_resolver.py', 'TestIsSupported').
python_method('TestIsSupported', 'test_known', 0, 4, 1).
python_method('TestIsSupported', 'test_unknown', 0, 2, 1).
python_method('TestIsSupported', 'test_empty_returns_false_or_default', 0, 2, 1).
python_class('tests/test_sql_dialect_resolver.py', 'TestSupportedDialectsConstant').
python_method('TestSupportedDialectsConstant', 'test_includes_canonical_names', 0, 3, 0).
python_class('tests/test_sql_dialect_resolver.py', 'TestTranspile').
python_method('TestTranspile', 'test_raises_when_sqlglot_missing', 1, 1, 3).
python_method('TestTranspile', 'test_round_trip_select', 0, 2, 4).
python_method('TestTranspile', 'test_passthrough_same_dialect', 0, 2, 4).
python_class('tests/test_sql_fixtures.py', 'TestConnectionFixture').
python_method('TestConnectionFixture', 'test_to_fixture', 0, 6, 2).
python_class('tests/test_sql_fixtures.py', 'TestSchemaFixtureFromRows').
python_method('TestSchemaFixtureFromRows', 'test_basic', 0, 6, 3).
python_method('TestSchemaFixtureFromRows', 'test_skips_empty_rows', 0, 3, 2).
python_method('TestSchemaFixtureFromRows', 'test_truthy_flags', 0, 4, 1).
python_method('TestSchemaFixtureFromRows', 'test_default_dash_treated_as_none', 0, 2, 1).
python_method('TestSchemaFixtureFromRows', 'test_default_value_preserved', 0, 2, 1).
python_method('TestSchemaFixtureFromRows', 'test_to_fixture_shape', 0, 4, 2).
python_class('tests/test_sql_query_parser.py', 'TestClassify').
python_method('TestClassify', 'test_select', 0, 3, 1).
python_method('TestClassify', 'test_with_cte', 0, 2, 1).
python_method('TestClassify', 'test_insert', 0, 2, 1).
python_method('TestClassify', 'test_update', 0, 2, 1).
python_method('TestClassify', 'test_delete', 0, 2, 1).
python_method('TestClassify', 'test_merge', 0, 2, 1).
python_method('TestClassify', 'test_other', 0, 2, 1).
python_method('TestClassify', 'test_empty', 0, 2, 1).
python_class('tests/test_sql_query_parser.py', 'TestAnalyzeQueryRegexFallback').
python_method('TestAnalyzeQueryRegexFallback', 'test_basic_kind_set', 0, 3, 1).
python_class('tests/test_sql_query_parser.py', 'TestAnalyzeQuerySqlglot').
python_method('TestAnalyzeQuerySqlglot', 'test_extracts_tables', 0, 3, 1).
python_method('TestAnalyzeQuerySqlglot', 'test_extracts_columns', 0, 3, 1).
python_method('TestAnalyzeQuerySqlglot', 'test_formatted_present', 0, 3, 2).
python_method('TestAnalyzeQuerySqlglot', 'test_returns_kind_only_on_unparseable', 0, 2, 2).
python_class('tests/test_sql_scenarios_e2e.py', 'TestScenarios').
python_method('TestScenarios', 'test_dir_not_empty', 0, 2, 1).
python_method('TestScenarios', 'test_parse_succeeds', 1, 5, 4).
python_method('TestScenarios', 'test_has_sql_steps', 1, 4, 3).
python_method('TestScenarios', 'test_round_trip_preserves_step_count', 1, 6, 5).
python_method('TestScenarios', 'test_dialect_propagates_to_steps', 1, 4, 3).
python_class('tests/test_sql_scenarios_e2e.py', 'TestSpecificScenarios').
python_method('TestSpecificScenarios', 'test_users_contract_postgres', 0, 6, 3).
python_method('TestSpecificScenarios', 'test_orders_sqlite', 0, 5, 4).
python_class('tests/test_suite_cmd_helpers.py', 'TestFindFiles').
python_method('TestFindFiles', 'test_returns_empty_for_missing_dir', 1, 2, 1).
python_method('TestFindFiles', 'test_finds_matching_files', 1, 3, 3).
python_method('TestFindFiles', 'test_finds_files_in_subdirs', 1, 2, 4).
python_method('TestFindFiles', 'test_path_with_separator', 1, 2, 4).
python_method('TestFindFiles', 'test_path_with_missing_subdir', 1, 2, 1).
python_class('tests/test_suite_cmd_helpers.py', 'TestCollectFromSuite').
python_method('TestCollectFromSuite', 'test_named_suite', 1, 2, 3).
python_method('TestCollectFromSuite', 'test_string_pattern_in_suite', 1, 2, 3).
python_method('TestCollectFromSuite', 'test_missing_suite_name', 1, 2, 1).
python_method('TestCollectFromSuite', 'test_uses_parent_when_file', 1, 2, 3).
python_class('tests/test_suite_cmd_helpers.py', 'TestCollectByPattern').
python_method('TestCollectByPattern', 'test_finds_matching', 1, 2, 3).
python_method('TestCollectByPattern', 'test_no_match', 1, 2, 1).
python_class('tests/test_suite_cmd_helpers.py', 'TestCollectRecursive').
python_method('TestCollectRecursive', 'test_finds_testql_files', 1, 2, 4).
python_method('TestCollectRecursive', 'test_empty_project', 1, 2, 1).
python_class('tests/test_suite_cmd_helpers.py', 'TestCollectTestFiles').
python_method('TestCollectTestFiles', 'test_single_file_target', 1, 2, 2).
python_method('TestCollectTestFiles', 'test_suite_takes_priority', 1, 2, 2).
python_method('TestCollectTestFiles', 'test_pattern_used_when_no_suite', 1, 2, 3).
python_method('TestCollectTestFiles', 'test_deduplication', 1, 2, 3).
python_method('TestCollectTestFiles', 'test_nonexistent_files_excluded', 1, 2, 1).
python_class('tests/test_suite_execution.py', 'FakeResult').
python_method('FakeResult', '__init__', 5, 2, 0).
python_class('tests/test_suite_execution.py', 'TestRunSingleFile').
python_method('TestRunSingleFile', 'test_ok_result', 0, 5, 4).
python_method('TestRunSingleFile', 'test_fail_result', 0, 3, 4).
python_method('TestRunSingleFile', 'test_exception_returns_error_dict', 0, 4, 4).
python_class('tests/test_suite_execution.py', 'TestRunSuiteFiles').
python_method('TestRunSuiteFiles', 'test_empty_files', 0, 2, 1).
python_method('TestRunSuiteFiles', 'test_all_pass', 0, 3, 6).
python_method('TestRunSuiteFiles', 'test_one_fail_continues', 0, 3, 6).
python_method('TestRunSuiteFiles', 'test_fail_fast_stops', 0, 2, 6).
python_method('TestRunSuiteFiles', 'test_uses_config_default_url', 0, 2, 6).
python_class('tests/test_suite_listing.py', 'TestParseTesttoonHeader').
python_method('TestParseTesttoonHeader', 'test_returns_none_for_no_header', 0, 2, 1).
python_method('TestParseTesttoonHeader', 'test_parses_scenario_header', 0, 4, 1).
python_method('TestParseTesttoonHeader', 'test_parses_type_without_scenario', 0, 3, 1).
python_method('TestParseTesttoonHeader', 'test_returns_none_for_plain_content', 0, 2, 1).
python_method('TestParseTesttoonHeader', 'test_tags_default_empty', 0, 2, 1).
python_class('tests/test_suite_listing.py', 'TestParseYamlMetaBlock').
python_method('TestParseYamlMetaBlock', 'test_returns_none_without_meta', 0, 2, 1).
python_method('TestParseYamlMetaBlock', 'test_parses_meta_block', 0, 3, 1).
python_method('TestParseYamlMetaBlock', 'test_meta_with_tags', 0, 2, 1).
python_method('TestParseYamlMetaBlock', 'test_empty_meta_block', 0, 2, 2).
python_class('tests/test_suite_listing.py', 'TestParseMeta').
python_method('TestParseMeta', 'test_default_meta_from_stem', 1, 3, 2).
python_method('TestParseMeta', 'test_uses_header_when_present', 1, 3, 2).
python_method('TestParseMeta', 'test_uses_yaml_meta_when_no_header', 1, 2, 2).
python_method('TestParseMeta', 'test_returns_default_on_missing_file', 1, 2, 3).
python_class('tests/test_suite_listing.py', 'TestFilterTests').
python_method('TestFilterTests', '_make_files', 1, 2, 2).
python_method('TestFilterTests', 'test_filter_all', 1, 2, 3).
python_method('TestFilterTests', 'test_filter_by_type', 1, 3, 3).
python_method('TestFilterTests', 'test_filter_by_tag', 1, 2, 3).
python_method('TestFilterTests', 'test_empty_input', 1, 2, 1).
python_method('TestFilterTests', 'test_result_has_required_keys', 1, 6, 2).
python_class('tests/test_suite_listing.py', 'TestRenderTestList').
python_method('TestRenderTestList', 'test_render_json', 1, 2, 3).
python_method('TestRenderTestList', 'test_render_simple', 1, 2, 2).
python_method('TestRenderTestList', 'test_render_table', 1, 4, 2).
python_method('TestRenderTestList', 'test_render_table_empty_tags', 1, 2, 2).
python_class('tests/test_sumd_parser.py', 'TestSumdMetadata').
python_method('TestSumdMetadata', 'test_defaults', 0, 3, 1).
python_class('tests/test_sumd_parser.py', 'TestSumdParser').
python_method('TestSumdParser', 'test_parse_returns_document', 0, 2, 3).
python_method('TestSumdParser', 'test_parse_metadata_name', 0, 2, 2).
python_method('TestSumdParser', 'test_parse_metadata_version', 0, 2, 2).
python_method('TestSumdParser', 'test_parse_metadata_ecosystem', 0, 2, 2).
python_method('TestSumdParser', 'test_parse_metadata_ai_model', 0, 2, 2).
python_method('TestSumdParser', 'test_parse_metadata_fallback_header', 0, 2, 2).
python_method('TestSumdParser', 'test_parse_architecture', 0, 2, 2).
python_method('TestSumdParser', 'test_parse_empty_architecture', 0, 2, 2).
python_method('TestSumdParser', 'test_parse_interface_rest', 0, 4, 3).
python_method('TestSumdParser', 'test_parse_workflow', 0, 5, 3).
python_method('TestSumdParser', 'test_extract_section', 0, 2, 2).
python_method('TestSumdParser', 'test_extract_section_missing', 0, 2, 2).
python_method('TestSumdParser', 'test_generate_testql_scenarios', 0, 3, 5).
python_method('TestSumdParser', 'test_parse_file', 1, 2, 2).
python_method('TestSumdParser', 'test_parse_toon_testql_block_with_api_entries', 0, 2, 3).
python_method('TestSumdParser', 'test_parse_toon_code_block_scenario', 0, 2, 3).
python_method('TestSumdParser', 'test_generate_testql_scenarios_with_testql_scenarios', 0, 2, 4).
python_method('TestSumdParser', 'test_generate_testql_scenarios_empty_interfaces_and_scenarios', 0, 3, 4).
python_method('TestSumdParser', 'test_parse_toon_api_block_with_comment_and_blank_lines', 0, 2, 3).
python_method('TestSumdParser', 'test_parse_toon_scenario_with_type_meta_comment', 0, 2, 3).
python_class('tests/test_targets.py', 'TestRegistry').
python_method('TestRegistry', 'test_three_builtin_targets', 0, 2, 2).
python_method('TestRegistry', 'test_get', 1, 3, 3).
python_method('TestRegistry', 'test_get_unknown', 0, 2, 1).
python_class('tests/test_targets.py', 'TestTestToonTarget').
python_method('TestTestToonTarget', 'test_extension', 0, 2, 1).
python_method('TestTestToonTarget', 'test_render_includes_meta', 0, 4, 3).
python_class('tests/test_targets.py', 'TestNLTarget').
python_method('TestNLTarget', 'test_extension', 0, 2, 1).
python_method('TestNLTarget', 'test_render', 0, 3, 3).
python_class('tests/test_targets.py', 'TestPytestTarget').
python_method('TestPytestTarget', 'test_extension', 0, 2, 1).
python_method('TestPytestTarget', 'test_emits_one_test_per_step', 0, 2, 4).
python_method('TestPytestTarget', 'test_safe_idents', 0, 2, 4).
python_method('TestPytestTarget', 'test_summary_in_docstring', 0, 2, 3).
python_method('TestPytestTarget', 'test_handles_unnamed_steps', 0, 2, 4).
python_class('tests/test_test_generator.py', 'TestTestGeneratorAnalyze').
python_method('TestTestGeneratorAnalyze', 'test_analyze_returns_profile', 1, 2, 3).
python_method('TestTestGeneratorAnalyze', 'test_analyze_empty_project_mixed_type', 1, 2, 3).
python_method('TestTestGeneratorAnalyze', 'test_analyze_fastapi_project', 1, 2, 4).
python_method('TestTestGeneratorAnalyze', 'test_analyze_cli_project', 1, 2, 4).
python_method('TestTestGeneratorAnalyze', 'test_analyze_argparse_cli_project', 1, 2, 5).
python_method('TestTestGeneratorAnalyze', 'test_analyze_typer_cli_project', 1, 2, 4).
python_method('TestTestGeneratorAnalyze', 'test_analyze_sets_project_path', 1, 2, 4).
python_class('tests/test_test_generator.py', 'TestTestGeneratorGenerateTests').
python_method('TestTestGeneratorGenerateTests', 'test_generate_empty_project_returns_empty_list', 1, 2, 3).
python_method('TestTestGeneratorGenerateTests', 'test_generate_creates_output_dir', 1, 2, 4).
python_method('TestTestGeneratorGenerateTests', 'test_generate_default_output_dir', 1, 2, 4).
python_method('TestTestGeneratorGenerateTests', 'test_generate_auto_analyzes_if_not_analyzed', 1, 2, 3).
python_method('TestTestGeneratorGenerateTests', 'test_generate_returns_list', 1, 2, 4).
python_method('TestTestGeneratorGenerateTests', 'test_generate_with_python_tests', 1, 2, 7).
python_method('TestTestGeneratorGenerateTests', 'test_generate_accepts_string_output_dir', 1, 2, 4).
python_method('TestTestGeneratorGenerateTests', 'test_generate_with_discovered_routes', 1, 2, 6).
python_class('tests/test_testtoon_adapter.py', 'TestDetect').
python_method('TestDetect', 'test_detect_by_extension', 1, 3, 3).
python_method('TestDetect', 'test_detect_by_metadata_header', 0, 2, 2).
python_method('TestDetect', 'test_detect_negative', 0, 3, 2).
python_method('TestDetect', 'test_detect_section_header', 0, 2, 2).
python_class('tests/test_testtoon_adapter.py', 'TestParse').
python_method('TestParse', 'test_parse_string', 0, 5, 2).
python_method('TestParse', 'test_parse_file', 1, 2, 2).
python_method('TestParse', 'test_api_steps', 0, 8, 3).
python_method('TestParse', 'test_api_step_has_status_assert', 0, 4, 3).
python_method('TestParse', 'test_navigate_step', 0, 7, 3).
python_method('TestParse', 'test_encoder_step', 0, 7, 3).
python_method('TestParse', 'test_assert_section', 0, 6, 2).
python_method('TestParse', 'test_unknown_section_falls_through_to_generic', 0, 5, 2).
python_method('TestParse', 'test_indented_row_starting_with_hash_is_not_comment', 0, 6, 2).
python_class('tests/test_testtoon_adapter.py', 'TestRender').
python_method('TestRender', 'test_render_round_trip_basic', 0, 8, 4).
python_method('TestRender', 'test_render_includes_metadata', 0, 4, 2).
python_method('TestRender', 'test_render_includes_config', 0, 3, 2).
python_method('TestRender', 'test_render_empty_plan', 0, 2, 2).
python_method('TestRender', 'test_round_trip_preserves_flow_steps', 0, 10, 4).
python_method('TestRender', 'test_round_trip_preserves_wait_steps', 0, 5, 3).
python_method('TestRender', 'test_round_trip_preserves_include_steps', 0, 6, 3).
python_class('tests/test_testtoon_adapter.py', 'TestAdapterRegistration').
python_method('TestAdapterRegistration', 'test_adapter_registered_in_default_registry', 0, 3, 2).
python_method('TestAdapterRegistration', 'test_extensions_match', 0, 3, 1).
python_class('tests/test_testtoon_adapter.py', 'TestFlowExpansion').
python_method('TestFlowExpansion', '_expand', 1, 1, 1).
python_method('TestFlowExpansion', 'test_flow_value_column_quoted_for_input', 0, 2, 1).
python_method('TestFlowExpansion', 'test_flow_text_column_alias', 0, 3, 1).
python_method('TestFlowExpansion', 'test_flow_meta_dash_emits_no_extra_arg', 0, 3, 1).
python_method('TestFlowExpansion', 'test_flow_value_dash_does_not_pollute_click', 0, 3, 1).
python_method('TestFlowExpansion', 'test_flow_value_null_treated_as_empty', 0, 2, 1).
python_method('TestFlowExpansion', 'test_flow_meta_dict_legacy_passthrough', 0, 3, 1).
python_method('TestFlowExpansion', 'test_flow_two_column_still_works', 0, 3, 1).
python_class('tests/test_testtoon_adapter.py', 'TestShellExpansion').
python_method('TestShellExpansion', '_expand', 1, 1, 1).
python_method('TestShellExpansion', 'test_shell_section_quotes_compound_command', 0, 2, 1).
python_method('TestShellExpansion', 'test_shell_expected_exit_column_alias', 0, 5, 1).
python_method('TestShellExpansion', 'test_shell_quoted_row_in_testtoon', 0, 2, 2).
python_method('TestShellExpansion', 'test_shell_dry_run_executes_full_command_not_first_token', 0, 7, 5).
python_class('tests/test_testtoon_adapter.py', 'TestBackwardCompatibility').
python_method('TestBackwardCompatibility', 'test_legacy_parser_imports', 0, 3, 3).
python_method('TestBackwardCompatibility', 'test_interpreter_package_reexports', 0, 2, 2).
python_class('tests/test_toon_parser.py', 'TestToonParser').
python_method('TestToonParser', 'test_init', 0, 2, 2).
python_method('TestToonParser', 'test_parse_empty', 0, 4, 2).
python_method('TestToonParser', 'test_parse_api_get', 0, 5, 3).
python_method('TestToonParser', 'test_parse_api_post', 0, 3, 3).
python_method('TestToonParser', 'test_parse_api_no_status_defaults_200', 0, 3, 3).
python_method('TestToonParser', 'test_parse_assert_block', 0, 5, 3).
python_method('TestToonParser', 'test_parse_log_block_sets_base_url', 0, 2, 2).
python_method('TestToonParser', 'test_parse_multiple_api_blocks', 0, 2, 3).
python_method('TestToonParser', 'test_parse_resets_contract_between_calls', 0, 3, 3).
python_method('TestToonParser', 'test_parse_file', 1, 3, 3).
python_class('tests/test_topology.py', 'TestTopologyBuilder').
python_method('TestTopologyBuilder', 'test_builds_root_type_dependency_and_evidence_nodes', 0, 9, 2).
python_method('TestTopologyBuilder', 'test_builds_interface_node_for_openapi', 0, 3, 2).
python_method('TestTopologyBuilder', 'test_to_dict_can_embed_manifest', 0, 4, 3).
python_class('tests/test_topology.py', 'TestTopologySerializers').
python_method('TestTopologySerializers', 'test_render_json', 0, 3, 3).
python_method('TestTopologySerializers', 'test_render_yaml', 0, 3, 5).
python_method('TestTopologySerializers', 'test_render_toon', 0, 4, 2).
python_class('tests/test_topology.py', 'TestTopologyCli').
python_method('TestTopologyCli', 'test_topology_help_is_available', 0, 3, 2).
python_method('TestTopologyCli', 'test_topology_default_toon_output', 0, 4, 3).
python_method('TestTopologyCli', 'test_topology_json_output', 0, 4, 5).
python_method('TestTopologyCli', 'test_topology_missing_path_exits_nonzero', 0, 3, 3).
python_class('tests/test_topology_generator.py', 'TestNodeToStepMapping').
python_method('TestNodeToStepMapping', 'test_interface_http_becomes_api_step', 0, 5, 5).
python_method('TestNodeToStepMapping', 'test_page_becomes_gui_navigate', 0, 4, 5).
python_method('TestNodeToStepMapping', 'test_link_becomes_api_get', 0, 3, 5).
python_method('TestNodeToStepMapping', 'test_form_post_becomes_api_post', 0, 5, 5).
python_method('TestNodeToStepMapping', 'test_dependency_becomes_shell_step', 0, 4, 5).
python_method('TestNodeToStepMapping', 'test_evidence_becomes_shell_file_check', 0, 4, 5).
python_method('TestNodeToStepMapping', 'test_unsupported_node_returns_none', 0, 2, 4).
python_class('tests/test_topology_generator.py', 'TestFromTrace').
python_method('TestFromTrace', 'test_trace_produces_plan_with_steps', 0, 7, 3).
python_method('TestFromTrace', 'test_plan_skips_missing_nodes', 0, 3, 5).
python_method('TestFromTrace', 'test_assertions_from_edge_conditions', 0, 4, 5).
python_class('tests/test_topology_generator.py', 'TestToTesttoon').
python_method('TestToTesttoon', 'test_round_trip_contains_expected_sections', 0, 3, 4).
python_class('tests/test_topology_generator.py', 'TestConfigOverride').
python_method('TestConfigOverride', 'test_custom_http_method', 0, 3, 6).
python_class('tests/test_unit_execution.py', 'TestUnitExecution').
python_method('TestUnitExecution', 'interpreter', 0, 1, 1).
python_method('TestUnitExecution', 'test_unit_import_success', 1, 2, 2).
python_method('TestUnitExecution', 'test_unit_import_failure', 1, 2, 2).
python_method('TestUnitExecution', 'test_unit_assert_success', 1, 2, 2).
python_method('TestUnitExecution', 'test_unit_assert_failure', 1, 2, 2).
python_method('TestUnitExecution', 'test_unit_assert_builtin_function', 1, 2, 2).
python_method('TestUnitExecution', 'test_unit_pytest_no_args', 1, 2, 3).
python_method('TestUnitExecution', 'test_unit_pytest_dry_run', 1, 3, 2).
python_class('tests/test_unit_execution.py', 'TestUnitDryRun').
python_method('TestUnitDryRun', 'interpreter', 0, 1, 1).
python_method('TestUnitDryRun', 'test_unit_import_dry_run', 1, 2, 2).
python_method('TestUnitDryRun', 'test_unit_pytest_discover_dry_run', 1, 2, 2).
python_class('tests/test_validation.py', 'TestValidateExpansion').
python_method('TestValidateExpansion', 'test_validate_row_emits_validate_oql_line', 0, 4, 2).
python_method('TestValidateExpansion', 'test_validate_quotes_regex_metachars', 0, 4, 2).
python_method('TestValidateExpansion', 'test_validate_pipe_inside_quoted_criteria_is_literal', 0, 5, 3).
python_method('TestValidateExpansion', 'test_validate_comma_inside_quoted_criteria_is_literal', 0, 3, 2).
python_method('TestValidateExpansion', 'test_validate_skips_rows_without_type_or_target', 0, 2, 2).
python_class('tests/test_validation.py', 'TestValidateContains').
python_method('TestValidateContains', 'test_contains_pass', 1, 2, 2).
python_method('TestValidateContains', 'test_contains_fail', 1, 3, 3).
python_method('TestValidateContains', 'test_not_contains_pass', 1, 2, 2).
python_method('TestValidateContains', 'test_not_contains_fail', 1, 2, 2).
python_class('tests/test_validation.py', 'TestValidateRegex').
python_method('TestValidateRegex', 'test_regex_pass', 1, 2, 2).
python_method('TestValidateRegex', 'test_regex_fail', 1, 2, 2).
python_class('tests/test_validation.py', 'TestValidateTemplate').
python_method('TestValidateTemplate', 'test_template_pass', 2, 2, 3).
python_method('TestValidateTemplate', 'test_template_missing_file', 2, 2, 2).
python_class('tests/test_validation.py', 'TestValidateSemantic').
python_method('TestValidateSemantic', 'test_semantic_emits_event_and_passes', 1, 7, 4).

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────
makefile_target('help', 'Default target').
makefile_target('install', 'Installation').
makefile_target('install-dev', '').
makefile_target('test', 'Testing').
makefile_target('test-cov', '').
makefile_target('lint', 'Code quality').
makefile_target('format', '').
makefile_target('clean', 'Utilities').
makefile_target('publish', 'Release helpers').
makefile_target('publish-confirm', '').
makefile_target('publish-test', '').
makefile_target('version', '').

% ── Taskfile Tasks ───────────────────────────────────────
taskfile_task('', 'Install Python dependencies (editable)').
taskfile_task('', 'Upgrade all outdated Python packages in the active / project venv').
taskfile_task('', 'Run pyqual quality pipeline (test + lint + format check)').
taskfile_task('', 'Run pyqual with auto-fix (format + lint fix)').
taskfile_task('', 'Generate pyqual quality report').
taskfile_task('', 'Run pytest suite').
taskfile_task('', 'Run ruff lint check').
taskfile_task('', 'Auto-format with ruff').
taskfile_task('', 'Build wheel + sdist').
taskfile_task('', 'Remove build artefacts').
taskfile_task('', 'Run install, quality check, test').
taskfile_task('', 'Run OQL scenario file').
taskfile_task('', 'Start OQL interactive shell').
taskfile_task('', 'Reverse-engineer testql project structure').
taskfile_task('', 'Validate app.doql.less syntax').
taskfile_task('', 'Run doql health checks').
taskfile_task('', 'Generate code from app.doql.less').
taskfile_task('', 'Full doql analysis (adopt + validate + doctor)').
taskfile_task('', 'Build Docker image via docker-compose').
taskfile_task('', 'Start Docker containers').
taskfile_task('', 'Stop Docker containers').
taskfile_task('', 'Build and publish package').
taskfile_task('', 'Show available tasks').

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', '*(not set)*', 'Required: OpenRouter API key (https://openrouter.ai/keys)').
env_variable('LLM_MODEL', 'openrouter/qwen/qwen3-coder-next', 'Model (default: openrouter/qwen/qwen3-coder-next)').
env_variable('PFIX_AUTO_APPLY', 'true', 'true = apply fixes without asking').
env_variable('PFIX_AUTO_INSTALL_DEPS', 'true', 'true = auto pip/uv install').
env_variable('PFIX_AUTO_RESTART', 'false', 'true = os.execv restart after fix').
env_variable('PFIX_MAX_RETRIES', '3', '').
env_variable('PFIX_DRY_RUN', 'false', '').
env_variable('PFIX_ENABLED', 'true', '').
env_variable('PFIX_GIT_COMMIT', 'false', 'true = auto-commit fixes').
env_variable('PFIX_GIT_PREFIX', 'pfix:', 'commit message prefix').
env_variable('PFIX_CREATE_BACKUPS', 'false', 'false = disable .pfix_backups/ directory').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('api-crud-template.testql.toon.yaml', 'api').
testql_scenario('api-health.testql.toon.yaml', 'api').
testql_scenario('api-smoke.testql.toon.yaml', 'api').
testql_scenario('auth-login.testql.toon.yaml', 'api').
testql_scenario('backend-diagnostic.testql.toon.yaml', 'api').
testql_scenario('connect-config-feature-flags.testql.toon.yaml', 'gui').
testql_scenario('connect-config-labels.testql.toon.yaml', 'gui').
testql_scenario('connect-config-settings.testql.toon.yaml', 'gui').
testql_scenario('connect-config-tables.testql.toon.yaml', 'gui').
testql_scenario('connect-config-theme.testql.toon.yaml', 'gui').
testql_scenario('connect-config-users.testql.toon.yaml', 'gui').
testql_scenario('connect-id-barcode.testql.toon.yaml', 'gui').
testql_scenario('connect-id-list.testql.toon.yaml', 'gui').
testql_scenario('connect-id-manual.testql.toon.yaml', 'gui').
testql_scenario('connect-id-qr.testql.toon.yaml', 'gui').
testql_scenario('connect-id-rfid.testql.toon.yaml', 'gui').
testql_scenario('connect-manager-activities.testql.toon.yaml', 'gui').
testql_scenario('connect-manager-intervals.testql.toon.yaml', 'gui').
testql_scenario('connect-manager-library.testql.toon.yaml', 'gui').
testql_scenario('connect-manager-scenarios.testql.toon.yaml', 'gui').
testql_scenario('connect-manager-test-types.testql.toon.yaml', 'gui').
testql_scenario('connect-reports-chart.testql.toon.yaml', 'gui').
testql_scenario('connect-reports-custom.testql.toon.yaml', 'gui').
testql_scenario('connect-reports-filter.testql.toon.yaml', 'gui').
testql_scenario('connect-reports-month.testql.toon.yaml', 'gui').
testql_scenario('connect-reports-quarter.testql.toon.yaml', 'gui').
testql_scenario('connect-reports-week.testql.toon.yaml', 'gui').
testql_scenario('connect-reports-year.testql.toon.yaml', 'gui').
testql_scenario('connect-test-devices-search.testql.toon.yaml', 'gui').
testql_scenario('connect-test-full-test.testql.toon.yaml', 'gui').
testql_scenario('connect-test-protocols.testql.toon.yaml', 'gui').
testql_scenario('connect-test-scenario-view.testql.toon.yaml', 'gui').
testql_scenario('connect-test-testing-barcode.testql.toon.yaml', 'gui').
testql_scenario('connect-test-testing-qr.testql.toon.yaml', 'gui').
testql_scenario('connect-test-testing-rfid.testql.toon.yaml', 'gui').
testql_scenario('connect-test-testing-search.testql.toon.yaml', 'gui').
testql_scenario('connect-workshop-dispositions-search.testql.toon.yaml', 'gui').
testql_scenario('connect-workshop-requests-search.testql.toon.yaml', 'gui').
testql_scenario('connect-workshop-services-search.testql.toon.yaml', 'gui').
testql_scenario('connect-workshop-transport-search.testql.toon.yaml', 'gui').
testql_scenario('connect-workshop-transport.testql.toon.yaml', 'gui').
testql_scenario('create-todays-reports.testql.toon.yaml', 'gui').
testql_scenario('device-identification.testql.toon.yaml', 'gui').
testql_scenario('encoder-navigation.testql.toon.yaml', 'gui').
testql_scenario('encoder-workshop.testql.toon.yaml', 'gui').
testql_scenario('full-diagnostic.testql.toon.yaml', 'gui').
testql_scenario('generate-test-reports.testql.toon.yaml', 'interaction').
testql_scenario('generated-api-integration.testql.toon.yaml', 'api').
testql_scenario('generated-api-smoke.testql.toon.yaml', 'api').
testql_scenario('generated-asset-assert.testql.toon.yaml', 'web').
testql_scenario('generated-cli-extended.testql.toon.yaml', 'cli').
testql_scenario('generated-cli-tests.testql.toon.yaml', 'cli').
testql_scenario('generated-from-pytests.testql.toon.yaml', 'integration').
testql_scenario('generated-sitemap-assert.testql.toon.yaml', 'web').
testql_scenario('health-check.testql.toon.yaml', 'api').
testql_scenario('quick-navigation.testql.toon.yaml', 'gui').
testql_scenario('recorded-test-session.testql.toon.yaml', 'gui').
testql_scenario('reproduce-view.testql.toon.yaml', 'gui').
testql_scenario('run-all-views.testql.toon.yaml', 'api').
testql_scenario('run-mask-test-protocol.testql.toon.yaml', 'api').
testql_scenario('session-recording.testql.toon.yaml', 'interaction').
testql_scenario('test-api.testql.toon.yaml', 'api').
testql_scenario('test-app-lifecycle.testql.toon.yaml', 'api').
testql_scenario('test-device-flow.testql.toon.yaml', 'interaction').
testql_scenario('test-devices-crud.testql.toon.yaml', 'api').
testql_scenario('test-dsl-objects.testql.toon.yaml', 'api').
testql_scenario('test-encoder.testql.toon.yaml', 'gui').
testql_scenario('test-gui-all.testql.toon.yaml', 'api').
testql_scenario('test-gui-connect-config.testql.toon.yaml', 'gui').
testql_scenario('test-gui-connect-id.testql.toon.yaml', 'gui').
testql_scenario('test-gui-connect-manager.testql.toon.yaml', 'gui').
testql_scenario('test-gui-connect-reports.testql.toon.yaml', 'gui').
testql_scenario('test-gui-connect-test.testql.toon.yaml', 'gui').
testql_scenario('test-gui-connect-workshop.testql.toon.yaml', 'gui').
testql_scenario('test-mixed-workflow.testql.toon.yaml', 'e2e').
testql_scenario('test-protocol-flow.testql.toon.yaml', 'api').
testql_scenario('test-ui-navigation.testql.toon.yaml', 'api').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('openapi.yaml', 'openapi').
sumd_declared_file('testql/scenarios/generic/api-crud-template.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/c2004/smoke/api-health.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/c2004/smoke/api-smoke.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/generic/auth-login.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/diagnostics/backend-diagnostic.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-config-feature-flags.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-config-labels.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-config-settings.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-config-tables.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-config-theme.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-config-users.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-id-barcode.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-id-list.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-id-manual.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-id-qr.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-id-rfid.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-manager-activities.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-manager-intervals.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-manager-library.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-manager-scenarios.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-manager-test-types.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-reports-chart.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-reports-custom.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-reports-filter.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-reports-month.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-reports-quarter.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-reports-week.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-reports-year.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-test-devices-search.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-test-full-test.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-test-protocols.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-test-scenario-view.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-test-testing-barcode.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-test-testing-qr.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-test-testing-rfid.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-test-testing-search.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-workshop-dispositions-search.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-workshop-requests-search.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-workshop-services-search.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/connect-workshop-transport-search.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/c2004/gui/connect-workshop-transport.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/diagnostics/create-todays-reports.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/examples/device-identification.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/c2004/encoder/encoder-navigation.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/c2004/encoder/encoder-workshop.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/diagnostics/full-diagnostic.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/diagnostics/generate-test-reports.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-api-integration.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-api-smoke.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-asset-assert.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-cli-extended.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-cli-tests.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-from-pytests.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-sitemap-assert.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/generic/health-check.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/examples/quick-navigation.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/recordings/recorded-test-session.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/reproduce-view.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/views/run-all-views.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/run-mask-test-protocol.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/recordings/session-recording.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-api.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-app-lifecycle.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/examples/test-device-flow.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-devices-crud.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-dsl-objects.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-encoder.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-gui-all.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-gui-connect-config.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-gui-connect-id.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-gui-connect-manager.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-gui-connect-reports.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-gui-connect-test.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-gui-connect-workshop.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-mixed-workflow.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-protocol-flow.testql.toon.yaml', 'testql').
sumd_declared_file('testql/scenarios/tests/test-ui-navigation.testql.toon.yaml', 'testql').
sumd_declared_file('Taskfile.yml', 'taskfile').
sumd_declared_file('pyqual.yaml', 'pyqual').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_declared_file('openapi.yaml', 'openapi').
sumd_interface('api', '').
sumd_interface('cli', 'click').
sumd_interface('cli', '').
sumd_workflow('install', 'manual').
sumd_workflow_step('install', 1, 'echo "📦 Installing testql..."').
sumd_workflow_step('install', 2, 'if command -v uv > /dev/null 2>&1').
sumd_workflow_step('install', 3, 'uv pip install -e .').
sumd_workflow_step('install', 4, 'else \').
sumd_workflow_step('install', 5, 'pip install -e .').
sumd_workflow_step('install', 6, 'fi').
sumd_workflow_step('install', 7, 'echo "✅ Installation completed!"').
sumd_workflow('install-dev', 'manual').
sumd_workflow_step('install-dev', 1, 'echo "📦 Installing testql with dev dependencies..."').
sumd_workflow_step('install-dev', 2, 'if command -v uv > /dev/null 2>&1').
sumd_workflow_step('install-dev', 3, 'uv pip install -e ".[dev]"').
sumd_workflow_step('install-dev', 4, 'else \').
sumd_workflow_step('install-dev', 5, 'pip install -e ".[dev]"').
sumd_workflow_step('install-dev', 6, 'fi').
sumd_workflow_step('install-dev', 7, 'echo "✅ Dev installation completed!"').
sumd_workflow('test', 'manual').
sumd_workflow_step('test', 1, 'echo "🧪 Running tests..."').
sumd_workflow_step('test', 2, '.venv/bin/python -m pytest tests/ -v --tb=short').
sumd_workflow('test-cov', 'manual').
sumd_workflow_step('test-cov', 1, 'echo "🧪 Running tests with coverage..."').
sumd_workflow_step('test-cov', 2, '.venv/bin/python -m pytest tests/ -v --cov=testql --cov-report=term-missing --cov-report=json').
sumd_workflow('lint', 'manual').
sumd_workflow_step('lint', 1, 'echo "🔍 Running linting with ruff..."').
sumd_workflow_step('lint', 2, '.venv/bin/python -m ruff check testql/').
sumd_workflow_step('lint', 3, '.venv/bin/python -m ruff check tests/').
sumd_workflow('format', 'manual').
sumd_workflow_step('format', 1, 'echo "📝 Formatting code with ruff..."').
sumd_workflow_step('format', 2, '.venv/bin/python -m ruff format testql/').
sumd_workflow_step('format', 3, '.venv/bin/python -m ruff format tests/').
sumd_workflow('clean', 'manual').
sumd_workflow_step('clean', 1, 'echo "🧹 Cleaning temporary files..."').
sumd_workflow_step('clean', 2, 'find . -type f -name "*.pyc" -delete').
sumd_workflow_step('clean', 3, 'find . -type d -name "__pycache__" -delete').
sumd_workflow('publish', 'manual').
sumd_workflow_step('publish', 1, 'echo "📦 Publishing to PyPI..."').
sumd_workflow_step('publish', 2, 'command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build)').
sumd_workflow_step('publish', 3, 'rm -rf dist/ build/ *.egg-info/').
sumd_workflow_step('publish', 4, '.venv/bin/python -m build').
sumd_workflow_step('publish', 5, '.venv/bin/twine check dist/*').
sumd_workflow_step('publish', 6, 'echo "⚡ Ready to upload. Run: make publish-confirm to upload to PyPI"').
sumd_workflow('publish-confirm', 'manual').
sumd_workflow_step('publish-confirm', 1, 'echo "🚀 Uploading to PyPI..."').
sumd_workflow_step('publish-confirm', 2, '.venv/bin/twine upload dist/*').
sumd_workflow('publish-test', 'manual').
sumd_workflow_step('publish-test', 1, 'echo "📦 Publishing to TestPyPI..."').
sumd_workflow_step('publish-test', 2, 'command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build)').
sumd_workflow_step('publish-test', 3, 'rm -rf dist/ build/ *.egg-info/').
sumd_workflow_step('publish-test', 4, '.venv/bin/python -m build').
sumd_workflow_step('publish-test', 5, '.venv/bin/twine upload --repository testpypi dist/*').
sumd_workflow('version', 'manual').
sumd_workflow_step('version', 1, 'echo "📦 Version information..."').
sumd_workflow_step('version', 2, 'cat VERSION').
sumd_workflow_step('version', 3, '.venv/bin/python -c "from importlib.metadata import version').
sumd_workflow('deps:update', 'manual').
sumd_workflow('quality', 'manual').
sumd_workflow_step('quality', 1, 'pyqual run').
sumd_workflow('quality:fix', 'manual').
sumd_quality_workflow('quality:fix', 'fix').
sumd_workflow_step('quality:fix', 1, 'pyqual run --fix').
sumd_workflow('quality:report', 'manual').
sumd_quality_workflow('quality:report', 'report').
sumd_workflow_step('quality:report', 1, 'pyqual report').
sumd_workflow('fmt', 'manual').
sumd_workflow_step('fmt', 1, 'ruff format .').
sumd_workflow('build', 'manual').
sumd_workflow_step('build', 1, 'python -m build').
sumd_workflow('oql:run', 'manual').
sumd_workflow('oql:shell', 'manual').
sumd_workflow_step('oql:shell', 1, 'testql shell').
sumd_workflow('doql:adopt', 'manual').
sumd_workflow('doql:validate', 'manual').
sumd_workflow('doql:doctor', 'manual').
sumd_workflow('doql:build', 'manual').
sumd_workflow('docker:build', 'manual').
sumd_workflow_step('docker:build', 1, 'docker-compose build').
sumd_workflow('docker:up', 'manual').
sumd_workflow_step('docker:up', 1, 'docker-compose up -d').
sumd_workflow('docker:down', 'manual').
sumd_workflow_step('docker:down', 1, 'docker-compose down').
sumd_workflow('help', 'manual').
sumd_workflow_step('help', 1, 'task --list').
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

*525 nodes · 500 edges · 109 modules · CC̄=3.7*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `print` *(in examples.browser-inspection.run)* | 0 | 48 | 0 | **48** |
| `_render_toon` *(in testql.results.serializers)* | 6 | 1 | 46 | **47** |
| `_render_plan` *(in testql.adapters.testtoon_adapter)* | 9 | 4 | 31 | **35** |
| `parse_testtoon` *(in TODO.testtoon_parser)* | 14 ⚠ | 1 | 31 | **32** |
| `write_inspection_artifacts` *(in testql.results.artifacts)* | 1 | 3 | 28 | **31** |
| `heal_scenario` *(in testql.commands.heal_scenario_cmd)* | 8 | 0 | 30 | **30** |
| `_cmd_assert_json` *(in testql.interpreter._assertions.AssertionsMixin)* | 13 ⚠ | 0 | 30 | **30** |
| `_cmd_validate` *(in testql.interpreter._validation.ValidationMixin)* | 10 ⚠ | 0 | 30 | **30** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/oqlos/testql
# generated in 0.27s
# nodes: 525 | edges: 500 | modules: 109
# CC̄=3.7

HUBS[20]:
  examples.browser-inspection.run.print
    CC=0  in:48  out:0  total:48
  testql.results.serializers._render_toon
    CC=6  in:1  out:46  total:47
  testql.adapters.testtoon_adapter._render_plan
    CC=9  in:4  out:31  total:35
  TODO.testtoon_parser.parse_testtoon
    CC=14  in:1  out:31  total:32
  testql.results.artifacts.write_inspection_artifacts
    CC=1  in:3  out:28  total:31
  testql.commands.heal_scenario_cmd.heal_scenario
    CC=8  in:0  out:30  total:30
  testql.interpreter._assertions.AssertionsMixin._cmd_assert_json
    CC=13  in:0  out:30  total:30
  testql.interpreter._validation.ValidationMixin._cmd_validate
    CC=10  in:0  out:30  total:30
  testql.adapters.scenario_yaml._render_step
    CC=10  in:2  out:26  total:28
  testql._base_fallback.VariableStore.set
    CC=1  in:27  out:0  total:27
  testql.commands.watchdog_cmd._update_metrics
    CC=11  in:2  out:23  total:25
  testql.commands.generate_cmd._print_routes_section
    CC=10  in:1  out:23  total:24
  testql.commands.generate_topology_cmd.generate_topology
    CC=5  in:0  out:24  total:24
  testql.commands.inspect_cmd.inspect
    CC=6  in:0  out:24  total:24
  testql.commands.encoder_routes._run_oql_lines
    CC=6  in:1  out:22  total:23
  testql.adapters.base.read_source
    CC=5  in:14  out:9  total:23
  testql.commands.echo.parsers.doql._parse_workflows
    CC=7  in:1  out:22  total:23
  testql.adapters.scenario_yaml._gui_step
    CC=9  in:0  out:23  total:23
  testql.report_generator.generate_report
    CC=3  in:2  out:20  total:22
  testql.runner.parse_line
    CC=9  in:2  out:20  total:22

MODULES:
  TODO.testtoon_parser  [3 funcs]
    parse_testtoon  CC=14  out:31
    print_parsed  CC=8  out:12
    validate  CC=2  out:2
  examples.artifact-bundle.generate_bundle  [1 funcs]
    main  CC=2  out:10
  examples.browser-inspection.run  [1 funcs]
    print  CC=0  out:0
  testql._base_fallback  [4 funcs]
    emit  CC=2  out:2
    all  CC=1  out:1
    has  CC=1  out:0
    set  CC=1  out:0
  testql.adapters.base  [1 funcs]
    read_source  CC=5  out:9
  testql.adapters.graphql.schema_introspection  [1 funcs]
    parse_schema  CC=4  out:6
  testql.adapters.nl.entity_extractor  [5 funcs]
    all_backticked  CC=2  out:2
    first_backtick  CC=2  out:2
    first_path  CC=6  out:6
    first_quoted  CC=3  out:4
    first_selector  CC=7  out:7
  testql.adapters.nl.grammar  [1 funcs]
    normalize  CC=1  out:3
  testql.adapters.nl.intent_recognizer  [3 funcs]
    _intent_table  CC=5  out:8
    recognize_intent  CC=4  out:11
    recognize_operator  CC=6  out:8
  testql.adapters.nl.llm_fallback  [1 funcs]
    get_resolver  CC=1  out:0
  testql.adapters.nl.nl_adapter  [12 funcs]
    _api_status_part  CC=2  out:3
    _assert_expected  CC=4  out:3
    _assert_field  CC=7  out:7
    _build_api  CC=6  out:8
    _build_assert  CC=2  out:5
    _build_encoder  CC=2  out:5
    _build_step  CC=3  out:4
    _build_unresolved  CC=2  out:4
    _render_assert  CC=4  out:0
    _render_by_kind  CC=3  out:2
  testql.adapters.nlp2dsl.llm_provider  [2 funcs]
    live_llm_enabled  CC=2  out:3
    resolve_llm_provider  CC=4  out:6
  testql.adapters.nlp2dsl.mock_llm  [1 funcs]
    load_mock_replies  CC=5  out:9
  testql.adapters.nlp2dsl.nlp2dsl_adapter  [1 funcs]
    detect  CC=7  out:10
  testql.adapters.proto.descriptor_loader  [1 funcs]
    parse_proto  CC=4  out:9
  testql.adapters.registry  [1 funcs]
    detect  CC=9  out:8
  testql.adapters.scenario_yaml  [33 funcs]
    detect  CC=5  out:9
    parse  CC=3  out:5
    render  CC=9  out:7
    _add_common_step_attributes  CC=7  out:1
    _api_step  CC=9  out:19
    _as_dict  CC=2  out:1
    _as_list  CC=3  out:1
    _assertion_from_field  CC=3  out:11
    _assertions_from_expect  CC=9  out:13
    _captures_from  CC=2  out:5
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
  testql.adapters.sql.query_parser  [4 funcs]
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
  testql.adapters.testtoon_adapter  [20 funcs]
    detect  CC=9  out:12
    parse  CC=1  out:3
    render  CC=1  out:1
    _assert_json_section_apply  CC=12  out:19
    _capture_section_apply  CC=8  out:12
    _config_to_dict  CC=3  out:3
    _context_section_to_config  CC=1  out:1
    _derive_columns  CC=4  out:4
    _format_extra_value  CC=6  out:4
    _group_generic_steps  CC=9  out:4
  testql.cli  [5 funcs]
    _fetch_latest_version  CC=2  out:3
    check_and_upgrade  CC=4  out:3
    cli  CC=1  out:3
    main  CC=1  out:2
    mcp_serve  CC=2  out:4
  testql.commands.auto_cmd  [4 funcs]
    _render_console_report  CC=4  out:13
    _render_markdown_report  CC=4  out:8
    _run_generation_phase  CC=2  out:10
    _run_report_phase  CC=3  out:11
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
    _execute_oql_line  CC=10  out:13
  testql.commands.endpoints_cmd  [5 funcs]
    _format_endpoints  CC=3  out:3
    _format_endpoints_csv  CC=5  out:7
    _format_endpoints_json  CC=3  out:3
    _format_endpoints_table  CC=5  out:8
    endpoints  CC=9  out:20
  testql.commands.generate_cmd  [2 funcs]
    _count_routes_by  CC=2  out:3
    _print_routes_section  CC=10  out:23
  testql.commands.generate_ir_cmd  [2 funcs]
    _split_from_arg  CC=2  out:6
    generate_ir  CC=2  out:12
  testql.commands.generate_topology_cmd  [2 funcs]
    _pick_trace  CC=5  out:1
    generate_topology  CC=5  out:24
  testql.commands.heal_scenario_cmd  [5 funcs]
    _collect_selectors  CC=3  out:6
    _heal_with_browser  CC=7  out:12
    _heal_with_elements  CC=6  out:5
    _selector_resolves  CC=2  out:2
    heal_scenario  CC=8  out:30
  testql.commands.inspect_cmd  [1 funcs]
    inspect  CC=6  out:24
  testql.commands.misc_cmds  [4 funcs]
    _create_templates  CC=4  out:4
    echo  CC=4  out:20
    init  CC=4  out:20
    report  CC=4  out:22
  testql.commands.run_cmd  [4 funcs]
    _emit_multi_json  CC=3  out:8
    _emit_single_json  CC=1  out:4
    _maybe_planfile  CC=9  out:5
    run  CC=10  out:21
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
  testql.commands.watchdog_cmd  [5 funcs]
    _extract_failures  CC=10  out:15
    _post_failures  CC=4  out:5
    _process_one_scenario  CC=3  out:8
    _run_scenario  CC=3  out:5
    _update_metrics  CC=11  out:23
  testql.discovery.manifest  [7 funcs]
    from_probe_results  CC=8  out:6
    _dedupe_dicts  CC=4  out:8
    _dependencies_from_metadata  CC=4  out:7
    _interfaces_from_metadata  CC=5  out:7
    _merge_metadata  CC=10  out:7
    _score_confidence  CC=5  out:1
    _unique  CC=3  out:3
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
  testql.doql_parser  [1 funcs]
    parse_doql_file  CC=1  out:2
  testql.generators.api_generator  [1 funcs]
    _deduplicate_rest_routes  CC=4  out:3
  testql.generators.base  [1 funcs]
    _should_exclude_path  CC=1  out:3
  testql.generators.page_analyzer  [29 funcs]
    _add_assert_visible_step  CC=1  out:4
    _add_body_assertion  CC=1  out:2
    _add_click_step  CC=1  out:3
    _add_input_step  CC=1  out:4
    _add_navigate_step  CC=2  out:2
    _build_element_haystack  CC=4  out:6
    _create_base_plan  CC=3  out:2
    _css_escape  CC=1  out:2
    _find_exact_match  CC=6  out:4
    _find_fuzzy_match  CC=9  out:4
  testql.generators.pipeline  [6 funcs]
    _resolve_source  CC=3  out:4
    _resolve_target  CC=3  out:4
    run  CC=5  out:13
    sorted_sources  CC=1  out:1
    sorted_targets  CC=1  out:1
    write  CC=5  out:9
  testql.generators.sources  [2 funcs]
    available_sources  CC=1  out:4
    get_source  CC=5  out:5
  testql.generators.sources.config_source  [13 funcs]
    load  CC=6  out:15
    _auto_detect_parser  CC=4  out:0
    _extract_phony_targets  CC=3  out:3
    _extract_target_commands  CC=13  out:9
    _filter_commands  CC=14  out:17
    _load_file  CC=4  out:7
    _load_includes  CC=6  out:8
    _parse_buf_yaml  CC=1  out:0
    _parse_docker_compose  CC=4  out:4
    _parse_makefile  CC=4  out:8
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
  testql.generators.sources.page_source  [5 funcs]
    _fetch_via_playwright  CC=4  out:8
    load  CC=1  out:5
    _origin  CC=3  out:1
    _path_of  CC=2  out:1
    extract_elements_from_page  CC=1  out:1
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
  testql.integrations.planfile_hook  [1 funcs]
    create_test_failure_ticket  CC=6  out:7
  testql.interpreter._api_runner  [8 funcs]
    _cmd_capture  CC=3  out:13
    _handle_length_virtual  CC=2  out:2
    _handle_mixed_notation  CC=3  out:6
    _navigate_bracket_notation  CC=3  out:3
    _navigate_dot_notation  CC=3  out:2
    _navigate_dot_part  CC=4  out:4
    _navigate_json_path  CC=4  out:4
    _navigate_step  CC=4  out:4
  testql.interpreter._assertions  [1 funcs]
    _cmd_assert_json  CC=13  out:30
  testql.interpreter._flow  [1 funcs]
    _cmd_include  CC=7  out:17
  testql.interpreter._parser  [1 funcs]
    parse_oql  CC=5  out:10
  testql.interpreter._testtoon_parser  [7 funcs]
    _append_api_asserts  CC=9  out:11
    _expand_api  CC=4  out:9
    _expand_shell  CC=6  out:12
    _quote_shell_command  CC=1  out:2
    _shell_expected_exit  CC=7  out:8
    _shell_timeout_ms  CC=5  out:9
    testtoon_to_oql  CC=2  out:4
  testql.interpreter._validation  [2 funcs]
    _cmd_validate  CC=10  out:30
    _resolve_target  CC=11  out:16
  testql.interpreter.converter.core  [3 funcs]
    convert_directory  CC=4  out:7
    convert_file  CC=1  out:3
    convert_oql_to_testtoon  CC=5  out:10
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
  testql.interpreter.dom_scan_formatters  [1 funcs]
    to_text_audit  CC=4  out:2
  testql.interpreter.dom_scan_mixin  [1 funcs]
    _handle_audit_report  CC=4  out:11
  testql.interpreter.dom_scanner  [4 funcs]
    assert_aria  CC=5  out:8
    scan_aria  CC=4  out:9
    _aom_node_to_element  CC=2  out:13
    _flatten_aom  CC=2  out:3
  testql.interpreter.interpreter  [3 funcs]
    __init__  CC=3  out:6
    execute  CC=4  out:16
    parse  CC=2  out:3
  testql.interpreter.testtoon_parser  [21 funcs]
    _add_bare_commands_section  CC=3  out:4
    _add_row_to_section  CC=5  out:5
    _detect_separator  CC=2  out:1
    _find_commands_insert_position  CC=3  out:1
    _is_bare_command  CC=2  out:1
    _is_comment  CC=1  out:1
    _is_meta_line  CC=1  out:1
    _make_data_row  CC=2  out:6
    _make_mapping_row  CC=4  out:9
    _make_mapping_section  CC=1  out:2
  testql.ir_runner.engine  [1 funcs]
    run_plan  CC=1  out:2
  testql.mcp.server  [1 funcs]
    run_server  CC=1  out:2
  testql.openapi_generator  [5 funcs]
    _load_spec  CC=2  out:3
    _extract_parameters  CC=1  out:3
    _infer_tags  CC=7  out:9
    _extract_ep_params  CC=7  out:8
    _extract_path_params  CC=4  out:4
  testql.report_generator  [1 funcs]
    generate_report  CC=3  out:20
  testql.results.analyzer  [38 funcs]
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
  testql.results.artifacts  [3 funcs]
    _render_summary_md  CC=10  out:17
    _write_group  CC=2  out:3
    write_inspection_artifacts  CC=1  out:28
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
  testql.toon_parser  [1 funcs]
    parse_toon_file  CC=1  out:2
  testql.topology.builder  [1 funcs]
    build_topology  CC=1  out:2
  testql.topology.serializers  [1 funcs]
    render_topology  CC=4  out:5

EDGES:
  examples.artifact-bundle.generate_bundle.main → examples.browser-inspection.run.print
  examples.artifact-bundle.generate_bundle.main → testql.results.analyzer.inspect_source
  examples.artifact-bundle.generate_bundle.main → testql.results.artifacts.write_inspection_artifacts
  TODO.testtoon_parser.print_parsed → examples.browser-inspection.run.print
  TODO.testtoon_parser.print_parsed → TODO.testtoon_parser.validate
  testql.cli.mcp_serve → testql.mcp.server.run_server
  testql.cli.check_and_upgrade → testql.cli._fetch_latest_version
  testql.cli.check_and_upgrade → examples.browser-inspection.run.print
  testql.cli.main → testql.cli.check_and_upgrade
  testql.cli.main → testql.cli.cli
  testql.runner.parse_line → examples.browser-inspection.run.print
  testql.runner.parse_script → testql.runner.parse_line
  testql.runner.DslCliExecutor._dispatch → examples.browser-inspection.run.print
  testql.runner.DslCliExecutor.cmd_log → examples.browser-inspection.run.print
  testql.runner.DslCliExecutor.cmd_print → examples.browser-inspection.run.print
  testql.runner.DslCliExecutor.run_script → testql.runner.parse_script
  testql.runner.DslCliExecutor.run_script → examples.browser-inspection.run.print
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
  testql.commands.self_test_cmd.self_test → testql.commands.self_test_cmd._print_human
  testql.commands.discover_cmd.discover → testql.discovery.registry.discover_path
  testql.commands.generate_cmd._print_routes_section → testql.commands.generate_cmd._count_routes_by
  testql.commands.topology_cmd.topology → testql.topology.builder.build_topology
  testql.commands.topology_cmd.topology → testql.topology.serializers.render_topology
  testql.commands.misc_cmds.init → testql.commands.misc_cmds._create_templates
  testql.commands.misc_cmds.report → testql.report_generator.generate_report
  testql.commands.misc_cmds.echo → testql.commands.echo_helpers.render_echo
  testql.commands.misc_cmds.echo → testql.commands.echo_helpers.collect_toon_data
  testql.commands.run_ir_cmd.run_ir → testql.ir_runner.engine.run_plan
  testql.commands.run_ir_cmd.run_ir → testql.commands.run_ir_cmd._emit_json
  testql.commands.heal_scenario_cmd._collect_selectors → testql._base_fallback.VariableStore.set
  testql.commands.heal_scenario_cmd.heal_scenario → testql.commands.heal_scenario_cmd._collect_selectors
  testql.commands.heal_scenario_cmd._heal_with_elements → testql.generators.page_analyzer.pick_selector
  testql.commands.heal_scenario_cmd._heal_with_elements → testql.generators.page_analyzer.find_replacement
  testql.commands.heal_scenario_cmd._heal_with_elements → testql.adapters.testtoon_adapter._toon_safe_selector
  testql.commands.heal_scenario_cmd._heal_with_browser → testql.generators.sources.page_source.extract_elements_from_page
```

## API Stubs

*testql API v1.0.0 — auto-generated stubs from `openapi.yaml`.*

```python markpact:openapi path=openapi.yaml
# fastapi
def oql_read_file() -> Response:  # Read a TestQL file content (.testql.toon.yaml / .oql / .tql).
    "GET /oql/file"
def oql_list_files() -> Response:  # List all .testql.toon.yaml files in the project (with .oql/.tql fallback).
    "GET /oql/files"
def oql_read_log() -> Response:  # Read a specific log file.
    "GET /oql/log"
def oql_list_logs() -> Response:  # List available log files.
    "GET /oql/logs"
def oql_run_file() -> Response:  # Run an entire OQL file with validation. Returns structured results + saves log.
    "POST /oql/run-file"
def oql_run_line() -> Response:  # Execute a single OQL command line via the encoder bridge.
    "POST /oql/run-line"
def oql_list_tables() -> Response:  # Extract table names from an OQL file.
    "GET /oql/tables"

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
- `GET /oql/files` → `200`
- `GET /oql/file` → `200`
- `GET /oql/tables` → `200`
- assert `status < 500`
- assert `response_time < 2000`
- detectors: FastAPIDetector, OpenAPIDetector

**`health-check.testql.toon.yaml — generic health check scenario`**
- `GET /health` → `200`
- `GET /api/v3/version` → `200`

**`run-all-views.testql.toon.yaml — Master runner for all per-view OQL tests`**

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

### Cli (2)

**`Extended CLI Smoke Tests`**
- assert `exit_code == 0`

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

**`test-encoder.testql.toon.yaml — Encoder navigation tests via OQL`**

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
- assert `exit_code == 0`

### Interaction (3)

**`Generate Test Reports Scenario`**

**`Session Recording Example`**

**`DSL Example: Complete Device Test Flow`**

### Web (2)

**`Internal Asset Availability (excluding known-external 403s)`**
- `GET /favicon.ico` → `200`
- `GET /robots.txt` → `200`
- assert `status < 500`
- assert `response_time < 3000`

**`Sitemap Uniqueness and Asset Availability`**
- `GET /sitemap.xml` → `200`
- `GET /pl/` → `200`
- `GET /de/` → `200`
- assert `status < 500`
- assert `response_time < 5000`

## Intent

TestQL — Multi-DSL Test Platform: TestTOON / NL / SQL / Proto / GraphQL adapters with Unified IR, generator engine, and meta-testing
