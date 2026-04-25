# TestTOON Basics Example — Makefile

.PHONY: help run dry-run minimal variables assertions

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: ## Run all TestTOON examples
	./run.sh

dry-run: ## Validate without executing
	./run.sh --dry-run

minimal: ## Run minimal scenario (dry-run)
	testql run minimal.testql.toon.yaml --dry-run

variables: ## Run variables scenario (dry-run)
	testql run variables.testql.toon.yaml --dry-run

assertions: ## Run assertions scenario (dry-run)
	testql run assertions.testql.toon.yaml --dry-run
