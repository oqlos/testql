# Unit Testing Example — Makefile

.PHONY: help run dry-run math pytest

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: ## Run all unit test examples (requires Python env)
	./run.sh

dry-run: ## Validate scenarios without executing
	./run.sh --dry-run

math: ## Run math assertions test (dry-run)
	testql run test-math.iql --dry-run

pytest: ## Run pytest suite test (dry-run)
	testql run test-pytest.iql --dry-run
