#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TESTQL="$ROOT_DIR/venv/bin/testql"
if [ ! -x "$TESTQL" ]; then TESTQL="testql"; fi

set -euo pipefail

echo "=== Basic Commands Test ===="
"$TESTQL" run "$ROOT_DIR/examples/shell-testing/basic-commands.oql" --dry-run

echo ""
echo "=== File Operations Test ==="
"$TESTQL" run "$ROOT_DIR/examples/shell-testing/file-operations.oql" --dry-run

echo ""
echo "All shell tests completed."
