# Browser Inspection Example

Use Playwright to render the page in a headless browser, capture console errors, and log network calls.

## Prerequisites

```bash
pip install playwright
playwright install chromium
```

## Quick start

```bash
cd browser-inspection
./run.sh https://tom.sapletta.com/
```

Or run directly:

```bash
testql inspect https://tom.sapletta.com/ \
  --scan-network \
  --browser \
  --out-dir .testql-browser
```

## What it captures

| Data | Description |
|------|-------------|
| `title` | JS-rendered page title |
| `links` | All `<a>` tags after JS execution |
| `assets` | All `<script>`, `<link>`, `<img>` after JS execution |
| `forms` | All `<form>` elements after JS execution |
| `console_errors` | JavaScript console errors during load |
| `network_calls` | All network requests (XHR, fetch, websocket, ...) |

## Additional browser checks

When `--browser` is enabled, the analyzer adds:

```
check.browser.render   — Page was rendered in a browser environment.
check.browser.console  — No console errors detected.
check.browser.network  — Captured N network call(s).
```

## Compare HTTP vs Browser

| Mode | Command | Captures JS-rendered content |
|------|---------|------------------------------|
| HTTP | `testql inspect URL --scan-network` | No |
| Browser | `testql inspect URL --scan-network --browser` | Yes |

## Programmatic usage

```python
from testql.topology import build_topology

topology = build_topology(
    "https://tom.sapletta.com/",
    scan_network=True,
    use_browser=True,
)
page = next(n for n in topology.nodes if n.kind == "page")
print("console errors:", page.metadata.get("console_errors", []))
print("network calls:", len(page.metadata.get("network_calls", [])))
```
