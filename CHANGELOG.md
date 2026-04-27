# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.10] - 2026-04-25

### Fixed
- Fix ai-boilerplate issues (ticket-3ab87bce)
- Fix smart-return-type issues (ticket-0ffa8da6)
- Fix unused-imports issues (ticket-e7d3db7a)
- Fix ai-boilerplate issues (ticket-eaa83cd3)
- Fix duplicate-imports issues (ticket-2bc02840)
- Fix smart-return-type issues (ticket-6661134e)
- Fix ai-boilerplate issues (ticket-9bef7a51)
- Fix unused-imports issues (ticket-276a0040)
- Fix magic-numbers issues (ticket-28878ebe)
- Fix relative-imports issues (ticket-52ad90d2)
- Fix relative-imports issues (ticket-049b5620)
- Fix string-concat issues (ticket-4905d15b)
- Fix unused-imports issues (ticket-5a769ac3)
- Fix relative-imports issues (ticket-495ca82b)
- Fix smart-return-type issues (ticket-19db84d1)
- Fix unused-imports issues (ticket-06a0662c)
- Fix relative-imports issues (ticket-d2afe350)
- Fix string-concat issues (ticket-6b1313b4)
- Fix unused-imports issues (ticket-e01dbf4a)
- Fix magic-numbers issues (ticket-b4725322)
- Fix relative-imports issues (ticket-bd4e67d9)
- Fix unused-imports issues (ticket-985d4781)
- Fix unused-imports issues (ticket-d85fe2e1)
- Fix relative-imports issues (ticket-750054c3)
- Fix unused-imports issues (ticket-583bf3b0)
- Fix unused-imports issues (ticket-5814de13)
- Fix duplicate-imports issues (ticket-17ade819)
- Fix string-concat issues (ticket-34dda1ad)
- Fix unused-imports issues (ticket-c5a24a62)
- Fix duplicate-imports issues (ticket-6e1852a3)
- Fix magic-numbers issues (ticket-3cd9ef58)
- Fix string-concat issues (ticket-1e184955)
- Fix unused-imports issues (ticket-744e426a)
- Fix duplicate-imports issues (ticket-07761a3c)
- Fix relative-imports issues (ticket-1b834778)
- Fix smart-return-type issues (ticket-e56faf2d)
- Fix string-concat issues (ticket-81a326f8)
- Fix unused-imports issues (ticket-7525697a)
- Fix magic-numbers issues (ticket-a3951532)
- Fix relative-imports issues (ticket-954124c9)
- Fix unused-imports issues (ticket-538b495d)
- Fix unused-imports issues (ticket-ddd4785e)
- Fix relative-imports issues (ticket-069078ea)
- Fix unused-imports issues (ticket-1d087dee)
- Fix string-concat issues (ticket-870e06c8)
- Fix unused-imports issues (ticket-019f2720)
- Fix magic-numbers issues (ticket-0dc8c55c)
- Fix unused-imports issues (ticket-ec0e4788)
- Fix duplicate-imports issues (ticket-caf170d6)
- Fix string-concat issues (ticket-7e5fcc77)
- Fix unused-imports issues (ticket-8e6c8b42)
- Fix magic-numbers issues (ticket-7f03c92c)
- Fix string-concat issues (ticket-6973fa64)
- Fix unused-imports issues (ticket-850489eb)
- Fix magic-numbers issues (ticket-ab5434e6)
- Fix relative-imports issues (ticket-ee8e9336)
- Fix unused-imports issues (ticket-6f2e587a)
- Fix relative-imports issues (ticket-ce7e034d)
- Fix string-concat issues (ticket-ce8f3544)
- Fix unused-imports issues (ticket-1f909b6a)
- Fix unused-imports issues (ticket-a0d5d507)
- Fix relative-imports issues (ticket-62752b16)
- Fix relative-imports issues (ticket-a759a879)
- Fix unused-imports issues (ticket-a8996fa0)
- Fix relative-imports issues (ticket-701ad13d)
- Fix string-concat issues (ticket-1f182970)
- Fix unused-imports issues (ticket-a826b6cc)
- Fix magic-numbers issues (ticket-ce85ae9c)
- Fix relative-imports issues (ticket-38095c43)
- Fix string-concat issues (ticket-f74b8e43)
- Fix unused-imports issues (ticket-d885784a)
- Fix relative-imports issues (ticket-8cc4f988)
- Fix string-concat issues (ticket-66ded905)
- Fix unused-imports issues (ticket-3d4e844a)
- Fix magic-numbers issues (ticket-516016b6)
- Fix relative-imports issues (ticket-419a1eb0)
- Fix string-concat issues (ticket-2a33e8e8)
- Fix unused-imports issues (ticket-8d33d325)
- Fix relative-imports issues (ticket-a8f11c1a)
- Fix string-concat issues (ticket-a64fb907)
- Fix unused-imports issues (ticket-b41fb5f3)
- Fix relative-imports issues (ticket-a1a99b91)
- Fix string-concat issues (ticket-2e4b51a3)
- Fix unused-imports issues (ticket-3026ce5c)
- Fix magic-numbers issues (ticket-3376a001)
- Fix unused-imports issues (ticket-36904e44)
- Fix magic-numbers issues (ticket-354323f1)
- Fix relative-imports issues (ticket-fc1e18f7)
- Fix string-concat issues (ticket-7a0d3fde)
- Fix unused-imports issues (ticket-a87b6e2e)
- Fix relative-imports issues (ticket-4f01158d)
- Fix unused-imports issues (ticket-17e3e236)
- Fix magic-numbers issues (ticket-30e233ef)
- Fix relative-imports issues (ticket-207f96f9)
- Fix string-concat issues (ticket-dd4aeb75)
- Fix unused-imports issues (ticket-d4afc64c)
- Fix relative-imports issues (ticket-a50f9748)
- Fix string-concat issues (ticket-4e1e2991)
- Fix unused-imports issues (ticket-b86d3e4e)
- Fix magic-numbers issues (ticket-d4a09f0e)

