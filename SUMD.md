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
- **generated_from**: pyproject.toml, Taskfile.yml, testql(74), openapi(7 ep), app.doql.less, app.doql.css, pyqual.yaml, goal.yaml, .env.example, src(11 mod)

## Intent

TestQL with endpoint detection, OpenAPI generation, and AI echo

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`, `app.doql.css`)

```less
app {
  name: testql;
  version: 0.2.1;
}
```

### DOQL Interfaces

- `interface[type="cli"]` page=`testql` — 

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

| Method | Path | OperationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/iql/file` | `iql_read_file` | Read a TestQL file content (.testql.toon.yaml / .iql / .tql). |
| `GET` | `/iql/files` | `iql_list_files` | List all .testql.toon.yaml files in the project (with .iql/.tql fallback). |
| `GET` | `/iql/log` | `iql_read_log` | Read a specific log file. |
| `GET` | `/iql/logs` | `iql_list_logs` | List available log files. |
| `POST` | `/iql/run-file` | `iql_run_file` | Run an entire IQL file with validation. Returns structured results + saves log. |
| `POST` | `/iql/run-line` | `iql_run_line` | Execute a single IQL command line via the encoder bridge. |
| `GET` | `/iql/tables` | `iql_list_tables` | Extract table names from an IQL file. |

**Schemas**: `Error`, `HealthCheck`

### testql Scenarios

#### `api-crud-template.testql.toon.yaml`

- **name**: api-crud-template.testql.toon.yaml — generic CRUD test template
- **type**: `api`
- **entity**: `items`
- **base_path**: `/api/v3/data/items`

#### `api-health.testql.toon.yaml`

- **name**: api-health.testql.toon.yaml — basic health check for c2004
- **type**: `api`
- **endpoints**:
  - `GET /health` → `200`

#### `api-smoke.testql.toon.yaml`

- **name**: api-smoke.testql.toon.yaml — smoke test for all main c2004 API endpoints
- **type**: `api`
- **endpoints**:
  - `GET /health` → `200`
  - `GET /api/v3/version` → `200`
  - `GET /api/v3/data/devices` → `200`
  - `GET /api/v3/data/users` → `200`
  - `GET /api/v3/data/scenarios` → `200`

#### `auth-login.testql.toon.yaml`

- **name**: auth-login.testql.toon.yaml — generic authentication login test template
- **type**: `api`
- **api_url**: `$TARGET_URL`
- **endpoints**:
  - `POST /api/v3/auth/login"` → `200`

#### `backend-diagnostic.testql.toon.yaml`

- **name**: Backend Diagnostic Tests
- **type**: `api`
- **endpoints**:
  - `GET /api/v3/health` → `200`
  - `GET /api/v3/template-json` → `200`
  - `GET /api/v3/template-json/default` → `200`
  - `GET /api/v3/data/report_templates` → `200`
  - `GET /api/v3/devices` → `200`
  - `GET /api/v3/customers` → `200`
  - `GET /api/v3/dsl/objects` → `200`
  - `GET /api/v3/dsl/functions` → `200`
  - `GET /api/v3/dsl/params` → `200`
  - `GET /api/v3/dsl/units` → `200`
  - `GET /api/v3/config/system` → `200`
  - `GET /api/v3/schema/devices` → `200`
  - `GET /api/v3/schema/customers` → `200`
  - `GET /api/v3/schema/protocols` → `200`
  - `GET /api/v3/data/protocols` → `200`
  - `GET /api/v3/auth/session` → `200`

#### `connect-config-feature-flags.testql.toon.yaml`

- **name**: connect-config-feature-flags.testql.toon.yaml — Test: Konfiguracja > Feature Flags
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-config-feature-flags,  500`

#### `connect-config-labels.testql.toon.yaml`

- **name**: connect-config-labels.testql.toon.yaml — Test: Konfiguracja > Etykiety
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-config-labels,  500`

#### `connect-config-settings.testql.toon.yaml`

