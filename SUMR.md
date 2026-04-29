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
- **version**: `1.2.40`
- **python_requires**: `>=3.10`
- **license**: {'text': 'Apache-2.0'}
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **openapi_title**: testql API v1.0.0
- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, testql(77), openapi(7 ep), app.doql.less, pyqual.yaml, goal.yaml, .env.example, src(16 mod), project/(6 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: testql;
  version: 1.2.40;
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

*505 nodes · 500 edges · 104 modules · CC̄=2.3*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `print` *(in examples.browser-inspection.run)* | 0 | 48 | 0 | **48** |
| `_render_toon` *(in testql.results.serializers)* | 6 | 1 | 46 | **47** |
| `any` *(in .testql.generated.generated-from-pytests.testql.toon)* | 0 | 34 | 0 | **34** |
| `list` *(in code2llm_output.map.toon)* | 0 | 34 | 0 | **34** |
| `write_inspection_artifacts` *(in testql.results.artifacts)* | 1 | 3 | 28 | **31** |
| `heal_scenario` *(in testql.commands.heal_scenario_cmd)* | 8 | 0 | 30 | **30** |
| `_cmd_assert_json` *(in testql.interpreter._assertions.AssertionsMixin)* | 13 ⚠ | 0 | 30 | **30** |
| `_render_step` *(in testql.adapters.scenario_yaml)* | 10 ⚠ | 2 | 26 | **28** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/oqlos/testql
# nodes: 505 | edges: 500 | modules: 104
# CC̄=2.3

HUBS[20]:
  examples.browser-inspection.run.print
    CC=0  in:48  out:0  total:48
  testql.results.serializers._render_toon
    CC=6  in:1  out:46  total:47
  .testql.generated.generated-from-pytests.testql.toon.any
    CC=0  in:34  out:0  total:34
  code2llm_output.map.toon.list
    CC=0  in:34  out:0  total:34
  testql.results.artifacts.write_inspection_artifacts
    CC=1  in:3  out:28  total:31
  testql.commands.heal_scenario_cmd.heal_scenario
    CC=8  in:0  out:30  total:30
  testql.interpreter._assertions.AssertionsMixin._cmd_assert_json
    CC=13  in:0  out:30  total:30
  testql.adapters.scenario_yaml._render_step
    CC=10  in:2  out:26  total:28
  testql._base_fallback.VariableStore.set
    CC=1  in:26  out:0  total:26
  testql.commands.generate_cmd._print_routes_section
    CC=10  in:1  out:23  total:24
  testql.commands.inspect_cmd.inspect
    CC=6  in:0  out:24  total:24
  testql.commands.generate_topology_cmd.generate_topology
    CC=5  in:0  out:24  total:24
  testql.commands.echo.parsers.doql._parse_workflows
    CC=7  in:1  out:22  total:23
  testql.adapters.scenario_yaml._gui_step
    CC=9  in:0  out:23  total:23
  testql.commands.encoder_routes._run_oql_lines
    CC=6  in:1  out:22  total:23
  testql.adapters.base.read_source
    CC=5  in:13  out:9  total:22
  testql.runner.parse_line
    CC=9  in:2  out:20  total:22
  testql.commands.misc_cmds.report
    CC=4  in:0  out:22  total:22
  testql.adapters.sql.fixtures.schema_fixture_from_rows
    CC=4  in:1  out:20  total:21
  testql.runner.DslCliExecutor.run_script
    CC=11  in:0  out:20  total:20

MODULES:
  .testql.generated.generated-from-pytests.testql.toon  [1 funcs]
    any  CC=0  out:0
  TODO.testtoon_parser  [2 funcs]
    print_parsed  CC=8  out:12
    validate  CC=2  out:2
  code2llm_output.map.toon  [12 funcs]
    _navigate_json_path  CC=0  out:0
    format_text_output  CC=0  out:0
    generate_context  CC=0  out:0
    generate_report  CC=0  out:0
    generate_sumd  CC=0  out:0
    list  CC=0  out:0
    parse_doql_file  CC=0  out:0
    parse_doql_less  CC=0  out:0
    parse_oql  CC=0  out:0
    parse_script  CC=0  out:0
  examples.api-testing.mock_server  [1 funcs]
    list_scenarios  CC=1  out:3
  examples.artifact-bundle.generate_bundle  [1 funcs]
    main  CC=2  out:10
  examples.browser-inspection.run  [1 funcs]
    print  CC=0  out:0
  project.map.toon  [5 funcs]
    _toon_safe_selector  CC=0  out:0
    available_sources  CC=0  out:0
    build_topology  CC=0  out:0
    get_source  CC=0  out:0
    run_self_test  CC=0  out:0
  testql._base_fallback  [3 funcs]
    emit  CC=2  out:2
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
  testql.adapters.proto.message_validator  [8 funcs]
    _missing_required  CC=4  out:1
    _row_issues  CC=3  out:4
    _validate_field_known  CC=2  out:2
    _validate_field_type  CC=3  out:2
    _validate_field_value  CC=3  out:2
    coerce_scalar  CC=5  out:6
    round_trip_equal  CC=6  out:4
    validate_message_instance  CC=5  out:7
  testql.adapters.proto.proto_adapter  [6 funcs]
    _apply_section  CC=2  out:6
    _h_message  CC=1  out:3
    _h_proto  CC=1  out:4
    _message_section  CC=5  out:8
    _proto_section  CC=3  out:7
    _toon_to_plan  CC=4  out:7
  testql.adapters.registry  [2 funcs]
    all  CC=1  out:2
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
  testql.discovery.probes.filesystem.container_dockerfile  [1 funcs]
    _metadata  CC=4  out:10
  testql.discovery.probes.filesystem.package_python  [15 funcs]
    _confidence  CC=10  out:4
    _find_python_files  CC=7  out:6
    _read_metadata  CC=8  out:13
    _call_kw  CC=2  out:3
    _dedupe_deps  CC=4  out:5
    _dep  CC=3  out:4
    _excluded  CC=2  out:1
    _parse_pyproject  CC=7  out:12
    _parse_pyproject_dependencies  CC=6  out:15
    _parse_requirements  CC=4  out:5
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
  testql.generators.analyzers  [2 funcs]
    _detect_hardware  CC=3  out:2
    _detect_python_type  CC=7  out:4
  testql.generators.api_generator  [1 funcs]
    _deduplicate_rest_routes  CC=4  out:3
  testql.generators.base  [1 funcs]
    _should_exclude_path  CC=1  out:3
  testql.generators.multi  [2 funcs]
    discover_projects  CC=6  out:6
    generate_cross_project_tests  CC=3  out:11
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
  testql.ir.metadata  [1 funcs]
    to_dict  CC=3  out:2
  testql.ir_runner.engine  [1 funcs]
    run_plan  CC=1  out:2
  testql.openapi_generator  [5 funcs]
    _load_spec  CC=2  out:3
    _extract_parameters  CC=1  out:3
    _infer_tags  CC=7  out:9
    _extract_ep_params  CC=7  out:8
    _extract_path_params  CC=4  out:4
  testql.pipeline  [1 funcs]
    _is_workspace  CC=5  out:5
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
  examples.api-testing.mock_server.list_scenarios → code2llm_output.map.toon.list
  TODO.testtoon_parser.print_parsed → examples.browser-inspection.run.print
  TODO.testtoon_parser.print_parsed → TODO.testtoon_parser.validate
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
  testql.pipeline.GenerationPipeline._is_workspace → .testql.generated.generated-from-pytests.testql.toon.any
  testql.sumd_parser.SumdParser._parse_interfaces → testql.sumd_parser._parse_block_interfaces
  testql.sumd_parser.SumdParser._parse_interfaces → testql.sumd_parser._parse_api_interfaces
  testql.commands.self_test_cmd.self_test → project.map.toon.run_self_test
  testql.commands.self_test_cmd.self_test → testql.commands.self_test_cmd._print_human
  testql.commands.discover_cmd.discover → testql.discovery.registry.discover_path
  testql.commands.generate_cmd._print_routes_section → testql.commands.generate_cmd._count_routes_by
  testql.commands.topology_cmd.topology → project.map.toon.build_topology
  testql.commands.topology_cmd.topology → testql.topology.serializers.render_topology
  testql.commands.misc_cmds.init → testql.commands.misc_cmds._create_templates
  testql.commands.misc_cmds.report → code2llm_output.map.toon.generate_report
  testql.commands.misc_cmds.echo → testql.commands.echo_helpers.render_echo
  testql.commands.misc_cmds.echo → testql.commands.echo_helpers.collect_toon_data
  testql.commands.run_ir_cmd.run_ir → testql.ir_runner.engine.run_plan
  testql.commands.run_ir_cmd.run_ir → testql.commands.run_ir_cmd._emit_json
  testql.commands.heal_scenario_cmd._collect_selectors → testql._base_fallback.VariableStore.set
  testql.commands.heal_scenario_cmd.heal_scenario → testql.commands.heal_scenario_cmd._collect_selectors
  testql.commands.heal_scenario_cmd._heal_with_elements → testql.generators.page_analyzer.pick_selector
  testql.commands.heal_scenario_cmd._heal_with_elements → testql.generators.page_analyzer.find_replacement
  testql.commands.heal_scenario_cmd._heal_with_elements → project.map.toon._toon_safe_selector
  testql.commands.heal_scenario_cmd._heal_with_browser → testql.generators.sources.page_source.extract_elements_from_page
  testql.commands.heal_scenario_cmd._heal_with_browser → testql.commands.heal_scenario_cmd._selector_resolves
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

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/oqlos/testql
# nodes: 505 | edges: 500 | modules: 104
# CC̄=2.3

HUBS[20]:
  examples.browser-inspection.run.print
    CC=0  in:48  out:0  total:48
  testql.results.serializers._render_toon
    CC=6  in:1  out:46  total:47
  .testql.generated.generated-from-pytests.testql.toon.any
    CC=0  in:34  out:0  total:34
  code2llm_output.map.toon.list
    CC=0  in:34  out:0  total:34
  testql.results.artifacts.write_inspection_artifacts
    CC=1  in:3  out:28  total:31
  testql.commands.heal_scenario_cmd.heal_scenario
    CC=8  in:0  out:30  total:30
  testql.interpreter._assertions.AssertionsMixin._cmd_assert_json
    CC=13  in:0  out:30  total:30
  testql.adapters.scenario_yaml._render_step
    CC=10  in:2  out:26  total:28
  testql._base_fallback.VariableStore.set
    CC=1  in:26  out:0  total:26
  testql.commands.generate_cmd._print_routes_section
    CC=10  in:1  out:23  total:24
  testql.commands.inspect_cmd.inspect
    CC=6  in:0  out:24  total:24
  testql.commands.generate_topology_cmd.generate_topology
    CC=5  in:0  out:24  total:24
  testql.commands.echo.parsers.doql._parse_workflows
    CC=7  in:1  out:22  total:23
  testql.adapters.scenario_yaml._gui_step
    CC=9  in:0  out:23  total:23
  testql.commands.encoder_routes._run_oql_lines
    CC=6  in:1  out:22  total:23
  testql.adapters.base.read_source
    CC=5  in:13  out:9  total:22
  testql.runner.parse_line
    CC=9  in:2  out:20  total:22
  testql.commands.misc_cmds.report
    CC=4  in:0  out:22  total:22
  testql.adapters.sql.fixtures.schema_fixture_from_rows
    CC=4  in:1  out:20  total:21
  testql.runner.DslCliExecutor.run_script
    CC=11  in:0  out:20  total:20

MODULES:
  .testql.generated.generated-from-pytests.testql.toon  [1 funcs]
    any  CC=0  out:0
  TODO.testtoon_parser  [2 funcs]
    print_parsed  CC=8  out:12
    validate  CC=2  out:2
  code2llm_output.map.toon  [12 funcs]
    _navigate_json_path  CC=0  out:0
    format_text_output  CC=0  out:0
    generate_context  CC=0  out:0
    generate_report  CC=0  out:0
    generate_sumd  CC=0  out:0
    list  CC=0  out:0
    parse_doql_file  CC=0  out:0
    parse_doql_less  CC=0  out:0
    parse_oql  CC=0  out:0
    parse_script  CC=0  out:0
  examples.api-testing.mock_server  [1 funcs]
    list_scenarios  CC=1  out:3
  examples.artifact-bundle.generate_bundle  [1 funcs]
    main  CC=2  out:10
  examples.browser-inspection.run  [1 funcs]
    print  CC=0  out:0
  project.map.toon  [5 funcs]
    _toon_safe_selector  CC=0  out:0
    available_sources  CC=0  out:0
    build_topology  CC=0  out:0
    get_source  CC=0  out:0
    run_self_test  CC=0  out:0
  testql._base_fallback  [3 funcs]
    emit  CC=2  out:2
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
  testql.adapters.proto.message_validator  [8 funcs]
    _missing_required  CC=4  out:1
    _row_issues  CC=3  out:4
    _validate_field_known  CC=2  out:2
    _validate_field_type  CC=3  out:2
    _validate_field_value  CC=3  out:2
    coerce_scalar  CC=5  out:6
    round_trip_equal  CC=6  out:4
    validate_message_instance  CC=5  out:7
  testql.adapters.proto.proto_adapter  [6 funcs]
    _apply_section  CC=2  out:6
    _h_message  CC=1  out:3
    _h_proto  CC=1  out:4
    _message_section  CC=5  out:8
    _proto_section  CC=3  out:7
    _toon_to_plan  CC=4  out:7
  testql.adapters.registry  [2 funcs]
    all  CC=1  out:2
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
  testql.discovery.probes.filesystem.container_dockerfile  [1 funcs]
    _metadata  CC=4  out:10
  testql.discovery.probes.filesystem.package_python  [15 funcs]
    _confidence  CC=10  out:4
    _find_python_files  CC=7  out:6
    _read_metadata  CC=8  out:13
    _call_kw  CC=2  out:3
    _dedupe_deps  CC=4  out:5
    _dep  CC=3  out:4
    _excluded  CC=2  out:1
    _parse_pyproject  CC=7  out:12
    _parse_pyproject_dependencies  CC=6  out:15
    _parse_requirements  CC=4  out:5
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
  testql.generators.analyzers  [2 funcs]
    _detect_hardware  CC=3  out:2
    _detect_python_type  CC=7  out:4
  testql.generators.api_generator  [1 funcs]
    _deduplicate_rest_routes  CC=4  out:3
  testql.generators.base  [1 funcs]
    _should_exclude_path  CC=1  out:3
  testql.generators.multi  [2 funcs]
    discover_projects  CC=6  out:6
    generate_cross_project_tests  CC=3  out:11
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
  testql.ir.metadata  [1 funcs]
    to_dict  CC=3  out:2
  testql.ir_runner.engine  [1 funcs]
    run_plan  CC=1  out:2
  testql.openapi_generator  [5 funcs]
    _load_spec  CC=2  out:3
    _extract_parameters  CC=1  out:3
    _infer_tags  CC=7  out:9
    _extract_ep_params  CC=7  out:8
    _extract_path_params  CC=4  out:4
  testql.pipeline  [1 funcs]
    _is_workspace  CC=5  out:5
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
  examples.api-testing.mock_server.list_scenarios → code2llm_output.map.toon.list
  TODO.testtoon_parser.print_parsed → examples.browser-inspection.run.print
  TODO.testtoon_parser.print_parsed → TODO.testtoon_parser.validate
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
  testql.pipeline.GenerationPipeline._is_workspace → .testql.generated.generated-from-pytests.testql.toon.any
  testql.sumd_parser.SumdParser._parse_interfaces → testql.sumd_parser._parse_block_interfaces
  testql.sumd_parser.SumdParser._parse_interfaces → testql.sumd_parser._parse_api_interfaces
  testql.commands.self_test_cmd.self_test → project.map.toon.run_self_test
  testql.commands.self_test_cmd.self_test → testql.commands.self_test_cmd._print_human
  testql.commands.discover_cmd.discover → testql.discovery.registry.discover_path
  testql.commands.generate_cmd._print_routes_section → testql.commands.generate_cmd._count_routes_by
  testql.commands.topology_cmd.topology → project.map.toon.build_topology
  testql.commands.topology_cmd.topology → testql.topology.serializers.render_topology
  testql.commands.misc_cmds.init → testql.commands.misc_cmds._create_templates
  testql.commands.misc_cmds.report → code2llm_output.map.toon.generate_report
  testql.commands.misc_cmds.echo → testql.commands.echo_helpers.render_echo
  testql.commands.misc_cmds.echo → testql.commands.echo_helpers.collect_toon_data
  testql.commands.run_ir_cmd.run_ir → testql.ir_runner.engine.run_plan
  testql.commands.run_ir_cmd.run_ir → testql.commands.run_ir_cmd._emit_json
  testql.commands.heal_scenario_cmd._collect_selectors → testql._base_fallback.VariableStore.set
  testql.commands.heal_scenario_cmd.heal_scenario → testql.commands.heal_scenario_cmd._collect_selectors
  testql.commands.heal_scenario_cmd._heal_with_elements → testql.generators.page_analyzer.pick_selector
  testql.commands.heal_scenario_cmd._heal_with_elements → testql.generators.page_analyzer.find_replacement
  testql.commands.heal_scenario_cmd._heal_with_elements → project.map.toon._toon_safe_selector
  testql.commands.heal_scenario_cmd._heal_with_browser → testql.generators.sources.page_source.extract_elements_from_page
  testql.commands.heal_scenario_cmd._heal_with_browser → testql.commands.heal_scenario_cmd._selector_resolves
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 448f 73172L | python:230,yaml:152,shell:23,json:18,txt:4,yml:2,doql:1,toml:1 | 2026-04-29
# CC̄=2.3 | critical:1/2190 | dups:0 | cycles:0

HEALTH[1]:
  🟡 CC    _parse_makefile CC=23 (limit:15)

REFACTOR[1]:
  1. split 1 high-CC methods  (CC>15)

PIPELINES[759]:
  [1] Src [main]: main → print
      PURITY: 100% pure
  [2] Src [health]: health
      PURITY: 100% pure
  [3] Src [devices]: devices
      PURITY: 100% pure
  [4] Src [list_scenarios]: list_scenarios → list
      PURITY: 100% pure
  [5] Src [create_scenario]: create_scenario
      PURITY: 100% pure

LAYERS:
  TODO/                           CC̄=5.9    ←in:0  →out:8  !! split
  │ testtoon_parser            141L  1C    7m  CC=14     ←0
  │
  testql/                         CC̄=3.7    ←in:35  →out:27  !! split
  │ !! _gui                       708L  1C   34m  CC=12     ←0
  │ !! page_analyzer              526L  1C   31m  CC=10     ←3
  │ !! scenario_yaml              506L  1C   43m  CC=13     ←1
  │ !! analyzer                   504L  0C   38m  CC=14     ←3
  │ !! testtoon_adapter           501L  1C   33m  CC=10     ←0
  │ encoder_routes             477L  0C   27m  CC=10     ←0
  │ _testtoon_parser           468L  0C   19m  CC=14     ←0
  │ openapi_generator          444L  3C   21m  CC=11     ←1
  │ dom_scanner                418L  1C   26m  CC=13     ←0
  │ pytest_source              389L  3C   13m  CC=13     ←0
  │ runner                     371L  3C   18m  CC=12     ←0
  │ nl_adapter                 353L  1C   30m  CC=7      ←0
  │ sql_adapter                333L  1C   26m  CC=8      ←3
  │ analyzers                  309L  1C   16m  CC=10     ←0
  │ heal_scenario_cmd          307L  1C    9m  CC=8      ←0
  │ oql_source                 306L  1C   22m  CC=10     ←0
  │ _assertions                304L  1C    7m  CC=13     ←0
  │ dom_scan_mixin             302L  1C    9m  CC=14     ←0
  │ api_generator              295L  2C   19m  CC=10     ←0
  │ misc_cmds                  292L  0C    7m  CC=6      ←0
  │ testtoon_parser            289L  0C   21m  CC=9      ←0
  │ _api_runner                288L  1C   16m  CC=10     ←1
  │ !! config_source              288L  1C   10m  CC=23     ←0
  │ sumd_parser                277L  5C   12m  CC=11     ←0
  │ graphql_adapter            273L  1C   23m  CC=6      ←0
  │ _unit                      267L  1C   10m  CC=10     ←0
  │ oql_parser                 267L  1C   20m  CC=7      ←0
  │ steps                      251L  11C   21m  CC=8      ←0
  │ report_generator           250L  4C    8m  CC=5      ←0
  │ _shell                     243L  1C    6m  CC=14     ←0
  │ proto_adapter              242L  1C   18m  CC=6      ←0
  │ generator                  241L  2C   17m  CC=8      ←0
  │ unified                    239L  1C   12m  CC=13     ←0
  │ _base_fallback             232L  7C   26m  CC=4      ←23
  │ ddl_parser                 228L  3C   17m  CC=7      ←2
  │ mutator                    219L  2C   12m  CC=6      ←0
  │ config_detector            211L  1C    7m  CC=14     ←0
  │ sumd_generator             208L  0C   11m  CC=7      ←0
  │ auto_cmd                   202L  0C    9m  CC=9      ←0
  │ package_python             200L  1C   19m  CC=10     ←0
  │ message_validator          187L  2C   11m  CC=7      ←1
  │ manifest                   173L  6C   12m  CC=10     ←1
  │ coverage_analyzer          173L  1C   15m  CC=6      ←0
  │ doql_parser                172L  1C    9m  CC=6      ←0
  │ _websockets                172L  1C    8m  CC=8      ←0
  │ page_source                172L  1C    6m  CC=4      ←1
  │ generate_cmd               171L  0C    9m  CC=10     ←0
  │ specialized_generator      170L  1C    5m  CC=1      ←0
  │ content                    166L  1C    9m  CC=2      ←1
  │ _flow                      165L  1C    6m  CC=9      ←0
  │ descriptor_loader          162L  3C   13m  CC=5      ←3
  │ http_endpoint              160L  2C   15m  CC=10     ←1
  │ run_cmd                    160L  0C    6m  CC=10     ←1
  │ server                     159L  1C    7m  CC=4      ←1
  │ interpreter                158L  1C    7m  CC=8      ←0
  │ echo_schemas               153L  6C    2m  CC=8      ←0
  │ fastapi_detector           153L  1C   12m  CC=6      ←0
  │ _validation                153L  1C    3m  CC=11     ←0
  │ registry                   150L  1C   13m  CC=9      ←1
  │ generate-test-reports.testql.toon.yaml   150L  0C    0m  CC=0.0    ←0
  │ playwright_page            147L  1C    6m  CC=10     ←0
  │ pytest_generator           147L  1C    9m  CC=7      ←0
  │ pipeline                   145L  2C    7m  CC=7      ←1
  │ artifacts                  144L  0C    4m  CC=10     ←3
  │ compatibility              143L  2C    8m  CC=6      ←0
  │ models                     140L  5C    6m  CC=5      ←1
  │ endpoints_cmd              136L  0C    6m  CC=9      ←0
  │ engine                     136L  1C    7m  CC=9      ←1
  │ schema_introspection       135L  1C    7m  CC=5      ←1
  │ assertion_eval             124L  1C    7m  CC=6      ←2
  │ collection                 122L  0C    8m  CC=6      ←1
  │ flask_detector             121L  1C    9m  CC=6      ←0
  │ sitemap                    119L  1C   12m  CC=9      ←0
  │ doql                       115L  0C    9m  CC=7      ←0
  │ entity_extractor           115L  0C   11m  CC=7      ←0
  │ planfile_hook              115L  0C    2m  CC=9      ←1
  │ listing                    114L  0C    6m  CC=7      ←1
  │ serializers                112L  0C    8m  CC=7      ←2
  │ run-all-views.testql.toon.yaml   112L  0C    0m  CC=0.0    ←0
  │ toon_parser                110L  1C    7m  CC=4      ←0
  │ _hardware                  110L  1C    4m  CC=8      ←0
  │ grammar                    107L  1C    7m  CC=5      ←2
  │ multi                      105L  1C    5m  CC=6      ←0
  │ fixtures                   105L  2C    7m  CC=5      ←1
  │ models                     105L  5C    6m  CC=6      ←0
  │ pl.yaml                    103L  0C    0m  CC=0.0    ←0
  │ cli                        102L  0C    5m  CC=4      ←0
  │ cli                        100L  0C    2m  CC=13     ←0
  │ _encoder                   100L  1C   13m  CC=9      ←0
  │ generate_from_page_cmd      99L  0C    2m  CC=8      ←0
  │ intent_recognizer           99L  1C    3m  CC=6      ←1
  │ base                        97L  3C    5m  CC=5      ←7
  │ text                        95L  0C    7m  CC=6      ←0
  │ pipeline                    95L  1C    6m  CC=5      ←4
  │ query_parser                95L  1C    5m  CC=5      ←0
  │ confidence_scorer           94L  2C    7m  CC=4      ←0
  │ parsers                     93L  0C    6m  CC=11     ←9
  │ openapi_source              93L  1C    5m  CC=7      ←0
  │ en.yaml                     93L  0C    0m  CC=0.0    ←0
  │ __init__                    91L  0C    1m  CC=8      ←0
  │ proto_source                90L  1C    5m  CC=5      ←0
  │ openapi_detector            90L  1C    3m  CC=9      ←0
  │ reports                     89L  0C    5m  CC=6      ←1
  │ dialect_resolver            88L  1C    4m  CC=4      ←3
  │ scenario_generator          87L  1C    2m  CC=13     ←0
  │ graphql_detector            87L  1C    3m  CC=5      ←0
  │ proto                       87L  0C    4m  CC=6      ←0
  │ dispatcher                  86L  1C    6m  CC=5      ←1
  │ dom_scan_formatters         84L  0C    4m  CC=13     ←1
  │ ui_source                   81L  1C    5m  CC=5      ←0
  │ junit                       79L  1C    3m  CC=8      ←0
  │ sql_source                  79L  1C    4m  CC=5      ←0
  │ encoder                     77L  0C    3m  CC=5      ←0
  │ toon                        76L  0C    4m  CC=5      ←0
  │ query_executor              76L  0C    5m  CC=6      ←1
  │ test-device-flow.testql.toon.yaml    76L  0C    0m  CC=0.0    ←0
  │ __init__                    75L  0C    3m  CC=4      ←0
  │ execution                   73L  0C    2m  CC=5      ←1
  │ api_openapi                 72L  1C    5m  CC=9      ←1
  │ base                        70L  3C    8m  CC=4      ←0
  │ test-gui-connect-id.testql.toon.yaml    70L  0C    0m  CC=0.0    ←0
  │ echo_helpers                68L  0C    4m  CC=8      ←1
  │ base                        68L  1C    7m  CC=5      ←10
  │ api                         67L  0C    5m  CC=4      ←0
  │ graphql_source              66L  1C    4m  CC=5      ←0
  │ __init__                    66L  0C    0m  CC=0.0    ←0
  │ full-diagnostic.testql.toon.yaml    66L  0C    0m  CC=0.0    ←0
  │ run_ir_cmd                  65L  0C    3m  CC=3      ←0
  │ sql                         65L  0C    4m  CC=5      ←0
  │ test-gui-connect-workshop.testql.toon.yaml    65L  0C    0m  CC=0.0    ←0
  │ renderer                    64L  0C    4m  CC=7      ←1
  │ pytest_target               64L  1C    4m  CC=5      ←0
  │ endpoint_detector           62L  0C    0m  CC=0.0    ←0
  │ _converter                  62L  0C    0m  CC=0.0    ←0
  │ generator                   61L  0C    0m  CC=0.0    ←0
  │ test-gui-connect-test.testql.toon.yaml    61L  0C    0m  CC=0.0    ←0
  │ models                      60L  2C    2m  CC=2      ←0
  │ registry                    59L  1C    6m  CC=5      ←1
  │ base                        59L  3C    3m  CC=1      ←0
  │ express_detector            59L  1C    3m  CC=5      ←0
  │ graphql                     59L  0C    3m  CC=5      ←0
  │ templates                   59L  0C    0m  CC=0.0    ←0
  │ generate_topology_cmd       58L  0C    2m  CC=5      ←0
  │ core                        58L  0C    3m  CC=5      ←0
  │ create-todays-reports.testql.toon.yaml    58L  0C    0m  CC=0.0    ←0
  │ context                     54L  0C    3m  CC=4      ←0
  │ package_node                54L  1C    2m  CC=14     ←0
  │ __init__                    53L  0C    1m  CC=2      ←0
  │ dom_scan_models             53L  4C    0m  CC=0.0    ←0
  │ __init__                    53L  0C    0m  CC=0.0    ←0
  │ __init__                    52L  0C    0m  CC=0.0    ←0
  │ recorded-test-session.testql.toon.yaml    52L  0C    0m  CC=0.0    ←0
  │ convenience                 51L  0C    2m  CC=1      ←0
  │ django_detector             51L  1C    2m  CC=4      ←0
  │ __init__                    51L  0C    3m  CC=1      ←1
  │ serializers                 51L  0C    3m  CC=5      ←3
  │ __init__                    50L  0C    0m  CC=0.0    ←0
  │ __init__                    50L  0C    0m  CC=0.0    ←0
  │ test-gui-connect-config.testql.toon.yaml    50L  0C    0m  CC=0.0    ←0
  │ generate_ir_cmd             49L  0C    2m  CC=2      ←0
  │ dispatcher                  49L  0C    1m  CC=3      ←0
  │ llm_fallback                49L  3C    4m  CC=1      ←1
  │ connect-reports-year.testql.toon.yaml    49L  0C    0m  CC=0.0    ←0
  │ websocket_detector          48L  1C    2m  CC=3      ←0
  │ test-gui-connect-reports.testql.toon.yaml    48L  0C    0m  CC=0.0    ←0
  │ __init__                    48L  0C    0m  CC=0.0    ←0
  │ encoder                     47L  0C    3m  CC=5      ←0
  │ test-gui-connect-manager.testql.toon.yaml    47L  0C    0m  CC=0.0    ←0
  │ discover_cmd                46L  0C    2m  CC=9      ←0
  │ shell                       46L  0C    3m  CC=5      ←0
  │ self_test_cmd               45L  0C    2m  CC=4      ←0
  │ session-recording.testql.toon.yaml    45L  0C    0m  CC=0.0    ←0
  │ connect-reports-month.testql.toon.yaml    45L  0C    0m  CC=0.0    ←0
  │ container_compose           44L  1C    3m  CC=9      ←0
  │ connect-id-rfid.testql.toon.yaml    44L  0C    0m  CC=0.0    ←0
  │ connect-reports-week.testql.toon.yaml    43L  0C    0m  CC=0.0    ←0
  │ plan                        42L  1C    1m  CC=3      ←0
  │ context                     42L  1C    1m  CC=1      ←0
  │ unit                        42L  0C    2m  CC=6      ←0
  │ connect-reports-quarter.testql.toon.yaml    42L  0C    0m  CC=0.0    ←0
  │ connect-reports-chart.testql.toon.yaml    42L  0C    0m  CC=0.0    ←0
  │ container_dockerfile        41L  1C    3m  CC=6      ←0
  │ __init__                    41L  0C    0m  CC=0.0    ←0
  │ test-encoder.testql.toon.yaml    41L  0C    0m  CC=0.0    ←0
  │ subscription_runner         40L  1C    1m  CC=1      ←0
  │ _dom_scan                   40L  0C    0m  CC=0.0    ←0
  │ test-mixed-workflow.testql.toon.yaml    40L  0C    0m  CC=0.0    ←0
  │ cli                         39L  0C    1m  CC=3      ←0
  │ flow                        39L  0C    1m  CC=3      ←0
  │ connect-reports-custom.testql.toon.yaml    39L  0C    0m  CC=0.0    ←0
  │ console                     38L  0C    1m  CC=6      ←0
  │ __init__                    38L  0C    2m  CC=3      ←1
  │ captures                    37L  1C    1m  CC=1      ←0
  │ base                        37L  0C    0m  CC=0.0    ←0
  │ connect-manager-scenarios.testql.toon.yaml    37L  0C    0m  CC=0.0    ←0
  │ __init__                    36L  0C    2m  CC=2      ←3
  │ __init__                    35L  0C    0m  CC=0.0    ←0
  │ inspect_cmd                 34L  0C    1m  CC=6      ←0
  │ assertions                  34L  0C    1m  CC=9      ←1
  │ base                        34L  1C    3m  CC=6      ←0
  │ __init__                    34L  0C    0m  CC=0.0    ←0
  │ connect-id-qr.testql.toon.yaml    34L  0C    0m  CC=0.0    ←0
  │ _parser                     33L  2C    1m  CC=5      ←0
  │ fixtures                    33L  1C    1m  CC=1      ←0
  │ assertions                  33L  1C    1m  CC=3      ←0
  │ source                      33L  2C    2m  CC=4      ←1
  │ json_reporter               33L  0C    1m  CC=2      ←0
  │ testtoon_models             33L  2C    1m  CC=3      ←0
  │ __init__                    33L  0C    0m  CC=0.0    ←0
  │ navigate                    32L  0C    1m  CC=6      ←0
  │ base                        32L  1C    1m  CC=1      ←0
  │ coverage_optimizer          32L  3C    2m  CC=1      ←0
  │ api                         31L  0C    1m  CC=6      ←0
  │ metadata                    31L  1C    1m  CC=3      ←0
  │ gui                         30L  0C    1m  CC=2      ←0
  │ oql_models                  30L  2C    0m  CC=0.0    ←0
  │ __init__                    30L  0C    0m  CC=0.0    ←0
  │ generators                  30L  0C    0m  CC=0.0    ←0
  │ interpolation               29L  0C    1m  CC=6      ←7
  │ test-app-lifecycle.testql.toon.yaml    29L  0C    0m  CC=0.0    ←0
  │ nl_source                   27L  1C    1m  CC=2      ←0
  │ select                      26L  0C    1m  CC=3      ←0
  │ edge_case_generator         26L  2C    2m  CC=1      ←0
  │ reproduce-view.testql.toon.yaml    26L  0C    0m  CC=0.0    ←0
  │ test-gui-all.testql.toon.yaml    26L  0C    0m  CC=0.0    ←0
  │ __init__                    25L  0C    0m  CC=0.0    ←0
  │ connect-config-users.testql.toon.yaml    25L  0C    0m  CC=0.0    ←0
  │ record                      24L  0C    2m  CC=1      ←0
  │ nl                          24L  0C    1m  CC=1      ←0
  │ test-protocol-flow.testql.toon.yaml    24L  0C    0m  CC=0.0    ←0
  │ topology_cmd                23L  0C    1m  CC=3      ←0
  │ testtoon_target             23L  1C    1m  CC=1      ←0
  │ connect-test-testing-search.testql.toon.yaml    23L  0C    0m  CC=0.0    ←0
  │ connect-test-protocols.testql.toon.yaml    23L  0C    0m  CC=0.0    ←0
  │ connect-test-devices-search.testql.toon.yaml    23L  0C    0m  CC=0.0    ←0
  │ wait                        22L  0C    1m  CC=4      ←0
  │ nl_target                   22L  1C    1m  CC=1      ←0
  │ __init__                    22L  0C    0m  CC=0.0    ←0
  │ backend-diagnostic.testql.toon.yaml    22L  0C    0m  CC=0.0    ←0
  │ connect-id-barcode.testql.toon.yaml    22L  0C    0m  CC=0.0    ←0
  │ connect-workshop-requests-search.testql.toon.yaml    22L  0C    0m  CC=0.0    ←0
  │ connect-manager-activities.testql.toon.yaml    22L  0C    0m  CC=0.0    ←0
  │ connect-id-list.testql.toon.yaml    22L  0C    0m  CC=0.0    ←0
  │ connect-config-labels.testql.toon.yaml    22L  0C    0m  CC=0.0    ←0
  │ connect-manager-intervals.testql.toon.yaml    22L  0C    0m  CC=0.0    ←0
  │ connect-workshop-services-search.testql.toon.yaml    22L  0C    0m  CC=0.0    ←0
  │ base                        21L  1C    1m  CC=1      ←1
  │ connect-config-settings.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │ connect-test-testing-rfid.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │ connect-config-tables.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │ connect-reports-filter.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │ connect-id-barcode.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │ connect-config-users.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │ connect-config-feature-flags.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │ connect-id-manual.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │ connect-test-full-test.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │ connect-workshop-transport-search.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │ connect-config-theme.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │ connect-workshop-dispositions-search.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │ __init__                    21L  0C    0m  CC=0.0    ←0
  │ models                      20L  2C    0m  CC=0.0    ←0
  │ __init__                    20L  0C    0m  CC=0.0    ←0
  │ connect-test-testing-barcode.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │ connect-manager-library.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │ connect-test-scenario-view.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │ connect-test-testing-qr.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │ connect-manager-test-types.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │ __init__                    19L  0C    0m  CC=0.0    ←0
  │ encoder-workshop.testql.toon.yaml    19L  0C    0m  CC=0.0    ←0
  │ device-identification.testql.toon.yaml    19L  0C    0m  CC=0.0    ←0
  │ unknown                     18L  0C    1m  CC=3      ←1
  │ __init__                    18L  0C    0m  CC=0.0    ←0
  │ test-api.testql.toon.yaml    17L  0C    0m  CC=0.0    ←0
  │ __init__                    16L  0C    0m  CC=0.0    ←0
  │ connect-workshop-transport.testql.toon.yaml    16L  0C    0m  CC=0.0    ←0
  │ __init__                    15L  0C    0m  CC=0.0    ←0
  │ encoder-navigation.testql.toon.yaml    15L  0C    0m  CC=0.0    ←0
  │ include                     14L  0C    1m  CC=1      ←0
  │ __init__                    14L  0C    0m  CC=0.0    ←0
  │ api-crud-template.testql.toon.yaml    14L  0C    0m  CC=0.0    ←0
  │ test-ui-navigation.testql.toon.yaml    13L  0C    0m  CC=0.0    ←0
  │ suite_cmd                   12L  0C    0m  CC=0.0    ←0
  │ test-dsl-objects.testql.toon.yaml    12L  0C    0m  CC=0.0    ←0
  │ health-check.testql.toon.yaml    12L  0C    0m  CC=0.0    ←0
  │ api-smoke.testql.toon.yaml    11L  0C    0m  CC=0.0    ←0
  │ run-mask-test-protocol.testql.toon.yaml    11L  0C    0m  CC=0.0    ←0
  │ quick-navigation.testql.toon.yaml    11L  0C    0m  CC=0.0    ←0
  │ auth-login.testql.toon.yaml    11L  0C    0m  CC=0.0    ←0
  │ __init__                    10L  0C    0m  CC=0.0    ←0
  │ test-devices-crud.testql.toon.yaml    10L  0C    0m  CC=0.0    ←0
  │ test-devices-crud.testql.toon.yaml    10L  0C    0m  CC=0.0    ←0
  │ __init__                     9L  0C    0m  CC=0.0    ←0
  │ test-protocol-flow.testql.toon.yaml     9L  0C    0m  CC=0.0    ←0
  │ __init__                     9L  0C    0m  CC=0.0    ←0
  │ __init__                     8L  0C    0m  CC=0.0    ←0
  │ __init__                     7L  0C    0m  CC=0.0    ←0
  │ api-health.testql.toon.yaml     7L  0C    0m  CC=0.0    ←0
  │ __main__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     0L  0C    0m  CC=0.0    ←0
  │ autoloop_runner              0L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=0.9    ←in:0  →out:0
  │ !! topology.json             5012L  0C    0m  CC=0.0    ←0
  │ !! inspection.yaml           3796L  0C    0m  CC=0.0    ←0
  │ !! inspection.yaml           3796L  0C    0m  CC=0.0    ←0
  │ !! topology.yaml             3324L  0C    0m  CC=0.0    ←0
  │ !! result.json                534L  0C    0m  CC=0.0    ←0
  │ !! result.json                534L  0C    0m  CC=0.0    ←0
  │ topology.toon.yaml         246L  0C    0m  CC=0.0    ←0
  │ topology.toon.yaml         246L  0C    0m  CC=0.0    ←0
  │ run-matrix.sh              101L  0C    0m  CC=0.0    ←0
  │ run.sh                      72L  0C    0m  CC=0.0    ←0
  │ run-all.sh                  71L  0C    1m  CC=0.0    ←0
  │ refactor-plan.yaml          69L  0C    0m  CC=0.0    ←0
  │ refactor-plan.yaml          69L  0C    0m  CC=0.0    ←0
  │ run.sh                      64L  0C    1m  CC=0.0    ←11
  │ mock_server                 50L  0C    8m  CC=2      ←0
  │ run.sh                      42L  0C    1m  CC=0.0    ←0
  │ crud-workflow.testql.yaml    42L  0C    0m  CC=0.0    ←0
  │ app.doql                    41L  0C    0m  CC=0.0    ←0
  │ run.sh                      37L  0C    0m  CC=0.0    ←0
  │ generate_bundle             36L  0C    1m  CC=2      ←0
  │ metadata.json               35L  0C    0m  CC=0.0    ←0
  │ metadata.json               35L  0C    0m  CC=0.0    ←0
  │ login-form.testql.yaml      34L  0C    0m  CC=0.0    ←0
  │ inspection.toon.yaml        34L  0C    0m  CC=0.0    ←0
  │ inspection.toon.yaml        34L  0C    0m  CC=0.0    ←0
  │ mixed-smoke.testql.yaml     33L  0C    0m  CC=0.0    ←0
  │ result.toon.yaml            31L  0C    0m  CC=0.0    ←0
  │ result.toon.yaml            31L  0C    0m  CC=0.0    ←0
  │ run.sh                      27L  0C    0m  CC=0.0    ←0
  │ basic-encoder.testql.yaml    23L  0C    0m  CC=0.0    ←0
  │ run.sh                      23L  0C    0m  CC=0.0    ←0
  │ run.sh                      22L  0C    0m  CC=0.0    ←0
  │ run.sh                      22L  0C    0m  CC=0.0    ←0
  │ run.sh                      22L  0C    0m  CC=0.0    ←0
  │ run.sh                      21L  0C    0m  CC=0.0    ←0
  │ mixed-smoke.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │ inspect-web.sh              20L  0C    0m  CC=0.0    ←0
  │ login-form.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │ health-check.testql.yaml    19L  0C    0m  CC=0.0    ←0
  │ run.sh                      18L  0C    0m  CC=0.0    ←0
  │ topology.sh                 18L  0C    0m  CC=0.0    ←0
  │ run.sh                      17L  0C    0m  CC=0.0    ←0
  │ api-contract.testql.toon.yaml    17L  0C    0m  CC=0.0    ←0
  │ run.sh                      16L  0C    0m  CC=0.0    ←0
  │ crud-workflow.testql.toon.yaml    15L  0C    0m  CC=0.0    ←0
  │ assertions.testql.toon.yaml    14L  0C    0m  CC=0.0    ←0
  │ discover-local.sh           14L  0C    0m  CC=0.0    ←0
  │ refactor-plan.toon.yaml     14L  0C    0m  CC=0.0    ←0
  │ refactor-plan.toon.yaml     14L  0C    0m  CC=0.0    ←0
  │ variables.testql.toon.yaml    13L  0C    0m  CC=0.0    ←0
  │ health-check.testql.toon.yaml    13L  0C    0m  CC=0.0    ←0
  │ run.sh                      13L  0C    0m  CC=0.0    ←0
  │ basic-commands.testql.yaml    12L  0C    0m  CC=0.0    ←0
  │ basic-encoder.testql.toon.yaml    11L  0C    0m  CC=0.0    ←0
  │ basic-commands.testql.toon.yaml     7L  0C    0m  CC=0.0    ←0
  │ minimal.testql.toon.yaml     7L  0C    0m  CC=0.0    ←0
  │ routes.txt                   3L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │
  code2llm_output/                CC̄=0.0    ←in:0  →out:0
  │ !! calls.yaml                 799L  0C    0m  CC=0.0    ←0
  │ map.toon.yaml              258L  0C   83m  CC=0.0    ←33
  │ analysis.toon.yaml          93L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         82L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  47L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml            9L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=0.0    ←in:0  →out:0
  │ install_testql_autoloop.sh   156L  0C    2m  CC=0.0    ←0
  │ setup_mcp_windsurf.sh       91L  0C    1m  CC=0.0    ←0
  │ smoke_manifest_flow.sh      70L  0C    1m  CC=0.0    ←0
  │
  .testql/                        CC̄=0.0    ←in:34  →out:0
  │ !! inspection.json           5644L  0C    0m  CC=0.0    ←0
  │ !! topology.json              672L  0C    0m  CC=0.0    ←0
  │ !! generated-from-pytests.testql.toon.yaml   626L  0C    2m  CC=0.0    ←20
  │ !! result.json                534L  0C    0m  CC=0.0    ←0
  │ topology.toon.yaml         246L  0C    0m  CC=0.0    ←0
  │ llm-decision.schema.json   113L  0C    0m  CC=0.0    ←0
  │ refactor-plan.yaml          69L  0C    0m  CC=0.0    ←0
  │ autoloop-state.json         58L  0C    0m  CC=0.0    ←0
  │ llm-decision.swe.json       49L  0C    0m  CC=0.0    ←0
  │ llm-decision.kimi.json      41L  0C    0m  CC=0.0    ←0
  │ generated-from-scenarios.testql.toon.yaml    40L  0C    0m  CC=0.0    ←0
  │ metadata.json               36L  0C    0m  CC=0.0    ←0
  │ inspection.toon.yaml        34L  0C    0m  CC=0.0    ←0
  │ result.toon.yaml            31L  0C    0m  CC=0.0    ←0
  │ llm-decision.json           27L  0C    0m  CC=0.0    ←0
  │ generated-api-smoke.testql.toon.yaml    18L  0C    0m  CC=0.0    ←0
  │ generated-api-integration.testql.toon.yaml    18L  0C    0m  CC=0.0    ←0
  │ refactor-plan.toon.yaml     14L  0C    0m  CC=0.0    ←0
  │ iteration.json               2L  0C    0m  CC=0.0    ←0
  │
  project/                        CC̄=0.0    ←in:0  →out:0
  │ !! calls.yaml                7392L  0C    0m  CC=0.0    ←0
  │ !! map.toon.yaml             2232L  0C  713m  CC=0.0    ←8
  │ !! calls.toon.yaml            597L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml         493L  0C    0m  CC=0.0    ←0
  │ validation.toon.yaml       421L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml           54L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         54L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  47L  0C    0m  CC=0.0    ←0
  │ duplication.toon.yaml        9L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! planfile.yaml             1319L  0C    0m  CC=0.0    ←0
  │ !! tree.txt                   804L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  511L  0C    0m  CC=0.0    ←0
  │ sumd.json                  204L  0C    0m  CC=0.0    ←0
  │ Taskfile.yml               185L  0C    0m  CC=0.0    ←0
  │ openapi.yaml               175L  0C    0m  CC=0.0    ←0
  │ Taskfile.testql.yml        117L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                91L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              88L  0C    0m  CC=0.0    ←0
  │ pyqual.yaml                 71L  0C    0m  CC=0.0    ←0
  │ project.sh                  50L  0C    0m  CC=0.0    ←0
  │ coverage.json                1L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-api-smoke.testql.toon.yaml    35L  0C    0m  CC=0.0    ←0
  │ generated-sitemap-assert.testql.toon.yaml    29L  0C    0m  CC=0.0    ←0
  │ generated-from-pytests.testql.toon.yaml    23L  0C    0m  CC=0.0    ←0
  │ generated-asset-assert.testql.toon.yaml    23L  0C    0m  CC=0.0    ←0
  │ generated-cli-extended.testql.toon.yaml    23L  0C    0m  CC=0.0    ←0
  │ orders-sqlite.sql.testql.yaml    22L  0C    0m  CC=0.0    ←0
  │ users-contract.sql.testql.yaml    21L  0C    0m  CC=0.0    ←0
  │ orders-mutations.graphql.testql.yaml    20L  0C    0m  CC=0.0    ←0
  │ generated-api-integration.testql.toon.yaml    18L  0C    0m  CC=0.0    ←0
  │ orders-events.proto.testql.yaml    16L  0C    0m  CC=0.0    ←0
  │ user-contract.proto.testql.yaml    15L  0C    0m  CC=0.0    ←0
  │ user-contract.graphql.testql.yaml    13L  0C    0m  CC=0.0    ←0
  │ generated-cli-tests.testql.toon.yaml    12L  0C    0m  CC=0.0    ←0
  │
  scenarios/                      CC̄=0.0    ←in:0  →out:0
  │ encoder-gui-full-flow.testql.toon.yaml   136L  0C    0m  CC=0.0    ←0
  │ encoder-gui-terminal.testql.toon.yaml    82L  0C    0m  CC=0.0    ←0
  │ c2004-all-modules-api.testql.toon.yaml    71L  0C    0m  CC=0.0    ←0
  │ encoder-terminal-cli.testql.toon.yaml    51L  0C    0m  CC=0.0    ←0
  │ encoder-navigation.testql.toon.yaml    50L  0C    0m  CC=0.0    ←0
  │ encoder-cli-hardware-sim.testql.toon.yaml    47L  0C    0m  CC=0.0    ←0
  │ encoder-connect-test-devices-admin-pl.testql.toon.yaml    29L  0C    0m  CC=0.0    ←0
  │
  .windsurf/                      CC̄=0.0    ←in:0  →out:0
  │ mcp_config.json             14L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     Makefile                                  0L
     examples/Makefile                         0L
     examples/api-testing/Makefile             0L
     examples/artifact-bundle/Makefile         0L
     examples/browser-inspection/Makefile      0L
     examples/discovery/Makefile               0L
     examples/encoder-testing/Makefile         0L
     examples/flow-control/Makefile            0L
     examples/gui-testing/Makefile             0L
     examples/project-echo/Makefile            0L
     examples/shell-testing/Makefile           0L
     examples/testtoon-basics/Makefile         0L
     examples/topology/Makefile                0L
     examples/unit-testing/Makefile            0L
     examples/web-inspection-dot-testql/Makefile  0L
     examples/web-inspection/Makefile          0L
     examples/web-inspection/c2004-localhost/Makefile  0L
     testql/autoloop_runner.py                 0L
     testql/runners/__init__.py                0L

COUPLING:
                                                    testql              testql.commands          code2llm_output.map  examples.browser-inspection            testql.generators                      .testql              testql.adapters               testql.results           testql.interpreter             testql.discovery                  project.map          testql.integrations             testql.ir_runner                   testql.mcp              testql.topology
                       testql                           ──                           ←8                            2                           22                           ←6                            2                           ←5                                                        ←3                           ←6                                                                                     ←2                            1                               hub
              testql.commands                            8                           ──                           13                            3                            9                            5                                                         7                                                         1                            6                            1                            1                           ←2                            1  !! fan-out
          code2llm_output.map                           ←2                          ←13                           ──                                                        ←5                                                        ←8                           ←8                           ←7                           ←2                                                                                                                                               ←2  hub
  examples.browser-inspection                          ←22                           ←3                                                        ──                                                                                                                                               ←1                                                                                     ←8                                                                                         hub
            testql.generators                            6                           ←9                            5                                                        ──                            7                            3                                                         1                                                         2                                                                                     ←3                           ←1  hub
                      .testql                           ←2                           ←5                                                                                     ←7                           ──                           ←5                           ←4                           ←3                           ←6                                                                                                                                               ←1  hub
              testql.adapters                            5                                                         8                                                        ←3                            5                           ──                                                                                                                                                                            ←6                                                            hub
               testql.results                                                        ←7                            8                                                                                      4                                                        ──                                                                                      1                                                                                                                   3  hub
           testql.interpreter                            3                                                         7                            1                            1                            3                                                                                     ──                                                                                                                                                                                !! fan-out
             testql.discovery                            6                           ←1                            2                                                                                      6                                                                                                                  ──                                                                                                                                                   !! fan-out
                  project.map                                                        ←6                                                                                     ←2                                                                                     ←1                                                                                     ──                                                                                     ←2                               hub
          testql.integrations                                                        ←1                                                         8                                                                                                                                                                                                                                      ──                                                                                         !! fan-out
             testql.ir_runner                            2                           ←1                                                                                                                                                6                                                                                                                                                                            ──                                                            !! fan-out
                   testql.mcp                           ←1                            2                                                                                      3                                                                                                                                                                             2                                                                                     ──                            1  !! fan-out
              testql.topology                                                        ←1                            2                                                         1                            1                                                        ←3                                                                                                                                                                            ←1                           ──  hub
  CYCLES: none
  HUB: project.map/ (fan-in=11)
  HUB: testql.generators/ (fan-in=14)
  HUB: testql.results/ (fan-in=9)
  HUB: testql.topology/ (fan-in=5)
  HUB: code2llm_output.map/ (fan-in=52)
  HUB: testql.adapters/ (fan-in=11)
  HUB: examples.browser-inspection/ (fan-in=48)
  HUB: .testql/ (fan-in=34)
  HUB: testql/ (fan-in=35)
  SMELL: testql.generators/ fan-out=24 → split needed
  SMELL: testql.results/ fan-out=16 → split needed
  SMELL: testql.mcp/ fan-out=8 → split needed
  SMELL: testql.adapters/ fan-out=18 → split needed
  SMELL: testql.integrations/ fan-out=8 → split needed
  SMELL: testql.commands/ fan-out=55 → split needed
  SMELL: testql.discovery/ fan-out=14 → split needed
  SMELL: testql.ir_runner/ fan-out=8 → split needed
  SMELL: TODO/ fan-out=8 → split needed
  SMELL: testql.interpreter/ fan-out=15 → split needed
  SMELL: testql.meta/ fan-out=8 → split needed
  SMELL: testql/ fan-out=27 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 0 groups | 1f 36L | 2026-04-29

SUMMARY:
  files_scanned: 1
  total_lines:   36
  dup_groups:    0
  dup_fragments: 0
  saved_lines:   0
  scan_ms:       4250
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 2174 func | 189f | 2026-04-29

NEXT[4] (ranked by impact):
  [1] !! SPLIT           testql/interpreter/_gui.py
      WHY: 708L, 1 classes, max CC=12
      EFFORT: ~4h  IMPACT: 8496

  [2] !! SPLIT           testql/generators/page_analyzer.py
      WHY: 526L, 1 classes, max CC=10
      EFFORT: ~4h  IMPACT: 5260

  [3] !  SPLIT-FUNC      _parse_makefile  CC=23  fan=19
      WHY: CC=23 exceeds 15
      EFFORT: ~1h  IMPACT: 437

  [4] !! SPLIT           test_manifest_and_generators.py
      WHY: 525L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[3]:
  ⚠ Splitting testql/interpreter/_gui.py may break 34 import paths
  ⚠ Splitting testql/generators/page_analyzer.py may break 31 import paths
  ⚠ Splitting test_manifest_and_generators.py may break 0 import paths

METRICS-TARGET:
  CC̄:          2.3 → ≤1.6
  max-CC:      23 → ≤11
  god-modules: 7 → 0
  high-CC(≥15): 1 → ≤0
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
  prev CC̄=2.3 → now CC̄=2.3
```

### Validation (`project/validation.toon.yaml`)

```toon markpact:analysis path=project/validation.toon.yaml
# vallm batch | 171f | 0✓ 138⚠ 0✗ | 2026-04-25

SUMMARY:
  scanned: 171  passed: 0 (0.0%)  warnings: 138  errors: 0  unsupported: 0

WARNINGS[138]{path,score}:
  .pyqual/runtime_errors.json,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse JSON: Download error: Language 'JSON' not available for download. Available groups: [""all""]",
  TODO/testtoon_parser.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  code2llm_output/calls.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  coverage.json,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse JSON: Download error: Language 'JSON' not available for download. Available groups: [""all""]",
  goal.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  openapi.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  project.sh,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse BASH: Download error: Language 'BASH' not available for download. Available groups: [""all""]",
  project/calls.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  pyproject.toml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse TOML: Download error: Language 'TOML' not available for download. Available groups: [""all""]",
  pyqual.yaml,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse YAML: Download error: Language 'YAML' not available for download. Available groups: [""all""]",
  sumd.json,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse JSON: Download error: Language 'JSON' not available for download. Available groups: [""all""]",
  testql/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/__main__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/_base_fallback.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/base.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/cli.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/echo.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/echo/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/echo/cli.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/echo/context.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/echo/formatters/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/echo/formatters/text.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/echo/parsers/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/echo/parsers/doql.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/echo/parsers/toon.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/echo_helpers.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/encoder_routes.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/endpoints_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/generate_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/misc_cmds.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/run_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/suite/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/suite/cli.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/suite/collection.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/suite/execution.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/suite/listing.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/suite/reports.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/suite_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/templates/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/templates/content.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/commands/templates/templates.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/detectors/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/detectors/base.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/detectors/config_detector.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/detectors/django_detector.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/detectors/express_detector.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/detectors/fastapi_detector.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/detectors/flask_detector.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/detectors/graphql_detector.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/detectors/models.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/detectors/openapi_detector.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/detectors/test_detector.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/detectors/unified.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/detectors/websocket_detector.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/doql_parser.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/echo_schemas.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/endpoint_detector.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/generator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/generators/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/generators/analyzers.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/generators/base.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/generators/convenience.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/generators/generators.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/generators/multi.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/generators/test_generator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/_api_runner.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/_assertions.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/_converter.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/_encoder.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/_flow.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/_gui.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/_parser.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/_shell.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/_testtoon_parser.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/_unit.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/_websockets.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/core.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/dispatcher.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/handlers/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/handlers/api.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/handlers/assertions.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/handlers/encoder.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/handlers/flow.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/handlers/include.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/handlers/navigate.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/handlers/record.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/handlers/select.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/handlers/unknown.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/handlers/wait.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/models.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/parsers.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/converter/renderer.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/dispatcher.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/interpreter/interpreter.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/openapi_generator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/report_generator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/reporters/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/reporters/console.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/reporters/json_reporter.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/reporters/junit.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/runner.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/runners/__init__.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/sumd_generator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/sumd_parser.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  testql/toon_parser.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_api_handler.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_cli.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_converter.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_converter_handlers.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_detectors.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_dispatcher.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_doql_parser_sumd_gen.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_echo.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_echo_doql_parser.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_echo_schemas_helpers.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_encoder_routes.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_generate_cmd.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_generators.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_gui_execution.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_interpreter.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_misc_cmds.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_openapi_generator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_report_generator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_reporters.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_runner.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_shell_execution.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_suite_cmd_helpers.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_suite_execution.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_suite_listing.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_sumd_parser.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_test_generator.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_toon_parser.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tests/test_unit_execution.py,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse PYTHON: Download error: Language 'PYTHON' not available for download. Available groups: [""all""]",
  tree.sh,0.78
    issues[1]{rule,severity,message,line}:
      syntax.unsupported,warning,"Could not parse BASH: Download error: Language 'BASH' not available for download. Available groups: [""all""]",
```

## Intent

TestQL — Multi-DSL Test Platform: TestTOON / NL / SQL / Proto / GraphQL adapters with Unified IR, generator engine, and meta-testing
