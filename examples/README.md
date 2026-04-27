# TestQL Examples

This directory contains runnable examples demonstrating TestQL's core features.

## Overview

| Example | What it demonstrates | Key command |
|---------|---------------------|-------------|
| [api-testing](api-testing/) | REST API testing with assertions | `make run` or `testql run *.testql.toon.yaml` |
| [gui-testing](gui-testing/) | Playwright-based GUI automation | `testql run *.oql` |
| [shell-testing](shell-testing/) | Shell command testing | `testql run *.oql` |
| [testtoon-basics](testtoon-basics/) | TestTOON tabular format syntax | `testql run *.testql.toon.yaml` |
| [project-echo](project-echo/) | AI-friendly project metadata + DOQL app generation | `make help` |
| [browser-inspection](browser-inspection/) | Playwright page rendering | `testql inspect --browser` |
| [web-inspection](web-inspection/) | HTTP page topology extraction | `testql inspect --scan-network` |
| [topology](topology/) | Generate topology graphs | `testql topology` |
| [artifact-bundle](artifact-bundle/) | Structured output bundles | `testql inspect --out-dir .testql` |
| [web-inspection-dot-testql](web-inspection-dot-testql/) | Legacy inspection pipeline | `testql inspect` |
| [unit-testing](unit-testing/) | Python unit test execution | `make dry-run` |
| [encoder-testing](encoder-testing/) | Hardware encoder control sequences | `make dry-run` |
| [flow-control](flow-control/) | Variables, logging, and script composition | `make dry-run` |

> **Tip:** All examples support `make help` to list available targets. Use `make dry-run` for validation without execution.

## Quick Start

```bash
# API tests (Makefile available)
cd api-testing && make run               # default URL
cd api-testing && make run-custom URL=http://localhost:8008

# Dry-run GUI tests (no browser needed)
cd gui-testing && ./run.sh --dry-run

# Run shell tests
cd shell-testing && ./run.sh

# Discover artifacts in the current project
cd discovery && ./discover-local.sh

# Inspect a live URL with Playwright
cd browser-inspection && ./run.sh https://example.com

# Generate AI project context
cd project-echo && ./run.sh echo json > ai-context.json

# Full end-to-end: build app from DOQL, start Docker, run contract tests
cd project-echo && make build && make test-contract

# Unit testing examples (dry-run)
cd unit-testing && make dry-run

# Encoder control sequences (dry-run)
cd encoder-testing && make dry-run

# Variables and flow control (dry-run)
cd flow-control && make dry-run
```

## Running All Examples

```bash
# Run each example
for dir in */; do
  if [ -f "$dir/run.sh" ]; then
    echo "=== Running $dir ==="
    (cd "$dir" && bash run.sh --dry-run 2>/dev/null || bash run.sh 2>/dev/null)
  fi
  if [ -f "$dir/Makefile" ]; then
    echo "=== Makefile in $dir ==="
    (cd "$dir" && make help 2>/dev/null || true)
  fi
done
```

## Format Reference

TestQL supports three file formats:

- **`.testql.toon.yaml`** — TestTOON tabular format (recommended for API tests)
- **`.oql`** — Legacy imperative commands (recommended for GUI/shell tests)
- **`.tql`** — Compact single-line commands (legacy)

See [testtoon-basics](testtoon-basics/) for TestTOON syntax examples.
