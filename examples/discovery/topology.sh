#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TESTQL="$ROOT_DIR/venv/bin/testql"
if [ ! -x "$TESTQL" ]; then TESTQL="testql"; fi

set -euo pipefail

TARGET="${1:-$ROOT_DIR}"
OUT_DIR="${2:-$ROOT_DIR/examples/discovery/output}"

mkdir -p "$OUT_DIR"

echo "=== Building topology for: $TARGET ==="
"$TESTQL" topology "$TARGET" --format toon --out "$OUT_DIR/topology.toon.yaml"

echo ""
echo "Topology written to: $OUT_DIR/topology.toon.yaml"
echo "Formats available: json, yaml, toon"
