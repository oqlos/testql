# GUI Testing Example — Makefile

.PHONY: help run dry-run login search

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: ## Run all GUI tests (requires Playwright)
	./run.sh

dry-run: ## Validate without browser
	./run.sh --dry-run

login: ## Run only login-form test (dry-run)
	testql run login-form.iql --dry-run

search: ## Run only search-workflow test (dry-run)
	testql run search-workflow.iql --dry-run
