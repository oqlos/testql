# TestQL — Interface Query Language for Testing

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Dependencies](#dependencies)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `testql`
- **version**: `0.6.5`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **openapi_title**: testql API v1.0.0
- **generated_from**: pyproject.toml, Taskfile.yml, testql(74), openapi(7 ep), app.doql.less, pyqual.yaml, goal.yaml, .env.example, src(14 mod), project/(6 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: testql;
  version: 0.4.2;
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

workflow[name="analyze"] {
  trigger: manual;
  step-1: run cmd=echo "🔬 Running project analysis...";
  step-2: run cmd=testql analyze . --tools code2llm,redup,vallm;
}

deploy {
  target: docker-compose;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
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
- `testql.report_generator`
- `testql.runner`
- `testql.sumd_generator`
- `testql.sumd_parser`
- `testql.toon_parser`

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
fastapi
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Source Map

*Top 5 modules by symbol density — signatures for LLM orientation.*

### `testql.endpoint_detector` (`testql/endpoint_detector.py`)

```python
def detect_endpoints(project_path)  # CC=1, fan=2
class EndpointInfo:  # Standardized endpoint information.
    def to_testql_api_call(base_url)  # CC=2
    def _infer_expected_status()  # CC=1
class ServiceInfo:  # Information about a service/application.
class BaseEndpointDetector:  # Base class for endpoint detectors.
    def __init__(project_path)  # CC=1
    def detect()  # CC=3
    def _find_files(pattern, exclude_dirs)  # CC=6
class FastAPIDetector:  # Detect FastAPI endpoints using AST analysis.
    def detect()  # CC=3
    def _analyze_file(py_file)  # CC=7
    def _detect_router_assignment(node, routers)  # CC=9
    def _detect_app_assignment(node)  # CC=1
    def _extract_include_router(node)  # CC=6
    def _analyze_route_handler(node, py_file, content, routers)  # CC=4
    def _extract_route_info(decorator)  # CC=6
    def _get_router_prefix(decorator, routers)  # CC=6
    def _extract_parameters(node)  # CC=4
    def _get_annotation_name(annotation)  # CC=4
    def _extract_docstring(node)  # CC=5
class FlaskDetector:  # Detect Flask endpoints including Blueprints.
    def detect()  # CC=3
    def _analyze_flask_file(py_file)  # CC=4
    def _detect_blueprint(node, blueprints)  # CC=9
    def _analyze_flask_route(node, py_file, content, blueprints)  # CC=5
    def _extract_flask_route_info(decorator, blueprints)  # CC=13 ⚠
class DjangoDetector:  # Detect Django URL patterns.
    def detect()  # CC=3
    def _analyze_urls_py(urls_file)  # CC=3
class ExpressDetector:  # Detect Express.js routes from JavaScript/TypeScript files.
    def detect()  # CC=3
    def _analyze_express_file(js_file)  # CC=4
class OpenAPIDetector:  # Detect endpoints from OpenAPI/Swagger specifications.
    def detect()  # CC=3
    def _parse_spec(spec_file)  # CC=10 ⚠
class TestEndpointDetector:  # Detect API calls in test files to infer endpoints.
    def detect()  # CC=3
    def _analyze_test_file(test_file)  # CC=6
class GraphQLDetector:  # Detect GraphQL schemas and resolvers.
    def detect()  # CC=3
    def _analyze_schema(schema_file)  # CC=3
    def _analyze_python_graphql(py_file)  # CC=4
class WebSocketDetector:  # Detect WebSocket endpoints.
    def detect()  # CC=3
class ConfigEndpointDetector:  # Detect endpoints from configuration files.
    def detect()  # CC=3
    def _analyze_docker_compose(compose_file)  # CC=9
    def _infer_protocol(port)  # CC=1
class UnifiedEndpointDetector:  # Unified detector that runs all specialized detectors.
    def __init__(project_path)  # CC=1
    def detect_all()  # CC=4
    def _deduplicate_endpoints(endpoints)  # CC=3
    def get_endpoints_by_type(endpoint_type)  # CC=3
    def get_endpoints_by_framework(framework)  # CC=3
    def generate_testql_scenario(output_file)  # CC=9
    def _rest_block(rest_eps)  # CC=3
    def _graphql_block(graphql_eps)  # CC=4
    def _ws_block(ws_eps)  # CC=3
```

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

### `testql.generator` (`testql/generator.py`)

```python
def generate_for_project(project_path)  # CC=1, fan=2
def generate_for_workspace(workspace_path)  # CC=1, fan=3
class TestPattern:  # Discovered test pattern from source code.
class ProjectProfile:  # Analyzed project profile.
class TestGenerator:  # Base class for test generators.
    def __init__(project_path)  # CC=1
    def _detect_project_type()  # CC=12 ⚠
    def analyze()  # CC=1
    def _scan_directory_structure()  # CC=8
    def _analyze_python_tests()  # CC=12 ⚠
    def _extract_test_pattern(node, content, class_name, source_file)  # CC=14 ⚠
    def _analyze_config_files()  # CC=6
    def _analyze_api_routes()  # CC=3
    def _analyze_api_routes_fallback()  # CC=4
    def _analyze_scenarios()  # CC=5
    def generate_tests(output_dir)  # CC=12 ⚠
    def _generate_api_tests(output_dir)  # CC=23 ⚠
    def _generate_from_python_tests(output_dir)  # CC=12 ⚠
    def _generate_from_scenarios(output_dir)  # CC=3
    def _generate_api_integration_tests(output_dir)  # CC=1
    def _generate_cli_tests(output_dir)  # CC=1
    def _generate_lib_tests(output_dir)  # CC=1
    def _generate_frontend_tests(output_dir)  # CC=1
    def _generate_hardware_tests(output_dir)  # CC=1
class MultiProjectTestGenerator:  # Generator that operates across multiple projects.
    def __init__(workspace_path)  # CC=1
    def discover_projects()  # CC=6
    def analyze_all()  # CC=2
    def generate_all()  # CC=2
    def generate_cross_project_tests(output_dir)  # CC=3
```

### `testql.openapi_generator` (`testql/openapi_generator.py`)

```python
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
    def _extract_parameters(ep)  # CC=11 ⚠
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

## Call Graph

*65 nodes · 49 edges · 21 modules · CC̄=4.6*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `convert_iql_to_testtoon` *(in testql.interpreter._converter)* | 66 ⚠ | 1 | 116 | **117** |
| `parse_doql_less` *(in testql.commands.echo)* | 29 ⚠ | 1 | 85 | **86** |
| `format_text_output` *(in testql.commands.echo)* | 19 ⚠ | 1 | 46 | **47** |
| `iql_run_file` *(in testql.commands.encoder_routes)* | 12 ⚠ | 0 | 43 | **43** |
| `parse_testtoon` *(in testql.interpreter._testtoon_parser)* | 12 ⚠ | 1 | 31 | **32** |
| `list_tests` *(in testql.commands.suite_cmd)* | 9 | 0 | 27 | **27** |
| `_collect_test_files` *(in testql.commands.suite_cmd)* | 15 ⚠ | 1 | 23 | **24** |
| `parse_line` *(in testql.runner)* | 9 | 2 | 20 | **22** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/oqlos/testql
# nodes: 65 | edges: 49 | modules: 21
# CC̄=4.6

HUBS[20]:
  testql.interpreter._converter.convert_iql_to_testtoon
    CC=66  in:1  out:116  total:117
  testql.commands.echo.parse_doql_less
    CC=29  in:1  out:85  total:86
  testql.commands.echo.format_text_output
    CC=19  in:1  out:46  total:47
  testql.commands.encoder_routes.iql_run_file
    CC=12  in:0  out:43  total:43
  testql.interpreter._testtoon_parser.parse_testtoon
    CC=12  in:1  out:31  total:32
  testql.commands.suite_cmd.list_tests
    CC=9  in:0  out:27  total:27
  testql.commands.suite_cmd._collect_test_files
    CC=15  in:1  out:23  total:24
  testql.runner.parse_line
    CC=9  in:2  out:20  total:22
  testql.commands.echo.parse_toon_scenarios
    CC=8  in:1  out:21  total:22
  testql.commands.misc_cmds.report
    CC=4  in:0  out:22  total:22
  testql.report_generator.generate_report
    CC=3  in:1  out:20  total:21
  testql.commands.misc_cmds.create
    CC=6  in:0  out:21  total:21
  testql.runner.DslCliExecutor.run_script
    CC=11  in:0  out:20  total:20
  testql.commands.endpoints_cmd.endpoints
    CC=9  in:0  out:20  total:20
  testql.commands.endpoints_cmd._format_endpoints
    CC=13  in:1  out:18  total:19
  testql.interpreter._assertions.AssertionsMixin._cmd_assert_json
    CC=6  in:0  out:17  total:17
  testql.interpreter._flow.FlowMixin._cmd_include
    CC=7  in:0  out:17  total:17
  testql.commands.echo.echo
    CC=3  in:0  out:17  total:17
  testql.interpreter.interpreter.IqlInterpreter.execute
    CC=4  in:0  out:16  total:16
  testql.commands.encoder_routes.iql_list_tables
    CC=4  in:0  out:15  total:15

MODULES:
  TODO.testtoon_parser  [2 funcs]
    print_parsed  CC=8  out:12
    validate  CC=2  out:2
  testql._base_fallback  [2 funcs]
    all  CC=1  out:1
    set  CC=1  out:0
  testql.cli  [2 funcs]
    cli  CC=1  out:2
    main  CC=1  out:1
  testql.commands.echo  [5 funcs]
    echo  CC=3  out:17
    format_text_output  CC=19  out:46
    generate_context  CC=7  out:9
    parse_doql_less  CC=29  out:85
    parse_toon_scenarios  CC=8  out:21
  testql.commands.encoder_routes  [12 funcs]
    _evaluate_assertion  CC=10  out:12
    _exec_assert_cmd  CC=7  out:11
    _exec_browser_cmd  CC=9  out:10
    _exec_encoder_cmd  CC=6  out:4
    _execute_iql_line  CC=10  out:13
    _normalize_iql_path  CC=10  out:13
    _resolve_iql_path  CC=1  out:2
    iql_list_files  CC=7  out:14
    iql_list_tables  CC=4  out:15
    iql_read_file  CC=3  out:11
  testql.commands.endpoints_cmd  [2 funcs]
    _format_endpoints  CC=13  out:18
    endpoints  CC=9  out:20
  testql.commands.misc_cmds  [3 funcs]
    _build_test_content  CC=7  out:1
    create  CC=6  out:21
    report  CC=4  out:22
  testql.commands.suite_cmd  [4 funcs]
    _collect_test_files  CC=15  out:23
    _find_files  CC=9  out:8
    _parse_meta  CC=12  out:10
    list_tests  CC=9  out:27
  testql.endpoint_detector  [1 funcs]
    _deduplicate_endpoints  CC=3  out:4
  testql.generator  [1 funcs]
    _scan_directory_structure  CC=8  out:6
  testql.interpreter._api_runner  [2 funcs]
    _cmd_capture  CC=3  out:13
    _navigate_json_path  CC=10  out:13
  testql.interpreter._assertions  [1 funcs]
    _cmd_assert_json  CC=6  out:17
  testql.interpreter._converter  [5 funcs]
    _detect_scenario_type  CC=12  out:7
    _extract_scenario_name  CC=6  out:8
    convert_directory  CC=4  out:7
    convert_file  CC=1  out:3
    convert_iql_to_testtoon  CC=66  out:116
  testql.interpreter._flow  [1 funcs]
    _cmd_include  CC=7  out:17
  testql.interpreter._parser  [1 funcs]
    parse_iql  CC=5  out:10
  testql.interpreter._testtoon_parser  [2 funcs]
    parse_testtoon  CC=12  out:31
    testtoon_to_iql  CC=2  out:4
  testql.interpreter.interpreter  [3 funcs]
    __init__  CC=2  out:3
    execute  CC=4  out:16
    parse  CC=2  out:3
  testql.openapi_generator  [1 funcs]
    _infer_tags  CC=7  out:9
  testql.report_generator  [1 funcs]
    generate_report  CC=3  out:20
  testql.runner  [3 funcs]
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

EDGES:
  testql.cli.main → testql.cli.cli
  testql.generator.TestGenerator._scan_directory_structure → testql._base_fallback.VariableStore.set
  TODO.testtoon_parser.print_parsed → TODO.testtoon_parser.validate
  testql.openapi_generator.OpenAPIGenerator._infer_tags → testql._base_fallback.VariableStore.set
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
  testql.runner.parse_script → testql.runner.parse_line
  testql.runner.DslCliExecutor.run_script → testql.runner.parse_script
  testql.commands.echo.generate_context → testql.commands.echo.parse_toon_scenarios
  testql.commands.echo.generate_context → testql.commands.echo.parse_doql_less
  testql.commands.echo.echo → testql.commands.echo.generate_context
  testql.commands.echo.echo → testql.commands.echo.format_text_output
  testql.commands.endpoints_cmd.endpoints → testql.commands.endpoints_cmd._format_endpoints
  testql.endpoint_detector.UnifiedEndpointDetector._deduplicate_endpoints → testql._base_fallback.VariableStore.set
  testql.commands.misc_cmds.create → testql.commands.misc_cmds._build_test_content
  testql.commands.misc_cmds.report → testql.report_generator.generate_report
  testql.commands.suite_cmd._collect_test_files → testql._base_fallback.VariableStore.set
  testql.commands.suite_cmd._collect_test_files → testql.commands.suite_cmd._find_files
  testql.commands.suite_cmd.list_tests → testql._base_fallback.VariableStore.set
  testql.commands.suite_cmd.list_tests → testql.commands.suite_cmd._parse_meta
  testql.interpreter._api_runner.ApiRunnerMixin._cmd_capture → testql.interpreter._api_runner._navigate_json_path
  testql.interpreter._flow.FlowMixin._cmd_include → testql.interpreter._parser.parse_iql
  testql.interpreter._testtoon_parser.testtoon_to_iql → testql.interpreter._testtoon_parser.parse_testtoon
  testql.interpreter._assertions.AssertionsMixin._cmd_assert_json → testql.interpreter._api_runner._navigate_json_path
  testql.interpreter._converter.convert_iql_to_testtoon → testql.interpreter._converter._extract_scenario_name
  testql.interpreter._converter.convert_iql_to_testtoon → testql.interpreter._converter._detect_scenario_type
  testql.interpreter._converter.convert_file → testql.interpreter._converter.convert_iql_to_testtoon
  testql.interpreter._converter.convert_directory → testql.interpreter._converter.convert_file
  testql.interpreter.interpreter.IqlInterpreter.__init__ → testql._base_fallback.VariableStore.set
  testql.interpreter.interpreter.IqlInterpreter.parse → testql.interpreter._parser.parse_iql
  testql.interpreter.interpreter.IqlInterpreter.parse → testql.interpreter._testtoon_parser.testtoon_to_iql
  testql.interpreter.interpreter.IqlInterpreter.execute → testql._base_fallback.VariableStore.all
  testql.commands.encoder_routes._resolve_iql_path → testql.commands.encoder_routes._normalize_iql_path
  testql.commands.encoder_routes._exec_assert_cmd → testql.commands.encoder_routes._evaluate_assertion
  testql.commands.encoder_routes._execute_iql_line → testql.commands.encoder_routes._exec_encoder_cmd
  testql.commands.encoder_routes._execute_iql_line → testql.commands.encoder_routes._exec_browser_cmd
  testql.commands.encoder_routes.iql_list_files → testql._base_fallback.VariableStore.set
  testql.commands.encoder_routes.iql_read_file → testql.commands.encoder_routes._resolve_iql_path
  testql.commands.encoder_routes.iql_list_tables → testql.commands.encoder_routes._resolve_iql_path
  testql.commands.encoder_routes.iql_run_line → testql.commands.encoder_routes._execute_iql_line
  testql.commands.encoder_routes.iql_run_file → testql.commands.encoder_routes._resolve_iql_path
```

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
- `GET /iql/files` → `200` — `iql_list_files`
- `GET /iql/file` → `200` — `iql_read_file`
- `GET /iql/tables` → `200` — `iql_list_tables`
- assert `status < 500`
- assert `response_time < 2000`
- detectors: FastAPIDetector

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

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/oqlos/testql
# nodes: 65 | edges: 49 | modules: 21
# CC̄=4.6

HUBS[20]:
  testql.interpreter._converter.convert_iql_to_testtoon
    CC=66  in:1  out:116  total:117
  testql.commands.echo.parse_doql_less
    CC=29  in:1  out:85  total:86
  testql.commands.echo.format_text_output
    CC=19  in:1  out:46  total:47
  testql.commands.encoder_routes.iql_run_file
    CC=12  in:0  out:43  total:43
  testql.interpreter._testtoon_parser.parse_testtoon
    CC=12  in:1  out:31  total:32
  testql.commands.suite_cmd.list_tests
    CC=9  in:0  out:27  total:27
  testql.commands.suite_cmd._collect_test_files
    CC=15  in:1  out:23  total:24
  testql.runner.parse_line
    CC=9  in:2  out:20  total:22
  testql.commands.echo.parse_toon_scenarios
    CC=8  in:1  out:21  total:22
  testql.commands.misc_cmds.report
    CC=4  in:0  out:22  total:22
  testql.report_generator.generate_report
    CC=3  in:1  out:20  total:21
  testql.commands.misc_cmds.create
    CC=6  in:0  out:21  total:21
  testql.runner.DslCliExecutor.run_script
    CC=11  in:0  out:20  total:20
  testql.commands.endpoints_cmd.endpoints
    CC=9  in:0  out:20  total:20
  testql.commands.endpoints_cmd._format_endpoints
    CC=13  in:1  out:18  total:19
  testql.interpreter._assertions.AssertionsMixin._cmd_assert_json
    CC=6  in:0  out:17  total:17
  testql.interpreter._flow.FlowMixin._cmd_include
    CC=7  in:0  out:17  total:17
  testql.commands.echo.echo
    CC=3  in:0  out:17  total:17
  testql.interpreter.interpreter.IqlInterpreter.execute
    CC=4  in:0  out:16  total:16
  testql.commands.encoder_routes.iql_list_tables
    CC=4  in:0  out:15  total:15

MODULES:
  TODO.testtoon_parser  [2 funcs]
    print_parsed  CC=8  out:12
    validate  CC=2  out:2
  testql._base_fallback  [2 funcs]
    all  CC=1  out:1
    set  CC=1  out:0
  testql.cli  [2 funcs]
    cli  CC=1  out:2
    main  CC=1  out:1
  testql.commands.echo  [5 funcs]
    echo  CC=3  out:17
    format_text_output  CC=19  out:46
    generate_context  CC=7  out:9
    parse_doql_less  CC=29  out:85
    parse_toon_scenarios  CC=8  out:21
  testql.commands.encoder_routes  [12 funcs]
    _evaluate_assertion  CC=10  out:12
    _exec_assert_cmd  CC=7  out:11
    _exec_browser_cmd  CC=9  out:10
    _exec_encoder_cmd  CC=6  out:4
    _execute_iql_line  CC=10  out:13
    _normalize_iql_path  CC=10  out:13
    _resolve_iql_path  CC=1  out:2
    iql_list_files  CC=7  out:14
    iql_list_tables  CC=4  out:15
    iql_read_file  CC=3  out:11
  testql.commands.endpoints_cmd  [2 funcs]
    _format_endpoints  CC=13  out:18
    endpoints  CC=9  out:20
  testql.commands.misc_cmds  [3 funcs]
    _build_test_content  CC=7  out:1
    create  CC=6  out:21
    report  CC=4  out:22
  testql.commands.suite_cmd  [4 funcs]
    _collect_test_files  CC=15  out:23
    _find_files  CC=9  out:8
    _parse_meta  CC=12  out:10
    list_tests  CC=9  out:27
  testql.endpoint_detector  [1 funcs]
    _deduplicate_endpoints  CC=3  out:4
  testql.generator  [1 funcs]
    _scan_directory_structure  CC=8  out:6
  testql.interpreter._api_runner  [2 funcs]
    _cmd_capture  CC=3  out:13
    _navigate_json_path  CC=10  out:13
  testql.interpreter._assertions  [1 funcs]
    _cmd_assert_json  CC=6  out:17
  testql.interpreter._converter  [5 funcs]
    _detect_scenario_type  CC=12  out:7
    _extract_scenario_name  CC=6  out:8
    convert_directory  CC=4  out:7
    convert_file  CC=1  out:3
    convert_iql_to_testtoon  CC=66  out:116
  testql.interpreter._flow  [1 funcs]
    _cmd_include  CC=7  out:17
  testql.interpreter._parser  [1 funcs]
    parse_iql  CC=5  out:10
  testql.interpreter._testtoon_parser  [2 funcs]
    parse_testtoon  CC=12  out:31
    testtoon_to_iql  CC=2  out:4
  testql.interpreter.interpreter  [3 funcs]
    __init__  CC=2  out:3
    execute  CC=4  out:16
    parse  CC=2  out:3
  testql.openapi_generator  [1 funcs]
    _infer_tags  CC=7  out:9
  testql.report_generator  [1 funcs]
    generate_report  CC=3  out:20
  testql.runner  [3 funcs]
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

EDGES:
  testql.cli.main → testql.cli.cli
  testql.generator.TestGenerator._scan_directory_structure → testql._base_fallback.VariableStore.set
  TODO.testtoon_parser.print_parsed → TODO.testtoon_parser.validate
  testql.openapi_generator.OpenAPIGenerator._infer_tags → testql._base_fallback.VariableStore.set
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
  testql.runner.parse_script → testql.runner.parse_line
  testql.runner.DslCliExecutor.run_script → testql.runner.parse_script
  testql.commands.echo.generate_context → testql.commands.echo.parse_toon_scenarios
  testql.commands.echo.generate_context → testql.commands.echo.parse_doql_less
  testql.commands.echo.echo → testql.commands.echo.generate_context
  testql.commands.echo.echo → testql.commands.echo.format_text_output
  testql.commands.endpoints_cmd.endpoints → testql.commands.endpoints_cmd._format_endpoints
  testql.endpoint_detector.UnifiedEndpointDetector._deduplicate_endpoints → testql._base_fallback.VariableStore.set
  testql.commands.misc_cmds.create → testql.commands.misc_cmds._build_test_content
  testql.commands.misc_cmds.report → testql.report_generator.generate_report
  testql.commands.suite_cmd._collect_test_files → testql._base_fallback.VariableStore.set
  testql.commands.suite_cmd._collect_test_files → testql.commands.suite_cmd._find_files
  testql.commands.suite_cmd.list_tests → testql._base_fallback.VariableStore.set
  testql.commands.suite_cmd.list_tests → testql.commands.suite_cmd._parse_meta
  testql.interpreter._api_runner.ApiRunnerMixin._cmd_capture → testql.interpreter._api_runner._navigate_json_path
  testql.interpreter._flow.FlowMixin._cmd_include → testql.interpreter._parser.parse_iql
  testql.interpreter._testtoon_parser.testtoon_to_iql → testql.interpreter._testtoon_parser.parse_testtoon
  testql.interpreter._assertions.AssertionsMixin._cmd_assert_json → testql.interpreter._api_runner._navigate_json_path
  testql.interpreter._converter.convert_iql_to_testtoon → testql.interpreter._converter._extract_scenario_name
  testql.interpreter._converter.convert_iql_to_testtoon → testql.interpreter._converter._detect_scenario_type
  testql.interpreter._converter.convert_file → testql.interpreter._converter.convert_iql_to_testtoon
  testql.interpreter._converter.convert_directory → testql.interpreter._converter.convert_file
  testql.interpreter.interpreter.IqlInterpreter.__init__ → testql._base_fallback.VariableStore.set
  testql.interpreter.interpreter.IqlInterpreter.parse → testql.interpreter._parser.parse_iql
  testql.interpreter.interpreter.IqlInterpreter.parse → testql.interpreter._testtoon_parser.testtoon_to_iql
  testql.interpreter.interpreter.IqlInterpreter.execute → testql._base_fallback.VariableStore.all
  testql.commands.encoder_routes._resolve_iql_path → testql.commands.encoder_routes._normalize_iql_path
  testql.commands.encoder_routes._exec_assert_cmd → testql.commands.encoder_routes._evaluate_assertion
  testql.commands.encoder_routes._execute_iql_line → testql.commands.encoder_routes._exec_encoder_cmd
  testql.commands.encoder_routes._execute_iql_line → testql.commands.encoder_routes._exec_browser_cmd
  testql.commands.encoder_routes.iql_list_files → testql._base_fallback.VariableStore.set
  testql.commands.encoder_routes.iql_read_file → testql.commands.encoder_routes._resolve_iql_path
  testql.commands.encoder_routes.iql_list_tables → testql.commands.encoder_routes._resolve_iql_path
  testql.commands.encoder_routes.iql_run_line → testql.commands.encoder_routes._execute_iql_line
  testql.commands.encoder_routes.iql_run_file → testql.commands.encoder_routes._resolve_iql_path
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 41f 7839L | python:39,shell:2 | 2026-04-19
# CC̄=4.6 | critical:7/308 | dups:0 | cycles:2

HEALTH[9]:
  🔴 GOD   testql/generator.py = 709L, 4 classes, 26m, max CC=23
  🔴 GOD   testql/endpoint_detector.py = 835L, 13 classes, 46m, max CC=13
  🟡 CC    _generate_api_tests CC=23 (limit:15)
  🟡 CC    parse_doql_less CC=29 (limit:15)
  🟡 CC    format_text_output CC=19 (limit:15)
  🟡 CC    echo CC=16 (limit:15)
  🟡 CC    _collect_test_files CC=15 (limit:15)
  🟡 CC    suite CC=18 (limit:15)
  🟡 CC    convert_iql_to_testtoon CC=66 (limit:15)

REFACTOR[4]:
  1. split testql/generator.py  (god module)
  2. split testql/endpoint_detector.py  (god module)
  3. split 7 high-CC methods  (CC>15)
  4. break 2 circular dependencies

PIPELINES[236]:
  [1] Src [main]: main → cli
      PURITY: 100% pure
  [2] Src [parse_testql_results]: parse_testql_results
      PURITY: 100% pure
  [3] Src [to_json]: to_json
      PURITY: 100% pure
  [4] Src [__init__]: __init__
      PURITY: 100% pure
  [5] Src [generate]: generate
      PURITY: 100% pure

LAYERS:
  TODO/                           CC̄=5.9    ←in:0  →out:0
  │ testtoon_parser            141L  1C    7m  CC=14     ←0
  │
  testql/                         CC̄=4.6    ←in:14  →out:0
  │ !! endpoint_detector          835L  13C   46m  CC=13     ←0
  │ !! generator                  709L  4C   26m  CC=23     ←0
  │ !! misc_cmds                  529L  0C    7m  CC=16     ←0
  │ !! _converter                 475L  2C    8m  CC=66     ←0
  │ openapi_generator          449L  3C   19m  CC=11     ←0
  │ encoder_routes             424L  0C   15m  CC=12     ←0
  │ _testtoon_parser           393L  2C   19m  CC=12     ←1
  │ runner                     371L  3C   18m  CC=12     ←0
  │ !! suite_cmd                  314L  0C    8m  CC=18     ←0
  │ sumd_parser                287L  5C   10m  CC=12     ←0
  │ !! echo                       262L  0C    5m  CC=29     ←0
  │ report_generator           248L  4C    8m  CC=5      ←1
  │ _base_fallback             221L  7C   26m  CC=4      ←9
  │ sumd_generator             208L  0C   11m  CC=7      ←1
  │ doql_parser                172L  1C    9m  CC=6      ←1
  │ _websockets                172L  1C    7m  CC=9      ←0
  │ _api_runner                168L  1C    5m  CC=10     ←1
  │ echo_schemas               153L  6C    2m  CC=8      ←0
  │ generate_cmd               140L  0C    4m  CC=11     ←0
  │ endpoints_cmd              137L  0C    3m  CC=13     ←0
  │ _flow                      136L  1C    6m  CC=9      ←0
  │ interpreter                125L  1C    7m  CC=4      ←0
  │ toon_parser                110L  1C    7m  CC=4      ←1
  │ _assertions                103L  1C    4m  CC=6      ←0
  │ __init__                    89L  0C    1m  CC=8      ←0
  │ junit                       79L  1C    3m  CC=8      ←0
  │ _encoder                    73L  1C   11m  CC=6      ←0
  │ run_cmd                     56L  0C    1m  CC=3      ←0
  │ cli                         41L  0C    2m  CC=1      ←0
  │ console                     38L  0C    1m  CC=6      ←0
  │ base                        37L  0C    0m  CC=0.0    ←0
  │ _parser                     33L  2C    1m  CC=5      ←2
  │ json_reporter               33L  0C    1m  CC=2      ←0
  │ __init__                    27L  0C    0m  CC=0.0    ←0
  │ __main__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     0L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ project.sh                  35L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     testql/runners/__init__.py                0L

COUPLING:
                                  testql     testql.commands  testql.interpreter
              testql                  ──                 ←11                  ←3  hub
     testql.commands                  11                  ──                      !! fan-out
  testql.interpreter                   3                                      ──
  CYCLES: 2
  HUB: testql/ (fan-in=14)
  SMELL: testql.commands/ fan-out=11 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 0 groups | 0f 0L | 2026-04-19

SUMMARY:
  files_scanned: 0
  total_lines:   0
  dup_groups:    0
  dup_fragments: 0
  saved_lines:   0
  scan_ms:       3915
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 308 func | 33f | 2026-04-19

NEXT[10] (ranked by impact):
  [1] !! SPLIT           testql/generator.py
      WHY: 709L, 4 classes, max CC=23
      EFFORT: ~4h  IMPACT: 16307

  [2] !! SPLIT           testql/endpoint_detector.py
      WHY: 835L, 13 classes, max CC=13
      EFFORT: ~4h  IMPACT: 10855

  [3] !! SPLIT           testql/commands/misc_cmds.py
      WHY: 529L, 0 classes, max CC=16
      EFFORT: ~4h  IMPACT: 8464

  [4] !! SPLIT-FUNC      convert_iql_to_testtoon  CC=66  fan=40
      WHY: CC=66 exceeds 15
      EFFORT: ~1h  IMPACT: 2640

  [5] !! SPLIT-FUNC      parse_doql_less  CC=29  fan=20
      WHY: CC=29 exceeds 15
      EFFORT: ~1h  IMPACT: 580

  [6] !  SPLIT-FUNC      suite  CC=18  fan=26
      WHY: CC=18 exceeds 15
      EFFORT: ~1h  IMPACT: 468

  [7] !  SPLIT-FUNC      echo  CC=16  fan=22
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 352

  [8] !  SPLIT-FUNC      TestGenerator._generate_api_tests  CC=23  fan=12
      WHY: CC=23 exceeds 15
      EFFORT: ~1h  IMPACT: 276

  [9] !  SPLIT-FUNC      format_text_output  CC=19  fan=11
      WHY: CC=19 exceeds 15
      EFFORT: ~1h  IMPACT: 209

  [10] !  SPLIT-FUNC      _collect_test_files  CC=15  fan=13
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 195


RISKS[3]:
  ⚠ Splitting testql/endpoint_detector.py may break 46 import paths
  ⚠ Splitting testql/generator.py may break 26 import paths
  ⚠ Splitting testql/commands/misc_cmds.py may break 7 import paths

METRICS-TARGET:
  CC̄:          4.6 → ≤3.2
  max-CC:      66 → ≤20
  god-modules: 3 → 0
  high-CC(≥15): 7 → ≤3
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
  prev CC̄=4.9 → now CC̄=4.6
```

### Validation (`project/validation.toon.yaml`)

```toon markpact:analysis path=project/validation.toon.yaml
# vallm batch | 77f | 44✓ 6⚠ 3✗ | 2026-04-19

SUMMARY:
  scanned: 77  passed: 44 (57.1%)  warnings: 6  errors: 3  unsupported: 30

WARNINGS[6]{path,score}:
  testql/cli.py,0.80
    issues[12]{rule,severity,message,line}:
      complexity.cyclomatic,warning,analyze has cyclomatic complexity 16 (max: 15),125
      complexity.cyclomatic,warning,endpoints has cyclomatic complexity 21 (max: 15),201
      complexity.cyclomatic,warning,suite has cyclomatic complexity 47 (max: 15),671
      complexity.cyclomatic,warning,list has cyclomatic complexity 21 (max: 15),862
      complexity.cyclomatic,warning,echo has cyclomatic complexity 17 (max: 15),942
      complexity.maintainability,warning,Low maintainability index: 7.1 (threshold: 20),
      complexity.lizard_cc,warning,analyze: CC=16 exceeds limit 15,125
      complexity.lizard_cc,warning,endpoints: CC=21 exceeds limit 15,201
      complexity.lizard_cc,warning,suite: CC=43 exceeds limit 15,671
      complexity.lizard_length,warning,suite: 120 lines exceeds limit 100,671
      complexity.lizard_cc,warning,list: CC=21 exceeds limit 15,862
      complexity.lizard_cc,warning,echo: CC=17 exceeds limit 15,942
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
  testql/sumd_generator.py,0.93
    issues[3]{rule,severity,message,line}:
      complexity.cyclomatic,warning,generate_sumd has cyclomatic complexity 29 (max: 15),11
      complexity.lizard_cc,warning,generate_sumd: CC=29 exceeds limit 15,11
      complexity.lizard_length,warning,generate_sumd: 130 lines exceeds limit 100,11
  testql/endpoint_detector.py,0.96
    issues[2]{rule,severity,message,line}:
      complexity.cyclomatic,warning,generate_testql_scenario has cyclomatic complexity 16 (max: 15),768
      complexity.maintainability,warning,Low maintainability index: 6.6 (threshold: 20),
  testql/generator.py,0.96
    issues[3]{rule,severity,message,line}:
      complexity.cyclomatic,warning,_generate_api_tests has cyclomatic complexity 23 (max: 15),342
      complexity.maintainability,warning,Low maintainability index: 15.1 (threshold: 20),
      complexity.lizard_cc,warning,_generate_api_tests: CC=23 exceeds limit 15,342

ERRORS[3]{path,score}:
  testql/commands/encoder_routes.py,0.92
    issues[2]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'fastapi' not found,12
      python.import.resolvable,error,Module 'fastapi.responses' not found,13
  testql/interpreter/_websockets.py,0.93
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'websockets' not found,46
  testql/_base_fallback.py,0.95
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'websockets' not found,186

UNSUPPORTED[4]{bucket,count}:
  *.md,10
  *.txt,2
  *.yml,2
  other,16
```

## Intent

TestQL with endpoint detection, OpenAPI, SUMD generation, SUMD parser and HTML report generation
