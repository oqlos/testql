#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TESTQL="$ROOT_DIR/venv/bin/testql"
if [ ! -x "$TESTQL" ]; then TESTQL="testql"; fi

# Web inspection demo — run against a target URL

set -euo pipefail

URL="${1:-https://tom.sapletta.com/}"
OUTDIR="${2:-.testql}"

echo "==> Inspecting $URL"
echo "==> Output directory: $OUTDIR"

# Full scan with network probes
"$TESTQL" inspect "$URL" --scan-network --out-dir "$OUTDIR"

echo "==> Generated files in $OUTDIR:"
ls -la "$OUTDIR"

echo "==> Topology summary (top 5 nodes)"
python3 -c "
import json, sys
with open('$OUTDIR/topology.json') as f:
    data = json.load(f)
for n in data.get('nodes', [])[:5]:
    print(f\"  {n['id']:20}  {n['kind']:12}  {str(n['source'])[:60]}\")
print(f\"  ... and {len(data.get('nodes',[])) - 5} more nodes\")
"

echo "==> Check results summary"
python3 -c "
import json, sys
with open('$OUTDIR/result.json') as f:
    data = json.load(f)
for c in data.get('checks', []):
    status = c['status'].upper()
    print(f\"  [{status:8}] {c['id']:40} {c['summary']}\")
"

echo "==> Done"
