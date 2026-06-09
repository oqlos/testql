#!/usr/bin/env bash
# Run all desktop E2E scenarios (requires DISPLAY=:0, testql venv active).
set -euo pipefail
cd "$(dirname "$0")/../.."
export DISPLAY="${DISPLAY:-:0}"

run() {
  echo ""
  echo "========== $1 =========="
  testql run "$1"
}

run examples/desktop/gui-e2e-inspect.oql
run examples/desktop/gui-e2e-interact.oql
run examples/desktop/gui-e2e-multi-monitor.oql

echo ""
echo "All desktop E2E scenarios passed."
