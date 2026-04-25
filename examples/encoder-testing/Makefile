# Encoder Testing Example — Makefile

.PHONY: help run dry-run basic complex

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: ## Run all encoder examples (requires hardware)
	./run.sh

dry-run: ## Validate without executing
	./run.sh --dry-run

basic: ## Run basic encoder lifecycle (dry-run)
	testql run basic-encoder.iql --dry-run

complex: ## Run complex sequence (dry-run)
	testql run complex-sequence.iql --dry-run