## [Unreleased]

### Added
- Add artifact discovery core with manifests, probes, and `testql discover`.
- Add topology graph generation with `testql topology` and JSON/YAML/TOON output.
- Add structured inspection results, refactor-plan envelope, NLP summaries, and `.testql` artifact bundle writer.
- Add opt-in URL inspection via `--scan-network`, extracting HTTP status, title, links, assets, forms, page topology, and web-specific checks.
- Add asset classification (script, stylesheet, image, icon, preload, link) in `HTTPPageProbe`.
- Add bounded link and asset crawling with HEAD validation, broken-resource findings, and `investigate_broken_resources` refactor action.
- Add `build_sitemap()` in `topology.sitemap` for bounded sub-page crawl (refactored to reduce CC below 15). (max 10 pages, 5s timeout) with title/link extraction and duplicate-title detection.
- Add `PlaywrightPageProbe` with `--browser` CLI flag for JS-rendered page inspection, console error capture, and network call logging.
- Add browser-specific checks: `check.browser.render`, `check.browser.console`, `check.browser.network`.
- Add `examples/web-inspection-dot-testql/` showing live web inspection with all generated data and metadata stored under `.testql/`.

### Changed
- Improve OpenAPI discovery to avoid treating test fixtures as production topology when scanning project roots.
- Include HTTP status and content type in page schema metadata for reliable web findings.

### Remaining
- Add Playwright-backed browser execution, JavaScript-rendered DOM capture, screenshots, console errors, network logs, link-by-link validation, accessibility/performance checks, MCP service integration, and runtime-vs-code delta reports.

## [1.2.31] - 2026-04-27

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update project/README.md
- Update project/context.md

### Test
- Update testql/commands/auto_cmd.py
- Update testql/generators/api_generator.py
- Update testql/generators/sources/__init__.py
- Update testql/generators/sources/oql_models.py
- Update testql/generators/sources/oql_parser.py
- Update testql/generators/sources/oql_source.py

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
- ... and 8 more files

## [1.2.30] - 2026-04-27

### Docs
- Update CHANGELOG.md
- Update DSL.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update articles/testql-multi-dsl-refactor-plan.md
- Update articles/testql-plugins-and-formats.md
- Update code2llm_output/context.md
- Update docs/README.md
- ... and 9 more files

