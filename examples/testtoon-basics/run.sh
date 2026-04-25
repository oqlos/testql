#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
URL="${1:-http://localhost:8101}"

echo "=== Minimal Example ==="
testql run "$ROOT_DIR/examples/testtoon-basics/minimal.testql.toon.yaml" --url "$URL" --dry-run

echo ""
echo "=== Variables Example ==="
testql run "$ROOT_DIR/examples/testtoon-basics/variables.testql.toon.yaml" --url "$URL" --dry-run

echo ""
echo "=== Assertions Example ==="
testql run "$ROOT_DIR/examples/testtoon-basics/assertions.testql.toon.yaml" --url "$URL" --dry-run

echo ""
echo "All TestTOON examples completed."