- **name**: connect-config-settings.testql.toon.yaml — Test: Konfiguracja > Ustawienia
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-config-settings,  500`

#### `connect-config-tables.testql.toon.yaml`

- **name**: connect-config-tables.testql.toon.yaml — Test: Konfiguracja > Tabele
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-config-tables,  500`

#### `connect-config-theme.testql.toon.yaml`

- **name**: connect-config-theme.testql.toon.yaml — Test: Konfiguracja > Motyw
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-config-theme,  500`

#### `connect-config-users.testql.toon.yaml`

- **name**: connect-config-users.testql.toon.yaml — Test: Konfiguracja > Użytkownicy
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-config-users,  500`

#### `connect-id-barcode.testql.toon.yaml`

- **name**: connect-id-barcode.testql.toon.yaml — Test: Identyfikacja > Barcode
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-id/barcode,  500`

#### `connect-id-list.testql.toon.yaml`

- **name**: connect-id-list.testql.toon.yaml — Test: Identyfikacja > Lista użytkowników
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-id/list,  500`

#### `connect-id-manual.testql.toon.yaml`

- **name**: connect-id-manual.testql.toon.yaml — Test: Identyfikacja > Logowanie ręczne
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-id/manual,  500`

#### `connect-id-qr.testql.toon.yaml`

- **name**: connect-id-qr.testql.toon.yaml — Test: Identyfikacja > QR Code
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-id/qr,  500`

#### `connect-id-rfid.testql.toon.yaml`

- **name**: connect-id-rfid.testql.toon.yaml — Test: Identyfikacja > RFID
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-id/rfid,  800`

#### `connect-manager-activities.testql.toon.yaml`

- **name**: connect-manager-activities.testql.toon.yaml — Test: Manager > Czynności
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-manager/activities,  500`

#### `connect-manager-intervals.testql.toon.yaml`

- **name**: connect-manager-intervals.testql.toon.yaml — Test: Manager > Interwały
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-manager/intervals,  500`

#### `connect-manager-library.testql.toon.yaml`

- **name**: connect-manager-library.testql.toon.yaml — Test: Manager > Biblioteka
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-manager/library,  500`

#### `connect-manager-scenarios.testql.toon.yaml`

- **name**: connect-manager-scenarios.testql.toon.yaml — Test: Manager > Scenariusze
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-manager/scenarios,  800`

#### `connect-manager-test-types.testql.toon.yaml`

- **name**: connect-manager-test-types.testql.toon.yaml — Test: Manager > Rodzaj Testu
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-manager/test-types,  500`

#### `connect-reports-chart.testql.toon.yaml`

- **name**: connect-reports-chart.testql.toon.yaml — Test: Raporty > Wykres
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-reports/chart?filter=all,  800`

#### `connect-reports-custom.testql.toon.yaml`

- **name**: connect-reports-custom.testql.toon.yaml — Test: Raporty > Niestandardowy
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-reports/custom?filter=all,  800`

#### `connect-reports-filter.testql.toon.yaml`

- **name**: connect-reports-filter.testql.toon.yaml — Test: Raporty > Filtruj
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-reports/filter?filter=all,  500`

#### `connect-reports-month.testql.toon.yaml`

- **name**: connect-reports-month.testql.toon.yaml — Test: Raporty > Miesiąc
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-reports/month?filter=all,  800`

#### `connect-reports-quarter.testql.toon.yaml`

- **name**: connect-reports-quarter.testql.toon.yaml — Test: Raporty > Kwartał
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-reports/quarter?filter=all,  800`

#### `connect-reports-week.testql.toon.yaml`

- **name**: connect-reports-week.testql.toon.yaml — Test: Raporty > Tydzień
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-reports/week?filter=all,  800`

#### `connect-reports-year.testql.toon.yaml`

- **name**: connect-reports-year.testql.toon.yaml — Test: Raporty > Rok
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-reports/year?filter=all,  1500`

#### `connect-test-devices-search.testql.toon.yaml`

- **name**: connect-test-devices-search.testql.toon.yaml — Test: Testowanie > Wyszukiwanie urządzeń
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-test/device-devices-search,  500`

