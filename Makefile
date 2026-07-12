# Makefile for testql
# Provides convenient commands for development, testing, and deployment

.PHONY: help install install-dev test clean publish publish-confirm publish-test version

# Default target
help:
	@echo "🚀 TestQL Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Setup:"
	@echo "  install          Install testql in development mode"
	@echo "  install-dev      Install testql with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  test             Run tests"
	@echo "  lint             Run linting"
	@echo "  format           Format code"
	@echo "  clean            Clean temporary files"
	@echo ""
	@echo "Release:"
	@echo "  publish          Build package for PyPI (dry-run)"
	@echo "  publish-confirm  Upload to PyPI"
	@echo "  publish-test     Upload to TestPyPI"
	@echo "  version          Show current version"
	@echo ""

# Installation
install:
	@echo "📦 Installing testql..."
	@if command -v uv > /dev/null 2>&1; then \
		uv pip install -e .; \
	else \
		pip install -e .; \
	fi
	@echo "✅ Installation completed!"

install-dev:
	@echo "📦 Installing testql with dev dependencies..."
	@if command -v uv > /dev/null 2>&1; then \
		uv pip install -e ".[dev]"; \
	else \
		pip install -e ".[dev]"; \
	fi
	@echo "✅ Dev installation completed!"

# Testing
test:
	@echo "🧪 Running tests..."
	.venv/bin/python -m pytest tests/ -v --tb=short

test-cov:
	@echo "🧪 Running tests with coverage..."
	.venv/bin/python -m pytest tests/ -v --cov=testql --cov-report=term-missing --cov-report=json

# Code quality
lint:
	@echo "🔍 Running linting with ruff..."
	.venv/bin/python -m ruff check testql/
	.venv/bin/python -m ruff check tests/

format:
	@echo "📝 Formatting code with ruff..."
	.venv/bin/python -m ruff format testql/
	.venv/bin/python -m ruff format tests/

# Utilities
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ coverage.json
	@echo "✅ Clean completed!"

# Release helpers
publish:
	@echo "📦 Publishing to PyPI..."
	@command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build)
	rm -rf dist/ build/ *.egg-info/
	.venv/bin/python -m build
	.venv/bin/twine check dist/*
	@echo "⚡ Ready to upload. Run: make publish-confirm to upload to PyPI"

publish-confirm:
	@echo "🚀 Uploading to PyPI..."
	.venv/bin/twine upload dist/*

publish-test:
	@echo "📦 Publishing to TestPyPI..."
	@command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build)
	rm -rf dist/ build/ *.egg-info/
	.venv/bin/python -m build
	.venv/bin/twine upload --repository testpypi dist/*

version:
	@echo "📦 Version information..."
	@cat VERSION
	@.venv/bin/python -c "from importlib.metadata import version; print(f'Installed version: {version(\"testql\")}')"

# TestQL Testing Targets
.PHONY: testql-encoder testql-menu testql-parallel testql-visual testql-all testql-results

testql-encoder:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  🎯 TestQL Encoder Test - Basic (9 modules)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	python parallel_test.py --concurrent 5 --headless
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  ✅ Encoder test completed!"
	@echo "  📄 Results: parallel_test_results.json"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

testql-menu:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  🎯 TestQL Menu Test - Complete (69 combinations)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	python test_all_menu_combinations.py --headless --concurrent 5
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  ✅ Menu test completed!"
	@echo "  📄 Results: complete_menu_test_results.json"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

testql-parallel:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  🚀 TestQL Parallel Test - Fast"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	python parallel_test.py --concurrent 9 --headless
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  ✅ Parallel test completed!"
	@echo "  📄 Results: parallel_test_results.json"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

testql-visual:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  🎬 TestQL Visual Test - Browser Window"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "  📺 WATCH YOUR SCREEN - Browser window will open!"
	@echo ""
	python show_browser.py
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  ✅ Visual test completed!"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

testql-all:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  🎯 TestQL - Running ALL Tests"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "1️⃣  Parallel Test..."
	@$(MAKE) testql-parallel
	@echo ""
	@echo "2️⃣  Complete Menu Test..."
	@$(MAKE) testql-menu
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  ✅ All tests completed!"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

testql-results:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  📊 TestQL Results Summary"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@if [ -f parallel_test_results.json ]; then \
		echo "📄 Parallel Test:"; \
		cat parallel_test_results.json | python -m json.tool | grep -E '"(total|passed|failed|total_time)"' | head -5; \
		echo ""; \
	fi
	@if [ -f complete_menu_test_results.json ]; then \
		echo "📄 Complete Menu Test:"; \
		cat complete_menu_test_results.json | python -m json.tool | grep -E '"(total|passed|failed|total_time)"' | head -5; \
		echo ""; \
	fi
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
