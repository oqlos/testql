# Project Echo — Makefile
# Quick reference for common tasks in this example.

.PHONY: help echo echo-json echo-sumd export-less build run run-local stop test-api clean

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ─── TestQL echo ───

echo: ## Run testql echo (text format)
	@./run.sh echo text

echo-json: ## Run testql echo (JSON format, for LLM consumption)
	@./run.sh echo json

echo-sumd: ## Run testql echo (SUMD format)
	@./run.sh echo sumd

# ─── DOQL build / export ───

export-less: ## Re-export app.doql -> app.doql.less (sync LESS with DOQL source)
	@./run.sh export-less

build: ## Generate working application from DOQL into build/
	@./run.sh build

# ─── Run the generated application ───

run: ## Start the generated app in Docker (docker compose up)
	@echo "=== Starting Docker services ==="
	cd build/infra && docker compose up --build

run-daemon: ## Start Docker services in background
	@echo "=== Starting Docker services (detached) ==="
	cd build/infra && docker compose up --build -d

stop: ## Stop Docker services
	@echo "=== Stopping Docker services ==="
	cd build/infra && docker compose down

run-local: ## Run the FastAPI app locally (requires Python + deps in build/api/)
	@echo "=== Starting FastAPI locally ==="
	cd build/api && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# ─── Test / verify ───

test-api: ## Quick curl smoke tests against the running API
	@echo "=== API Smoke Tests ==="
	@echo "Health check:"
	@curl -s http://localhost:8008/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8008/health
	@echo ""
	@echo "List devices:"
	@curl -s http://localhost:8008/api/v1/devices | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8008/api/v1/devices
	@echo ""
	@echo "Create scenario:"
	@curl -s -X POST http://localhost:8008/api/v1/scenarios \
		-H "Content-Type: application/json" \
		-d '{"name":"test-scenario","config":{}}' | python3 -m json.tool 2>/dev/null || true

test-api-local: ## Quick curl against local uvicorn (port 8000)
	@echo "=== API Smoke Tests (local port 8000) ==="
	@curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health

# ─── End-to-end: TestQL against built app ───

test-contract: ## Start Docker, wait for API, then run TestQL contract tests
	@echo "=== Starting API in Docker (detached) ==="
	cd build/infra && docker compose up --build -d
	@echo "=== Waiting for API health ==="
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		if curl -s http://localhost:8008/health >/dev/null 2>&1; then \
			echo "API is up."; break; \
		fi; \
		echo "... ($$i/10)"; sleep 2; \
	done
	@echo "=== Running TestQL contract ==="
	testql run api-contract.testql.toon.yaml --output json || python3 -m testql run api-contract.testql.toon.yaml --output json
	@echo "=== Stopping Docker ==="
	cd build/infra && docker compose down

# ─── Cleanup ───

clean: ## Remove build/ directory
	@echo "=== Removing build/ ==="
	rm -rf build/

rebuild: clean build run-daemon ## Full rebuild: clean + build + start detached
