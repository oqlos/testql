#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TESTQL="$ROOT_DIR/venv/bin/testql"
if [ ! -x "$TESTQL" ]; then TESTQL="testql"; fi

set -euo pipefail

URL="${1:-http://localhost:8101}"

echo "=== Minimal Example ==="
"$TESTQL" run "$ROOT_DIR/examples/testtoon-basics/minimal.testql.toon.yaml" --url "$URL" --dry-run

echo ""
echo "=== Variables Example ==="
"$TESTQL" run "$ROOT_DIR/examples/testtoon-basics/variables.testql.toon.yaml" --url "$URL" --dry-run

echo ""
echo "=== Assertions Example ==="
"$TESTQL" run "$ROOT_DIR/examples/testtoon-basics/assertions.testql.toon.yaml" --url "$URL" --dry-run

echo ""
echo "All TestTOON examples completed."
