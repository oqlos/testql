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
- **version**: `1.2.59`
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
  version: 1.2.59;
}

dependencies {
  runtime: "httpx>=0.27, click>=8.0, rich>=13.0, pyyaml>=6.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60, websockets>=13.0, pytest-cov>=7.0, fastapi>=0.100";
  playwright: playwright>=1.40;
  desktop: "pyautogui>=0.9.54, mss>=9.0, opencv-python-headless>=4.8, dogtail>=0.9.11; platform_system=='Linux', pynput>=1.7";
  vision: "img2nl[analyze,similarity,opencv,scan]>=0.1.2, imgl>=0.7.2, vdisplay[pillow]>=0.1.3, pytesseract>=0.3.10";
  sql: sqlglot>=20.0;
  proto: protobuf>=4.21;
  graphql: graphql-core>=3.2;
  nlp2env: "mcp>=1.0, nlp2env[mcp]>=0.1.2";
  mcp: mcp>=1.0;
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
  entry: testql.cli:main;
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

tests {
  import: .testql-manifest-smoke/generated/**/*.testql.toon.yaml;
  import: .testql/generated/**/*.testql.toon.yaml;
  import: examples/api-testing/**/*.testql.toon.yaml;
  import: examples/desktop/**/*.testql.toon.yaml;
  import: examples/encoder-testing/**/*.testql.toon.yaml;
  import: examples/environment/**/*.testql.toon.yaml;
  import: examples/flow-control/**/*.testql.toon.yaml;
  import: examples/gui-testing/**/*.testql.toon.yaml;
  import: examples/project-echo/**/*.testql.toon.yaml;
  import: examples/shell-testing/**/*.testql.toon.yaml;
  import: examples/testtoon-basics/**/*.testql.toon.yaml;
  import: scenarios/**/*.testql.toon.yaml;
  import: testql-scenarios/**/*.testql.toon.yaml;
  import: testql/scenarios/c2004/api/**/*.testql.toon.yaml;
  import: testql/scenarios/c2004/encoder/**/*.testql.toon.yaml;
  import: testql/scenarios/c2004/gui/**/*.testql.toon.yaml;
  import: testql/scenarios/c2004/smoke/**/*.testql.toon.yaml;
  import: testql/scenarios/c2004/views/**/*.testql.toon.yaml;
  import: testql/scenarios/c2004/views/views/**/*.testql.toon.yaml;
  import: testql/scenarios/diagnostics/**/*.testql.toon.yaml;
  import: testql/scenarios/examples/**/*.testql.toon.yaml;
  import: testql/scenarios/generic/**/*.testql.toon.yaml;
  import: testql/scenarios/recordings/**/*.testql.toon.yaml;
  import: testql/scenarios/tests/**/*.testql.toon.yaml;
  import: testql/scenarios/tests/views/**/*.testql.toon.yaml;
  import: **/*.testql.yaml;
}

env_vars {
  keys: OPENROUTER_API_KEY, LLM_MODEL, AIDER_MODEL, OPENROUTER_MODEL, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_MAX_RETRIES, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_CREATE_BACKUPS, AIDER_MODEL_PRIMARY, AIDER_MODEL_FALLBACK, AIDER_EDIT_FORMAT;
}

deploy {
  target: docker;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  template_file: .env.example;
  python_version: >=3.10;
  vars: AIDER_MODEL, LLM_MODEL, OPENROUTER_API_KEY, OPENROUTER_MODEL, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
  runtime_llm: OPENROUTER_API_KEY, OPENROUTER_MODEL;
  runtime_pfix: PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
}

environment[name="testql.autoloop.example"] {
  runtime: docker-compose;
  env_file: .env.testql.autoloop.example;
  vars: AIDER_EDIT_FORMAT, AIDER_MODEL_FALLBACK, AIDER_MODEL_PRIMARY, OPENROUTER_API_KEY;
  runtime_llm: OPENROUTER_API_KEY;
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
    def _select_icon(cmd, result)  # CC=4
    def _format_result_output(cmd, result, index, total)  # CC=1
    def _print_verbose_result(result)  # CC=3
    def _handle_execution_error(result, stop_on_error)  # CC=2
    def run_script(content, stop_on_error)  # CC=6
    def _format_cmd(cmd)  # CC=2
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

*501 nodes · 500 edges · 118 modules · CC̄=3.8*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `print` *(in examples.browser-inspection.run)* | 0 | 67 | 0 | **67** |
| `capture_monitor_mirror_virtual` *(in testql.desktop.vdisplay_capture)* | 9 | 1 | 34 | **35** |
| `_cmd_desktop_assert_elements` *(in testql.interpreter._desktop.DesktopMixin)* | 14 ⚠ | 0 | 34 | **34** |
| `parse_testtoon` *(in TODO.testtoon_parser)* | 14 ⚠ | 1 | 31 | **32** |
| `write_inspection_artifacts` *(in testql.results.artifacts)* | 1 | 3 | 28 | **31** |
| `_cmd_assert_json` *(in testql.interpreter._assertions.AssertionsMixin)* | 13 ⚠ | 0 | 30 | **30** |
| `_cmd_validate` *(in testql.interpreter._validation.ValidationMixin)* | 10 ⚠ | 0 | 30 | **30** |
| `heal_scenario` *(in testql.commands.heal_scenario_cmd)* | 8 | 0 | 30 | **30** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/oqlos/testql
# generated in 0.40s
# nodes: 501 | edges: 500 | modules: 118
# CC̄=3.8

HUBS[20]:
  examples.browser-inspection.run.print
    CC=0  in:67  out:0  total:67
  testql.desktop.vdisplay_capture.capture_monitor_mirror_virtual
    CC=9  in:1  out:34  total:35
  testql.interpreter._desktop.DesktopMixin._cmd_desktop_assert_elements
    CC=14  in:0  out:34  total:34
  TODO.testtoon_parser.parse_testtoon
    CC=14  in:1  out:31  total:32
  testql.results.artifacts.write_inspection_artifacts
    CC=1  in:3  out:28  total:31
  testql.interpreter._assertions.AssertionsMixin._cmd_assert_json
    CC=13  in:0  out:30  total:30
  testql.interpreter._validation.ValidationMixin._cmd_validate
    CC=10  in:0  out:30  total:30
  testql.commands.heal_scenario_cmd.heal_scenario
    CC=8  in:0  out:30  total:30
  testql.commands.nlp2env_cmd.nlp2env_run
    CC=10  in:0  out:29  total:29
  testql._base_fallback.VariableStore.set
    CC=1  in:27  out:0  total:27
  packages.mcp2testql.src.mcp2testql.server.TestqlMCPServer._register_tools
    CC=1  in:0  out:26  total:26
  testql.commands.watchdog_cmd._update_metrics
    CC=11  in:2  out:23  total:25
  testql.commands.inspect_cmd.inspect
    CC=6  in:0  out:24  total:24
  packages.dsl2testql.src.dsl2testql.pb_codec._set_body
    CC=6  in:1  out:23  total:24
  testql.desktop.window_discovery.is_capture_window
    CC=12  in:1  out:23  total:24
  testql.commands.generate_topology_cmd.generate_topology
    CC=5  in:0  out:24  total:24
  testql.commands.generate_cmd._print_routes_section
    CC=10  in:1  out:23  total:24
  testql.commands.generate_cmd.analyze
    CC=4  in:2  out:22  total:24
  testql.context.runtime.detect_runtime_profile
    CC=12  in:3  out:20  total:23
  testql.commands.encoder_routes._run_oql_lines
    CC=6  in:1  out:22  total:23

MODULES:
  TODO.testtoon_parser  [3 funcs]
    parse_testtoon  CC=14  out:31
    print_parsed  CC=8  out:12
    validate  CC=2  out:2
  examples.artifact-bundle.generate_bundle  [1 funcs]
    main  CC=2  out:10
  examples.browser-inspection.run  [1 funcs]
    print  CC=0  out:0
  packages.dsl2testql.src.dsl2testql.bus  [5 funcs]
    _bytes_to_cmd  CC=3  out:5
    _dispatch_cmd  CC=5  out:12
    dispatch  CC=6  out:15
    execute_dsl  CC=4  out:6
    execute_dsl_line  CC=1  out:1
  packages.dsl2testql.src.dsl2testql.cli  [3 funcs]
    _main_legacy  CC=9  out:20
    _main_subcommands  CC=2  out:2
    main  CC=4  out:2
  packages.dsl2testql.src.dsl2testql.cli_handlers  [8 funcs]
    _print_result  CC=4  out:6
    cmd_decode  CC=2  out:9
    cmd_encode  CC=2  out:7
    cmd_exec  CC=2  out:7
    cmd_replay  CC=2  out:8
    cmd_run  CC=3  out:9
    cmd_shell  CC=7  out:11
    cmd_validate_schema  CC=3  out:3
  packages.dsl2testql.src.dsl2testql.codec  [4 funcs]
    decode_protobuf  CC=1  out:1
    encode_protobuf  CC=1  out:1
    encode_text  CC=2  out:2
    roundtrip_text  CC=3  out:6
  packages.dsl2testql.src.dsl2testql.engine  [1 funcs]
    dispatch  CC=1  out:1
  packages.dsl2testql.src.dsl2testql.events  [1 funcs]
    default_event_store  CC=2  out:7
  packages.dsl2testql.src.dsl2testql.grammar  [7 funcs]
    _parse_generate  CC=3  out:3
    _parse_patch  CC=4  out:2
    _parse_query  CC=4  out:3
    parse_line  CC=3  out:4
    pick_flag  CC=3  out:2
    split_command  CC=4  out:4
    to_text  CC=6  out:11
  packages.dsl2testql.src.dsl2testql.handlers.command  [4 funcs]
    _read_content  CC=1  out:3
    handle_from_tokens  CC=7  out:11
    handle_generate  CC=1  out:4
    handle_patch  CC=3  out:11
  packages.dsl2testql.src.dsl2testql.handlers.query  [2 funcs]
    handle_query  CC=4  out:8
    handle_validate  CC=5  out:10
  packages.dsl2testql.src.dsl2testql.pb_codec  [8 funcs]
    _set_body  CC=6  out:23
    decode_protobuf  CC=1  out:3
    decode_protobuf_to_text  CC=1  out:2
    encode_protobuf  CC=1  out:6
    encode_result_protobuf  CC=1  out:2
    encode_text_to_protobuf  CC=2  out:3
    envelope_to_dict  CC=4  out:6
    result_to_pb  CC=4  out:4
  packages.dsl2testql.src.dsl2testql.schema_registry  [5 funcs]
    _load_schemas  CC=3  out:9
    all_schemas  CC=1  out:2
    schema_for_verb  CC=1  out:3
    validate_command_dict  CC=3  out:7
    validate_schema_registry  CC=3  out:6
  packages.mcp2testql.src.mcp2testql.cli  [1 funcs]
    main  CC=4  out:9
  packages.mcp2testql.src.mcp2testql.server  [5 funcs]
    __post_init__  CC=1  out:3
    _register_tools  CC=1  out:26
    _require_fastmcp  CC=2  out:1
    create_server  CC=1  out:1
    run_server  CC=1  out:2
  packages.nlp2testql.src.nlp2testql.pipeline  [2 funcs]
    generate_spec  CC=6  out:13
    plan_with_rules  CC=2  out:4
  packages.nlp2testql.src.nlp2testql.validate  [2 funcs]
    validate_testql  CC=2  out:3
    validate_testql_file  CC=2  out:4
  packages.uri2testql.src.uri2testql.block_resolver  [5 funcs]
    _find_named  CC=3  out:2
    extract_block_data  CC=12  out:10
    parse_block_ref  CC=6  out:6
    render_block_partial  CC=14  out:8
    selector_from_ref  CC=10  out:0
  packages.uri2testql.src.uri2testql.files  [1 funcs]
    resolve_testql_file  CC=8  out:12
  packages.uri2testql.src.uri2testql.materialize  [4 funcs]
    _materialize_block  CC=5  out:12
    _materialize_file  CC=4  out:9
    _materialize_generate  CC=6  out:9
    materialize_uri  CC=9  out:12
  packages.uri2testql.src.uri2testql.patch  [8 funcs]
    _find_block_span  CC=5  out:2
    _selector_pattern  CC=12  out:16
    append_blocks_to_text  CC=3  out:2
    append_uri  CC=6  out:12
    apply_uri  CC=8  out:8
    patch_uri  CC=6  out:16
    replace_block_in_text  CC=3  out:9
    update_uri  CC=1  out:1
  packages.uri2testql.src.uri2testql.query  [9 funcs]
    _apply_output_format  CC=3  out:2
    _extract_data  CC=1  out:2
    _query_block_source  CC=3  out:12
    _query_file_source  CC=4  out:11
    _query_generate_source  CC=6  out:7
    _render_partial  CC=1  out:2
    _selector_from_parts  CC=2  out:3
    _to_plain  CC=8  out:10
    query_uri  CC=9  out:15
  packages.uri2testql.src.uri2testql.uri  [8 funcs]
    _decode  CC=2  out:1
    _encode  CC=1  out:1
    build_testql_uri_index  CC=1  out:4
    is_testql_uri  CC=1  out:2
    parse_testql_uri  CC=7  out:14
    uri_for_block  CC=7  out:9
    uri_for_file  CC=2  out:2
    uri_for_generate  CC=2  out:2
  testql._base_fallback  [3 funcs]
    emit  CC=2  out:2
    all  CC=1  out:1
    set  CC=1  out:0
  testql.adapters.nlp2dsl.llm_provider  [2 funcs]
    live_llm_enabled  CC=2  out:3
    resolve_llm_provider  CC=4  out:6
  testql.adapters.testtoon_adapter  [1 funcs]
    _toon_safe_selector  CC=3  out:2
  testql.artifacts.registry  [1 funcs]
    get_artifact_registry  CC=2  out:5
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
  testql.commands.conversation_cmd  [6 funcs]
    _create_runner  CC=2  out:2
    _format_mode  CC=4  out:1
    _output_text  CC=6  out:4
    _resolve_base_url  CC=4  out:2
    _validate_scenario  CC=3  out:2
    conversation_run  CC=6  out:21
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
  testql.commands.generate_cmd  [3 funcs]
    _count_routes_by  CC=2  out:3
    _print_routes_section  CC=10  out:23
    analyze  CC=4  out:22
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
  testql.commands.nlp2env_cmd  [2 funcs]
    _validate  CC=5  out:5
    nlp2env_run  CC=10  out:29
  testql.commands.run_cmd  [7 funcs]
    _emit_multi_json  CC=3  out:8
    _emit_single_json  CC=1  out:4
    _is_nlp2env_scenario  CC=2  out:4
    _maybe_planfile  CC=9  out:5
    _run_nlp2env  CC=1  out:6
    _run_single  CC=2  out:6
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
  testql.context.runtime  [3 funcs]
    _coerce_profile_dict  CC=4  out:13
    apply_profile  CC=4  out:6
    detect_runtime_profile  CC=12  out:20
  testql.conversation.runner  [7 funcs]
    __init__  CC=4  out:6
    _determine_nlp2dsl_status  CC=4  out:2
    _extract_captures  CC=3  out:2
    _run_step  CC=7  out:10
    _run_via_ir  CC=7  out:7
    _extract_path  CC=4  out:3
    _step_status_name  CC=4  out:0
  testql.desktop.backend  [21 funcs]
    list_windows  CC=1  out:0
    __init__  CC=2  out:2
    _active_window_id  CC=5  out:6
    _click_wayland  CC=6  out:11
    _click_x11  CC=4  out:8
    _list_windows_vdisplay  CC=4  out:3
    _list_windows_xdotool  CC=10  out:12
    _match_window  CC=8  out:5
    _screenshot_is_blank  CC=2  out:1
    _screenshot_vdisplay  CC=4  out:2
  testql.desktop.catalog  [1 funcs]
    collect_desktop_catalog  CC=4  out:3
  testql.desktop.element_assert  [1 funcs]
    evaluate_element_assert  CC=5  out:3
  testql.desktop.screenshot_tools  [2 funcs]
    screenshot_candidates  CC=8  out:16
    try_screenshot_candidates  CC=12  out:10
  testql.desktop.vdisplay_capture  [26 funcs]
    _allocate_virtual_display  CC=3  out:1
    _capture_virtual_window  CC=4  out:3
    _composite_windows  CC=5  out:3
    _desktop_bounds  CC=7  out:10
    _finalize_desktop_composite  CC=2  out:4
    _find_mirror_window  CC=4  out:6
    _format_window_id  CC=2  out:5
    _match_output_by_index  CC=5  out:3
    _match_output_by_name  CC=5  out:3
    _mirror_capture_result  CC=5  out:8
  testql.desktop.vision  [9 funcs]
    _collect_ocr_text  CC=9  out:7
    _display  CC=2  out:3
    analyze_layout  CC=9  out:21
    check_vision_availability  CC=4  out:3
    describe_image  CC=4  out:8
    find_text  CC=8  out:17
    inspect_environment  CC=5  out:19
    list_monitors  CC=8  out:18
    list_os_windows  CC=14  out:17
  testql.desktop.window_discovery  [12 funcs]
    _display  CC=3  out:5
    _filter_capture_windows  CC=3  out:1
    _has_unusable_title  CC=3  out:0
    _is_internal_without_title  CC=3  out:2
    _matches_junk_marker  CC=3  out:1
    _meets_min_size  CC=2  out:0
    _vdisplay_available  CC=2  out:0
    is_capture_window  CC=12  out:23
    list_capture_windows  CC=6  out:8
    window_display_title  CC=8  out:9
  testql.desktop.wmctrl  [1 funcs]
    parse_wmctrl_listing  CC=3  out:12
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
  testql.export.scenario_builder  [7 funcs]
    config  CC=3  out:6
    context  CC=3  out:6
    environment  CC=3  out:6
    flow  CC=8  out:13
    gui  CC=7  out:14
    shell  CC=4  out:9
    _csv  CC=3  out:3
  testql.generators.page_analyzer  [2 funcs]
    find_replacement  CC=3  out:5
    pick_selector  CC=3  out:1
  testql.generators.sources  [1 funcs]
    available_sources  CC=1  out:4
  testql.generators.sources.page_source  [1 funcs]
    extract_elements_from_page  CC=1  out:1
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
  testql.interpreter._context  [2 funcs]
    _cmd_context_apply  CC=5  out:10
    _cmd_context_detect  CC=5  out:9
  testql.interpreter._desktop  [3 funcs]
    _capture_is_stale_blank  CC=2  out:1
    _cmd_desktop_assert_elements  CC=14  out:34
    _desktop  CC=3  out:2
  testql.interpreter._flow  [1 funcs]
    _cmd_include  CC=7  out:17
  testql.interpreter._gui_expand  [1 funcs]
    expand_gui_row  CC=9  out:13
  testql.interpreter._parser  [1 funcs]
    parse_oql  CC=5  out:10
  testql.interpreter._testtoon_parser  [12 funcs]
    _append_api_asserts  CC=9  out:11
    _append_raw_command  CC=2  out:2
    _expand_api  CC=4  out:9
    _expand_context  CC=8  out:12
    _expand_desktop  CC=11  out:12
    _expand_environment  CC=9  out:15
    _expand_gui  CC=3  out:2
    _expand_shell  CC=6  out:12
    _quote_shell_command  CC=1  out:2
    _shell_expected_exit  CC=7  out:8
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
  testql.ir_runner.executors.base  [1 funcs]
    assemble_result  CC=5  out:6
  testql.openapi_generator  [4 funcs]
    _extract_parameters  CC=1  out:3
    _infer_tags  CC=7  out:9
    _extract_ep_params  CC=7  out:8
    _extract_path_params  CC=4  out:4
  testql.report_generator  [1 funcs]
    generate_report  CC=3  out:20
  testql.results.analyzer  [16 funcs]
    _actions_from_findings  CC=4  out:6
    _check_asset_statuses  CC=12  out:16
    _check_confidence  CC=2  out:2
    _check_edges  CC=2  out:3
    _check_evidence  CC=4  out:4
    _check_interfaces  CC=4  out:4
    _check_link_statuses  CC=14  out:17
    _check_nodes  CC=2  out:3
    _crawl_checks  CC=3  out:3
    _findings_from_checks  CC=4  out:5
  testql.results.artifacts  [3 funcs]
    _render_summary_md  CC=10  out:17
    _write_group  CC=2  out:3
    write_inspection_artifacts  CC=1  out:28
  testql.results.serializers  [1 funcs]
    _render_nlp  CC=1  out:3
  testql.runner  [8 funcs]
    _dispatch  CC=6  out:6
    _handle_execution_error  CC=2  out:2
    _print_verbose_result  CC=3  out:2
    cmd_log  CC=2  out:3
    cmd_print  CC=2  out:4
    run_script  CC=6  out:18
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
  packages.dsl2testql.src.dsl2testql.bus._dispatch_cmd → packages.dsl2testql.src.dsl2testql.schema_registry.validate_command_dict
  packages.dsl2testql.src.dsl2testql.bus._dispatch_cmd → packages.dsl2testql.src.dsl2testql.grammar.split_command
  packages.dsl2testql.src.dsl2testql.bus._dispatch_cmd → packages.dsl2testql.src.dsl2testql.handlers.command.handle_from_tokens
  packages.dsl2testql.src.dsl2testql.bus._dispatch_cmd → packages.dsl2testql.src.dsl2testql.events.default_event_store
  packages.dsl2testql.src.dsl2testql.bus._bytes_to_cmd → packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf
  packages.dsl2testql.src.dsl2testql.bus._bytes_to_cmd → packages.dsl2testql.src.dsl2testql.grammar.to_text
  packages.dsl2testql.src.dsl2testql.bus._bytes_to_cmd → packages.dsl2testql.src.dsl2testql.grammar.parse_line
  packages.dsl2testql.src.dsl2testql.bus.dispatch → packages.dsl2testql.src.dsl2testql.grammar.split_command
  packages.dsl2testql.src.dsl2testql.bus.dispatch → packages.dsl2testql.src.dsl2testql.bus._dispatch_cmd
  packages.dsl2testql.src.dsl2testql.bus.dispatch → packages.dsl2testql.src.dsl2testql.bus._bytes_to_cmd
  packages.dsl2testql.src.dsl2testql.bus.dispatch → packages.dsl2testql.src.dsl2testql.grammar.to_text
  packages.dsl2testql.src.dsl2testql.bus.execute_dsl_line → packages.dsl2testql.src.dsl2testql.bus.dispatch
  packages.dsl2testql.src.dsl2testql.bus.execute_dsl → packages.dsl2testql.src.dsl2testql.bus.execute_dsl_line
  packages.dsl2testql.src.dsl2testql.engine.dispatch → testql.runner.DslCliExecutor._dispatch
  packages.dsl2testql.src.dsl2testql.cli._main_legacy → packages.dsl2testql.src.dsl2testql.bus.execute_dsl_line
  packages.dsl2testql.src.dsl2testql.cli._main_legacy → packages.dsl2testql.src.dsl2testql.bus.execute_dsl
  packages.dsl2testql.src.dsl2testql.cli.main → packages.dsl2testql.src.dsl2testql.cli._main_legacy
  packages.dsl2testql.src.dsl2testql.cli.main → packages.dsl2testql.src.dsl2testql.cli._main_subcommands
  packages.dsl2testql.src.dsl2testql.pb_codec.encode_protobuf → packages.dsl2testql.src.dsl2testql.pb_codec._set_body
  packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf → packages.dsl2testql.src.dsl2testql.pb_codec.envelope_to_dict
  packages.dsl2testql.src.dsl2testql.pb_codec.encode_text_to_protobuf → packages.dsl2testql.src.dsl2testql.grammar.parse_line
  packages.dsl2testql.src.dsl2testql.pb_codec.encode_text_to_protobuf → packages.dsl2testql.src.dsl2testql.pb_codec.encode_protobuf
  packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf_to_text → packages.dsl2testql.src.dsl2testql.grammar.to_text
  packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf_to_text → packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf
  packages.dsl2testql.src.dsl2testql.pb_codec.encode_result_protobuf → packages.dsl2testql.src.dsl2testql.pb_codec.result_to_pb
  packages.dsl2testql.src.dsl2testql.schema_registry.schema_for_verb → packages.dsl2testql.src.dsl2testql.schema_registry._load_schemas
  packages.dsl2testql.src.dsl2testql.schema_registry.all_schemas → packages.dsl2testql.src.dsl2testql.schema_registry._load_schemas
  packages.dsl2testql.src.dsl2testql.schema_registry.validate_command_dict → packages.dsl2testql.src.dsl2testql.schema_registry.schema_for_verb
  packages.dsl2testql.src.dsl2testql.schema_registry.validate_schema_registry → packages.dsl2testql.src.dsl2testql.schema_registry._load_schemas
  packages.dsl2testql.src.dsl2testql.grammar._parse_query → packages.dsl2testql.src.dsl2testql.grammar.pick_flag
  packages.dsl2testql.src.dsl2testql.grammar._parse_patch → packages.dsl2testql.src.dsl2testql.grammar.pick_flag
  packages.dsl2testql.src.dsl2testql.grammar._parse_generate → packages.dsl2testql.src.dsl2testql.grammar.pick_flag
  packages.dsl2testql.src.dsl2testql.grammar.parse_line → packages.dsl2testql.src.dsl2testql.grammar.split_command
  packages.dsl2testql.src.dsl2testql.codec.encode_text → packages.dsl2testql.src.dsl2testql.grammar.parse_line
  packages.dsl2testql.src.dsl2testql.codec.encode_text → packages.dsl2testql.src.dsl2testql.schema_registry.validate_command_dict
  packages.dsl2testql.src.dsl2testql.codec.roundtrip_text → packages.dsl2testql.src.dsl2testql.grammar.parse_line
  packages.dsl2testql.src.dsl2testql.codec.roundtrip_text → packages.dsl2testql.src.dsl2testql.schema_registry.validate_command_dict
  packages.dsl2testql.src.dsl2testql.codec.roundtrip_text → packages.dsl2testql.src.dsl2testql.grammar.to_text
  packages.dsl2testql.src.dsl2testql.codec.encode_protobuf → packages.dsl2testql.src.dsl2testql.pb_codec.encode_text_to_protobuf
  packages.dsl2testql.src.dsl2testql.codec.decode_protobuf → packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf_to_text
  packages.dsl2testql.src.dsl2testql.cli_handlers._print_result → examples.browser-inspection.run.print
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_validate_schema → packages.dsl2testql.src.dsl2testql.schema_registry.validate_schema_registry
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_validate_schema → examples.browser-inspection.run.print
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_exec → packages.dsl2testql.src.dsl2testql.bus.execute_dsl_line
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_exec → packages.dsl2testql.src.dsl2testql.cli_handlers._print_result
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_run → packages.dsl2testql.src.dsl2testql.bus.execute_dsl
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_run → packages.dsl2testql.src.dsl2testql.cli_handlers._print_result
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_encode → packages.dsl2testql.src.dsl2testql.pb_codec.encode_text_to_protobuf
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_decode → examples.browser-inspection.run.print
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_decode → packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf_to_text
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
# generated in 0.40s
# nodes: 501 | edges: 500 | modules: 118
# CC̄=3.8

HUBS[20]:
  examples.browser-inspection.run.print
    CC=0  in:67  out:0  total:67
  testql.desktop.vdisplay_capture.capture_monitor_mirror_virtual
    CC=9  in:1  out:34  total:35
  testql.interpreter._desktop.DesktopMixin._cmd_desktop_assert_elements
    CC=14  in:0  out:34  total:34
  TODO.testtoon_parser.parse_testtoon
    CC=14  in:1  out:31  total:32
  testql.results.artifacts.write_inspection_artifacts
    CC=1  in:3  out:28  total:31
  testql.interpreter._assertions.AssertionsMixin._cmd_assert_json
    CC=13  in:0  out:30  total:30
  testql.interpreter._validation.ValidationMixin._cmd_validate
    CC=10  in:0  out:30  total:30
  testql.commands.heal_scenario_cmd.heal_scenario
    CC=8  in:0  out:30  total:30
  testql.commands.nlp2env_cmd.nlp2env_run
    CC=10  in:0  out:29  total:29
  testql._base_fallback.VariableStore.set
    CC=1  in:27  out:0  total:27
  packages.mcp2testql.src.mcp2testql.server.TestqlMCPServer._register_tools
    CC=1  in:0  out:26  total:26
  testql.commands.watchdog_cmd._update_metrics
    CC=11  in:2  out:23  total:25
  testql.commands.inspect_cmd.inspect
    CC=6  in:0  out:24  total:24
  packages.dsl2testql.src.dsl2testql.pb_codec._set_body
    CC=6  in:1  out:23  total:24
  testql.desktop.window_discovery.is_capture_window
    CC=12  in:1  out:23  total:24
  testql.commands.generate_topology_cmd.generate_topology
    CC=5  in:0  out:24  total:24
  testql.commands.generate_cmd._print_routes_section
    CC=10  in:1  out:23  total:24
  testql.commands.generate_cmd.analyze
    CC=4  in:2  out:22  total:24
  testql.context.runtime.detect_runtime_profile
    CC=12  in:3  out:20  total:23
  testql.commands.encoder_routes._run_oql_lines
    CC=6  in:1  out:22  total:23

MODULES:
  TODO.testtoon_parser  [3 funcs]
    parse_testtoon  CC=14  out:31
    print_parsed  CC=8  out:12
    validate  CC=2  out:2
  examples.artifact-bundle.generate_bundle  [1 funcs]
    main  CC=2  out:10
  examples.browser-inspection.run  [1 funcs]
    print  CC=0  out:0
  packages.dsl2testql.src.dsl2testql.bus  [5 funcs]
    _bytes_to_cmd  CC=3  out:5
    _dispatch_cmd  CC=5  out:12
    dispatch  CC=6  out:15
    execute_dsl  CC=4  out:6
    execute_dsl_line  CC=1  out:1
  packages.dsl2testql.src.dsl2testql.cli  [3 funcs]
    _main_legacy  CC=9  out:20
    _main_subcommands  CC=2  out:2
    main  CC=4  out:2
  packages.dsl2testql.src.dsl2testql.cli_handlers  [8 funcs]
    _print_result  CC=4  out:6
    cmd_decode  CC=2  out:9
    cmd_encode  CC=2  out:7
    cmd_exec  CC=2  out:7
    cmd_replay  CC=2  out:8
    cmd_run  CC=3  out:9
    cmd_shell  CC=7  out:11
    cmd_validate_schema  CC=3  out:3
  packages.dsl2testql.src.dsl2testql.codec  [4 funcs]
    decode_protobuf  CC=1  out:1
    encode_protobuf  CC=1  out:1
    encode_text  CC=2  out:2
    roundtrip_text  CC=3  out:6
  packages.dsl2testql.src.dsl2testql.engine  [1 funcs]
    dispatch  CC=1  out:1
  packages.dsl2testql.src.dsl2testql.events  [1 funcs]
    default_event_store  CC=2  out:7
  packages.dsl2testql.src.dsl2testql.grammar  [7 funcs]
    _parse_generate  CC=3  out:3
    _parse_patch  CC=4  out:2
    _parse_query  CC=4  out:3
    parse_line  CC=3  out:4
    pick_flag  CC=3  out:2
    split_command  CC=4  out:4
    to_text  CC=6  out:11
  packages.dsl2testql.src.dsl2testql.handlers.command  [4 funcs]
    _read_content  CC=1  out:3
    handle_from_tokens  CC=7  out:11
    handle_generate  CC=1  out:4
    handle_patch  CC=3  out:11
  packages.dsl2testql.src.dsl2testql.handlers.query  [2 funcs]
    handle_query  CC=4  out:8
    handle_validate  CC=5  out:10
  packages.dsl2testql.src.dsl2testql.pb_codec  [8 funcs]
    _set_body  CC=6  out:23
    decode_protobuf  CC=1  out:3
    decode_protobuf_to_text  CC=1  out:2
    encode_protobuf  CC=1  out:6
    encode_result_protobuf  CC=1  out:2
    encode_text_to_protobuf  CC=2  out:3
    envelope_to_dict  CC=4  out:6
    result_to_pb  CC=4  out:4
  packages.dsl2testql.src.dsl2testql.schema_registry  [5 funcs]
    _load_schemas  CC=3  out:9
    all_schemas  CC=1  out:2
    schema_for_verb  CC=1  out:3
    validate_command_dict  CC=3  out:7
    validate_schema_registry  CC=3  out:6
  packages.mcp2testql.src.mcp2testql.cli  [1 funcs]
    main  CC=4  out:9
  packages.mcp2testql.src.mcp2testql.server  [5 funcs]
    __post_init__  CC=1  out:3
    _register_tools  CC=1  out:26
    _require_fastmcp  CC=2  out:1
    create_server  CC=1  out:1
    run_server  CC=1  out:2
  packages.nlp2testql.src.nlp2testql.pipeline  [2 funcs]
    generate_spec  CC=6  out:13
    plan_with_rules  CC=2  out:4
  packages.nlp2testql.src.nlp2testql.validate  [2 funcs]
    validate_testql  CC=2  out:3
    validate_testql_file  CC=2  out:4
  packages.uri2testql.src.uri2testql.block_resolver  [5 funcs]
    _find_named  CC=3  out:2
    extract_block_data  CC=12  out:10
    parse_block_ref  CC=6  out:6
    render_block_partial  CC=14  out:8
    selector_from_ref  CC=10  out:0
  packages.uri2testql.src.uri2testql.files  [1 funcs]
    resolve_testql_file  CC=8  out:12
  packages.uri2testql.src.uri2testql.materialize  [4 funcs]
    _materialize_block  CC=5  out:12
    _materialize_file  CC=4  out:9
    _materialize_generate  CC=6  out:9
    materialize_uri  CC=9  out:12
  packages.uri2testql.src.uri2testql.patch  [8 funcs]
    _find_block_span  CC=5  out:2
    _selector_pattern  CC=12  out:16
    append_blocks_to_text  CC=3  out:2
    append_uri  CC=6  out:12
    apply_uri  CC=8  out:8
    patch_uri  CC=6  out:16
    replace_block_in_text  CC=3  out:9
    update_uri  CC=1  out:1
  packages.uri2testql.src.uri2testql.query  [9 funcs]
    _apply_output_format  CC=3  out:2
    _extract_data  CC=1  out:2
    _query_block_source  CC=3  out:12
    _query_file_source  CC=4  out:11
    _query_generate_source  CC=6  out:7
    _render_partial  CC=1  out:2
    _selector_from_parts  CC=2  out:3
    _to_plain  CC=8  out:10
    query_uri  CC=9  out:15
  packages.uri2testql.src.uri2testql.uri  [8 funcs]
    _decode  CC=2  out:1
    _encode  CC=1  out:1
    build_testql_uri_index  CC=1  out:4
    is_testql_uri  CC=1  out:2
    parse_testql_uri  CC=7  out:14
    uri_for_block  CC=7  out:9
    uri_for_file  CC=2  out:2
    uri_for_generate  CC=2  out:2
  testql._base_fallback  [3 funcs]
    emit  CC=2  out:2
    all  CC=1  out:1
    set  CC=1  out:0
  testql.adapters.nlp2dsl.llm_provider  [2 funcs]
    live_llm_enabled  CC=2  out:3
    resolve_llm_provider  CC=4  out:6
  testql.adapters.testtoon_adapter  [1 funcs]
    _toon_safe_selector  CC=3  out:2
  testql.artifacts.registry  [1 funcs]
    get_artifact_registry  CC=2  out:5
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
  testql.commands.conversation_cmd  [6 funcs]
    _create_runner  CC=2  out:2
    _format_mode  CC=4  out:1
    _output_text  CC=6  out:4
    _resolve_base_url  CC=4  out:2
    _validate_scenario  CC=3  out:2
    conversation_run  CC=6  out:21
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
  testql.commands.generate_cmd  [3 funcs]
    _count_routes_by  CC=2  out:3
    _print_routes_section  CC=10  out:23
    analyze  CC=4  out:22
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
  testql.commands.nlp2env_cmd  [2 funcs]
    _validate  CC=5  out:5
    nlp2env_run  CC=10  out:29
  testql.commands.run_cmd  [7 funcs]
    _emit_multi_json  CC=3  out:8
    _emit_single_json  CC=1  out:4
    _is_nlp2env_scenario  CC=2  out:4
    _maybe_planfile  CC=9  out:5
    _run_nlp2env  CC=1  out:6
    _run_single  CC=2  out:6
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
  testql.context.runtime  [3 funcs]
    _coerce_profile_dict  CC=4  out:13
    apply_profile  CC=4  out:6
    detect_runtime_profile  CC=12  out:20
  testql.conversation.runner  [7 funcs]
    __init__  CC=4  out:6
    _determine_nlp2dsl_status  CC=4  out:2
    _extract_captures  CC=3  out:2
    _run_step  CC=7  out:10
    _run_via_ir  CC=7  out:7
    _extract_path  CC=4  out:3
    _step_status_name  CC=4  out:0
  testql.desktop.backend  [21 funcs]
    list_windows  CC=1  out:0
    __init__  CC=2  out:2
    _active_window_id  CC=5  out:6
    _click_wayland  CC=6  out:11
    _click_x11  CC=4  out:8
    _list_windows_vdisplay  CC=4  out:3
    _list_windows_xdotool  CC=10  out:12
    _match_window  CC=8  out:5
    _screenshot_is_blank  CC=2  out:1
    _screenshot_vdisplay  CC=4  out:2
  testql.desktop.catalog  [1 funcs]
    collect_desktop_catalog  CC=4  out:3
  testql.desktop.element_assert  [1 funcs]
    evaluate_element_assert  CC=5  out:3
  testql.desktop.screenshot_tools  [2 funcs]
    screenshot_candidates  CC=8  out:16
    try_screenshot_candidates  CC=12  out:10
  testql.desktop.vdisplay_capture  [26 funcs]
    _allocate_virtual_display  CC=3  out:1
    _capture_virtual_window  CC=4  out:3
    _composite_windows  CC=5  out:3
    _desktop_bounds  CC=7  out:10
    _finalize_desktop_composite  CC=2  out:4
    _find_mirror_window  CC=4  out:6
    _format_window_id  CC=2  out:5
    _match_output_by_index  CC=5  out:3
    _match_output_by_name  CC=5  out:3
    _mirror_capture_result  CC=5  out:8
  testql.desktop.vision  [9 funcs]
    _collect_ocr_text  CC=9  out:7
    _display  CC=2  out:3
    analyze_layout  CC=9  out:21
    check_vision_availability  CC=4  out:3
    describe_image  CC=4  out:8
    find_text  CC=8  out:17
    inspect_environment  CC=5  out:19
    list_monitors  CC=8  out:18
    list_os_windows  CC=14  out:17
  testql.desktop.window_discovery  [12 funcs]
    _display  CC=3  out:5
    _filter_capture_windows  CC=3  out:1
    _has_unusable_title  CC=3  out:0
    _is_internal_without_title  CC=3  out:2
    _matches_junk_marker  CC=3  out:1
    _meets_min_size  CC=2  out:0
    _vdisplay_available  CC=2  out:0
    is_capture_window  CC=12  out:23
    list_capture_windows  CC=6  out:8
    window_display_title  CC=8  out:9
  testql.desktop.wmctrl  [1 funcs]
    parse_wmctrl_listing  CC=3  out:12
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
  testql.export.scenario_builder  [7 funcs]
    config  CC=3  out:6
    context  CC=3  out:6
    environment  CC=3  out:6
    flow  CC=8  out:13
    gui  CC=7  out:14
    shell  CC=4  out:9
    _csv  CC=3  out:3
  testql.generators.page_analyzer  [2 funcs]
    find_replacement  CC=3  out:5
    pick_selector  CC=3  out:1
  testql.generators.sources  [1 funcs]
    available_sources  CC=1  out:4
  testql.generators.sources.page_source  [1 funcs]
    extract_elements_from_page  CC=1  out:1
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
  testql.interpreter._context  [2 funcs]
    _cmd_context_apply  CC=5  out:10
    _cmd_context_detect  CC=5  out:9
  testql.interpreter._desktop  [3 funcs]
    _capture_is_stale_blank  CC=2  out:1
    _cmd_desktop_assert_elements  CC=14  out:34
    _desktop  CC=3  out:2
  testql.interpreter._flow  [1 funcs]
    _cmd_include  CC=7  out:17
  testql.interpreter._gui_expand  [1 funcs]
    expand_gui_row  CC=9  out:13
  testql.interpreter._parser  [1 funcs]
    parse_oql  CC=5  out:10
  testql.interpreter._testtoon_parser  [12 funcs]
    _append_api_asserts  CC=9  out:11
    _append_raw_command  CC=2  out:2
    _expand_api  CC=4  out:9
    _expand_context  CC=8  out:12
    _expand_desktop  CC=11  out:12
    _expand_environment  CC=9  out:15
    _expand_gui  CC=3  out:2
    _expand_shell  CC=6  out:12
    _quote_shell_command  CC=1  out:2
    _shell_expected_exit  CC=7  out:8
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
  testql.ir_runner.executors.base  [1 funcs]
    assemble_result  CC=5  out:6
  testql.openapi_generator  [4 funcs]
    _extract_parameters  CC=1  out:3
    _infer_tags  CC=7  out:9
    _extract_ep_params  CC=7  out:8
    _extract_path_params  CC=4  out:4
  testql.report_generator  [1 funcs]
    generate_report  CC=3  out:20
  testql.results.analyzer  [16 funcs]
    _actions_from_findings  CC=4  out:6
    _check_asset_statuses  CC=12  out:16
    _check_confidence  CC=2  out:2
    _check_edges  CC=2  out:3
    _check_evidence  CC=4  out:4
    _check_interfaces  CC=4  out:4
    _check_link_statuses  CC=14  out:17
    _check_nodes  CC=2  out:3
    _crawl_checks  CC=3  out:3
    _findings_from_checks  CC=4  out:5
  testql.results.artifacts  [3 funcs]
    _render_summary_md  CC=10  out:17
    _write_group  CC=2  out:3
    write_inspection_artifacts  CC=1  out:28
  testql.results.serializers  [1 funcs]
    _render_nlp  CC=1  out:3
  testql.runner  [8 funcs]
    _dispatch  CC=6  out:6
    _handle_execution_error  CC=2  out:2
    _print_verbose_result  CC=3  out:2
    cmd_log  CC=2  out:3
    cmd_print  CC=2  out:4
    run_script  CC=6  out:18
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
  packages.dsl2testql.src.dsl2testql.bus._dispatch_cmd → packages.dsl2testql.src.dsl2testql.schema_registry.validate_command_dict
  packages.dsl2testql.src.dsl2testql.bus._dispatch_cmd → packages.dsl2testql.src.dsl2testql.grammar.split_command
  packages.dsl2testql.src.dsl2testql.bus._dispatch_cmd → packages.dsl2testql.src.dsl2testql.handlers.command.handle_from_tokens
  packages.dsl2testql.src.dsl2testql.bus._dispatch_cmd → packages.dsl2testql.src.dsl2testql.events.default_event_store
  packages.dsl2testql.src.dsl2testql.bus._bytes_to_cmd → packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf
  packages.dsl2testql.src.dsl2testql.bus._bytes_to_cmd → packages.dsl2testql.src.dsl2testql.grammar.to_text
  packages.dsl2testql.src.dsl2testql.bus._bytes_to_cmd → packages.dsl2testql.src.dsl2testql.grammar.parse_line
  packages.dsl2testql.src.dsl2testql.bus.dispatch → packages.dsl2testql.src.dsl2testql.grammar.split_command
  packages.dsl2testql.src.dsl2testql.bus.dispatch → packages.dsl2testql.src.dsl2testql.bus._dispatch_cmd
  packages.dsl2testql.src.dsl2testql.bus.dispatch → packages.dsl2testql.src.dsl2testql.bus._bytes_to_cmd
  packages.dsl2testql.src.dsl2testql.bus.dispatch → packages.dsl2testql.src.dsl2testql.grammar.to_text
  packages.dsl2testql.src.dsl2testql.bus.execute_dsl_line → packages.dsl2testql.src.dsl2testql.bus.dispatch
  packages.dsl2testql.src.dsl2testql.bus.execute_dsl → packages.dsl2testql.src.dsl2testql.bus.execute_dsl_line
  packages.dsl2testql.src.dsl2testql.engine.dispatch → testql.runner.DslCliExecutor._dispatch
  packages.dsl2testql.src.dsl2testql.cli._main_legacy → packages.dsl2testql.src.dsl2testql.bus.execute_dsl_line
  packages.dsl2testql.src.dsl2testql.cli._main_legacy → packages.dsl2testql.src.dsl2testql.bus.execute_dsl
  packages.dsl2testql.src.dsl2testql.cli.main → packages.dsl2testql.src.dsl2testql.cli._main_legacy
  packages.dsl2testql.src.dsl2testql.cli.main → packages.dsl2testql.src.dsl2testql.cli._main_subcommands
  packages.dsl2testql.src.dsl2testql.pb_codec.encode_protobuf → packages.dsl2testql.src.dsl2testql.pb_codec._set_body
  packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf → packages.dsl2testql.src.dsl2testql.pb_codec.envelope_to_dict
  packages.dsl2testql.src.dsl2testql.pb_codec.encode_text_to_protobuf → packages.dsl2testql.src.dsl2testql.grammar.parse_line
  packages.dsl2testql.src.dsl2testql.pb_codec.encode_text_to_protobuf → packages.dsl2testql.src.dsl2testql.pb_codec.encode_protobuf
  packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf_to_text → packages.dsl2testql.src.dsl2testql.grammar.to_text
  packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf_to_text → packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf
  packages.dsl2testql.src.dsl2testql.pb_codec.encode_result_protobuf → packages.dsl2testql.src.dsl2testql.pb_codec.result_to_pb
  packages.dsl2testql.src.dsl2testql.schema_registry.schema_for_verb → packages.dsl2testql.src.dsl2testql.schema_registry._load_schemas
  packages.dsl2testql.src.dsl2testql.schema_registry.all_schemas → packages.dsl2testql.src.dsl2testql.schema_registry._load_schemas
  packages.dsl2testql.src.dsl2testql.schema_registry.validate_command_dict → packages.dsl2testql.src.dsl2testql.schema_registry.schema_for_verb
  packages.dsl2testql.src.dsl2testql.schema_registry.validate_schema_registry → packages.dsl2testql.src.dsl2testql.schema_registry._load_schemas
  packages.dsl2testql.src.dsl2testql.grammar._parse_query → packages.dsl2testql.src.dsl2testql.grammar.pick_flag
  packages.dsl2testql.src.dsl2testql.grammar._parse_patch → packages.dsl2testql.src.dsl2testql.grammar.pick_flag
  packages.dsl2testql.src.dsl2testql.grammar._parse_generate → packages.dsl2testql.src.dsl2testql.grammar.pick_flag
  packages.dsl2testql.src.dsl2testql.grammar.parse_line → packages.dsl2testql.src.dsl2testql.grammar.split_command
  packages.dsl2testql.src.dsl2testql.codec.encode_text → packages.dsl2testql.src.dsl2testql.grammar.parse_line
  packages.dsl2testql.src.dsl2testql.codec.encode_text → packages.dsl2testql.src.dsl2testql.schema_registry.validate_command_dict
  packages.dsl2testql.src.dsl2testql.codec.roundtrip_text → packages.dsl2testql.src.dsl2testql.grammar.parse_line
  packages.dsl2testql.src.dsl2testql.codec.roundtrip_text → packages.dsl2testql.src.dsl2testql.schema_registry.validate_command_dict
  packages.dsl2testql.src.dsl2testql.codec.roundtrip_text → packages.dsl2testql.src.dsl2testql.grammar.to_text
  packages.dsl2testql.src.dsl2testql.codec.encode_protobuf → packages.dsl2testql.src.dsl2testql.pb_codec.encode_text_to_protobuf
  packages.dsl2testql.src.dsl2testql.codec.decode_protobuf → packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf_to_text
  packages.dsl2testql.src.dsl2testql.cli_handlers._print_result → examples.browser-inspection.run.print
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_validate_schema → packages.dsl2testql.src.dsl2testql.schema_registry.validate_schema_registry
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_validate_schema → examples.browser-inspection.run.print
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_exec → packages.dsl2testql.src.dsl2testql.bus.execute_dsl_line
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_exec → packages.dsl2testql.src.dsl2testql.cli_handlers._print_result
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_run → packages.dsl2testql.src.dsl2testql.bus.execute_dsl
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_run → packages.dsl2testql.src.dsl2testql.cli_handlers._print_result
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_encode → packages.dsl2testql.src.dsl2testql.pb_codec.encode_text_to_protobuf
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_decode → examples.browser-inspection.run.print
  packages.dsl2testql.src.dsl2testql.cli_handlers.cmd_decode → packages.dsl2testql.src.dsl2testql.pb_codec.decode_protobuf_to_text
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 501f 52557L | python:309,yaml:122,shell:25,json:15,toml:6,txt:2,yml:2,proto:2,doql:1 | 2026-06-09
# generated in 0.18s
# CC̅=3.8 | critical:0/1835 | dups:0 | cycles:0

HEALTH[0]: ok

REFACTOR[0]: none needed

PIPELINES[935]:
  [1] Src [execute_dsl_line]: execute_dsl_line
      PURITY: 100% pure
  [2] Src [execute_dsl]: execute_dsl
      PURITY: 100% pure
  [3] Src [dispatch]: dispatch → _dispatch → print
      PURITY: 100% pure
  [4] Src [main]: main → _main_legacy → execute_dsl_line → dispatch → ...(1 more)
      PURITY: 100% pure
  [5] Src [to_dict]: to_dict
      PURITY: 100% pure
  [6] Src [__init__]: __init__
      PURITY: 100% pure
  [7] Src [replay]: replay → envelope_to_dict
      PURITY: 100% pure
  [8] Src [all_schemas]: all_schemas → _load_schemas
      PURITY: 100% pure
  [9] Src [_parse_query]: _parse_query → pick_flag
      PURITY: 100% pure
  [10] Src [_parse_patch]: _parse_patch → pick_flag
      PURITY: 100% pure
  [11] Src [_parse_generate]: _parse_generate → pick_flag
      PURITY: 100% pure
  [12] Src [encode_text]: encode_text → parse_line → split_command
      PURITY: 100% pure
  [13] Src [roundtrip_text]: roundtrip_text → parse_line → split_command
      PURITY: 100% pure
  [14] Src [encode_protobuf]: encode_protobuf → encode_text_to_protobuf → parse_line → split_command
      PURITY: 100% pure
  [15] Src [decode_protobuf]: decode_protobuf → decode_protobuf_to_text → to_text
      PURITY: 100% pure
  [16] Src [cmd_validate_schema]: cmd_validate_schema → validate_schema_registry → _load_schemas
      PURITY: 100% pure
  [17] Src [cmd_exec]: cmd_exec → execute_dsl_line → dispatch → split_command
      PURITY: 100% pure
  [18] Src [cmd_run]: cmd_run → execute_dsl → execute_dsl_line → dispatch → ...(1 more)
      PURITY: 100% pure
  [19] Src [cmd_encode]: cmd_encode → encode_text_to_protobuf → parse_line → split_command
      PURITY: 100% pure
  [20] Src [cmd_decode]: cmd_decode → print
      PURITY: 100% pure
  [21] Src [cmd_replay]: cmd_replay → default_event_store
      PURITY: 100% pure
  [22] Src [cmd_shell]: cmd_shell → print
      PURITY: 100% pure
  [23] Src [uri_for_file]: uri_for_file → _encode
      PURITY: 100% pure
  [24] Src [uri_for_generate]: uri_for_generate → _encode
      PURITY: 100% pure
  [25] Src [build_testql_uri_index]: build_testql_uri_index → uri_for_block → _encode
      PURITY: 100% pure
  [26] Src [main]: main → create_server
      PURITY: 100% pure
  [27] Src [__post_init__]: __post_init__ → _require_fastmcp
      PURITY: 100% pure
  [28] Src [_register_tools]: _register_tools → query_uri → parse_testql_uri → _decode
      PURITY: 100% pure
  [29] Src [run]: run
      PURITY: 100% pure
  [30] Src [main]: main → print
      PURITY: 100% pure
  [31] Src [health]: health
      PURITY: 100% pure
  [32] Src [devices]: devices
      PURITY: 100% pure
  [33] Src [list_scenarios]: list_scenarios
      PURITY: 100% pure
  [34] Src [create_scenario]: create_scenario
      PURITY: 100% pure
  [35] Src [get_scenario]: get_scenario
      PURITY: 100% pure
  [36] Src [update_scenario]: update_scenario
      PURITY: 100% pure
  [37] Src [delete_scenario]: delete_scenario
      PURITY: 100% pure
  [38] Src [users]: users
      PURITY: 100% pure
  [39] Src [validate]: validate
      PURITY: 100% pure
  [40] Src [print_parsed]: print_parsed → print
      PURITY: 100% pure
  [41] Src [__init__]: __init__
      PURITY: 100% pure
  [42] Src [parse_file]: parse_file
      PURITY: 100% pure
  [43] Src [parse]: parse
      PURITY: 100% pure
  [44] Src [_parse_api_block]: _parse_api_block
      PURITY: 100% pure
  [45] Src [_parse_assert_block]: _parse_assert_block
      PURITY: 100% pure
  [46] Src [_parse_log_block]: _parse_log_block
      PURITY: 100% pure
  [47] Src [mcp_serve]: mcp_serve → run_server → create_server
      PURITY: 100% pure
  [48] Src [main]: main → check_and_upgrade → _fetch_latest_version
      PURITY: 100% pure
  [49] Src [__init__]: __init__
      PURITY: 100% pure
  [50] Src [parse_file]: parse_file
      PURITY: 100% pure

LAYERS:
  TODO/                           CC̄=5.9    ←in:1  →out:8  !! split
  │ testtoon_parser            141L  1C    7m  CC=14     ←1
  │
  testql/                         CC̄=3.8    ←in:43  →out:23  !! split
  │ !! testtoon_adapter           742L  1C   46m  CC=12     ←4
  │ !! _gui                       722L  1C   34m  CC=12     ←0
  │ !! _desktop                   683L  1C   21m  CC=14     ←0
  │ !! vdisplay_capture           673L  2C   32m  CC=13     ←3
  │ !! _testtoon_parser           656L  0C   29m  CC=14     ←1
  │ !! page_analyzer              526L  1C   31m  CC=10     ←3
  │ !! scenario_yaml              506L  1C   43m  CC=13     ←1
  │ !! analyzer                   504L  0C   38m  CC=14     ←3
  │ encoder_routes             477L  0C   27m  CC=10     ←0
  │ backend                    447L  2C   30m  CC=12     ←5
  │ openapi_generator          444L  3C   21m  CC=11     ←1
  │ dom_scanner                418L  1C   26m  CC=13     ←0
  │ pytest_source              389L  3C   13m  CC=13     ←0
  │ runner                     387L  3C   22m  CC=12     ←1
  │ vision                     363L  2C   11m  CC=14     ←0
  │ nl_adapter                 353L  1C   30m  CC=7      ←0
  │ sql_adapter                333L  1C   26m  CC=8      ←0
  │ dom_scan_mixin             318L  1C   11m  CC=9      ←0
  │ steps                      318L  14C   27m  CC=8      ←0
  │ analyzers                  309L  1C   16m  CC=10     ←0
  │ heal_scenario_cmd          307L  1C    9m  CC=8      ←0
  │ oql_source                 306L  1C   22m  CC=10     ←0
  │ config_source              305L  1C   13m  CC=14     ←0
  │ _assertions                304L  1C    7m  CC=13     ←0
  │ _api_runner                302L  1C   16m  CC=13     ←2
  │ api_generator              298L  2C   19m  CC=10     ←0
  │ testtoon_parser            296L  0C   21m  CC=11     ←0
  │ misc_cmds                  292L  0C    7m  CC=6      ←0
  │ runner                     286L  3C   18m  CC=9      ←1
  │ watchdog_cmd               282L  0C    9m  CC=14     ←0
  │ sumd_parser                277L  5C   12m  CC=11     ←0
  │ graphql_adapter            273L  1C   23m  CC=6      ←0
  │ _unit                      267L  1C   10m  CC=10     ←0
  │ oql_parser                 267L  1C   20m  CC=7      ←0
  │ _shell                     260L  1C    9m  CC=8      ←0
  │ report_generator           250L  4C    8m  CC=5      ←1
  │ proto_adapter              242L  1C   18m  CC=6      ←0
  │ generator                  241L  2C   17m  CC=8      ←0
  │ unified                    239L  1C   12m  CC=13     ←0
  │ _base_fallback             232L  7C   26m  CC=4      ←25
  │ _modbus                    232L  1C   10m  CC=14     ←0
  │ ddl_parser                 228L  3C   17m  CC=7      ←2
  │ runner                     226L  1C   11m  CC=11     ←0
  │ scenarios                  222L  1C   13m  CC=13     ←2
  │ mutator                    219L  2C   12m  CC=6      ←0
  │ config_detector            218L  1C   10m  CC=14     ←0
  │ sumd_generator             208L  0C   11m  CC=7      ←1
  │ catalog                    207L  0C    1m  CC=4      ←0
  │ auto_cmd                   202L  0C    9m  CC=9      ←0
  │ package_python             200L  1C   19m  CC=10     ←0
  │ message_validator          187L  2C   11m  CC=7      ←1
  │ run_cmd                    183L  0C    8m  CC=10     ←1
  │ _gui_expand                180L  0C   10m  CC=9      ←1
  │ manifest                   173L  6C   12m  CC=10     ←0
  │ coverage_analyzer          173L  1C   15m  CC=6      ←0
  │ doql_parser                172L  1C    9m  CC=6      ←1
  │ _websockets                172L  1C    8m  CC=8      ←0
  │ page_source                172L  1C    6m  CC=4      ←1
  │ generate_cmd               171L  0C    9m  CC=10     ←1
  │ specialized_generator      170L  1C    5m  CC=1      ←0
  │ content                    166L  1C    9m  CC=2      ←0
  │ _flow                      165L  1C    6m  CC=9      ←0
  │ runtime                    163L  1C   10m  CC=12     ←1
  │ descriptor_loader          162L  3C   13m  CC=5      ←3
  │ interpreter                161L  1C    7m  CC=8      ←0
  │ http_endpoint              160L  2C   15m  CC=10     ←1
  │ server                     159L  1C    7m  CC=4      ←0
  │ echo_schemas               153L  6C    2m  CC=8      ←0
  │ _validation                153L  1C    3m  CC=11     ←0
  │ fastapi_detector           153L  1C   12m  CC=6      ←0
  │ registry                   150L  1C   13m  CC=9      ←1
  │ generate-test-reports.testql.toon.yaml   150L  0C    0m  CC=0.0    ←0
  │ playwright_page            147L  1C    6m  CC=10     ←0
  │ pytest_generator           147L  1C    9m  CC=7      ←0
  │ pipeline                   145L  2C    7m  CC=7      ←0
  │ artifacts                  144L  0C    4m  CC=10     ←3
  │ compatibility              143L  2C    8m  CC=6      ←0
  │ builder                    142L  1C   14m  CC=5      ←4
  │ models                     140L  5C    6m  CC=5      ←0
  │ endpoints_cmd              136L  0C    6m  CC=9      ←0
  │ engine                     136L  1C    7m  CC=9      ←1
  │ schema_introspection       135L  1C    7m  CC=5      ←1
  │ window_discovery           133L  0C   12m  CC=12     ←3
  │ assertion_eval             124L  1C    7m  CC=6      ←2
  │ collection                 122L  0C    8m  CC=6      ←1
  │ flask_detector             121L  1C    9m  CC=6      ←0
  │ sitemap                    119L  1C   12m  CC=9      ←1
  │ doql                       115L  0C    9m  CC=7      ←1
  │ entity_extractor           115L  0C   11m  CC=7      ←0
  │ planfile_hook              115L  0C    2m  CC=9      ←1
  │ listing                    114L  0C    6m  CC=7      ←1
  │ serializers                112L  0C    8m  CC=7      ←2
  │ run-all-views.testql.toon.yaml   112L  0C    0m  CC=0.0    ←0
  │ toon_parser                110L  1C    7m  CC=4      ←1
  │ _hardware                  109L  1C    4m  CC=8      ←0
  │ cli                        108L  0C    5m  CC=4      ←0
  │ conversation_cmd           108L  0C    8m  CC=6      ←0
  │ grammar                    107L  1C    7m  CC=5      ←2
  │ multi                      105L  1C    5m  CC=6      ←0
  │ fixtures                   105L  2C    7m  CC=5      ←1
  │ models                     105L  5C    6m  CC=6      ←0
  │ scenario_builder           104L  1C   11m  CC=8      ←0
  │ pl.yaml                    103L  0C    0m  CC=0.0    ←0
  │ llm                        101L  0C    5m  CC=7      ←1
  │ cli                        100L  0C    2m  CC=13     ←0
  │ _encoder                   100L  1C   13m  CC=9      ←0
  │ generate_from_page_cmd      99L  0C    2m  CC=8      ←0
  │ intent_recognizer           99L  1C    3m  CC=6      ←1
  │ base                        97L  3C    5m  CC=5      ←9
  │ text                        95L  0C    7m  CC=6      ←1
  │ pipeline                    95L  1C    6m  CC=5      ←0
  │ query_parser                95L  1C    5m  CC=5      ←0
  │ confidence_scorer           94L  2C    7m  CC=4      ←0
  │ parsers                     93L  0C    6m  CC=11     ←9
  │ openapi_source              93L  1C    5m  CC=7      ←0
  │ en.yaml                     93L  0C    0m  CC=0.0    ←0
  │ __init__                    91L  0C    1m  CC=8      ←0
  │ dispatcher                  90L  1C    6m  CC=5      ←0
  │ proto_source                90L  1C    5m  CC=5      ←0
  │ live_llm                    90L  1C    5m  CC=6      ←0
  │ openapi_detector            90L  1C    3m  CC=9      ←0
  │ reports                     89L  0C    5m  CC=6      ←1
  │ dialect_resolver            88L  1C    4m  CC=4      ←3
  │ scenario_generator          87L  1C    2m  CC=13     ←0
  │ graphql_detector            87L  1C    3m  CC=5      ←0
  │ proto                       87L  0C    4m  CC=6      ←0
  │ __init__                    85L  0C    3m  CC=5      ←3
  │ nlp2env_cmd                 84L  0C    3m  CC=10     ←0
  │ dom_scan_formatters         84L  0C    4m  CC=13     ←1
  │ ui_source                   81L  1C    5m  CC=5      ←0
  │ nlp2dsl_adapter             81L  1C    4m  CC=7      ←0
  │ junit                       79L  1C    3m  CC=8      ←0
  │ sql_source                  79L  1C    4m  CC=5      ←0
  │ mcp_client                  78L  0C    5m  CC=7      ←1
  │ encoder                     77L  0C    3m  CC=5      ←0
  │ toon                        76L  0C    4m  CC=5      ←1
  │ query_executor              76L  0C    5m  CC=6      ←1
  │ test-device-flow.testql.toon.yaml    76L  0C    0m  CC=0.0    ←0
  │ execution                   73L  0C    2m  CC=5      ←1
  │ nlp2env_adapter             73L  1C    5m  CC=7      ←0
  │ api_openapi                 72L  1C    5m  CC=9      ←1
  │ base                        70L  3C    8m  CC=4      ←0
  │ test-gui-connect-id.testql.toon.yaml    70L  0C    0m  CC=0.0    ←0
  │ conversation_generator      69L  1C    3m  CC=8      ←0
  │ echo_helpers                68L  0C    4m  CC=8      ←1
  │ base                        68L  1C    7m  CC=5      ←12
  │ api                         67L  0C    5m  CC=4      ←0
  │ graphql_source              66L  1C    4m  CC=5      ←0
  │ __init__                    66L  0C    0m  CC=0.0    ←0
  │ full-diagnostic.testql.toon.yaml    66L  0C    0m  CC=0.0    ←0
  │ run_ir_cmd                  65L  0C    3m  CC=3      ←0
  │ sql                         65L  0C    4m  CC=5      ←0
  │ test-gui-connect-workshop.testql.toon.yaml    65L  0C    0m  CC=0.0    ←0
  │ renderer                    64L  0C    4m  CC=7      ←1
  │ pytest_target               64L  1C    4m  CC=5      ←0
  │ screenshot_tools            62L  0C    2m  CC=12     ←1
  │ client                      62L  2C    6m  CC=5      ←0
  │ endpoint_detector           62L  0C    0m  CC=0.0    ←0
  │ _converter                  62L  0C    0m  CC=0.0    ←0
  │ _context                    61L  1C    3m  CC=5      ←0
  │ generator                   61L  0C    0m  CC=0.0    ←0
  │ test-gui-connect-test.testql.toon.yaml    61L  0C    0m  CC=0.0    ←0
  │ models                      60L  2C    2m  CC=2      ←0
  │ registry                    59L  1C    6m  CC=5      ←2
  │ base                        59L  3C    3m  CC=1      ←0
  │ express_detector            59L  1C    3m  CC=5      ←0
  │ graphql                     59L  0C    3m  CC=5      ←0
  │ templates                   59L  0C    0m  CC=0.0    ←0
  │ generate_topology_cmd       58L  0C    2m  CC=5      ←0
  │ core                        58L  0C    3m  CC=5      ←0
  │ create-todays-reports.testql.toon.yaml    58L  0C    0m  CC=0.0    ←0
  │ __init__                    56L  0C    0m  CC=0.0    ←0
  │ context                     54L  0C    3m  CC=4      ←1
  │ package_node                54L  1C    2m  CC=14     ←0
  │ __init__                    54L  0C    0m  CC=0.0    ←0
  │ __init__                    53L  0C    1m  CC=2      ←0
  │ __init__                    53L  0C    3m  CC=1      ←1
  │ dom_scan_models             53L  4C    0m  CC=0.0    ←0
  │ __init__                    53L  0C    0m  CC=0.0    ←0
  │ element_assert              52L  1C    1m  CC=5      ←1
  │ __init__                    52L  0C    0m  CC=0.0    ←0
  │ recorded-test-session.testql.toon.yaml    52L  0C    0m  CC=0.0    ←0
  │ convenience                 51L  0C    2m  CC=1      ←0
  │ django_detector             51L  1C    2m  CC=4      ←0
  │ serializers                 51L  0C    3m  CC=5      ←4
  │ __init__                    50L  0C    0m  CC=0.0    ←0
  │ test-gui-connect-config.testql.toon.yaml    50L  0C    0m  CC=0.0    ←0
  │ generate_ir_cmd             49L  0C    2m  CC=2      ←0
  │ dispatcher                  49L  0C    1m  CC=3      ←0
  │ llm_fallback                49L  3C    4m  CC=1      ←1
  │ connect-reports-year.testql.toon.yaml    49L  0C    0m  CC=0.0    ←0
  │ websocket_detector          48L  1C    2m  CC=3      ←0
  │ test-gui-connect-reports.testql.toon.yaml    48L  0C    0m  CC=0.0    ←0
  │ encoder                     47L  0C    3m  CC=5      ←0
  │ test-gui-connect-manager.testql.toon.yaml    47L  0C    0m  CC=0.0    ←0
  │ discover_cmd                46L  0C    2m  CC=9      ←0
  │ mock_llm                    46L  1C    2m  CC=6      ←1
  │ shell                       46L  0C    3m  CC=5      ←0
  │ self_test_cmd               45L  0C    2m  CC=4      ←0
  │ session-recording.testql.toon.yaml    45L  0C    0m  CC=0.0    ←0
  │ connect-reports-month.testql.toon.yaml    45L  0C    0m  CC=0.0    ←0
  │ email_checker               44L  1C    2m  CC=10     ←0
  │ container_compose           44L  1C    3m  CC=9      ←0
  │ connect-id-rfid.testql.toon.yaml    44L  0C    0m  CC=0.0    ←0
  │ __init__                    43L  0C    1m  CC=2      ←0
  │ connect-reports-week.testql.toon.yaml    43L  0C    0m  CC=0.0    ←0
  │ file_checker                42L  1C    1m  CC=9      ←0
  │ plan                        42L  1C    1m  CC=3      ←0
  │ llm_provider                42L  1C    3m  CC=4      ←2
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
  │ registry                    35L  1C    4m  CC=2      ←1
  │ conversation                35L  1C    1m  CC=6      ←0
  │ inspect_cmd                 34L  0C    1m  CC=6      ←0
  │ assertions                  34L  0C    1m  CC=9      ←1
  │ base                        34L  1C    3m  CC=6      ←0
  │ __init__                    34L  0C    0m  CC=0.0    ←0
  │ connect-id-qr.testql.toon.yaml    34L  0C    0m  CC=0.0    ←0
  │ _parser                     33L  2C    1m  CC=5      ←2
  │ testtoon_models             33L  2C    1m  CC=3      ←0
  │ fixtures                    33L  1C    1m  CC=1      ←0
  │ assertions                  33L  1C    1m  CC=3      ←0
  │ source                      33L  2C    2m  CC=4      ←0
  │ json_reporter               33L  0C    1m  CC=2      ←0
  │ __init__                    33L  0C    0m  CC=0.0    ←0
  │ navigate                    32L  0C    1m  CC=6      ←0
  │ wmctrl                      32L  0C    1m  CC=3      ←1
  │ base                        32L  1C    1m  CC=1      ←0
  │ coverage_optimizer          32L  3C    2m  CC=1      ←0
  │ api                         31L  0C    1m  CC=6      ←0
  │ metadata                    31L  1C    1m  CC=3      ←0
  │ gui                         30L  0C    1m  CC=2      ←0
  │ assert_json                 30L  0C    2m  CC=5      ←0
  │ oql_models                  30L  2C    0m  CC=0.0    ←0
  │ __init__                    30L  0C    0m  CC=0.0    ←0
  │ generators                  30L  0C    0m  CC=0.0    ←0
  │ interpolation               29L  0C    1m  CC=6      ←7
  │ test-app-lifecycle.testql.toon.yaml    29L  0C    0m  CC=0.0    ←0
  │ nl_source                   27L  1C    1m  CC=2      ←0
  │ select                      26L  0C    1m  CC=3      ←0
  │ edge_case_generator         26L  2C    2m  CC=1      ←0
  │ models                      26L  2C    0m  CC=0.0    ←0
  │ reproduce-view.testql.toon.yaml    26L  0C    0m  CC=0.0    ←0
  │ test-gui-all.testql.toon.yaml    26L  0C    0m  CC=0.0    ←0
  │ __init__                    25L  0C    0m  CC=0.0    ←0
  │ connect-config-users.testql.toon.yaml    25L  0C    0m  CC=0.0    ←0
  │ record                      24L  0C    2m  CC=1      ←0
  │ base                        24L  2C    1m  CC=1      ←0
  │ __init__                    24L  0C    1m  CC=3      ←0
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
  │ __init__                    21L  0C    0m  CC=0.0    ←0
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
  │ device-identification.testql.toon.yaml    19L  0C    0m  CC=0.0    ←0
  │ encoder-workshop.testql.toon.yaml    19L  0C    0m  CC=0.0    ←0
  │ unknown                     18L  0C    1m  CC=3      ←1
  │ __init__                    18L  0C    0m  CC=0.0    ←0
  │ __init__                    17L  0C    0m  CC=0.0    ←0
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
  │ __init__                    12L  0C    0m  CC=0.0    ←0
  │ test-dsl-objects.testql.toon.yaml    12L  0C    0m  CC=0.0    ←0
  │ health-check.testql.toon.yaml    12L  0C    0m  CC=0.0    ←0
  │ quick-navigation.testql.toon.yaml    11L  0C    0m  CC=0.0    ←0
  │ api-smoke.testql.toon.yaml    11L  0C    0m  CC=0.0    ←0
  │ run-mask-test-protocol.testql.toon.yaml    11L  0C    0m  CC=0.0    ←0
  │ auth-login.testql.toon.yaml    11L  0C    0m  CC=0.0    ←0
  │ __init__                    10L  0C    0m  CC=0.0    ←0
  │ __init__                    10L  0C    0m  CC=0.0    ←0
  │ test-devices-crud.testql.toon.yaml    10L  0C    0m  CC=0.0    ←0
  │ test-devices-crud.testql.toon.yaml    10L  0C    0m  CC=0.0    ←0
  │ __init__                     9L  0C    0m  CC=0.0    ←0
  │ __init__                     9L  0C    0m  CC=0.0    ←0
  │ test-protocol-flow.testql.toon.yaml     9L  0C    0m  CC=0.0    ←0
  │ __init__                     8L  0C    0m  CC=0.0    ←0
  │ __init__                     7L  0C    0m  CC=0.0    ←0
  │ api-health.testql.toon.yaml     7L  0C    0m  CC=0.0    ←0
  │ __main__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │
  packages/                       CC̄=3.6    ←in:0  →out:0
  │ patch                      199L  1C    9m  CC=12     ←2
  │ query                      179L  1C   10m  CC=9      ←4
  │ pb_codec                   126L  0C   11m  CC=6      ←5
  │ server                     118L  1C    6m  CC=2      ←3
  │ cli_handlers               113L  0C    8m  CC=7      ←0
  │ materialize                109L  1C    5m  CC=9      ←2
  │ uri                        102L  0C    8m  CC=7      ←3
  │ events                     101L  2C    5m  CC=7      ←3
  │ block_resolver              91L  1C    5m  CC=14     ←1
  │ cli                         89L  0C    3m  CC=9      ←0
  │ grammar                     81L  0C    7m  CC=6      ←4
  │ bus                         76L  0C    5m  CC=6      ←5
  │ command                     72L  0C    4m  CC=7      ←1
  │ pipeline                    59L  0C    2m  CC=6      ←3
  │ cli_handlers                56L  0C    4m  CC=6      ←1
  │ cli                         51L  0C    2m  CC=6      ←0
  │ schema_registry             46L  0C    5m  CC=3      ←3
  │ models                      44L  2C    1m  CC=1      ←0
  │ command_pb2                 44L  0C    0m  CC=0.0    ←0
  │ query                       41L  0C    2m  CC=5      ←1
  │ result_pb2                  39L  0C    0m  CC=0.0    ←0
  │ codec                       35L  0C    4m  CC=3      ←0
  │ command.proto               35L  0C    0m  CC=0.0    ←0
  │ cli                         32L  0C    1m  CC=4      ←0
  │ pyproject.toml              31L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              31L  0C    0m  CC=0.0    ←0
  │ __init__                    30L  0C    0m  CC=0.0    ←0
  │ result                      28L  1C    1m  CC=1      ←0
  │ pyproject.toml              27L  0C    0m  CC=0.0    ←0
  │ files                       26L  0C    1m  CC=8      ←3
  │ validate                    26L  0C    2m  CC=2      ←3
  │ engine                      24L  0C    3m  CC=1      ←0
  │ result.proto                23L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              18L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              17L  0C    0m  CC=0.0    ←0
  │ __init__                    13L  0C    0m  CC=0.0    ←0
  │ patch.schema.json           12L  0C    0m  CC=0.0    ←0
  │ query.schema.json           12L  0C    0m  CC=0.0    ←0
  │ generate.schema.json        11L  0C    0m  CC=0.0    ←0
  │ validate.schema.json        10L  0C    0m  CC=0.0    ←0
  │ generate-proto.sh            7L  0C    0m  CC=0.0    ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=0.8    ←in:0  →out:0
  │ !! screen.imgl.json          8136L  0C    0m  CC=0.0    ←0
  │ run-matrix.sh              101L  0C    0m  CC=0.0    ←0
  │ Makefile                    88L  0C    0m  CC=0.0    ←0
  │ Makefile                    78L  0C    0m  CC=0.0    ←0
  │ run.sh                      72L  0C    0m  CC=0.0    ←0
  │ run-all.sh                  71L  0C    1m  CC=0.0    ←0
  │ run.sh                      64L  0C    1m  CC=0.0    ←14
  │ mock_server                 50L  0C    8m  CC=2      ←0
  │ interact-shot.imgl.json     43L  0C    0m  CC=0.0    ←0
  │ gui-e2e-inspect.imgl.json    43L  0C    0m  CC=0.0    ←0
  │ run.sh                      42L  0C    1m  CC=0.0    ←0
  │ crud-workflow.testql.yaml    42L  0C    0m  CC=0.0    ←0
  │ app.doql                    41L  0C    0m  CC=0.0    ←0
  │ run.sh                      37L  0C    0m  CC=0.0    ←0
  │ generate_bundle             36L  0C    1m  CC=2      ←0
  │ login-form.testql.yaml      34L  0C    0m  CC=0.0    ←0
  │ mixed-smoke.testql.yaml     33L  0C    0m  CC=0.0    ←0
  │ run.sh                      27L  0C    0m  CC=0.0    ←0
  │ complex-replay.testql.toon.yaml    27L  0C    0m  CC=0.0    ←0
  │ Makefile                    24L  0C    0m  CC=0.0    ←0
  │ Makefile                    24L  0C    0m  CC=0.0    ←0
  │ basic-encoder.testql.yaml    23L  0C    0m  CC=0.0    ←0
  │ run.sh                      23L  0C    0m  CC=0.0    ←0
  │ run.sh                      22L  0C    0m  CC=0.0    ←0
  │ Makefile                    22L  0C    0m  CC=0.0    ←0
  │ run.sh                      22L  0C    0m  CC=0.0    ←0
  │ run.sh                      22L  0C    0m  CC=0.0    ←0
  │ Makefile                    21L  0C    0m  CC=0.0    ←0
  │ run.sh                      21L  0C    0m  CC=0.0    ←0
  │ mixed-smoke.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │ inspect-web.sh              20L  0C    0m  CC=0.0    ←0
  │ login-form.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │ Makefile                    20L  0C    0m  CC=0.0    ←0
  │ health-check.testql.yaml    19L  0C    0m  CC=0.0    ←0
  │ run-all.sh                  18L  0C    1m  CC=0.0    ←0
  │ Makefile                    18L  0C    0m  CC=0.0    ←0
  │ run.sh                      18L  0C    0m  CC=0.0    ←0
  │ topology.sh                 18L  0C    0m  CC=0.0    ←0
  │ Makefile                    18L  0C    0m  CC=0.0    ←0
  │ Makefile                    18L  0C    0m  CC=0.0    ←0
  │ Makefile                    18L  0C    0m  CC=0.0    ←0
  │ run.sh                      17L  0C    0m  CC=0.0    ←0
  │ Makefile                    17L  0C    0m  CC=0.0    ←0
  │ Makefile                    17L  0C    0m  CC=0.0    ←0
  │ Makefile                    17L  0C    0m  CC=0.0    ←0
  │ api-contract.testql.toon.yaml    17L  0C    0m  CC=0.0    ←0
  │ Makefile                    17L  0C    0m  CC=0.0    ←0
  │ run.sh                      16L  0C    0m  CC=0.0    ←0
  │ Makefile                    15L  0C    0m  CC=0.0    ←0
  │ crud-workflow.testql.toon.yaml    15L  0C    0m  CC=0.0    ←0
  │ assertions.testql.toon.yaml    14L  0C    0m  CC=0.0    ←0
  │ discover-local.sh           14L  0C    0m  CC=0.0    ←0
  │ variables.testql.toon.yaml    13L  0C    0m  CC=0.0    ←0
  │ health-check.testql.toon.yaml    13L  0C    0m  CC=0.0    ←0
  │ run.sh                      13L  0C    0m  CC=0.0    ←0
  │ basic-commands.testql.yaml    12L  0C    0m  CC=0.0    ←0
  │ interact-shot.png.vdisplay.json    12L  0C    0m  CC=0.0    ←0
  │ click-shot.png.vdisplay.json    12L  0C    0m  CC=0.0    ←0
  │ capture-dp2.png.vdisplay.json    12L  0C    0m  CC=0.0    ←0
  │ gui-e2e-inspect.png.vdisplay.json    12L  0C    0m  CC=0.0    ←0
  │ capture-hdmi.png.vdisplay.json    12L  0C    0m  CC=0.0    ←0
  │ capture-dp1.png.vdisplay.json    12L  0C    0m  CC=0.0    ←0
  │ gui-e2e-interact.testql.toon.yaml    11L  0C    0m  CC=0.0    ←0
  │ basic-encoder.testql.toon.yaml    11L  0C    0m  CC=0.0    ←0
  │ gui-e2e-inspect.testql.toon.yaml     9L  0C    0m  CC=0.0    ←0
  │ basic-commands.testql.toon.yaml     7L  0C    0m  CC=0.0    ←0
  │ minimal.testql.toon.yaml     7L  0C    0m  CC=0.0    ←0
  │ routes.txt                   3L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=0.0    ←in:0  →out:0
  │ install_testql_autoloop.sh   156L  0C    2m  CC=0.0    ←0
  │ setup_mcp_windsurf.sh       91L  0C    1m  CC=0.0    ←0
  │ smoke_manifest_flow.sh      70L  0C    1m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! planfile.yaml             1319L  0C    0m  CC=0.0    ←0
  │ !! tree.txt                  1252L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  511L  0C    0m  CC=0.0    ←0
  │ sumd.json                  204L  0C    0m  CC=0.0    ←0
  │ Taskfile.yml               185L  0C    0m  CC=0.0    ←0
  │ openapi.yaml               175L  0C    0m  CC=0.0    ←0
  │ Taskfile.testql.yml        117L  0C    0m  CC=0.0    ←0
  │ pyproject.toml             109L  0C    0m  CC=0.0    ←0
  │ Makefile                    99L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                91L  0C    0m  CC=0.0    ←0
  │ pyqual.yaml                 71L  0C    0m  CC=0.0    ←0
  │ project.sh                  50L  0C    0m  CC=0.0    ←0
  │ coverage.json                1L  0C    0m  CC=0.0    ←0
  │ topology.toon.yaml           0L  0C    0m  CC=0.0    ←0
  │
  docs/                           CC̄=0.0    ←in:0  →out:0
  │ conversation-refactor-plan.toon.yaml    56L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-api-smoke.testql.toon.yaml    35L  0C    0m  CC=0.0    ←0
  │ generated-sitemap-assert.testql.toon.yaml    29L  0C    0m  CC=0.0    ←0
  │ generated-cli-extended.testql.toon.yaml    23L  0C    0m  CC=0.0    ←0
  │ generated-asset-assert.testql.toon.yaml    23L  0C    0m  CC=0.0    ←0
  │ generated-from-pytests.testql.toon.yaml    23L  0C    0m  CC=0.0    ←0
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
  ── zero ──
     topology.toon.yaml                        0L

COUPLING:
                               examples.browser-inspection                       testql              testql.commands          packages.dsl2testql           testql.interpreter              testql.adapters            testql.generators               testql.results          packages.mcp2testql             testql.ir_runner              testql.topology                         TODO          packages.uri2testql          testql.integrations          packages.cli2testql
  examples.browser-inspection                           ──                          ←22                           ←3                          ←14                           ←1                                                                                                                                                                                                         ←8                                                        ←8                           ←5  hub
                       testql                           22                           ──                          ←13                           ←1                           ←3                           ←6                           ←6                                                         1                           ←2                                                                                                                                                   hub
              testql.commands                            3                           13                           ──                                                                                      4                            7                            7                                                         1                            3                                                                                      1                               !! fan-out
          packages.dsl2testql                           14                            1                                                        ──                           ←9                                                                                                                  ←4                                                                                                                   2                                                        ←3  hub
           testql.interpreter                            1                            3                                                         9                           ──                                                        ←1                                                                                                                                                1                                                                                         !! fan-out
              testql.adapters                                                         6                           ←4                                                                                     ──                           ←3                                                                                     ←6                                                                                                                                                   hub
            testql.generators                                                         6                           ←7                                                         1                            3                           ──                                                                                                                  ←1                                                                                                                      hub
               testql.results                                                                                     ←7                                                                                                                                               ──                                                                                      4                                                                                                                      hub
          packages.mcp2testql                                                        ←1                                                         4                                                                                                                                               ──                                                                                                                   5                                                            !! fan-out
             testql.ir_runner                                                         2                           ←1                                                                                      6                                                                                                                  ──                                                                                                                                                   !! fan-out
              testql.topology                                                                                     ←3                                                                                                                   1                           ←4                                                                                     ──                                                                                                                      hub
                         TODO                            8                                                                                                                  ←1                                                                                                                                                                                                         ──                                                                                         !! fan-out
          packages.uri2testql                                                                                                                  ←2                                                                                                                                               ←5                                                                                                                  ──                                                            hub
          testql.integrations                            8                                                        ←1                                                                                                                                                                                                                                                                                                                             ──                               !! fan-out
          packages.cli2testql                            5                                                                                      3                                                                                                                                                                                                                                                                                                                             ──  !! fan-out
  CYCLES: none
  HUB: testql.desktop/ (fan-in=5)
  HUB: testql.adapters/ (fan-in=16)
  HUB: testql/ (fan-in=43)
  HUB: testql.topology/ (fan-in=9)
  HUB: testql.results/ (fan-in=9)
  HUB: testql.context/ (fan-in=6)
  HUB: testql.generators/ (fan-in=10)
  HUB: packages.dsl2testql/ (fan-in=16)
  HUB: packages.nlp2testql/ (fan-in=5)
  HUB: examples.browser-inspection/ (fan-in=67)
  HUB: packages.uri2testql/ (fan-in=7)
  SMELL: packages.cli2testql/ fan-out=8 → split needed
  SMELL: testql.adapters/ fan-out=8 → split needed
  SMELL: packages.mcp2testql/ fan-out=10 → split needed
  SMELL: testql/ fan-out=23 → split needed
  SMELL: TODO/ fan-out=8 → split needed
  SMELL: testql.generators/ fan-out=10 → split needed
  SMELL: packages.dsl2testql/ fan-out=19 → split needed
  SMELL: testql.commands/ fan-out=40 → split needed
  SMELL: testql.ir_runner/ fan-out=9 → split needed
  SMELL: testql.interpreter/ fan-out=25 → split needed
  SMELL: testql.integrations/ fan-out=8 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 0 groups | 1f 36L | 2026-06-09

SUMMARY:
  files_scanned: 1
  total_lines:   36
  dup_groups:    0
  dup_fragments: 0
  saved_lines:   0
  scan_ms:       2921
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 1818 func | 249f | 2026-06-09
# generated in 0.01s

NEXT[3] (ranked by impact):
  [1] !! SPLIT           testql/adapters/testtoon_adapter.py
      WHY: 742L, 1 classes, max CC=12
      EFFORT: ~4h  IMPACT: 8904

  [2] !! SPLIT           planfile.yaml
      WHY: 1319L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0

  [3] !! SPLIT           tree.txt
      WHY: 1252L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[3]:
  ⚠ Splitting planfile.yaml may break 0 import paths
  ⚠ Splitting tree.txt may break 0 import paths
  ⚠ Splitting testql/adapters/testtoon_adapter.py may break 46 import paths

METRICS-TARGET:
  CC̄:          3.8 → ≤2.7
  max-CC:      14 → ≤7
  god-modules: 11 → 0
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
  prev CC̄=3.8 → now CC̄=3.8
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