### Test
- Update testql-scenarios/generated-api-smoke.testql.toon.yaml
- Update testql-scenarios/generated-from-pytests.testql.toon.yaml
- Update testql/_base_fallback.py
- Update testql/adapters/scenario_yaml.py
- Update testql/adapters/testtoon_adapter.py
- Update testql/cli.py
- Update testql/commands/encoder_routes.py
- Update testql/commands/run_cmd.py
- Update testql/commands/suite/collection.py
- Update testql/commands/suite/execution.py
- ... and 53 more files

### Other
- Update Taskfile.yml
- Update app.doql.less
- Update code2llm_output/analysis.toon.yaml
- Update code2llm_output/calls.yaml
- Update code2llm_output/evolution.toon.yaml
- Update code2llm_output/map.toon.yaml
- Update coverage.json
- Update examples/encoder-testing/basic-encoder.oql
- Update examples/encoder-testing/complex-sequence.oql
- Update examples/encoder-testing/run.sh
- ... and 30 more files

## [1.2.29] - 2026-04-27

### Docs
- Update README.md

### Test
- Update testql/interpreter/_gui.py

### Other
- Update coverage.json

## [1.2.28] - 2026-04-27

### Docs
- Update README.md

### Test
- Update testql/interpreter/_assertions.py
- Update tests/test_interpreter.py

### Other
- Update coverage.json
- Update scenarios/encoder-connect-test-devices-admin-pl.testql.toon.yaml

## [1.2.27] - 2026-04-27

### Docs
- Update README.md

### Test
- Update testql/interpreter/_assertions.py
- Update testql/interpreter/_encoder.py
- Update testql/interpreter/_testtoon_parser.py
- Update tests/test_interpreter.py

### Other
- Update coverage.json
- Update scenarios/c2004-all-modules-api.testql.toon.yaml
- Update scenarios/encoder-cli-hardware-sim.testql.toon.yaml
- Update scenarios/encoder-connect-test-devices-admin-pl.testql.toon.yaml
- Update scenarios/encoder-gui-full-flow.testql.toon.yaml
- Update scenarios/encoder-gui-terminal.testql.toon.yaml
- Update scenarios/encoder-navigation.testql.toon.yaml
- Update scenarios/encoder-terminal-cli.testql.toon.yaml

## [1.2.26] - 2026-04-27

### Docs
- Update README.md

### Test
- Update testql/interpreter/_testtoon_parser.py
- Update testql/interpreter/interpreter.py

### Other
- Update coverage.json

## [1.2.25] - 2026-04-27

### Docs
- Update README.md

### Test
- Update testql/commands/run_cmd.py
- Update testql/interpreter/_gui.py
- Update testql/interpreter/interpreter.py

### Other
- Update coverage.json

## [1.2.24] - 2026-04-26

### Docs
- Update README.md

### Test
- Update testql/discovery/probes/browser/playwright_page.py
- Update testql/generators/sources/page_source.py
- Update testql/interpreter/_api_runner.py
- Update testql/interpreter/_gui.py
- Update tests/test_browser_discovery.py

### Other
- Update coverage.json

## [1.2.23] - 2026-04-26

### Docs
- Update README.md

### Test
- Update testql/commands/heal_scenario_cmd.py
- Update testql/generators/page_analyzer.py
- Update tests/test_generate_from_page_cli.py

### Other
- Update coverage.json

## [1.2.22] - 2026-04-26

### Docs
- Update README.md

### Test
- Update testql/adapters/testtoon_adapter.py
- Update testql/generators/page_analyzer.py
- Update testql/interpreter/_testtoon_parser.py
- Update tests/test_generate_from_page_cli.py
- Update tests/test_testtoon_adapter.py

### Other
- Update coverage.json

## [1.2.21] - 2026-04-26

### Docs
- Update README.md

### Test
- Update testql/cli.py
- Update testql/commands/generate_from_page_cmd.py
- Update testql/commands/heal_scenario_cmd.py
- Update testql/generators/page_analyzer.py
- Update testql/generators/sources/__init__.py
- Update testql/generators/sources/page_source.py
- Update testql/interpreter/_flow.py
- Update testql/interpreter/_gui.py
- Update testql/interpreter/_testtoon_parser.py
- Update tests/test_generate_from_page_cli.py
- ... and 3 more files

### Other
- Update coverage.json

## [1.2.20] - 2026-04-26

### Docs
- Update README.md

