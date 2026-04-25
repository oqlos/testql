#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
URL="${1:-http://localhost:8101}"

echo "=== API Health Check ==="
testql run "$ROOT_DIR/examples/api-testing/health-check.testql.toon.yaml" --url "$URL"

echo ""
echo "=== CRUD Workflow ==="
testql run "$ROOT_DIR/examples/api-testing/crud-workflow.testql.toon.yaml" --url "$URL"

echo ""
echo "All API tests completed."