#### `connect-test-full-test.testql.toon.yaml`

- **name**: connect-test-full-test.testql.toon.yaml — Test: Testowanie > Test automatyczny
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-test/full-test,  500`

#### `connect-test-protocols.testql.toon.yaml`

- **name**: connect-test-protocols.testql.toon.yaml — Test: Testowanie > Raporty (protokoły)
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-test/protocols,  500`

#### `connect-test-scenario-view.testql.toon.yaml`

- **name**: connect-test-scenario-view.testql.toon.yaml — Test: Testowanie > Scenariusz/Interwały
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-test/scenario-view,  500`

#### `connect-test-testing-barcode.testql.toon.yaml`

- **name**: connect-test-testing-barcode.testql.toon.yaml — Test: Testowanie > Barcode
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-test/testing-barcode,  500`

#### `connect-test-testing-qr.testql.toon.yaml`

- **name**: connect-test-testing-qr.testql.toon.yaml — Test: Testowanie > QR
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-test/testing-qr,  500`

#### `connect-test-testing-rfid.testql.toon.yaml`

- **name**: connect-test-testing-rfid.testql.toon.yaml — Test: Testowanie > RFID
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-test/testing-rfid,  500`

#### `connect-test-testing-search.testql.toon.yaml`

- **name**: connect-test-testing-search.testql.toon.yaml — Test: Testowanie > Wyszukiwanie testów
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-test/testing-search,  500`

#### `connect-workshop-dispositions-search.testql.toon.yaml`

- **name**: connect-workshop-dispositions-search.testql.toon.yaml — Test: Warsztat > Dyspozycje
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-workshop/dispositions-search,  500`

#### `connect-workshop-requests-search.testql.toon.yaml`

- **name**: connect-workshop-requests-search.testql.toon.yaml — Test: Warsztat > Zgłoszenia
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-workshop/requests-search,  500`

#### `connect-workshop-services-search.testql.toon.yaml`

- **name**: connect-workshop-services-search.testql.toon.yaml — Test: Warsztat > Serwisy
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-workshop/services-search,  500`

#### `connect-workshop-transport-search.testql.toon.yaml`

- **name**: connect-workshop-transport-search.testql.toon.yaml — Test: Warsztat > Transport
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **navigate**: `/connect-workshop/transport-search,  500`

#### `connect-workshop-transport.testql.toon.yaml`

- **name**: connect-workshop-transport.testql.toon.yaml — GUI test for workshop transport view
- **type**: `gui`
- **navigate**: `/connect-workshop-transport,  500`

#### `create-todays-reports.testql.toon.yaml`

- **name**: Create Today's Reports
- **type**: `gui`
- **navigate**: `/connect-test/testing,  300`, `/connect-reports,  300`

#### `device-identification.testql.toon.yaml`

- **name**: Device Identification Example
- **type**: `gui`
- **navigate**: `/connect-id/device-rfid,  300`, `/connect-test/testing,  300`

#### `encoder-navigation.testql.toon.yaml`

- **name**: encoder-navigation.testql.toon.yaml — encoder hardware navigation test
- **type**: `gui`

#### `encoder-workshop.testql.toon.yaml`

- **name**: encoder-workshop.testql.toon.yaml — encoder navigation in workshop context
- **type**: `gui`
- **navigate**: `/connect-workshop,  500`

#### `full-diagnostic.testql.toon.yaml`