### Other
- Update coverage.json

## [1.2.19] - 2026-04-26

### Docs
- Update README.md

### Other
- Update coverage.json

## [1.2.18] - 2026-04-26

### Docs
- Update README.md

### Other
- Update coverage.json

## [1.2.17] - 2026-04-25

### Docs
- Update README.md

### Test
- Update testql/commands/run_cmd.py

### Other
- Update coverage.json

## [1.2.16] - 2026-04-25

### Docs
- Update README.md

### Test
- Update testql/interpreter/_testtoon_parser.py

### Other
- Update coverage.json

## [1.2.15] - 2026-04-25

### Docs
- Update README.md

### Test
- Update testql/interpreter/_testtoon_parser.py

### Other
- Update coverage.json

## [1.2.14] - 2026-04-25

### Docs
- Update README.md

### Test
- Update testql/generators/generators.py
- Update testql/interpreter/_dom_scan.py
- Update testql/interpreter/_testtoon_parser.py

### Other
- Update coverage.json

## [1.2.13] - 2026-04-25

### Docs
- Update README.md

### Test
- Update testql/_base_fallback.py
- Update testql/commands/run_cmd.py
- Update testql/generators/generators.py
- Update testql/integrations/planfile_hook.py
- Update testql/interpreter/_assertions.py
- Update testql/interpreter/_dom_scan.py
- Update testql/interpreter/_gui.py
- Update testql/interpreter/interpreter.py

### Other
- Update coverage.json

## [1.2.12] - 2026-04-25

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update project/README.md
- Update project/context.md

### Test
- Update testql/commands/generate_cmd.py
- Update testql/detectors/config_detector.py
- Update testql/detectors/unified.py
- Update testql/generators/analyzers.py
- Update testql/generators/generators.py
- Update testql/generators/sources/__init__.py
- Update testql/generators/sources/oql_source.py
- Update testql/generators/sources/pytest_source.py
- Update testql/interpreter/_api_runner.py
- Update testql/interpreter/_assertions.py
- ... and 8 more files

### Other
- Update app.doql.less
- Update coverage.json
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- ... and 10 more files

## [1.2.11] - 2026-04-25

### Docs
- Update README.md

### Test
- Update testql/detectors/unified.py
- Update testql/generators/generators.py
- Update testql/interpreter/_assertions.py

### Other
- Update coverage.json

## [1.2.10] - 2026-04-25

### Docs
- Update README.md

### Test
- Update testql/cli.py
- Update testql/commands/auto_cmd.py

### Other
- Update coverage.json

## [1.2.9] - 2026-04-25

### Docs
- Update README.md

### Test
- Update testql/detectors/config_detector.py
- Update testql/detectors/unified.py
- Update testql/results/artifacts.py
- Update tests/test_detectors.py

### Other
- Update coverage.json

## [1.2.8] - 2026-04-25

### Docs
- Update README.md

### Test
- Update testql/results/artifacts.py
- Update tests/test_results.py

### Other
- Update coverage.json

## [1.2.7] - 2026-04-25

### Docs
- Update DSL.md
- Update README.md
- Update articles/testql-plugins-and-formats.md
- Update examples/web-inspection/c2004-localhost/README.md

### Test
- Update testql/adapters/__init__.py
- Update testql/adapters/registry.py
- Update testql/adapters/scenario_yaml.py
- Update testql/adapters/testtoon_adapter.py
- Update testql/ir_runner/engine.py
- Update testql/results/analyzer.py
- Update tests/test_network_discovery.py
- Update tests/test_plugin_registry.py
- Update tests/test_scenario_yaml_adapter.py

### Other
- Update .gitignore
- Update coverage.json
- Update examples/api-testing/crud-workflow.testql.toon.yaml
- Update examples/api-testing/crud-workflow.testql.yaml
- Update examples/api-testing/health-check.testql.toon.yaml
- Update examples/api-testing/health-check.testql.yaml
- Update examples/encoder-testing/basic-encoder.testql.toon.yaml
- Update examples/encoder-testing/basic-encoder.testql.yaml
- Update examples/flow-control/mixed-smoke.testql.toon.yaml
- Update examples/flow-control/mixed-smoke.testql.yaml
- ... and 8 more files

