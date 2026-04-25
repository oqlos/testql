# API Testing Example — Makefile

.PHONY: help run run-custom dry-run

URL ?= http://localhost:8101

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: ## Run all API tests against default URL (http://localhost:8101)
	./run.sh

run-custom: ## Run against a custom URL: make run-custom URL=http://localhost:8008
	./run.sh $(URL)

dry-run: ## Validate scenarios without executing
	testql run health-check.testql.toon.yaml --url $(URL) --dry-run
	testql run crud-workflow.testql.toon.yaml --url $(URL) --dry-run

health: ## Run only health-check scenario
	testql run health-check.testql.toon.yaml --url $(URL)

crud: ## Run only CRUD workflow scenario
	testql run crud-workflow.testql.toon.yaml --url $(URL)
