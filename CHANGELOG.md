# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.22] - 2026-04-25

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update project/context.md

### Other
- Update app.doql.less
- Update coverage.json
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/duplication.toon.yaml
- Update project/index.html
- Update project/mermaid.export
- ... and 1 more files

## [0.6.21] - 2026-04-25

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update project/README.md
- Update project/context.md

### Test
- Update testql/interpreter/_unit.py

### Other
- Update app.doql.less
- Update coverage.json
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- ... and 7 more files

## [0.6.20] - 2026-04-25

### Docs
- Update README.md

### Other
- Update coverage.json

## [0.6.19] - 2026-04-25

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update app.doql.css
- Update app.doql.less
- Update planfile.yaml
- Update prefact.yaml
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- ... and 12 more files

## [0.6.18] - 2026-04-24

### Added
- **CLI/Shell Execution**: Complete shell command execution with `SHELL`, `EXEC`, `RUN` commands
- **GUI Execution**: Playwright/Selenium support with `GUI_START`, `GUI_CLICK`, `GUI_INPUT`, `GUI_ASSERT_VISIBLE`, `GUI_ASSERT_TEXT`, `GUI_CAPTURE`, `GUI_STOP`
- **Unit Test Execution**: Python test integration with `UNIT_PYTEST`, `UNIT_PYTEST_DISCOVER`, `UNIT_ASSERT`, `UNIT_IMPORT`
- **CommandDispatcher**: Centralized command dispatcher with auto-discovery of `_cmd_*` methods from mixins
- **Better Error Messages**: "Did you mean..." suggestions for unknown commands

### Changed
- **Architecture**: Refactored interpreter to use CommandDispatcher with auto-discovery
- **Test Coverage**: Increased from 16% to 65% (target: ≥50% achieved)
- **Code Quality**: Resolved all CC hotspots (max CC ≤10), eliminated god modules (all files <500L)

### Fixed
- Workspace detection for Python packages with same-name subpackages
- `testql list` table/simple output rendering
- TestTOON header format recognition (`# SCENARIO:` / `# TYPE:`)

### Test
- Added 39 new tests across shell, GUI, unit, and dispatcher modules
- All tests passing (green)

### Docs
- Updated README.md with current feature set
- Updated TODO.md with completed tasks

## [0.6.17] - 2026-04-24

### Added
- Shell execution mixin with subprocess support
- GUI execution mixin with Playwright/Selenium drivers
- Unit test execution mixin with pytest integration

### Test
- Added test_shell_execution.py (9 tests)
- Added test_gui_execution.py (11 tests)
- Added test_unit_execution.py (9 tests)
- Added test_dispatcher.py (10 tests)

## [0.6.16] - 2026-04-24

### Changed
- Refactored generator analyzers for better project type detection
- Improved Python test analysis

### Test
- Updated test_test_generator.py for new analyzers

## [0.6.15] - 2026-04-24

### Docs
- Minor documentation updates

## [0.6.14] - 2026-04-19

### Changed
- Improved suite collection and listing
- Enhanced API runner, encoder, and WebSocket handling
- Better TestTOON parser and converter rendering

## [0.6.13] - 2026-04-19

### Changed
- Refactored echo helpers and formatters
- Improved encoder routes and generate commands
- Enhanced suite listing with better metadata parsing
- Updated SUMD parser and OpenAPI generator

## [0.6.12] - 2026-04-19

### Changed
- Complete echo command refactoring with modular parsers and formatters
- Improved endpoints command with multiple output formats
- Enhanced task integration with DOQL

### Docs
- Updated SUMR.md and TODO.md

## [0.6.11] - 2026-04-19

### Changed
- Improved converter handlers for API, encoder, navigate, flow, and assertions
- Enhanced suite execution and reporting
- Better API handler and converter integration

### Test
- Updated comprehensive test suite for converter and handlers

## [0.6.10] - 2026-04-19

### Changed
- Refactored converter core with better handler dispatch
- Improved converter handlers for all command types
- Enhanced renderer with better section building

## [0.6.9] - 2026-04-19

### Changed
- Improved converter models and parsers
- Enhanced handler implementations

## [0.6.8] - 2026-04-19

### Changed
- Improved echo helpers and misc commands
- Updated command templates

## [0.6.7] - 2026-04-19

### Changed
- Improved detector implementations for better endpoint detection
- Enhanced generators with better test generation
- Updated suite command with improved collection
- Better command templates

### Docs
- Updated SUMR.md and TODO.md

## [0.6.16] - 2026-04-24

### Changed
- Refactored generator analyzers for better project type detection
- Improved Python test analysis

### Test
- Updated test_test_generator.py for new analyzers

## [0.6.15] - 2026-04-24

### Docs
- Minor documentation updates

## [0.6.14] - 2026-04-19

### Changed
- Improved suite collection and listing
- Enhanced API runner, encoder, and WebSocket handling
- Better TestTOON parser and converter rendering

## [0.6.13] - 2026-04-19

### Changed
- Refactored echo helpers and formatters
- Improved encoder routes and generate commands
- Enhanced suite listing with better metadata parsing
- Updated SUMD parser and OpenAPI generator

## [0.6.12] - 2026-04-19

### Changed
- Complete echo command refactoring with modular parsers and formatters
- Improved endpoints command with multiple output formats
- Enhanced task integration with DOQL

### Docs
- Updated SUMR.md and TODO.md

## [0.6.11] - 2026-04-19

### Changed
- Improved converter handlers for API, encoder, navigate, flow, and assertions
- Enhanced suite execution and reporting
- Better API handler and converter integration

### Test
- Updated comprehensive test suite for converter and handlers

## [0.6.10] - 2026-04-19

