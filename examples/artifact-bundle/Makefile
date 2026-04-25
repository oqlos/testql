# Artifact Bundle Example — Makefile

.PHONY: help run generate dry-run

URL ?= https://tom.sapletta.com/
OUT_DIR ?= .testql

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: generate ## Alias for generate

generate: ## Generate artifact bundle for URL
	bash run.sh

dry-run: ## Show command without executing
	@echo "testql inspect $(URL) --scan-network --out-dir $(OUT_DIR)"
