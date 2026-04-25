# Artifact Bundle (`.testql`) Example

The `testql inspect` command can write a complete inspection artifact bundle into a `.testql/` directory.

## Generate a bundle

```bash
testql inspect https://tom.sapletta.com/ \
  --scan-network \
  --out-dir .testql
```

## Bundle contents

| File | Description |
|------|-------------|
| `inspection.json` | Merged envelope: topology + result + refactor plan |
| `topology.json` | Full topology with nodes, edges, traces |
| `topology.yaml` | YAML serialization of topology |
| `topology.toon.yaml` | TestQL-native TOON format |
| `result.json` | TestResultEnvelope with checks, findings, actions |
| `result.yaml` | YAML serialization of result |
| `result.toon.yaml` | TestQL-native TOON format |
| `refactor_plan.json` | RefactorPlan with findings and suggested actions |
| `refactor_plan.yaml` | YAML serialization of plan |
| `refactor_plan.toon.yaml` | TestQL-native TOON format |
| `metadata.json` | Bundle manifest: timestamp, source URL, summary |
| `summary.txt` | Human-readable plain-text summary |

## Re-inspect from bundle

```bash
# You can point any tool back at the bundle directory
cat .testql/metadata.json | python3 -m json.tool
```

## Run the example script

A single-file Python script is included. It performs the same inspection as the CLI command above and writes the bundle to `.testql/`.

```bash
cd examples/artifact-bundle
python3 generate_bundle.py
```

## Programmatic usage

```python
from pathlib import Path
from testql.results.artifacts import write_inspection_artifacts
from testql.results.analyzer import inspect_source

topology, envelope, plan = inspect_source("https://tom.sapletta.com/", scan_network=True)
write_inspection_artifacts(
    topology=topology,
    envelope=envelope,
    plan=plan,
    out_dir=Path(".testql"),
)
```
