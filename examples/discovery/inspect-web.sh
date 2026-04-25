#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TESTQL="$ROOT_DIR/venv/bin/testql"
if [ ! -x "$TESTQL" ]; then TESTQL="testql"; fi

set -euo pipefail

URL="${1:-https://example.com}"
OUT_DIR="$ROOT_DIR/examples/discovery/inspect-output"

mkdir -p "$OUT_DIR"

echo "=== Inspecting: $URL ==="
"$TESTQL" inspect "$URL" \
  --scan-network \
  --out-dir "$OUT_DIR"

echo ""
echo "Artifacts written to: $OUT_DIR"
echo "Summary: $OUT_DIR/summary.md"