## [1.2.6] - 2026-04-25

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update examples/README.md
- Update examples/api-testing/README.md
- Update examples/discovery/README.md
- Update examples/encoder-testing/README.md
- Update examples/flow-control/README.md
- Update examples/gui-testing/README.md
- Update examples/shell-testing/README.md
- ... and 4 more files

### Other
- Update app.doql.less
- Update examples/.gitignore
- Update examples/Makefile
- Update examples/api-testing/Makefile
- Update examples/api-testing/mock_server.py
- Update examples/api-testing/run.sh
- Update examples/artifact-bundle/Makefile
- Update examples/artifact-bundle/run.sh
- Update examples/browser-inspection/Makefile
- Update examples/browser-inspection/run.sh
- ... and 48 more files

## [1.2.5] - 2026-04-25

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update examples/project-echo/README.md

### Test
- Update testql/adapters/testtoon_adapter.py
- Update testql/generators/base.py
- Update testql/generators/targets/testtoon_target.py
- Update testql/generators/test_generator.py
- Update testql/ir/plan.py
- Update testql/report_generator.py

### Other
- Update app.doql.less
- Update coverage.json
- Update examples/project-echo/run.sh
- Update project.sh
- Update project/map.toon.yaml
- Update tree.txt

## [1.2.4] - 2026-04-25

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update project/README.md
- Update project/context.md

### Test
- Update testql/__init__.py
- Update testql/adapters/sql/sql_adapter.py
- Update testql/adapters/testtoon_adapter.py
- Update testql/cli.py
- Update testql/commands/__init__.py
- Update testql/commands/generate_cmd.py
- Update testql/commands/generate_topology_cmd.py
- Update testql/commands/inspect_cmd.py
- Update testql/discovery/probes/browser/__init__.py
- Update testql/discovery/probes/browser/playwright_page.py
- ... and 14 more files

### Other
- Update .gitignore
- Update VERSION
- Update app.doql.less
- Update coverage.json
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- ... and 12 more files

## [1.2.2] - 2026-04-25

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md

### Other
- Update coverage.json

## [1.2.1] - 2026-04-25

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update articles/testql-phase-6-artifact-discovery.md
- Update examples/web-inspection-dot-testql/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update testql/__init__.py
- Update testql/cli.py
- Update testql/commands/__init__.py
- Update testql/commands/discover_cmd.py
- Update testql/commands/inspect_cmd.py
- Update testql/commands/run_ir_cmd.py
- Update testql/commands/topology_cmd.py
- Update testql/discovery/probes/filesystem/api_openapi.py
- Update testql/discovery/probes/network/__init__.py
- Update testql/discovery/probes/network/http_endpoint.py
- ... and 39 more files

### Other
- Update VERSION
- Update app.doql.less
- Update coverage.json
- Update examples/web-inspection-dot-testql/.gitignore
- Update examples/web-inspection-dot-testql/run.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- ... and 12 more files

## [1.0.1] - 2026-04-25

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update articles/testql-multi-dsl-refactor-plan.md
- Update articles/testql-phase-6-artifact-discovery.md
- Update project/README.md
- Update project/context.md

### Test
- Update testql-scenarios/graphql/orders-mutations.graphql.testql.yaml
- Update testql-scenarios/graphql/user-contract.graphql.testql.yaml
- Update testql-scenarios/nl/api-smoke-en.nl.md
- Update testql-scenarios/nl/api-smoke.nl.md
- Update testql-scenarios/nl/encoder-flow.nl.md
- Update testql-scenarios/nl/login-en.nl.md
- Update testql-scenarios/nl/login.nl.md
- Update testql-scenarios/proto/orders-events.proto.testql.yaml
- Update testql-scenarios/proto/user-contract.proto.testql.yaml
- Update testql-scenarios/sql/orders-sqlite.sql.testql.yaml
- ... and 114 more files

### Other
- Update VERSION
- Update app.doql.less
- Update coverage.json
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- ... and 11 more files

## [0.6.23] - 2026-04-25

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update project/context.md

### Other
- Update app.doql.less
- Update coverage.json
- Update planfile.yaml
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- ... and 8 more files

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
- `convert_oql_to_testtoon` (CC 66 → ≤12): extracted `_handle_api`, `_handle_navigate`,
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

