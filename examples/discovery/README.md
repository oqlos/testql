# Discovery and Topology with TestQL

This example demonstrates TestQL's artifact discovery and topology building capabilities.

## Usage

```bash
# Discover local artifacts
./discover-local.sh

# Build topology from a project
./topology.sh ../..  # or any project path

# Inspect a live web page (with browser)
./inspect-web.sh https://example.com
```

## Commands demonstrated

- `testql discover` — Find and classify project artifacts
- `testql topology` — Build a topology graph from artifacts
- `testql inspect` — Deep inspection of URLs with Playwright
