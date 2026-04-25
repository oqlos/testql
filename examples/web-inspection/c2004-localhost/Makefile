.PHONY: help inspect inspect-matrix show show-matrix clean

URL ?= http://localhost:8100
OUT_DIR ?= .testql-c2004

help: ## Show help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

inspect: ## Run testql inspection and generate maps
	bash run.sh $(URL) $(OUT_DIR)

inspect-matrix: ## Run inspection for predefined SPA routes and aggregate report
	bash run-matrix.sh

show: ## Show generated service map
	@cat $(OUT_DIR)/service-map.txt

show-matrix: ## Show aggregated matrix summary and testql issues
	@cat .testql-matrix/summary.txt
	@echo ""
	@cat .testql-matrix/testql-issues.txt

clean: ## Remove generated artifacts
	rm -rf $(OUT_DIR)
