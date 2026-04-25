# Topology Generation Example

Generate a topology manifest from a local project or a live URL.

## Local project

```bash
testql topology /path/to/project --format yaml
```

Produces a `TopologyManifest` with nodes for:
- `artifact.root` — the discovered artifact
- `artifact_type.*` — detected project types (`python_package`, `docker`, `openapi3`, ...)
- `interface.*` — exposed interfaces (REST endpoints, CLI commands, ...)
- `dependency.*` — package dependencies
- `evidence.*` — supporting evidence files

## URL with network probes

```bash
testql topology https://tom.sapletta.com/ --scan-network --format toon.yaml
```

This adds:
- `page.root` — the inspected web page
- `link.*` — extracted anchor links
- `asset.*` — page assets (scripts, stylesheets, images)
- `form.*` — detected forms
- `sitemap.root` — bounded sitemap crawl (up to 10 subpages)
- `subpage.*` — crawled internal pages with title/link count metadata

## Format options

- `json` — structured JSON
- `yaml` — human-readable YAML
- `toon.yaml` — TestQL-native TOON format (lossless round-trip)

## Programmatic usage

```python
from testql.topology import build_topology, render_topology

topology = build_topology("/path/to/project", scan_network=False)
text = render_topology(topology, fmt="toon.yaml")
print(text)
```
