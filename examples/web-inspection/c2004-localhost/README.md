# c2004 Localhost Inspection (testql)

Inspect running c2004 instance on `http://localhost:8100`, generate service map artifacts, and validate links/assets.

## Quick start

```bash
cd /home/tom/github/oqlos/testql/examples/web-inspection/c2004-localhost
./run.sh
```

## What is generated

- `.testql-c2004/topology.json` and `.testql-c2004/topology.yaml`
- `.testql-c2004/result.json` and `.testql-c2004/result.yaml`
- `.testql-c2004/refactor_plan.json`
- `.testql-c2004/inspection.json`
- `.testql-c2004/service-map.txt` (human readable map)
- `.testql-c2004/service-map.mmd` (Mermaid graph)

## Commands

```bash
make inspect
make inspect URL=http://localhost:8100/connect-id/manual
make show
make inspect-matrix
make show-matrix
```

## SPA Matrix Mode

`inspect-matrix` runs predefined c2004 routes from `routes.txt` and stores outputs in `.testql-matrix/`:

- `summary.txt` - per-route status (warnings/failed/skipped)
- `testql-issues.txt` - extracted warning/failed checks and suggested `testql` fixes

This is useful for SPA apps where static anchor extraction often returns `links=0`.
