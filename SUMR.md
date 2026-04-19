# TestQL — Interface Query Language for Testing

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Dependencies](#dependencies)
- [Source Map](#source-map)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `testql`
- **version**: `0.6.0`
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
    def detect()  # CC=1
    def _find_files(pattern, exclude_dirs)  # CC=5
class FastAPIDetector:  # Detect FastAPI endpoints using AST analysis.
    def detect()  # CC=3
    def _analyze_file(py_file)  # CC=7
    def _detect_router_assignment(node, routers)  # CC=9
    def _detect_app_assignment(node)  # CC=1
    def _extract_include_router(node)  # CC=6
    def _analyze_route_handler(node, py_file, content, routers)  # CC=4
    def _extract_route_info(decorator)  # CC=6
    def _get_router_prefix(decorator, routers)  # CC=6
    def _extract_parameters(node)  # CC=3
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
    def _analyze_test_file(test_file)  # CC=5
class GraphQLDetector:  # Detect GraphQL schemas and resolvers.
    def detect()  # CC=5
    def _analyze_schema(schema_file)  # CC=3
    def _analyze_python_graphql(py_file)  # CC=4
class WebSocketDetector:  # Detect WebSocket endpoints.
    def detect()  # CC=4
class ConfigEndpointDetector:  # Detect endpoints from configuration files.
    def detect()  # CC=3
    def _analyze_docker_compose(compose_file)  # CC=8
    def _infer_protocol(port)  # CC=1
class UnifiedEndpointDetector:  # Unified detector that runs all specialized detectors.
    def __init__(project_path)  # CC=1
    def detect_all()  # CC=4
    def _deduplicate_endpoints(endpoints)  # CC=3
    def get_endpoints_by_type(endpoint_type)  # CC=1
    def get_endpoints_by_framework(framework)  # CC=1
    def generate_testql_scenario(output_file)  # CC=10 ⚠
```

### `testql._base_fallback` (`testql/_base_fallback.py`)

```python
class StepStatus:
class StepResult:
class ScriptResult:
    def passed()  # CC=1
    def failed()  # CC=1
    def summary()  # CC=1
class VariableStore:  # Simple key-value store with interpolation support.
    def __init__(initial)  # CC=2
    def set(key, value)  # CC=1
    def get(key, default)  # CC=1
    def has(key)  # CC=1
    def all()  # CC=1
    def clear()  # CC=1
    def interpolate(text)  # CC=2
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
    def run_file(path)  # CC=2
    def strip_comments(lines)  # CC=2
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
    def _detect_project_type()  # CC=9
    def analyze()  # CC=1
    def _scan_directory_structure()  # CC=8
    def _analyze_python_tests()  # CC=12 ⚠
    def _extract_test_pattern(node, content, class_name, source_file)  # CC=11 ⚠
    def _analyze_config_files()  # CC=6
    def _analyze_api_routes()  # CC=3
    def _analyze_api_routes_fallback()  # CC=4
    def _analyze_scenarios()  # CC=3
    def generate_tests(output_dir)  # CC=11 ⚠
    def _generate_api_tests(output_dir)  # CC=16 ⚠
    def _generate_from_python_tests(output_dir)  # CC=6
    def _generate_from_scenarios(output_dir)  # CC=3
    def _generate_api_integration_tests(output_dir)  # CC=1
    def _generate_cli_tests(output_dir)  # CC=1
    def _generate_lib_tests(output_dir)  # CC=1
    def _generate_frontend_tests(output_dir)  # CC=1
    def _generate_hardware_tests(output_dir)  # CC=1
class MultiProjectTestGenerator:  # Generator that operates across multiple projects.
    def __init__(workspace_path)  # CC=1
    def discover_projects()  # CC=5
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
    def __init__(project_path)  # CC=1
    def generate(title, version)  # CC=5
    def _normalize_path(path)  # CC=2
    def _build_operation(ep)  # CC=7
    def _infer_tags(ep)  # CC=6
    def _extract_parameters(ep)  # CC=10 ⚠
    def _build_request_body(ep)  # CC=6
    def _build_responses(ep)  # CC=3
    def save(output_path, format)  # CC=3
class ContractTestGenerator:  # Generate contract tests from OpenAPI specs.
    def __init__(spec)  # CC=3
    def _load_spec(path)  # CC=2
    def generate_contract_tests(output_file)  # CC=6
    def _get_expected_status(method, operation)  # CC=3
    def validate_response(endpoint, method, response)  # CC=10 ⚠
```

### `testql.runner` (`testql/runner.py`)

```python
def parse_line(line)  # CC=7, fan=8
def parse_script(content)  # CC=1, fan=2
def main()  # CC=7, fan=14
class DslCommand:
class ExecutionResult:
class DslCliExecutor:
    def __init__(base_url, verbose)  # CC=1
    def execute(cmd)  # CC=2
    def _dispatch(cmd)  # CC=6
    def cmd_api(cmd)  # CC=3
    def cmd_wait(cmd)  # CC=1
    def cmd_log(cmd)  # CC=1
    def cmd_print(cmd)  # CC=1
    def cmd_store(cmd)  # CC=1
    def cmd_env(cmd)  # CC=1
    def cmd_assert_status(cmd)  # CC=2
    def cmd_assert_json(cmd)  # CC=9
    def cmd_set_header(cmd)  # CC=1
    def cmd_set_base_url(cmd)  # CC=1
    def run_script(content, stop_on_error)  # CC=9
    def _format_cmd(cmd)  # CC=1
```

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/oqlos/testql
# nodes: 0 | edges: 0 | modules: 0
# CC̄=0.0

HUBS[20]:

MODULES:

EDGES:
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 0f 0L | unknown | 2026-04-19
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
# code2llm/evolution | 0 func | 1f | 2026-04-19

NEXT[3] (ranked by impact):
  [1] !! SPLIT           testql/cli.py
      WHY: 1181L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0

  [2] !! SPLIT           testql/endpoint_detector.py
      WHY: 827L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0

  [3] !! SPLIT           testql/generator.py
      WHY: 709L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[3]:
  ⚠ Splitting testql/cli.py may break 0 import paths
  ⚠ Splitting testql/endpoint_detector.py may break 0 import paths
  ⚠ Splitting testql/generator.py may break 0 import paths

METRICS-TARGET:
  CC̄:          0.0 → ≤0.0
  max-CC:      0 → ≤0
  god-modules: 3 → 0
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
  prev CC̄=4.9 → now CC̄=0.0
```

### Validation (`project/validation.toon.yaml`)

```toon markpact:analysis path=project/validation.toon.yaml
# vallm batch | 69f | 43✓ 6⚠ 3✗ | 2026-04-19

SUMMARY:
  scanned: 69  passed: 43 (62.3%)  warnings: 6  errors: 3  unsupported: 23

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
  *.md,8
  *.txt,1
  *.yml,2
  other,12
```

## Intent

TestQL with endpoint detection, OpenAPI, SUMD generation, SUMD parser and HTML report generation
