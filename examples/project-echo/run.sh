#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FORMAT="${1:-text}"

echo "=== Generating Project Echo ($FORMAT) ==="
testql echo \
  --toon-path "$ROOT_DIR/examples/project-echo" \
  --doql-path "$ROOT_DIR/examples/project-echo/app.doql.less" \
  --format "$FORMAT"

echo ""
echo "Done. Use 'json' format for LLM consumption."