- **name**: Full System Diagnostic - API + Routes + DSL
- **type**: `gui`
- **endpoints**:
  - `GET /api/v3/health` → `200`
  - `GET /api/v3/auth/session` → `200`
  - `GET /api/v3/config/system` → `200`
  - `GET /api/v3/data/devices` → `200`
  - `GET /api/v3/data/customers` → `200`
  - `GET /api/v3/data/protocols` → `200`
  - `GET /api/v3/data/report_templates` → `200`
  - `GET /api/v3/data/test_scenarios` → `200`
  - `GET /api/v3/data/workshops` → `200`
  - `GET /api/v3/schema/devices` → `200`
  - `GET /api/v3/schema/customers` → `200`
  - `GET /api/v3/schema/protocols` → `200`
  - `GET /api/v3/dsl/objects` → `200`
  - `GET /api/v3/dsl/functions` → `200`
  - `GET /api/v3/dsl/params` → `200`
  - `GET /api/v3/dsl/units` → `200`
  - `GET /api/v3/template-json` → `200`
  - `GET /api/v3/template-json/default` → `200`
  - `GET /api/v3/customers` → `200`
  - `GET /api/v3/devices` → `200`
  - `GET /api/v1/data/devices` → `200`
  - `GET /api/v1/data/customers` → `200`
  - `GET /api/v1/schema/devices` → `200`: ── Nawigacja UI ──────────────────────────────────────
- **navigate**: `/connect-test,  100`, `/connect-id,  300`, `/connect-test,  300`, `/connect-test-device,  300`, `/connect-test-protocol,  300`, `/connect-test-full,  300`, `/connect-data,  300`, `/connect-workshop,  300`, `/connect-config,  300`, `/connect-reports,  300`, `/connect-manager,  300`, `/connect-scenario,  300`, `/connect-template2,  300`, `/connect-menu-editor,  300`, `/connect-router,  300`

#### `generate-test-reports.testql.toon.yaml`

- **name**: Generate Test Reports Scenario
- **type**: `interaction`
- **navigate**: `/connect-id/device-rfid,  300`, `/connect-test/testing,  300`, `/connect-id/device-rfid,  300`, `/connect-test/testing,  300`, `/connect-id/device-rfid,  300`, `/connect-test/testing,  300`, `/connect-reports,  500`

#### `generated-api-integration.testql.toon.yaml`

- **name**: API Integration Tests
- **type**: `api`
- **base_url**: `http://localhost:8101`
- **timeout_ms**: `30000`
- **retry_count**: `3`
- **endpoints**:
  - `GET /health` → `200`
  - `GET /api/v1/status` → `200`
  - `POST /api/v1/test` → `201`
  - `GET /api/v1/docs` → `200`
- **asserts**:
  - `status == ok`
  - `response_time < 1000`

#### `generated-api-smoke.testql.toon.yaml`

