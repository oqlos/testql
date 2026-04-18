# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **New CLI commands for test management:**
  - `testql init` — Initialize project with directory structure, config file, and starter templates
  - `testql create <name>` — Generate test files from templates (gui, api, mixed, encoder, performance, workflow)
  - `testql suite [name]` — Run predefined or custom test suites with filtering
  - `testql list` — List all tests with metadata (type, tags, module)
  - `testql watch` — Watch mode for automatic test re-runs on file changes
- **Test templates:**
  - `gui` — GUI navigation and interaction tests
  - `api` — REST API endpoint tests
  - `mixed` — Combined API + GUI workflow tests
  - `encoder` — Hardware encoder interaction tests
  - `performance` — Load time and performance benchmarks
  - `workflow` — Multi-step business process tests
- **Suite configuration** via `testql.yaml` with predefined test suites (smoke, regression, api)
- **Filtering support:** by type, tags, and custom patterns
- **Report formats:** console, JSON, JUnit XML
- **Parallel execution** support with `-j` flag
- **Fail-fast mode** with `--fail-fast` flag

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

