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

### 1. `run.sh` — Quick commands

| Command | Description |
|---------|-------------|
| `./run.sh echo text` | Print human-readable AI context (default) |
| `./run.sh echo json` | Print JSON echo (pipe to `> ai-context.json`) |
| `./run.sh echo sumd` | Print SUMD-format echo |
| `./run.sh build` | Run `doql build` to regenerate `build/` from `app.doql` |
| `./run.sh export-less` | Re-export `app.doql` -> `app.doql.less` (sync formats) |

```bash
# Most common — get JSON context for an LLM
./run.sh echo json > ai-context.json

# Rebuild the application after editing app.doql
./run.sh build

# Re-export LESS after changing DOQL model
./run.sh export-less
```

### 2. Makefile — All tasks in one place

A `Makefile` is provided for convenience:

```bash
make help          # Show all available targets
make echo          # Same as ./run.sh echo text
make echo-json     # JSON echo
make build         # doql build
make export-less   # Sync LESS export
make run           # docker compose up (with build)
make run-daemon    # docker compose up -d
make stop          # docker compose down
make run-local     # uvicorn main:app --reload (inside build/api/)
make test-api      # curl smoke tests against :8008
make clean         # rm -rf build/
make rebuild       # clean + build + run-daemon
```

### 3. Generate AI context (TestQL echo)

```bash
# Generate text output (human-readable)
./run.sh echo text

# Generate JSON output (for LLM consumption)
./run.sh echo json

# Save to file
./run.sh echo json > ai-context.json
```

### 4. Generate a working application from DOQL

```bash
# Ensure doql CLI is installed
# pip install doql

# Build the entire app (FastAPI backend, Docker infra, workflows)
doql -f app.doql build

# Or via Makefile
make build

# Export to other formats
doql -f app.doql export --format openapi -o openapi.yaml
doql -f app.doql export --format less   -o app.doql.less
```

After `doql build`, the generated application is in `build/`:

| Artifact | Path | Description |
|----------|------|-------------|
| FastAPI app | `build/api/` | `main.py`, `routes.py`, `models.py`, `schemas.py` |
| Infrastructure | `build/infra/` | `docker-compose.yml`, `Dockerfile`, `.env.docker` |
| Workflows | `build/workflows/` | Workflow engine + scheduler |

### 5. Run the generated application

#### Docker (recommended)

```bash
# Start services (API + Traefik)
cd build/infra
docker compose up --build

# Or from project root
make run           # foreground
make run-daemon    # background
make stop          # stop everything
```

**Ports after `docker compose up`:**
- `http://localhost:8008` — API directly (host-mapped from container port 8000)
- `http://example-api-server.localhost` — via Traefik reverse proxy (port 80/443)

#### Local uvicorn (for quick dev)

```bash
cd build/api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or from project root
make run-local
```

### 6. Verify the running API

```bash
# Health check
curl http://localhost:8008/health

# List devices
curl http://localhost:8008/api/v1/devices

# Create a scenario
curl -X POST http://localhost:8008/api/v1/scenarios \
  -H "Content-Type: application/json" \
  -d '{"name":"demo","config":{}}'

# Or use the Makefile target
make test-api
```

> **Note:** `GET /` returns 404 — the application serves API routes under `/api/v1/*` and `/health`. This is expected.

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