- **name**: Auto-generated API Smoke Tests
- **type**: `api`
- **detectors**: FastAPIDetector
- **base_url**: `http://localhost:8101`
- **timeout_ms**: `10000`
- **retry_count**: `3`
- **endpoints**:
  - `GET /iql/files` → `200` — `iql_list_files`: List all .testql.toon.yaml files in the project (w
  - `GET /iql/file` → `200` — `iql_read_file`: Read a TestQL file content (.testql.toon.yaml / .i
  - `GET /iql/tables` → `200` — `iql_list_tables`: Extract table names from an IQL file.
  - `POST /iql/run-line` → `201` — `iql_run_line`: Execute a single IQL command line via the encoder
  - `POST /iql/run-file` → `201` — `iql_run_file`: Run an entire IQL file with validation. Returns st
  - `GET /iql/logs` → `200` — `iql_list_logs`: List available log files.
  - `GET /iql/log` → `200` — `iql_read_log`: Read a specific log file.
- **asserts**:
  - `status < 500`
  - `response_time < 2000`

#### `generated-cli-tests.testql.toon.yaml`

- **name**: CLI Command Tests
- **type**: `cli`
- **cli_command**: `python -mtestql`
- **timeout_ms**: `10000`

#### `generated-from-pytests.testql.toon.yaml`

- **name**: Auto-generated from Python Tests
- **type**: `integration`

#### `health-check.testql.toon.yaml`

- **name**: health-check.testql.toon.yaml — generic health check scenario
- **type**: `api`
- **api_url**: `$TARGET_URL`
- **endpoints**:
  - `GET /health` → `200`
  - `GET /api/v3/version` → `200`

#### `quick-navigation.testql.toon.yaml`

- **name**: Quick Navigation Example
- **type**: `gui`
- **navigate**: `/,  300`, `/connect-id,  300`, `/connect-test,  300`, `/connect-data,  300`, `/connect-reports,  300`

#### `recorded-test-session.testql.toon.yaml`

- **name**: DSL Session Recording
- **type**: `gui`
- **navigate**: `/connect-test-device,  500`, `/connect-test-protocol?protocol=pro-example123&step=1,  500`, `/connect-test/reports?protocol=pro-example123,  300`

#### `reproduce-view.testql.toon.yaml`

- **name**: Reproduce View - Connect Manager with Scenario Selection
- **type**: `gui`
- **navigate**: `/connect-manager,  300`

#### `run-all-views.testql.toon.yaml`

- **name**: run-all-views.testql.toon.yaml — Master runner for all per-view IQL tests
- **type**: `api`
- **encoder_url**: `http://localhost:8105`

#### `run-mask-test-protocol.testql.toon.yaml`

- **name**: =============================================================================
- **type**: `api`
- **endpoints**:
  - `GET /api/v3/scenarios/scn-drager-fps-7000-maska-nadcisnieniowa?include_content=true` → `200`
  - `POST /api/v3/protocols"` → `200`

#### `session-recording.testql.toon.yaml`

- **name**: Session Recording Example
- **type**: `interaction`
- **navigate**: `/connect-id/device-rfid,  300`, `/connect-test/testing,  300`

#### `test-api.testql.toon.yaml`

- **name**: Example DSL Script - API Testing
- **type**: `api`
- **endpoints**:
  - `GET /api/v3/data/devices?limit=5` → `200`
  - `GET /api/v3/data/customers?limit=5` → `200`
  - `GET /api/v3/data/intervals?limit=5` → `200`
  - `GET /api/v3/data/test_scenarios?limit=5` → `200`
  - `GET /api/v3/menu/configurations?limit=10` → `200`

#### `test-app-lifecycle.testql.toon.yaml`

- **name**: DSL Script - Application Lifecycle Test
- **type**: `api`
- **endpoints**:
  - `GET /api/v3/data/protocols?limit=3` → `200`
  - `GET /api/v3/data/test_scenarios?limit=3` → `200`

#### `test-device-flow.testql.toon.yaml`

- **name**: DSL Example: Complete Device Test Flow
- **type**: `interaction`
- **navigate**: `/connect-id/device-rfid,  300`, `/connect-test/testing,  300`, `/connect-test-protocol?protocol=pro-example-001&step=1,  300`, `/connect-test/reports?protocol=pro-example-001,  300`, `RECORD_STOP:`

#### `test-devices-crud.testql.toon.yaml`

- **name**: Example DSL Script - Devices CRUD Operations
- **type**: `api`
- **endpoints**:
  - `GET /api/v3/data/devices?limit=10` → `200`
  - `GET /api/v3/data/customers?limit=5` → `200`
  - `GET /api/v3/data/intervals?limit=10` → `200`
  - `GET /api/v3/data/scenario_goal_intervals?limit=10` → `200`

#### `test-dsl-objects.testql.toon.yaml`

- **name**: Example DSL Script - DSL Objects Test
- **type**: `api`
- **endpoints**:
  - `GET /api/v3/data/dsl_objects?limit=100` → `200`
  - `GET /api/v3/data/dsl_functions?limit=100` → `200`
  - `GET /api/v3/data/dsl_params?limit=100` → `200`
  - `GET /api/v3/data/dsl_units?limit=100` → `200`
  - `GET /api/v3/data/dsl_object_functions?limit=1000` → `200`
  - `GET /api/v3/data/dsl_param_units?limit=1000` → `200`

#### `test-encoder.testql.toon.yaml`

- **name**: test-encoder.testql.toon.yaml — Encoder navigation tests via IQL
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`

#### `test-gui-all.testql.toon.yaml`

- **name**: test-gui-all.testql.toon.yaml — Master GUI test suite — runs all module GUI tests
- **type**: `api`
- **encoder_url**: `http://localhost:8105`
- **api_url**: `http://localhost:8101`

#### `test-gui-connect-config.testql.toon.yaml`

- **name**: test-gui-connect-config.testql.toon.yaml — GUI tests for Connect Config module
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **api_url**: `http://localhost:8101`
- **endpoints**:
  - `GET /api/v3/config/settings` → `200`
  - `GET /api/v3/feature-flags` → `200`
- **navigate**: `/connect-config,  500`, `/connect-config/system,  300`, `/connect-config/devices,  300`, `/connect-config/security,  300`, `/connect-config/theme,  300`, `/connect-config/labels,  300`, `/connect-config/feature-flags,  300`, `/connect-config/tables,  300`, `/connect-config/sitemap,  300`, `/connect-config/module-registry,  300`

#### `test-gui-connect-id.testql.toon.yaml`

- **name**: test-gui-connect-id.testql.toon.yaml — GUI tests for Connect ID module
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **api_url**: `http://localhost:8101`
- **endpoints**:
  - `GET /api/v3/auth/users` → `200`
- **navigate**: `/connect-id,  500`, `/connect-id/rfid,  300`, `/connect-id/qr,  300`, `/connect-id/manual,  300`, `/connect-id/list,  300`, `/connect-id/barcode,  300`

#### `test-gui-connect-manager.testql.toon.yaml`

- **name**: test-gui-connect-manager.testql.toon.yaml — GUI tests for Connect Manager module
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **api_url**: `http://localhost:8101`
- **endpoints**:
  - `GET /api/v3/data/test_scenarios?limit=5` → `200`
  - `GET /api/v3/data/intervals?limit=5` → `200`
  - `GET /api/v3/activities?limit=5` → `200`
- **navigate**: `/connect-manager,  500`, `/connect-manager/scenario-editor,  300`, `/connect-manager/activities,  300`, `/connect-manager/test-types,  300`, `/connect-manager/intervals,  300`, `/connect-manager/library,  300`, `/connect-manager/variables,  300`

#### `test-gui-connect-reports.testql.toon.yaml`

- **name**: test-gui-connect-reports.testql.toon.yaml — GUI tests for Connect Reports module
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **api_url**: `http://localhost:8101`
- **endpoints**:
  - `GET /api/v3/data/protocols?limit=5` → `200`
- **navigate**: `/connect-reports,  500`, `/connect-reports/week,  300`, `/connect-reports/month,  300`, `/connect-reports/quarter,  300`, `/connect-reports/year,  300`, `/connect-reports/custom,  300`, `/connect-reports/filter,  300`, `/connect-reports/chart,  300`

#### `test-gui-connect-test.testql.toon.yaml`

- **name**: test-gui-connect-test.testql.toon.yaml — GUI tests for Connect Test module
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **api_url**: `http://localhost:8101`
- **endpoints**:
  - `GET /api/v3/data/devices?limit=5` → `200`
  - `GET /api/v3/data/test_scenarios?limit=5` → `200`
  - `GET /api/v3/data/protocols?limit=5` → `200`
- **navigate**: `/connect-test,  500`, `/connect-test/testing-rfid,  300`, `/connect-test/testing-qr,  300`, `/connect-test/testing-search,  300`, `/connect-test/testing-barcode,  300`, `/connect-test/devices-search,  300`, `/connect-test/scenario-view,  300`, `/connect-test/test-run,  300`, `/connect-test/protocols,  300`

#### `test-gui-connect-workshop.testql.toon.yaml`

- **name**: test-gui-connect-workshop.testql.toon.yaml — GUI tests for Connect Workshop module
- **type**: `gui`
- **encoder_url**: `http://localhost:8105`
- **api_url**: `http://localhost:8101`
- **endpoints**:
  - `GET /api/v3/data/customers?limit=5` → `200`
- **navigate**: `/connect-workshop,  500`, `/connect-workshop/requests-search,  300`, `/connect-workshop/services-search,  300`, `/connect-workshop/transport-search,  300`, `/connect-workshop/dispositions-search,  300`, `/connect-workshop/requests-new-request,  300`

#### `test-mixed-workflow.testql.toon.yaml`

- **name**: DSL Mixed Workflow Example
- **type**: `e2e`
- **endpoints**:
  - `GET /api/v3/data/devices?limit=3` → `200`
  - `GET /api/v3/data/customers?limit=3` → `200`
  - `GET /api/v3/data/intervals?limit=3` → `200`: ── Nawigacja UI ──────────────────────────────────────
  - `GET /api/v3/data/protocols?limit=3` → `200`
  - `GET /api/v3/data/test_scenarios?limit=3` → `200`
- **navigate**: `/connect-test-device,  500`

#### `test-protocol-flow.testql.toon.yaml`

- **name**: Example DSL Script - Protocol Flow Test (Read-Only)
- **type**: `api`
- **endpoints**:
  - `GET /api/v3/data/devices?limit=5` → `200`
  - `GET /api/v3/data/customers?limit=5` → `200`
  - `GET /api/v3/data/test_scenarios?limit=10` → `200`
  - `GET /api/v3/data/intervals?limit=10` → `200`
  - `GET /api/v3/data/scenario_goal_intervals?limit=20` → `200`
  - `GET /api/v3/data/protocols?limit=10` → `200`: ── Wybory domenowe ───────────────────────────────────

#### `test-ui-navigation.testql.toon.yaml`

- **name**: Example DSL Script - API Endpoints Test
- **type**: `api`
- **endpoints**:
  - `GET /api/v3/data/devices?limit=5` → `200`
  - `GET /api/v3/data/customers?limit=5` → `200`
  - `GET /api/v3/data/protocols?limit=10` → `200`
  - `GET /api/v3/data/test_scenarios?limit=10` → `200`
  - `GET /api/v3/data/intervals?limit=10` → `200`
  - `GET /api/v3/data/scenario_goal_intervals?limit=10` → `200`
  - `GET /api/v3/data/labels?limit=10` → `200`

## Workflows

### DOQL Workflows (`app.doql.less`, `app.doql.css`)

- **install** `[manual]`: `pip install -e .[dev]`
- **quality** `[manual]`: `pyqual run`
- **quality:fix** `[manual]`: `pyqual run --fix`
- **quality:report** `[manual]`: `pyqual report`
- **test** `[manual]`: `pytest -q`
- **lint** `[manual]`: `ruff check .`
- **fmt** `[manual]`: `ruff format .`
- **build** `[manual]`: `python -m build`
- **clean** `[manual]`: `rm -rf build/ dist/ *.egg-info`
- **iql:run** `[manual]`: `testql run {{.CLI_ARGS}}`
- **iql:shell** `[manual]`: `testql shell`
- **doql:adopt** `[manual]`: `if ! command -v {{.DOQL_CMD}} >/dev/null 2>&1; then`
- **doql:validate** `[manual]`: `if [ ! -f "{{.DOQL_OUTPUT}}" ]; then`
- **doql:doctor** `[manual]`: `{{.DOQL_CMD}} doctor`
- **doql:build** `[manual]`: `if [ ! -f "{{.DOQL_OUTPUT}}" ]; then`
- **docker:build** `[manual]`: `docker-compose build`
- **docker:up** `[manual]`: `docker-compose up -d`
- **docker:down** `[manual]`: `docker-compose down`
- **publish** `[manual]`: `twine upload dist/*`
- **help** `[manual]`: `task --list`

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

**Pipeline**: `quality-loop`

### Metrics / Thresholds

- `cc_max`: `10`
- `vallm_pass_min`: `60`

### Stages

- **analyze**: `code2llm-filtered`
- **validate**: `vallm-filtered`
- **prefact**: `prefact` *(optional)*
- **fix**: `llx-fix` *(optional)*
- **security**: `bandit` *(optional)*
- **typecheck**: `mypy`
- **test**: `pytest`
- **push**: `git-push` *(optional)*

### Loop Behavior

- `max_iterations`: `3`
- `on_fail`: `report`
- `ticket_backends`: `['markdown']`

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
