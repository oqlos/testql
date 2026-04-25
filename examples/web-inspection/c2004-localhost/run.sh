#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTQL="$ROOT_DIR/venv/bin/testql"
if [ ! -x "$TESTQL" ]; then
  TESTQL="testql"
fi

URL="${1:-http://localhost:8100}"
OUTDIR="${2:-.testql-c2004}"

echo "==> Inspecting: $URL"
echo "==> Output dir: $OUTDIR"
"$TESTQL" inspect "$URL" --scan-network --out-dir "$OUTDIR"

echo "==> Building service map artifacts"
export TESTQL_OUTDIR="$OUTDIR"
python3 - <<'PY'
import json
import os
from collections import Counter
from pathlib import Path

outdir = Path(os.environ["TESTQL_OUTDIR"])
topology = json.loads((outdir / "topology.json").read_text())
result = json.loads((outdir / "result.json").read_text())

nodes = topology.get("nodes", [])
edges = topology.get("edges", [])
by_kind = Counter(n.get("kind", "unknown") for n in nodes)

checks = result.get("checks", [])
status = result.get("status", "unknown")

lines = []
lines.append("c2004 service map")
lines.append("================")
lines.append(f"overall status: {status}")
lines.append(f"nodes: {len(nodes)}")
lines.append(f"edges: {len(edges)}")
lines.append("")
lines.append("node kinds:")
for kind, count in sorted(by_kind.items(), key=lambda x: (-x[1], x[0])):
    lines.append(f"- {kind}: {count}")
lines.append("")
lines.append("top nodes:")
for n in nodes[:25]:
    lines.append(f"- [{n.get('kind','unknown')}] {n.get('id','')} -> {n.get('source','')}")
lines.append("")
lines.append("checks:")
for c in checks:
    lines.append(f"- {c.get('status','unknown').upper():8} {c.get('id','')} :: {c.get('summary','')}")

(outdir / "service-map.txt").write_text("\n".join(lines) + "\n")

mmd = ["graph TD"]
for n in nodes:
    node_id = str(n.get("id", "node")).replace("-", "_").replace(":", "_").replace("/", "_").replace(".", "_")
    label = str(n.get("id", "node")).replace('"', "'")
    mmd.append(f"  {node_id}[\"{label}\"]")
for e in edges[:200]:
    src = str(e.get("source", "")).replace("-", "_").replace(":", "_").replace("/", "_").replace(".", "_")
    dst = str(e.get("target", "")).replace("-", "_").replace(":", "_").replace("/", "_").replace(".", "_")
    if src and dst:
        mmd.append(f"  {src} --> {dst}")
(outdir / "service-map.mmd").write_text("\n".join(mmd) + "\n")
PY

echo "==> Done"
echo "    - $OUTDIR/service-map.txt"
echo "    - $OUTDIR/service-map.mmd"
