# Shell Testing Example — Makefile

.PHONY: help run dry-run basic files

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: ## Run all shell tests
	./run.sh

dry-run: ## Validate without executing commands
	./run.sh --dry-run

basic: ## Run only basic-commands test (dry-run)
	testql run basic-commands.iql --dry-run

files: ## Run only file-operations test (dry-run)
	testql run file-operations.iql --dry-run
