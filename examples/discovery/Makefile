# Discovery Example — Makefile

.PHONY: help local web inspect topology

ROOT_DIR ?= $(shell cd ../.. && pwd)
TARGET ?= $(ROOT_DIR)
URL ?= https://example.com

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

local: ## Discover artifacts in default target (project root)
	bash discover-local.sh $(TARGET)

web: ## Inspect a live URL
	bash inspect-web.sh $(URL)

inspect: ## Alias for web
	bash inspect-web.sh $(URL)

topology: ## Build topology for default target
	bash topology.sh $(TARGET)
