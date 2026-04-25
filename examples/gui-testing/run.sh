#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DRY_RUN=""

if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN="--dry-run"
fi

echo "=== Login Form Test ==="
testql run "$ROOT_DIR/examples/gui-testing/login-form.iql" $DRY_RUN

echo ""
echo "=== Search Workflow ==="
testql run "$ROOT_DIR/examples/gui-testing/search-workflow.iql" $DRY_RUN

echo ""
echo "All GUI tests completed."
