#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="$ROOT_DIR/examples/web-inspection-dot-testql/.testql"
URL="${1:-https://tom.sapletta.com/}"

python3 -m testql.cli inspect "$URL" \
  --scan-network \
  --out-dir "$OUT_DIR"

echo "Artifacts written to: $OUT_DIR"
echo "Summary: $OUT_DIR/summary.md"
