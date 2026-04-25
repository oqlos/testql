# Web inspection with `.testql` artifact bundle

This example shows how to inspect a live web page and store every structured artifact under a local `.testql/` directory.

The command is opt-in for network access via `--scan-network`.

```bash
python3 -m testql.cli inspect https://tom.sapletta.com/ \
  --scan-network \
  --out-dir examples/web-inspection-dot-testql/.testql
```

After running, the `.testql/` directory contains machine-readable and LLM-friendly outputs:

```text
.testql/
├── metadata.json
├── topology.json
├── topology.yaml
├── topology.toon.yaml
├── result.json
├── result.yaml
├── result.toon.yaml
├── refactor-plan.json
├── refactor-plan.yaml
├── refactor-plan.toon.yaml
├── inspection.json
├── inspection.yaml
├── inspection.toon.yaml
└── summary.md
```

Suggested follow-up commands:

```bash
cat examples/web-inspection-dot-testql/.testql/summary.md
python3 -m json.tool examples/web-inspection-dot-testql/.testql/metadata.json
head -80 examples/web-inspection-dot-testql/.testql/topology.toon.yaml
```

## What this validates today

- HTTP reachability of the page.
- HTML title extraction.
- Link, asset, and form topology extraction.
- Structured result envelope.
- Refactor-plan placeholder generated from topology findings.
- NLP summary in `summary.md`.

## What comes next

This example does not yet perform full browser automation. The next layer should add Playwright navigation, screenshots, console-error capture, network logs, and link-by-link validation.
