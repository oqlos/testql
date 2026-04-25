#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "=== Basic Commands Test ==="
testql run "$ROOT_DIR/examples/shell-testing/basic-commands.iql" --dry-run

echo ""
echo "=== File Operations Test ==="
testql run "$ROOT_DIR/examples/shell-testing/file-operations.iql" --dry-run

echo ""
echo "All shell tests completed."
