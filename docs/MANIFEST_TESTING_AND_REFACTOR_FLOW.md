# Manifest Testing and Refactor Flow (TestQL + Windsurf)

This runbook shows how to:

1. Validate all supported manifest types.
2. Generate `*.testql.toon.yaml` scenarios.
3. Execute dry-run testing and collect JSON reports.
4. Use reports as input for refactoring iterations.
5. Verify current MCP integration status for Windsurf (JetBrains and VSCode).

## Supported manifest source types

`testql generate-ir` supports config-like sources:

- `makefile`
- `taskfile`
- `docker-compose`
- `buf`
- `config` (auto-detection alias)

## Quick smoke (all manifest types)

Run from your target project root:

```bash
bash /home/tom/github/oqlos/testql/scripts/smoke_manifest_flow.sh .
```

Artifacts are written to:

- `.testql-manifest-smoke/generated/*.testql.toon.yaml`
- `.testql-manifest-smoke/reports/manifest-run.json`
- `.testql-manifest-smoke/reports/topology.json`

## Manual command matrix

### 1) Generate tests from each manifest type

```bash
testql generate-ir --from makefile:./Makefile --to testtoon --out .testql/generated/makefile.testql.toon.yaml
testql generate-ir --from taskfile:./Taskfile.yml --to testtoon --out .testql/generated/taskfile.testql.toon.yaml
testql generate-ir --from docker-compose:./docker-compose.yml --to testtoon --out .testql/generated/docker-compose.testql.toon.yaml
testql generate-ir --from buf:./buf.yaml --to testtoon --out .testql/generated/buf.testql.toon.yaml
```

### 2) Validate alias auto-detection (`config`)

```bash
testql generate-ir --from config:./Makefile --to testtoon --out .testql/generated/config-makefile.testql.toon.yaml
testql generate-ir --from config:./Taskfile.yml --to testtoon --out .testql/generated/config-taskfile.testql.toon.yaml
testql generate-ir --from config:./docker-compose.yml --to testtoon --out .testql/generated/config-docker-compose.testql.toon.yaml
testql generate-ir --from config:./buf.yaml --to testtoon --out .testql/generated/config-buf.testql.toon.yaml
```

### 3) Run generated scenarios and write one aggregate report

```bash
testql run .testql/generated --dry-run --quiet --output json > .testql/reports/manifest-iteration.json
```

### 4) Optional topology snapshot

```bash
testql topology . --format json > .testql/reports/topology.json
```

## Refactor loop based on report

Use this loop for each iteration:

1. Read `.testql/reports/manifest-iteration.json`.
2. Extract failing scenarios and root cause (command, assertion, target path).
3. Refactor minimal code/config changes in source manifests or scripts.
4. Re-generate affected `*.testql.toon.yaml`.
5. Re-run `testql run .testql/generated --dry-run --quiet --output json`.
6. Stop after 2 consecutive clean runs.

Suggested metrics per iteration:

- `failed_files`
- total failed assertions
- mean `duration_ms`
- number of changed manifests/files

## MCP Windsurf status check (current)

Current repository state:

- `testql.mcp.server` module is available as MCP entrypoint.
- Tools exposed: source/target listing, IR generation, scenario run, topology build.

Meaning:

- TestQL can be used as an MCP stdio server in Windsurf.
- CLI workflows remain valid and can run alongside MCP tools.

### Quick verification

```bash
.venv/bin/python -c "import testql.mcp; print('ok')"
.venv/bin/python -m testql.mcp.server
```

If `mcp` package is missing:

```bash
pip install mcp
```

## Windsurf setup snippets

### VSCode Windsurf (`.windsurf/mcp.json`)

```json
{
  "mcpServers": {
    "testql": {
      "command": "python",
      "args": ["-m", "testql.mcp.server"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### JetBrains Windsurf plugin

Configure an MCP server with stdio transport:

- command: `python`
- args: `-m testql.mcp.server`
- working directory: your project root

Then execute TestQL loop commands from tasks/workflows/terminal:

- `testql generate-ir ...`
- `testql run ... --output json`
- `testql topology ... --format json`

## Next refactor steps in codebase

1. Add report summarization tool (`summarize_report`) returning compact NLP + metrics.
2. Add guarded refactor proposal tool (`propose_refactor`) based on report deltas.
3. Add MCP integration tests for stdio handshake and tool contract validation.
