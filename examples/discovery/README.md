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


## What each script does

| Script | Command | Output |
|--------|---------|--------|
| `discover-local.sh` | `testql discover .` | Artifact manifest (types, dependencies, interfaces) |
| `topology.sh` | `testql topology PROJECT` | Topology graph (nodes, edges, traces) |
| `inspect-web.sh` | `testql inspect URL --scan-network` | Full inspection bundle in `.testql/` |

## Network inspection

`./inspect-web.sh https://tom.sapletta.com/` performs:
- HTTP GET + parse HTML for title, links, assets, forms
- Bounded link validation (HEAD requests on internal links)
- Bounded asset validation (HEAD requests on all assets)
- Bounded sitemap crawl (up to 10 sub-pages)
- Generates `.testql/` artifact bundle
