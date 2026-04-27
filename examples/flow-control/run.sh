#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TESTQL="$ROOT_DIR/venv/bin/testql"
if [ ! -x "$TESTQL" ]; then TESTQL="testql"; fi

set -euo pipefail

DRY_RUN="--dry-run"
if [ "${1:-}" = "--live" ]; then
  DRY_RUN=""
fi

echo "=== Variables Test ($([ -n "$DRY_RUN" ] && echo dry-run || echo live)) ==="
"$TESTQL" run "$ROOT_DIR/examples/flow-control/variables.oql" $DRY_RUN

echo ""
echo "All flow control examples completed."
