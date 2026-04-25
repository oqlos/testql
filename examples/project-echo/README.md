# Project Echo (AI Context)

This example demonstrates generating AI-friendly project metadata by combining
TestTOON scenarios with DOQL system models, and shows how to generate a working
application from the DOQL model.

## Files

- `app.doql` — Source DOQL model (YAML-like, consumed by `doql` CLI)
- `app.doql.less` — System model exported to DOQL LESS format (consumed by TestQL)
- `api-contract.testql.toon.yaml` — API contract test scenarios
- `run.sh` — Generate the echo output
- `build/` — Generated application code (FastAPI + Docker) produced by `doql build`

## Usage

### 1. Generate AI context (TestQL echo)

```bash
# Generate text output (human-readable)
./run.sh text

# Generate JSON output (for LLM consumption)
./run.sh json

# Save to file
./run.sh json > ai-context.json
```

### 2. Generate a working application from DOQL

```bash
# Ensure doql CLI is installed
# pip install doql

# Build the entire app (FastAPI backend, Docker infra, workflows)
doql -f app.doql build

# Run locally (requires .env)
cp build/infra/.env.docker .env
doql -f app.doql run

# Export to other formats
doql -f app.doql export --format openapi -o openapi.yaml
doql -f app.doql export --format less   -o app.doql.less
```

After `doql build`, the generated application is in `build/`:

| Artifact | Path | Description |
|----------|------|-------------|
| FastAPI app | `build/api/` | `main.py`, `routes.py`, `models.py`, `schemas.py` |
| Infrastructure | `build/infra/` | `docker-compose.yml`, `Dockerfile` |
| Workflows | `build/workflows/` | Workflow engine + scheduler |

## TestQL vs DOQL — Data Comparison

| Aspect | TestQL (`api-contract.testql.toon.yaml`) | DOQL (`app.doql` / `app.doql.less`) |
|--------|------------------------------------------|--------------------------------------|
| **Purpose** | Describes *how to test* the API | Describes *what the system is* |
| **Base URL** | `http://localhost:8101` (v3) | Defined in `INTERFACE api` + deploy target |
| **Endpoints** | Concrete: `GET /health`, `GET /devices`, `POST /scenarios`, `DELETE /scenarios/{id}` | Generated automatically from entities (`Device`, `Scenario`) |
| **Entities** | Not present | `Device`, `Scenario` with full field definitions |
| **Workflows** | Not present | `device_provisioning` (Register → Configure → Activate → Monitor) |
| **Interfaces** | REST API assertions (status < 500, content-type) | `api` (REST), `ws` (WebSocket events) |
| **Auth** | BearerToken (in old LESS) | `bearer` (in DOQL interface) |
| **Deploy** | Not present | `docker-compose` target |

### Key Differences

- **TestQL is contract-first** — it lists the exact HTTP calls and expected responses.
- **DOQL is model-first** — it defines entities, fields, workflows and lets `doql build` derive routes, DB models, and Docker setup.
- The `DELETE /scenarios/{id}` test in TestQL maps 1-to-1 to the generated `DELETE /api/v1/scenarios/{item_id}` route from DOQL.
- The `Device` and `Scenario` entities in DOQL drive the generated SQLAlchemy models and CRUD routes, while TestQL only tests the resulting API surface.

## Is the DOQL correctly generated?

The `app.doql.less` file is produced by the official `doql` CLI:

```bash
doql -f app.doql export --format less -o app.doql.less
```

This guarantees it follows the DOQL LESS schema that TestQL's `doql_parser.py` understands (`app { ... }`, `entity[name="..."] { ... }`, `workflow[name="..."] { ... }`, etc.).

Before the fix, `app.doql.less` was hand-written in an incompatible LESS-like syntax (`.entity(Device) { ... }`) that TestQL could not parse. Now it is machine-exported and parseable.
