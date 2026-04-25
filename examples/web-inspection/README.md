# Web Inspection Example

Inspect a live URL, extract page topology (links, assets, forms), and validate link/asset reachability.

## Quick start

```bash
cd web-inspection
./run.sh https://tom.sapletta.com/
```

## Basic HTTP inspection

```bash
testql inspect https://tom.sapletta.com/ --scan-network --out-dir .testql
```

This performs:
- HTTP GET on the target page
- Extracts `<title>`, `<a href>`, `<script src>`, `<link href>`, `<img src>`, `<form action>`
- Classifies assets by kind (`script`, `stylesheet`, `image`, `icon`, `link`)
- HEAD-checks all internal links (up to 100)
- HEAD-checks all assets
- Produces a `.testql/` artifact bundle with:
  - `topology.json` / `topology.yaml`
  - `result.json` / `result.yaml`
  - `refactor_plan.json`
  - `inspection.json` (merged envelope)

## Output

```
status: passed
links: 100
assets: 61
asset kinds: {'image': 27, 'link': 13, 'script': 10, 'stylesheet': 9, 'icon': 2}
check.web.status: passed - Page returned HTTP 200.
check.web.link_status: passed - All 98 checked internal links returned successful status.
check.web.asset_status: failed - 4 of 61 assets returned error status.
```

## Sitemap crawl

With `--scan-network` the inspection also fetches up to 10 internal sub-pages, extracting their titles and link counts.

## Files

- `run.sh` — script that runs the full inspection pipeline.
