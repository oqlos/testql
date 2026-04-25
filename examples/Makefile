# Meta-runner for all TestQL examples
# Usage: make help  (shows all targets), make all  (runs every example)

EXAMPLES := api-testing testtoon-basics shell-testing gui-testing \
            discovery web-inspection topology artifact-bundle \
            browser-inspection project-echo web-inspection-dot-testql \
            unit-testing encoder-testing flow-control

.PHONY: all help $(EXAMPLES)

help: ## Show this help + per-example Makefile help
	@echo "Top-level targets:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | grep -v 'EXAMPLES' | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Per-example help (run in subdirectory):"
	@for d in $(EXAMPLES); do \
		if [ -f "$$d/Makefile" ]; then \
			echo "  cd $$d && make help"; \
		fi; \
	done

all: $(EXAMPLES) ## Run every example (best-effort, failures are ignored)

api-testing: ## REST API testing
	@echo "=== api-testing ==="
	cd api-testing && make run || true

testtoon-basics: ## TestTOON tabular format
	@echo "=== testtoon-basics ==="
	cd testtoon-basics && make run || true

shell-testing: ## Shell command testing
	@echo "=== shell-testing ==="
	cd shell-testing && make run || true

gui-testing: ## GUI automation (dry-run, no browser needed)
	@echo "=== gui-testing ==="
	cd gui-testing && make dry-run || true

discovery: ## Artifact discovery
	@echo "=== discovery ==="
	cd discovery && make local || true

web-inspection: ## HTTP topology extraction
	@echo "=== web-inspection ==="
	cd web-inspection && make dry-run || true

topology: ## Topology graph generation
	@echo "=== topology ==="
	cd topology && make dry-run || true

artifact-bundle: ## Structured artifact bundle
	@echo "=== artifact-bundle ==="
	cd artifact-bundle && make dry-run || true

browser-inspection: ## Playwright browser inspection
	@echo "=== browser-inspection ==="
	cd browser-inspection && make dry-run || true

project-echo: ## AI context + DOQL app generation
	@echo "=== project-echo ==="
	cd project-echo && make echo-json || true

web-inspection-dot-testql: ## Legacy .testql bundle
	@echo "=== web-inspection-dot-testql ==="
	cd web-inspection-dot-testql && bash run.sh --dry-run 2>/dev/null || true

unit-testing: ## Python unit test execution
	@echo "=== unit-testing ==="
	cd unit-testing && make dry-run || true

encoder-testing: ## Hardware encoder control sequences
	@echo "=== encoder-testing ==="
	cd encoder-testing && make dry-run || true

flow-control: ## Variables, logging, and script composition
	@echo "=== flow-control ==="
	cd flow-control && make dry-run || true
