#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TESTQL="testql"
if ! command -v "$TESTQL" >/dev/null 2>&1; then
  TESTQL="python3 -m testql"
fi

DRY_RUN=""
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN="--dry-run"
fi

echo "=== Test Math Module ==="
$TESTQL run "$ROOT_DIR/examples/unit-testing/test-math.oql" $DRY_RUN

echo ""
echo "=== Pytest Suite ==="
$TESTQL run "$ROOT_DIR/examples/unit-testing/test-pytest.oql" $DRY_RUN

echo ""
echo "All unit test examples completed."
