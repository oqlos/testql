# TestQL Examples

This directory contains runnable examples demonstrating TestQL's core features.

## Overview

| Example | What it demonstrates | Key command |
|---------|---------------------|-------------|
| [api-testing](api-testing/) | REST API testing with assertions | `testql run *.testql.toon.yaml` |
| [gui-testing](gui-testing/) | Playwright-based GUI automation | `testql run *.iql` |
| [shell-testing](shell-testing/) | Shell command testing | `testql run *.iql` |
| [testtoon-basics](testtoon-basics/) | TestTOON tabular format syntax | `testql run *.testql.toon.yaml` |
| [project-echo](project-echo/) | AI-friendly project metadata | `testql echo --toon-path ...` |
| [browser-inspection](browser-inspection/) | Playwright page rendering | `testql inspect --browser` |
| [web-inspection](web-inspection/) | HTTP page topology extraction | `testql inspect --scan-network` |
| [topology](topology/) | Generate topology graphs | `testql topology` |
| [artifact-bundle](artifact-bundle/) | Structured output bundles | `testql inspect --out-dir .testql` |
| [web-inspection-dot-testql](web-inspection-dot-testql/) | Legacy inspection pipeline | `testql inspect` |

## Quick Start

```bash
# Run all API test examples
cd api-testing && ./run.sh

# Dry-run GUI tests (no browser needed)
cd gui-testing && ./run.sh --dry-run

# Run shell tests
cd shell-testing && ./run.sh

# Discover artifacts in the current project
cd discovery && ./discover-local.sh

# Inspect a live URL with Playwright
cd browser-inspection && ./run.sh https://example.com

# Generate AI project context
cd project-echo && ./run.sh json
```

## Running All Examples

```bash
# Run each example
for dir in */; do
  if [ -f "$dir/run.sh" ]; then
    echo "=== Running $dir ==="
    (cd "$dir" && bash run.sh --dry-run 2>/dev/null || bash run.sh 2>/dev/null)
  fi
done
```

## Format Reference

TestQL supports three file formats:

- **`.testql.toon.yaml`** — TestTOON tabular format (recommended for API tests)
- **`.iql`** — Legacy imperative commands (recommended for GUI/shell tests)
- **`.tql`** — Compact single-line commands (legacy)

See [testtoon-basics](testtoon-basics/) for TestTOON syntax examples.
