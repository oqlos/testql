#!/usr/bin/env bash
# Topology generation demo — generate topology from local project or URL

set -euo pipefail

SOURCE="${1:-https://tom.sapletta.com/}"
FORMAT="${2:-toon.yaml}"

echo "==> Building topology for $SOURCE (format=$FORMAT)"

testql topology "$SOURCE" --scan-network --format "$FORMAT" > "topology.$FORMAT"

echo "==> Wrote topology.$FORMAT"
echo "==> Summary:"

python3 -c "
import json, sys
with open('topology.json', 'r') as f:
    data = json.load(f)
print(f\"Nodes: {len(data.get('nodes', []))}\")
print(f\"Edges: {len(data.get('edges', []))}\")
print(f\"Traces: {len(data.get('traces', []))}\")
for node in data.get('nodes', [])[:8]:
    print(f\"  [{node['kind']:12}] {node['id']:30} {str(node['source'])[:50]}\")
if len(data.get('nodes', [])) > 8:
    print(f\"  ... and {len(data.get('nodes', [])) - 8} more nodes\")
"

echo "==> Done"