### Changed
- Refactored converter core with better handler dispatch
- Improved converter handlers for all command types
- Enhanced renderer with better section building

## [0.6.9] - 2026-04-19

### Changed
- Improved converter models and parsers
- Enhanced handler implementations

## [0.6.8] - 2026-04-19

### Changed
- Improved echo helpers and misc commands
- Updated command templates

## [0.6.7] - 2026-04-19

### Changed
- Improved detector implementations for better endpoint detection
- Enhanced generators with better test generation
- Updated suite command with improved collection
- Better command templates

### Docs
- Updated SUMR.md and TODO.md

## [0.6.6] - 2026-04-19

### Refactored
- `convert_iql_to_testtoon` (CC 66 → ≤12): extracted `_handle_api`, `_handle_navigate`,
  `_handle_encoder`, `_handle_select`, `_handle_flow`, `_handle_record_*`, `_handle_wait`,
  `_handle_include`, `_dispatch`, `_parse_commands`, `_build_config_section`, `_render_sections`
- `parse_doql_less` (CC 29 → ≤8): split into `_parse_app_block`, `_parse_entities`,
  `_parse_interfaces`, `_parse_workflows`, `_parse_deploy`, `_parse_environment`,
  `_parse_integrations`, `_parse_kv_block`
- `format_text_output` (CC 19 → ≤6): split into `_fmt_interfaces`, `_fmt_workflows`,
  `_fmt_contracts`, `_fmt_entities`, `_fmt_suggestions`
- `suite` command (CC 18 → 13): extracted `_run_suite_files`, `_print_summary`
- `echo` command in misc_cmds (CC 16 → ≤10): extracted `_collect_toon_data`,
  `_collect_doql_data`, `_render_echo`

### Fixed
- `generate --analyze-only` crash: `TestGenerator.analyze()` now returns `self.profile`
- Workspace detection incorrectly classified Python projects with same-name subpackage
  (e.g. `testql/testql/`) as monorepo workspaces — guard added on `pyproject.toml` + `__init__.py`
- `testql list` produced empty output in `table`/`simple` format modes
- `testql list` did not recognise TestTOON header format (`# SCENARIO:` / `# TYPE:`)

### Added
- `testql generate` now correctly detects all 6 OqlOS projects as standalone Python projects
- `testql list` table format with file / type / tags columns
- `_is_workspace()` helper for reliable monorepo vs. single-project detection

### Docs
- Updated CHANGELOG and TODO



### Docs
- Update README.md
- Update SUMR.md

### Test
- Update testql/interpreter/_converter.py

### Other
- Update project/map.toon.yaml

## [0.6.5] - 2026-04-19

### Docs
- Update README.md

## [0.6.4] - 2026-04-19

### Docs
- Update README.md

## [0.6.3] - 2026-04-19

### Docs
- Update README.md

## [0.6.2] - 2026-04-19

### Docs
- Update README.md
- Update project/README.md
- Update project/context.md

### Test
- Update testql/cli.py
- Update testql/commands/__init__.py
- Update testql/commands/endpoints_cmd.py
- Update testql/commands/generate_cmd.py
- Update testql/commands/misc_cmds.py
- Update testql/commands/run_cmd.py
- Update testql/commands/suite_cmd.py
- Update testql/endpoint_detector.py
- Update testql/sumd_generator.py

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 4 more files

## [0.6.1] - 2026-04-19

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update code2llm_output/README.md
- Update code2llm_output/context.md
- Update project/README.md
- Update project/context.md

### Test
- Update testql/__init__.py
- Update testql/report_generator.py

### Other
- Update VERSION
- Update code2llm_output/analysis.toon.yaml
- Update code2llm_output/calls.mmd
- Update code2llm_output/calls.png
- Update code2llm_output/calls.yaml
- Update code2llm_output/compact_flow.mmd
- Update code2llm_output/compact_flow.png
- Update code2llm_output/evolution.toon.yaml
- Update code2llm_output/flow.mmd
- Update code2llm_output/flow.png
- ... and 21 more files

## [0.5.2] - 2026-04-18

### Docs
- Update README.md
- Update SUMD.md

### Test
- Update testql/cli.py
- Update testql/sumd_parser.py

### Other
- Update sumd.json

## [0.5.1] - 2026-04-18

### Docs
- Update README.md
- Update SUMD.md

### Test
- Update testql/__init__.py
- Update testql/cli.py
- Update testql/sumd_generator.py

### Other
- Update Taskfile.testql.yml
- Update VERSION
- Update app.doql.css
- Update project/calls.yaml
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml
- Update project/validation.toon.yaml
- ... and 1 more files

## [0.4.3] - 2026-04-18

### Docs
- Update README.md
- Update SUMD.md

### Test
- Update testql/__init__.py

### Other
- Update app.doql.css
- Update app.doql.less
- Update project/index.html
- Update project/map.toon.yaml
- Update sumd.json

## [0.4.1] - 2026-04-18

### Docs
- Update README.md

### Test
- Update testql/__init__.py
- Update testql/echo_schemas.py

### Other
- Update VERSION

## [0.2.1] - 2026-04-18

### Docs
- Update README.md

### Test
- Update testql/__init__.py

### Other
- Update Taskfile.yml
- Update VERSION
- Update app.doql.css
- Update app.doql.less
- Update app.doql.sass
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml
- ... and 3 more files

## [0.1.1] - 2026-04-15

### Docs
- Update README.md

### Test
- Update testql/commands/encoder_routes.py
- Update testql/scenarios/c2004/views/test-encoder.testql.toon.yaml
- Update testql/scenarios/recordings/recorded-test-session.testql.toon.yaml
- Update testql/scenarios/recordings/session-recording.testql.toon.yaml

### Other
- Update .env.example

