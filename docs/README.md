<!-- code2docs:start --># testql

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-1116-green)
> **1116** functions | **107** classes | **212** files | CC̄ = 3.7

> Auto-generated project documentation from source code analysis.

**Author:** Tom Softreck <tom@sapletta.com>  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/oqlos/testql](https://github.com/oqlos/testql)

## Installation

### From PyPI

```bash
pip install testql
```

### From Source

```bash
git clone https://github.com/oqlos/testql
cd testql
pip install -e .
```

### Optional Extras

```bash
pip install testql[playwright]    # playwright features
pip install testql[dev]    # development tools
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
testql ./my-project

# Only regenerate README
testql ./my-project --readme-only

# Preview what would be generated (no file writes)
testql ./my-project --dry-run

# Check documentation health
testql check ./my-project

# Sync — regenerate only changed modules
testql sync ./my-project
```

### Python API

```python
from testql import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```




## Architecture

```
testql/
├── SUMR
├── goal
├── coverage
├── SUMD
├── pyqual
├── sumd
├── pyproject
├── tree
    ├── testql
├── TODO
├── CHANGELOG
├── Taskfile
├── openapi
├── project
├── README
    ├── testql-spec
    ├── README
    ├── context
    ├── prompt
    ├── calls
        ├── toon
        ├── toon
    ├── README
        ├── toon
        ├── toon
    ├── testql-table-format-spec
    ├── testtoon_parser
        ├── toon
        ├── toon
            ├── toon
            ├── toon
            ├── toon
            ├── toon
    ├── toon_parser
    ├── base
    ├── cli
    ├── doql_parser
    ├── report_generator
    ├── generator
    ├── runner
    ├── openapi_generator
├── testql/
    ├── __main__
    ├── echo_schemas
    ├── _base_fallback
    ├── sumd_generator
    ├── endpoint_detector
    ├── interpreter/
    ├── sumd_parser
        ├── generate_cmd
        ├── echo/
        ├── misc_cmds
    ├── commands/
        ├── encoder_routes
        ├── run_cmd
        ├── echo_helpers
        ├── endpoints_cmd
        ├── suite_cmd
            ├── content
        ├── templates/
            ├── templates
            ├── cli
            ├── execution
            ├── listing
        ├── suite/
            ├── collection
            ├── reports
            ├── cli
            ├── context
            ├── formatters/
                ├── text
                ├── toon
            ├── parsers/
                ├── doql
        ├── _testtoon_parser
        ├── _parser
        ├── _api_runner
        ├── _gui
        ├── _shell
        ├── _converter
        ├── _unit
        ├── _flow
        ├── _encoder
        ├── _assertions
        ├── interpreter
        ├── _websockets
        ├── dispatcher
            ├── parsers
        ├── converter/
            ├── models
            ├── core
            ├── renderer
            ├── dispatcher
                ├── encoder
                ├── assertions
                ├── unknown
                ├── include
            ├── handlers/
                ├── api
                ├── select
                ├── navigate
                ├── flow
                ├── wait
                ├── record
    ├── reporters/
        ├── console
        ├── json_reporter
        ├── junit
        ├── convenience
        ├── base
    ├── generators/
        ├── multi
        ├── analyzers
        ├── generators
        ├── graphql_detector
        ├── fastapi_detector
        ├── base
        ├── django_detector
        ├── websocket_detector
    ├── detectors/
        ├── unified
        ├── flask_detector
        ├── models
        ├── openapi_detector
        ├── express_detector
        ├── config_detector
    ├── runners/
                    ├── toon
                    ├── toon
                    ├── toon
                    ├── toon
                    ├── toon
                    ├── toon
                    ├── toon
                    ├── toon
                    ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                        ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                            ├── toon
                        ├── toon
                        ├── toon
                    ├── toon
                    ├── toon
                    ├── toon
        ├── toon
        ├── toon
    ├── prompt
    ├── context
        ├── toon
    ├── README
        ├── toon
    ├── calls
        ├── toon
```

## API Overview

### Classes

- **`StepStatus`** — —
- **`StepResult`** — —
- **`ScriptResult`** — —
- **`VariableStore`** — —
- **`InterpreterOutput`** — —
- **`BaseInterpreter`** — —
- **`EventBridge`** — —
- **`OpenAPISpec`** — —
- **`OpenAPIGenerator`** — —
- **`ContractTestGenerator`** — —
- **`DslCommand`** — —
- **`ExecutionResult`** — —
- **`DslCliExecutor`** — —
- **`SumdMetadata`** — —
- **`SumdInterface`** — —
- **`SumdWorkflow`** — —
- **`SumdDocument`** — —
- **`SumdParser`** — —
- **`StepStatus`** — —
- **`StepResult`** — —
- **`ScriptResult`** — —
- **`VariableStore`** — —
- **`InterpreterOutput`** — —
- **`BaseInterpreter`** — —
- **`EventBridge`** — —
- **`OpenAPISpec`** — —
- **`OpenAPIGenerator`** — —
- **`ContractTestGenerator`** — —
- **`DslCommand`** — —
- **`ExecutionResult`** — —
- **`DslCliExecutor`** — —
- **`SumdMetadata`** — —
- **`SumdInterface`** — —
- **`SumdWorkflow`** — —
- **`SumdDocument`** — —
- **`SumdParser`** — —
- **`Section`** — —
- **`Section`** — —
- **`ToonParser`** — Parser for toon test files.
- **`DoqlParser`** — Parser for doql LESS files.
- **`TestResult`** — Single test result.
- **`TestSuiteReport`** — Test suite report data.
- **`ReportDataParser`** — Parse test results into structured data.json format.
- **`HTMLReportGenerator`** — Generate HTML reports from test data.
- **`DslCommand`** — —
- **`ExecutionResult`** — —
- **`DslCliExecutor`** — —
- **`OpenAPISpec`** — OpenAPI specification container.
- **`OpenAPIGenerator`** — Generate OpenAPI specs from detected endpoints.
- **`ContractTestGenerator`** — Generate contract tests from OpenAPI specs.
- **`APIContract`** — API contract layer from toon tests.
- **`Entity`** — Entity from doql model.
- **`Workflow`** — Workflow from doql.
- **`Interface`** — Interface from doql.
- **`SystemModel`** — System model from doql.
- **`ProjectEcho`** — Combined project echo for LLM consumption.
- **`StepStatus`** — —
- **`StepResult`** — —
- **`ScriptResult`** — —
- **`VariableStore`** — Simple key-value store with interpolation support.
- **`InterpreterOutput`** — Collects interpreter output lines for display or testing.
- **`BaseInterpreter`** — Abstract base for language interpreters.
- **`EventBridge`** — Optional WebSocket bridge to DSL Event Server (port 8104).
- **`SumdMetadata`** — Metadata from SUMD.
- **`SumdInterface`** — Interface from SUMD.
- **`SumdWorkflow`** — Workflow from SUMD.
- **`SumdDocument`** — Parsed SUMD document.
- **`SumdParser`** — Parser for SUMD markdown files.
- **`TestContentBuilder`** — Builds test content for different test types.
- **`ToonSection`** — —
- **`ToonScript`** — —
- **`IqlLine`** — —
- **`IqlScript`** — —
- **`ApiRunnerMixin`** — Mixin providing HTTP API execution commands: API, CAPTURE.
- **`GuiMixin`** — Mixin providing desktop GUI test commands using Playwright.
- **`ShellMixin`** — Mixin providing shell command execution: SHELL, EXEC, RUN, ASSERT_EXIT_CODE, etc.
- **`UnitMixin`** — Mixin providing unit test execution: UNIT_PYTEST, UNIT_IMPORT, UNIT_ASSERT.
- **`FlowMixin`** — Mixin providing: WAIT, LOG, PRINT, INCLUDE and _emit_event.
- **`EncoderMixin`** — Mixin providing all ENCODER_* hardware control commands.
- **`AssertionsMixin`** — Mixin providing ASSERT_STATUS, ASSERT_OK, ASSERT_CONTAINS, ASSERT_JSON.
- **`IqlInterpreter`** — IQL interpreter — runs .testql.toon.yaml / .iql / .tql scripts.
- **`WebSocketMixin`** — Mixin for WebSocket testing support.
- **`CommandDispatcher`** — Central command dispatcher with auto-discovery and better error messages.
- **`Row`** — A row of values in a section.
- **`Section`** — A section in the converted output.
- **`JUnitReporter`** — Generate JUnit XML from a TestQL ScriptResult.
- **`TestPattern`** — Discovered test pattern from source code.
- **`ProjectProfile`** — Analyzed project profile.
- **`BaseAnalyzer`** — Base class for project analyzers.
- **`MultiProjectTestGenerator`** — Generator that operates across multiple projects in a workspace.
- **`ProjectAnalyzer`** — Analyzes project structure to discover testable patterns.
- **`APIGeneratorMixin`** — Mixin for generating API-focused test scenarios.
- **`PythonTestGeneratorMixin`** — Mixin for generating tests from existing Python tests.
- **`ScenarioGeneratorMixin`** — Mixin for generating tests from OQL/CQL scenarios.
- **`SpecializedGeneratorMixin`** — Mixin for generating specialized test types.
- **`GraphQLDetector`** — Detect GraphQL schemas and resolvers.
- **`FastAPIDetector`** — Detect FastAPI endpoints using AST analysis.
- **`BaseEndpointDetector`** — Base class for endpoint detectors.
- **`DjangoDetector`** — Detect Django URL patterns.
- **`WebSocketDetector`** — Detect WebSocket endpoints.
- **`UnifiedEndpointDetector`** — Unified detector that runs all specialized detectors.
- **`FlaskDetector`** — Detect Flask endpoints including Blueprints.
- **`EndpointInfo`** — Standardized endpoint information.
- **`ServiceInfo`** — Information about a service/application.
- **`OpenAPIDetector`** — Detect endpoints from OpenAPI/Swagger specifications.
- **`ExpressDetector`** — Detect Express.js routes from JavaScript/TypeScript files.
- **`ConfigEndpointDetector`** — Detect endpoints from configuration files.

### Functions

- `passed()` — —
- `failed()` — —
- `summary()` — —
- `set()` — —
- `get()` — —
- `has()` — —
- `all()` — —
- `clear()` — —
- `interpolate()` — —
- `emit()` — —
- `info()` — —
- `ok()` — —
- `fail()` — —
- `warn()` — —
- `error()` — —
- `step()` — —
- `parse()` — —
- `execute()` — —
- `run()` — —
- `run_file()` — —
- `strip_comments()` — —
- `connect()` — —
- `disconnect()` — —
- `send_event()` — —
- `connected()` — —
- `generate_openapi_spec()` — —
- `generate_contract_tests_from_spec()` — —
- `to_dict()` — —
- `to_json()` — —
- `to_yaml()` — —
- `generate()` — —
- `save()` — —
- `generate_contract_tests()` — —
- `validate_response()` — —
- `parse_line()` — —
- `parse_script()` — —
- `main()` — —
- `cmd_api()` — —
- `cmd_wait()` — —
- `cmd_log()` — —
- `cmd_print()` — —
- `cmd_store()` — —
- `cmd_env()` — —
- `cmd_assert_status()` — —
- `cmd_assert_json()` — —
- `cmd_set_header()` — —
- `cmd_set_base_url()` — —
- `run_script()` — —
- `generate_sumd()` — —
- `save_sumd()` — —
- `parse_sumd_file()` — —
- `parse_file()` — —
- `generate_testql_scenarios()` — —
- `detect_separator()` — —
- `parse_value()` — —
- `parse_testtoon()` — —
- `validate()` — —
- `print_parsed()` — —
- `cli()` — —
- `main()` — —
- `echo()` — —
- `generate_context()` — —
- `format_text_output()` — —
- `parse_doql_less()` — —
- `parse_toon_scenarios()` — —
- `collect_toon_data()` — —
- `collect_doql_data()` — —
- `render_echo()` — —
- `iql_list_files()` — —
- `iql_read_file()` — —
- `iql_list_tables()` — —
- `iql_run_line()` — —
- `iql_run_file()` — —
- `iql_list_logs()` — —
- `iql_read_log()` — —
- `endpoints()` — —
- `openapi()` — —
- `generate()` — —
- `analyze()` — —
- `init()` — —
- `create()` — —
- `watch()` — —
- `from_sumd()` — —
- `report()` — —
- `run()` — —
- `suite()` — —
- `list_tests()` — —
- `collect_test_files()` — —
- `collect_list_files()` — —
- `run_single_file()` — —
- `run_suite_files()` — —
- `parse_meta()` — —
- `filter_tests()` — —
- `render_test_list()` — —
- `build_report_data()` — —
- `save_report()` — —
- `print_summary()` — —
- `detect_endpoints()` — —
- `parse_doql_file()` — —
- `generate_for_project()` — —
- `generate_for_workspace()` — —
- `parse_iql()` — —
- `validate_testtoon()` — —
- `testtoon_to_iql()` — —
- `convert_iql_to_testtoon()` — —
- `convert_file()` — —
- `convert_directory()` — —
- `dispatch()` — —
- `handle_api()` — —
- `collect_assert()` — —
- `handle_encoder()` — —
- `handle_flow()` — —
- `handle_include()` — —
- `handle_navigate()` — —
- `handle_record_start()` — —
- `handle_record_stop()` — —
- `handle_select()` — —
- `handle_unknown()` — —
- `handle_wait()` — —
- `parse_api_args()` — —
- `parse_meta_from_args()` — —
- `parse_target_from_args()` — —
- `parse_commands()` — —
- `detect_scenario_type()` — —
- `extract_scenario_name()` — —
- `build_config_section()` — —
- `render_sections()` — —
- `build_header()` — —
- `generate_openapi_spec()` — —
- `generate_contract_tests_from_spec()` — —
- `generate_report()` — —
- `report_console()` — —
- `report_json()` — —
- `report_junit()` — —
- `parse_line()` — —
- `parse_script()` — —
- `generate_sumd()` — —
- `save_sumd()` — —
- `parse_sumd_file()` — —
- `parse_toon_file()` — —
- `write_toon()` — —
- `test_normalize_legacy_test_path()` — —
- `test_normalize_legacy_view_path()` — —
- `test_normalize_testql_prefixed_path()` — —
- `test_normalize_passthrough_diagnostics_path()` — —
- `test_normalize_testtoon_path()` — —
- `test_resolve_new_format()` — —
- `make_result()` — —
- `make_step()` — —
- `passed()` — —
- `failed()` — —
- `summary()` — —
- `set()` — —
- `get()` — —
- `has()` — —
- `all()` — —
- `clear()` — —
- `interpolate()` — —
- `emit()` — —
- `info()` — —
- `ok()` — —
- `fail()` — —
- `warn()` — —
- `error()` — —
- `step()` — —
- `parse()` — —
- `execute()` — —
- `run_file()` — —
- `strip_comments()` — —
- `connect()` — —
- `disconnect()` — —
- `send_event()` — —
- `connected()` — —
- `to_dict()` — —
- `to_json()` — —
- `to_yaml()` — —
- `save()` — —
- `generate_contract_tests()` — —
- `validate_response()` — —
- `cmd_api()` — —
- `cmd_wait()` — —
- `cmd_log()` — —
- `cmd_print()` — —
- `cmd_store()` — —
- `cmd_env()` — —
- `cmd_assert_status()` — —
- `cmd_assert_json()` — —
- `cmd_set_header()` — —
- `cmd_set_base_url()` — —
- `run_script()` — —
- `parse_file()` — —
- `generate_testql_scenarios()` — —
- `generate_readme()` — —
- `convert_iql_to_testtoon()` — —
- `convert_file()` — —
- `convert_directory()` — —
- `cli()` — —
- `run()` — —
- `generate()` — —
- `analyze()` — —
- `endpoints()` — —
- `openapi()` — —
- `init()` — —
- `create()` — —
- `suite()` — —
- `list()` — —
- `echo()` — —
- `watch()` — —
- `from_sumd()` — —
- `report()` — —
- `main()` — —
- `generate_sumd()` — —
- `save_sumd()` — —
- `parse_doql_less()` — —
- `parse_toon_scenarios()` — —
- `generate_context()` — —
- `format_text_output()` — —
- `generate_for_project()` — —
- `generate_for_workspace()` — —
- `detect_endpoints()` — —
- `detect_separator()` — —
- `parse_value()` — —
- `parse_testtoon()` — —
- `validate()` — —
- `print_parsed()` — —
- `parse_line()` — —
- `parse_script()` — —
- `parse_sumd_file()` — —
- `validate_testtoon()` — —
- `testtoon_to_iql()` — —
- `iql_list_files()` — —
- `iql_read_file()` — —
- `iql_list_tables()` — —
- `iql_run_line()` — —
- `iql_run_file()` — —
- `iql_list_logs()` — —
- `iql_read_log()` — —
- `generate_openapi_spec()` — —
- `generate_contract_tests_from_spec()` — —
- `report_junit()` — —
- `parse_doql_file()` — —
- `report_console()` — —
- `generate_report()` — —
- `parse_iql()` — —
- `parse_toon_file()` — —
- `report_json()` — —
- `parse_testtoon()` — —
- `print()` — —
- `validate()` — —
- `detect_separator(line)` — Użyj | jeśli wiersz zawiera |, inaczej ,
- `parse_value(v)` — Parsuj wartości: -, liczby, {json}, tablice [1,2], stringi
- `parse_testtoon(text)` — —
- `validate(parsed)` — —
- `print_parsed(parsed)` — —
- `parse_toon_file(path)` — Parse a toon test file.
- `cli()` — TestQL — Interface Query Language for Testing.
- `main()` — Entry point for console script.
- `parse_doql_file(path)` — Parse a doql LESS file.
- `generate_report(data_json, output_html)` — Generate HTML report from data.json file.
- `parse_line(line)` — Parse a single DSL line
- `parse_script(content)` — Parse DSL script into commands
- `main()` — —
- `generate_openapi_spec(project_path, output, format)` — Convenience function to generate OpenAPI spec.
- `generate_contract_tests_from_spec(spec_path, output)` — Generate contract tests from existing OpenAPI spec.
- `generate_sumd(project_echo, project_path)` — Generate SUMD.md content from project echo.
- `save_sumd(project_echo, project_path, output_path)` — Generate and save SUMD.md file.
- `parse_sumd_file(path)` — Parse a SUMD.md file.
- `generate(path, output_dir, analyze_only, fmt)` — Generate TestQL scenarios from project structure.
- `analyze(path)` — Analyze project structure and show testability report.
- `init(path, name, project_type)` — Initialize TestQL project with templates and config.
- `create(name, test_type, module, output)` — Create new test file from template.
- `watch(path, pattern, command, debounce)` — Watch for file changes and re-run tests automatically.
- `from_sumd(sumd_file, output, dry_run)` — Generate TestQL scenarios from SUMD.md documentation.
- `report(data_json, output, example)` — Generate HTML report from test data.json.
- `echo(toon_path, doql_path, fmt, output)` — Generate AI-friendly project metadata echo from toon tests and doql model.
- `iql_list_files()` — List all .testql.toon.yaml files in the project (with .iql/.tql fallback).
- `iql_read_file(path)` — Read a TestQL file content (.testql.toon.yaml / .iql / .tql).
- `iql_list_tables(path)` — Extract table names from an IQL file.
- `iql_run_line(req)` — Execute a single IQL command line via the encoder bridge.
- `iql_run_file(req)` — Run an entire IQL file with validation. Returns structured results + saves log.
- `iql_list_logs()` — List available log files.
- `iql_read_log(name)` — Read a specific log file.
- `run(file, url, dry_run, output)` — Run a TestQL (.testql.toon.yaml) scenario.
- `collect_toon_data(toon_path, project_echo)` — Collect data from toon test files.
- `collect_doql_data(doql_path, project_echo)` — Collect data from doql LESS file.
- `render_echo(project_echo, fmt, project_path_obj)` — Render project echo in specified format.
- `endpoints(path, fmt, framework, endpoint_type)` — List all detected API endpoints in a project.
- `openapi(path, output, format, title)` — Generate OpenAPI spec from detected endpoints.
- `suite(suite_name, base_path, pattern, tags)` — Run test suite(s) — predefined or custom pattern.
- `list_tests(path, test_type, tag, fmt)` — List all available tests with metadata.
- `run_single_file(test_file, interp)` — Run a single test file and return result dict.
- `run_suite_files(test_files, url, output, fail_fast)` — Run suite of test files and return results.
- `parse_meta(tf, yaml_module)` — Parse test file metadata.
- `filter_tests(raw_files, target_path, test_type, tag)` — Parse meta and apply type/tag filters.
- `render_test_list(tests, fmt)` — Render test list in requested format.
- `collect_test_files(target_path, suite_name, pattern, config)` — Collect test files based on suite, pattern, or default recursive search.
- `collect_list_files(target_path)` — Glob test files from standard search locations.
- `build_report_data(suite_name, results, total_passed, total_failed)` — Build report data structure.
- `save_report(report_data, report_file, output)` — Save report in requested format.
- `print_summary(results, total_passed, total_failed, total_duration)` — Print execution summary to console.
- `echo(path, fmt, no_toon, no_doql)` — Generate AI-friendly project context (echo) from toon + doql.
- `generate_context(path, include_toon, include_doql)` — Generate unified project context from DOQL and TOON sources.
- `format_text_output(context)` — Format context as human-readable text.
- `parse_toon_scenarios(path)` — Parse .testql.toon.yaml files into API contract structure.
- `parse_doql_less(filepath)` — Parse .doql.less file into structured system model.
- `parse_testtoon(text, filename)` — Parse TestTOON source into structured ToonScript.
- `validate_testtoon(script)` — Validate row counts against declared counts.
- `testtoon_to_iql(text, filename)` — Parse TestTOON source and expand to IqlScript for execution.
- `parse_iql(source, filename)` — Parse IQL source into a flat command list, stripping comments.
- `main()` — CLI entry point — unchanged from original.
- `parse_api_args(args)` — Parse 'GET "/url"' or 'GET /url' → (method, endpoint).
- `parse_meta_from_args(args)` — Extract JSON-like metadata from command args.
- `parse_target_from_args(args)` — Extract quoted target from args.
- `parse_commands(source)` — Phase 1: tokenise source into (cmd, args) tuples and collect comments.
- `detect_scenario_type(commands)` — Heuristic to detect test type from commands.
- `extract_scenario_name(comments, filename)` — Extract scenario name from first meaningful comment or filename.
- `convert_iql_to_testtoon(source, filename)` — Convert IQL/TQL source text to TestTOON format.
- `convert_file(src)` — Convert a single .tql/.iql file to .testql.toon.yaml.
- `convert_directory(dir_path)` — Recursively convert all .tql and .iql files in a directory.
- `build_config_section(commands)` — Collect SET commands into a CONFIG section (or None if empty).
- `render_sections(sections)` — Phase 4: render collected sections to TestTOON text.
- `build_header(scenario_name, scenario_type)` — Build scenario header.
- `dispatch(filtered, i)` — Dispatch one command to its handler using registry; return (new_i, section).
- `handle_encoder(filtered, i)` — Collect consecutive ENCODER_* (+ optional WAIT) rows.
- `collect_assert(filtered, j)` — Scan ahead past ASSERT* commands; return (new_j, status, key, value).
- `handle_unknown(filtered, i)` — Handle unknown commands as generic FLOW entries.
- `handle_include(filtered, i)` — Handle INCLUDE command.
- `handle_api(filtered, i)` — Collect consecutive API + ASSERT* rows into one API Section.
- `handle_select(filtered, i)` — Collect consecutive SELECT* rows.
- `handle_navigate(filtered, i)` — Collect consecutive NAVIGATE (+ optional WAIT) rows.
- `handle_flow(filtered, i)` — Collect consecutive FLOW (semantic lifecycle) commands.
- `handle_wait(filtered, i)` — Collect consecutive standalone WAIT rows.
- `handle_record_start(filtered, i)` — Handle RECORD_START command.
- `handle_record_stop(filtered, i)` — Handle RECORD_STOP command.
- `report_console(result)` — Format a ScriptResult for console display.
- `report_json(result)` — Format a ScriptResult as JSON.
- `report_junit(result, suite_name)` — Convenience function — wraps JUnitReporter().generate().
- `generate_for_project(project_path)` — Generate tests for a single project.
- `generate_for_workspace(workspace_path)` — Generate tests for all projects in a workspace.
- `detect_endpoints(project_path)` — Convenience function to detect all endpoints in a project.
- `detect_separator()` — —
- `parse_value()` — —
- `parse_testtoon()` — —
- `validate()` — —
- `print_parsed()` — —
- `suite()` — —
- `list_tests()` — —
- `parse_line()` — —
- `parse_script()` — —
- `main()` — —
- `generate_openapi_spec()` — —
- `generate_contract_tests_from_spec()` — —
- `parse_sumd_file()` — —
- `parse_api_args()` — —
- `parse_meta_from_args()` — —
- `parse_target_from_args()` — —
- `parse_commands()` — —
- `detect_scenario_type()` — —
- `extract_scenario_name()` — —
- `generate()` — —
- `analyze()` — —
- `iql_list_files()` — —
- `iql_read_file()` — —
- `iql_list_tables()` — —
- `iql_run_line()` — —
- `iql_run_file()` — —
- `iql_list_logs()` — —
- `iql_read_log()` — —
- `endpoints()` — —
- `openapi()` — —
- `collect_assert()` — —
- `detect_endpoints()` — —
- `collect_toon_data()` — —
- `collect_doql_data()` — —
- `render_echo()` — —
- `validate_testtoon()` — —
- `testtoon_to_iql()` — —
- `report_junit()` — —
- `generate_sumd()` — —
- `save_sumd()` — —
- `parse_meta()` — —
- `filter_tests()` — —
- `render_test_list()` — —
- `parse_doql_less()` — —
- `build_config_section()` — —
- `render_sections()` — —
- `build_header()` — —
- `parse_doql_file()` — —
- `init()` — —
- `create()` — —
- `watch()` — —
- `from_sumd()` — —
- `report()` — —
- `echo()` — —
- `collect_test_files()` — —
- `collect_list_files()` — —
- `build_report_data()` — —
- `save_report()` — —
- `print_summary()` — —
- `format_text_output()` — —
- `handle_api()` — —
- `handle_navigate()` — —
- `report_console()` — —
- `generate_report()` — —
- `run_single_file()` — —
- `run_suite_files()` — —
- `parse_toon_scenarios()` — —
- `parse_iql()` — —
- `convert_iql_to_testtoon()` — —
- `convert_file()` — —
- `convert_directory()` — —
- `handle_encoder()` — —
- `parse_toon_file()` — —
- `generate_context()` — —
- `handle_wait()` — —
- `run()` — —
- `dispatch()` — —
- `handle_unknown()` — —
- `handle_select()` — —
- `handle_flow()` — —
- `report_json()` — —
- `cli()` — —
- `handle_include()` — —
- `handle_record_start()` — —
- `handle_record_stop()` — —
- `generate_for_project()` — —
- `generate_for_workspace()` — —
- `passed()` — —
- `failed()` — —
- `summary()` — —
- `set()` — —
- `get()` — —
- `has()` — —
- `all()` — —
- `clear()` — —
- `interpolate()` — —
- `emit()` — —
- `info()` — —
- `ok()` — —
- `fail()` — —
- `warn()` — —
- `error()` — —
- `step()` — —
- `parse()` — —
- `execute()` — —
- `run_file()` — —
- `strip_comments()` — —
- `connect()` — —
- `disconnect()` — —
- `send_event()` — —
- `connected()` — —
- `to_dict()` — —
- `to_json()` — —
- `to_yaml()` — —
- `save()` — —
- `generate_contract_tests()` — —
- `validate_response()` — —
- `cmd_api()` — —
- `cmd_wait()` — —
- `cmd_log()` — —
- `cmd_print()` — —
- `cmd_store()` — —
- `cmd_env()` — —
- `cmd_assert_status()` — —
- `cmd_assert_json()` — —
- `cmd_set_header()` — —
- `cmd_set_base_url()` — —
- `run_script()` — —
- `parse_file()` — —
- `generate_testql_scenarios()` — —
- `write_toon()` — —
- `test_normalize_legacy_test_path()` — —
- `test_normalize_legacy_view_path()` — —
- `test_normalize_testql_prefixed_path()` — —
- `test_normalize_passthrough_diagnostics_path()` — —
- `test_normalize_testtoon_path()` — —
- `test_resolve_new_format()` — —
- `make_result()` — —
- `make_step()` — —
- `list()` — —
- `print()` — —
- `generate_readme()` — —


## Project Structure

📄 `CHANGELOG`
📄 `README`
📄 `SUMD` (267 functions, 18 classes)
📄 `SUMR` (87 functions, 18 classes)
📄 `TODO`
📄 `TODO.testql-table-format-spec` (3 functions, 1 classes)
📄 `TODO.testtoon_parser` (7 functions, 1 classes)
📄 `Taskfile`
📄 `Taskfile.testql`
📄 `code2llm_output.README`
📄 `code2llm_output.analysis.toon`
📄 `code2llm_output.calls`
📄 `code2llm_output.context`
📄 `code2llm_output.evolution.toon`
📄 `code2llm_output.map.toon` (87 functions)
📄 `code2llm_output.project.toon`
📄 `code2llm_output.prompt`
📄 `coverage`
📄 `docs.README` (1 functions)
📄 `docs.testql-spec`
📄 `goal`
📄 `openapi`
📄 `project`
📄 `project.README`
📄 `project.analysis.toon`
📄 `project.calls`
📄 `project.calls.toon`
📄 `project.context`
📄 `project.duplication.toon`
📄 `project.evolution.toon`
📄 `project.map.toon` (1444 functions)
📄 `project.project.toon`
📄 `project.prompt`
📄 `project.validation.toon`
📄 `pyproject`
📄 `pyqual`
📄 `sumd`
📦 `testql`
📄 `testql-scenarios.generated-api-integration.testql.toon`
📄 `testql-scenarios.generated-api-smoke.testql.toon`
📄 `testql-scenarios.generated-cli-tests.testql.toon`
📄 `testql-scenarios.generated-from-pytests.testql.toon`
📄 `testql.__main__`
📄 `testql._base_fallback` (26 functions, 7 classes)
📄 `testql.base`
📄 `testql.cli` (2 functions)
📦 `testql.commands`
📦 `testql.commands.echo`
📄 `testql.commands.echo.cli` (1 functions)
📄 `testql.commands.echo.context` (3 functions)
📦 `testql.commands.echo.formatters`
📄 `testql.commands.echo.formatters.text` (7 functions)
📦 `testql.commands.echo.parsers`
📄 `testql.commands.echo.parsers.doql` (9 functions)
📄 `testql.commands.echo.parsers.toon` (4 functions)
📄 `testql.commands.echo_helpers` (4 functions)
📄 `testql.commands.encoder_routes` (27 functions)
📄 `testql.commands.endpoints_cmd` (6 functions)
📄 `testql.commands.generate_cmd` (6 functions)
📄 `testql.commands.misc_cmds` (7 functions)
📄 `testql.commands.run_cmd` (1 functions)
📦 `testql.commands.suite`
📄 `testql.commands.suite.cli` (2 functions)
📄 `testql.commands.suite.collection` (8 functions)
📄 `testql.commands.suite.execution` (2 functions)
📄 `testql.commands.suite.listing` (6 functions)
📄 `testql.commands.suite.reports` (5 functions)
📄 `testql.commands.suite_cmd`
📦 `testql.commands.templates`
📄 `testql.commands.templates.content` (9 functions, 1 classes)
📄 `testql.commands.templates.templates`
📦 `testql.detectors`
📄 `testql.detectors.base` (3 functions, 1 classes)
📄 `testql.detectors.config_detector` (4 functions, 1 classes)
📄 `testql.detectors.django_detector` (2 functions, 1 classes)
📄 `testql.detectors.express_detector` (3 functions, 1 classes)
📄 `testql.detectors.fastapi_detector` (12 functions, 1 classes)
📄 `testql.detectors.flask_detector` (9 functions, 1 classes)
📄 `testql.detectors.graphql_detector` (3 functions, 1 classes)
📄 `testql.detectors.models` (2 functions, 2 classes)
📄 `testql.detectors.openapi_detector` (3 functions, 1 classes)
📄 `testql.detectors.unified` (10 functions, 1 classes)
📄 `testql.detectors.websocket_detector` (2 functions, 1 classes)
📄 `testql.doql_parser` (9 functions, 1 classes)
📄 `testql.echo_schemas` (2 functions, 6 classes)
📄 `testql.endpoint_detector`
📄 `testql.generator`
📦 `testql.generators`
📄 `testql.generators.analyzers` (16 functions, 1 classes)
📄 `testql.generators.base` (3 functions, 3 classes)
📄 `testql.generators.convenience` (2 functions)
📄 `testql.generators.generators` (17 functions, 4 classes)
📄 `testql.generators.multi` (5 functions, 1 classes)
📦 `testql.interpreter` (1 functions)
📄 `testql.interpreter._api_runner` (10 functions, 1 classes)
📄 `testql.interpreter._assertions` (4 functions, 1 classes)
📄 `testql.interpreter._converter`
📄 `testql.interpreter._encoder` (12 functions, 1 classes)
📄 `testql.interpreter._flow` (6 functions, 1 classes)
📄 `testql.interpreter._gui` (10 functions, 1 classes)
📄 `testql.interpreter._parser` (1 functions, 2 classes)
📄 `testql.interpreter._shell` (6 functions, 1 classes)
📄 `testql.interpreter._testtoon_parser` (24 functions, 2 classes)
📄 `testql.interpreter._unit` (4 functions, 1 classes)
📄 `testql.interpreter._websockets` (8 functions, 1 classes)
📦 `testql.interpreter.converter`
📄 `testql.interpreter.converter.core` (3 functions)
📄 `testql.interpreter.converter.dispatcher` (1 functions)
📦 `testql.interpreter.converter.handlers`
📄 `testql.interpreter.converter.handlers.api` (1 functions)
📄 `testql.interpreter.converter.handlers.assertions` (1 functions)
📄 `testql.interpreter.converter.handlers.encoder` (3 functions)
📄 `testql.interpreter.converter.handlers.flow` (1 functions)
📄 `testql.interpreter.converter.handlers.include` (1 functions)
📄 `testql.interpreter.converter.handlers.navigate` (1 functions)
📄 `testql.interpreter.converter.handlers.record` (2 functions)
📄 `testql.interpreter.converter.handlers.select` (1 functions)
📄 `testql.interpreter.converter.handlers.unknown` (1 functions)
📄 `testql.interpreter.converter.handlers.wait` (1 functions)
📄 `testql.interpreter.converter.models` (2 classes)
📄 `testql.interpreter.converter.parsers` (6 functions)
📄 `testql.interpreter.converter.renderer` (4 functions)
📄 `testql.interpreter.dispatcher` (6 functions, 1 classes)
📄 `testql.interpreter.interpreter` (7 functions, 1 classes)
📄 `testql.openapi_generator` (21 functions, 3 classes)
📄 `testql.report_generator` (8 functions, 4 classes)
📦 `testql.reporters`
📄 `testql.reporters.console` (1 functions)
📄 `testql.reporters.json_reporter` (1 functions)
📄 `testql.reporters.junit` (3 functions, 1 classes)
📄 `testql.runner` (18 functions, 3 classes)
📦 `testql.runners`
📄 `testql.scenarios.c2004.api.test-devices-crud.testql.toon`
📄 `testql.scenarios.c2004.api.test-protocol-flow.testql.toon`
📄 `testql.scenarios.c2004.encoder.encoder-navigation.testql.toon`
📄 `testql.scenarios.c2004.encoder.encoder-workshop.testql.toon`
📄 `testql.scenarios.c2004.gui.connect-config-users.testql.toon`
📄 `testql.scenarios.c2004.gui.connect-id-barcode.testql.toon`
📄 `testql.scenarios.c2004.gui.connect-workshop-transport.testql.toon`
📄 `testql.scenarios.c2004.smoke.api-health.testql.toon`
📄 `testql.scenarios.c2004.smoke.api-smoke.testql.toon`
📄 `testql.scenarios.c2004.views.reproduce-view.testql.toon`
📄 `testql.scenarios.c2004.views.run-mask-test-protocol.testql.toon`
📄 `testql.scenarios.c2004.views.test-api.testql.toon`
📄 `testql.scenarios.c2004.views.test-app-lifecycle.testql.toon`
📄 `testql.scenarios.c2004.views.test-devices-crud.testql.toon`
📄 `testql.scenarios.c2004.views.test-dsl-objects.testql.toon`
📄 `testql.scenarios.c2004.views.test-encoder.testql.toon`
📄 `testql.scenarios.c2004.views.test-gui-all.testql.toon`
📄 `testql.scenarios.c2004.views.test-gui-connect-config.testql.toon`
📄 `testql.scenarios.c2004.views.test-gui-connect-id.testql.toon`
📄 `testql.scenarios.c2004.views.test-gui-connect-manager.testql.toon`
📄 `testql.scenarios.c2004.views.test-gui-connect-reports.testql.toon`
📄 `testql.scenarios.c2004.views.test-gui-connect-test.testql.toon`
📄 `testql.scenarios.c2004.views.test-gui-connect-workshop.testql.toon`
📄 `testql.scenarios.c2004.views.test-mixed-workflow.testql.toon`
📄 `testql.scenarios.c2004.views.test-protocol-flow.testql.toon`
📄 `testql.scenarios.c2004.views.test-ui-navigation.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-config-feature-flags.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-config-labels.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-config-settings.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-config-tables.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-config-theme.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-config-users.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-id-barcode.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-id-list.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-id-manual.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-id-qr.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-id-rfid.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-manager-activities.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-manager-intervals.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-manager-library.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-manager-scenarios.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-manager-test-types.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-reports-chart.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-reports-custom.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-reports-filter.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-reports-month.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-reports-quarter.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-reports-week.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-reports-year.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-test-devices-search.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-test-full-test.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-test-protocols.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-test-scenario-view.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-test-testing-barcode.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-test-testing-qr.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-test-testing-rfid.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-test-testing-search.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-workshop-dispositions-search.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-workshop-requests-search.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-workshop-services-search.testql.toon`
📄 `testql.scenarios.c2004.views.views.connect-workshop-transport-search.testql.toon`
📄 `testql.scenarios.c2004.views.views.run-all-views.testql.toon`
📄 `testql.scenarios.diagnostics.backend-diagnostic.testql.toon`
📄 `testql.scenarios.diagnostics.create-todays-reports.testql.toon`
📄 `testql.scenarios.diagnostics.full-diagnostic.testql.toon`
📄 `testql.scenarios.diagnostics.generate-test-reports.testql.toon`
📄 `testql.scenarios.examples.device-identification.testql.toon`
📄 `testql.scenarios.examples.quick-navigation.testql.toon`
📄 `testql.scenarios.examples.test-device-flow.testql.toon`
📄 `testql.scenarios.generic.api-crud-template.testql.toon`
📄 `testql.scenarios.generic.auth-login.testql.toon`
📄 `testql.scenarios.generic.health-check.testql.toon`
📄 `testql.scenarios.recordings.recorded-test-session.testql.toon`
📄 `testql.scenarios.recordings.session-recording.testql.toon`
📄 `testql.sumd_generator` (11 functions)
📄 `testql.sumd_parser` (12 functions, 5 classes)
📄 `testql.toon_parser` (7 functions, 1 classes)
📄 `tree`

## Requirements

- Python >= >=3.10
- httpx >=0.27- click >=8.0- rich >=13.0- pyyaml >=6.0- goal >=2.1.0- costs >=0.1.20- pfix >=0.1.60- websockets >=13.0

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Open an issue or pull request to get started.
### Development Setup

```bash
# Clone the repository
git clone https://github.com/oqlos/testql
cd testql

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```


<!-- code2docs:end -->