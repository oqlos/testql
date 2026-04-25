# Topology Example — Makefile

.PHONY: help run local url

TARGET ?= ../../
URL ?= https://tom.sapletta.com/

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: local ## Alias for local topology

local: ## Build topology for local project
	bash run.sh $(TARGET)

url: ## Build topology for live URL
	bash run.sh $(URL)

dry-run: ## Show command without executing
	@echo "testql topology $(TARGET) --format toon.yaml"
