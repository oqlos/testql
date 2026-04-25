# Flow Control Example — Makefile

.PHONY: help run dry-run variables

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: ## Run all flow control examples
	./run.sh

dry-run: ## Validate without executing
	./run.sh --dry-run

variables: ## Run variables test (dry-run)
	testql run variables.iql --dry-run
