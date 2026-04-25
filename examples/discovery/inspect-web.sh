#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
URL="${1:-https://example.com}"
OUT_DIR="$ROOT_DIR/examples/discovery/inspect-output"

mkdir -p "$OUT_DIR"

echo "=== Inspecting: $URL ==="
testql inspect "$URL" \
  --scan-network \
  --out-dir "$OUT_DIR"

echo ""
echo "Artifacts written to: $OUT_DIR"
echo "Summary: $OUT_DIR/summary.md"
