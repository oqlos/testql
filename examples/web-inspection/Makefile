# Web Inspection Example — Makefile

.PHONY: help run inspect

URL ?= https://tom.sapletta.com/
OUT_DIR ?= .testql

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: inspect ## Alias for inspect

inspect: ## Inspect URL with HTTP topology extraction
	bash demo.sh $(URL)

dry-run: ## Show command without executing
	@echo "testql inspect $(URL) --scan-network --out-dir $(OUT_DIR)"
