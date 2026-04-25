#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TESTQL="$ROOT_DIR/venv/bin/testql"
if [ ! -x "$TESTQL" ]; then TESTQL="testql"; fi

set -euo pipefail

DRY_RUN=""

if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN="--dry-run"
fi

echo "=== Login Form Test ==="
"$TESTQL" run "$ROOT_DIR/examples/gui-testing/login-form.iql" $DRY_RUN

echo ""
echo "=== Search Workflow ==="
"$TESTQL" run "$ROOT_DIR/examples/gui-testing/search-workflow.iql" $DRY_RUN

echo ""
echo "All GUI tests completed."
