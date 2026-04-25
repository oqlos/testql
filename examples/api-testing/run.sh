#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TESTQL="$ROOT_DIR/venv/bin/testql"
if [ ! -x "$TESTQL" ]; then TESTQL="testql"; fi

set -euo pipefail

URL="${1:-http://localhost:8101}"
DRY_RUN=""

if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN="--dry-run"
  URL="http://localhost:8101"
fi
if [ "${2:-}" = "--dry-run" ]; then
  DRY_RUN="--dry-run"
fi

echo "=== API Health Check ==="
"$TESTQL" run "$ROOT_DIR/examples/api-testing/health-check.testql.toon.yaml" --url "$URL" $DRY_RUN

echo ""
echo "=== CRUD Workflow ==="
"$TESTQL" run "$ROOT_DIR/examples/api-testing/crud-workflow.testql.toon.yaml" --url "$URL" $DRY_RUN

echo ""
echo "All API tests completed."
